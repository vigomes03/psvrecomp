#!/usr/bin/env python
"""REA local worker harness: a local Ollama model investigates a binary with REA,
under a contract enforced by code (not by the prompt).

Contract enforced:
  * the model can only act through the tools `rea` and `finish`;
  * `finish` is refused before MIN_CALLS successful REA calls;
  * every ev_... id cited in the report must come from a real REA call in this run;
  * the report must contain the required sections;
  * on refusal the model gets the exact reason (max 3 refusals, then FAIL).
Exit code 0 = report accepted (still to be reviewed by Claude), 2 = contract failure.

Usage:
  python tools/rea/rea_worker.py --target "D:\\Dev\\REA\\lab\\targets\\x.exe" \
      --question "Which function calls LookupAccountSidW and what does it do?" \
      --out D:\\Dev\\REA\\lab\\reports\\x-topic.md [--model qwen3-coder-64k] [--max-steps 14]
"""
import argparse, json, os, re, subprocess, sys, time, urllib.request
from pathlib import Path

NODE = r"C:\Program Files\nodejs\node.exe"
REA = r"D:\Dev\REA\rea-main\rea-main\scripts\rea.mjs"
ENV = {**os.environ,
       "GHIDRA_INSTALL_DIR": r"D:\Tools\ghidra_12.1.4_PUBLIC",
       "JAVA_HOME": r"D:\Tools\jdk-21.0.12.1+1",
       # real Windows temp dirs: an MSYS shell exports TMP=/tmp, which REA's native addon rejects
       "TMP": os.path.join(os.environ["LOCALAPPDATA"], "Temp"),
       "TEMP": os.path.join(os.environ["LOCALAPPDATA"], "Temp")}
OLLAMA = "http://127.0.0.1:11434/api/chat"
ALLOWED = {"analyze", "search", "xrefs", "function", "decompile", "callers"}
MIN_CALLS = 3
MAX_TOOL_CHARS = 7000
SECTIONS = ["## Observado", "## Inferido", "## Falhas"]
EV_RE = re.compile(r"ev_[0-9a-f]{16,64}")
SYM_RE = re.compile(r"\b(?:FUN|LAB|DAT)_[0-9a-fA-F]{6,}\b|\b0x[0-9a-fA-F]{6,}\b")

TOOLS = [
    {"type": "function", "function": {
        "name": "rea",
        "description": (
            "Run one REA (Ghidra) query on the target. Takes ~20 s per underlying query. Commands: "
            "callers (arg = API/function NAME like LookupAccountSidW, or an address): BEST FIRST STEP - finds the "
            "function, its references and the functions that contain each call site (name, entry address, signature); "
            "analyze (overview: segments, counts); "
            "search (arg = text; strings by default, add kind='procedures' to search function/import names); "
            "xrefs (arg = address or symbol, e.g. EXTERNAL:0x4): who references it. NOTE: xrefs of a STRING address only gives references to that text, not calls to the API; "
            "function (arg = address or name): the function CONTAINING that address, with signature, pseudocode, assembly; "
            "decompile (arg = function name or entry address): pseudocode only. "
            "Long outputs are cut; call again with offset=2000, 4000... to read further."),
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "enum": sorted(ALLOWED)},
            "arg": {"type": "string", "description": "pattern / address / function name (not used by analyze)"},
            "kind": {"type": "string", "enum": ["strings", "procedures"], "description": "only for search"},
            "offset": {"type": "integer", "description": "token offset for long outputs (0, 2000, 4000...)"}},
            "required": ["command"]}}},
    {"type": "function", "function": {
        "name": "finish",
        "description": "Submit the final markdown report. Refused if it cites evidence ids you did not receive.",
        "parameters": {"type": "object", "properties": {
            "report": {"type": "string", "description": "complete markdown report"}},
            "required": ["report"]}}},
]

SYSTEM = """Você é um analista de engenharia reversa trabalhando SOMENTE com a ferramenta `rea`.
Você ainda não sabe nada sobre o alvo. Tudo o que afirmar precisa vir de uma saída de `rea`.
Método: callers (nome da API) -> decompile na função que contém a chamada (use o nome FUN_... ou o endereço de entrada que `callers` mostrou) -> ler o pseudocódigo -> se preciso, callers dessa função para subir na cadeia.
Uma string com o nome da API (search de strings) NÃO é a função; use kind=procedures ou callers.
Endereços em .rdata são tabela de import (não são código); código fica em .text.
Faça UMA chamada de ferramenta por vez e leia o resultado antes da próxima.
Ao terminar, chame `finish` com um relatório markdown contendo exatamente estas seções:
# <alvo>: <tema>
## Pergunta
## Observado        (cada item termina com o evidence_id real entre parênteses)
## Código relevante (trecho copiado da saída, sem inventar)
## Inferido         (interpretação, citando os evidence_id em que se baseia)
## Falhas / perguntas em aberto
Nunca invente endereço, nome, string ou código. "Não encontrei" é uma resposta válida."""


def rea_json(target, cmd, arg=None, kind=None):
    """Run one REA CLI command; return (dict_or_None, error_text_or_None)."""
    argv = [NODE, REA, cmd, target]
    if cmd == "analyze":
        argv += ["--provider", "ghidra"]
    elif arg:
        argv.append(str(arg))
    if cmd == "search" and kind:
        argv += ["--kind", kind]
    argv += ["--format", "json"]
    try:
        p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=ENV, timeout=600)
    except subprocess.TimeoutExpired:
        return None, "ERROR: REA timed out after 600 s"
    try:
        j = json.loads(p.stdout)
    except Exception:
        return None, f"ERROR: REA exit {p.returncode}: {(p.stdout + p.stderr)[:1500]}"
    if "error" in j and "evidence_id" not in j:
        issues = "; ".join(i.get("message", "") for i in (j.get("details") or {}).get("issues", []))
        return None, f"ERROR ({j.get('code')}): {j.get('message')} {issues}"[:1500]
    return j, None


def lean(j):
    return {"evidence_id": j.get("evidence_id"), "confidence": j.get("confidence"),
            "result": j.get("normalized_result")}


def callers(target, arg):
    """Composite: name/address -> xrefs -> containing functions (name, entry, signature)."""
    ids, lines = [], []
    addrs = []
    if arg.startswith(("0x", "EXTERNAL:")):
        addrs = [arg]
    else:
        j, err = rea_json(target, "search", arg, "procedures")
        if err: return err, ids
        ids.append(j["evidence_id"])
        hits = j.get("normalized_result") or []
        lines.append(f"procedures matching '{arg}' ({j['evidence_id']}): " + json.dumps(hits)[:800])
        addrs = [h["address"] for h in hits][:3]
    for ad in addrs:
        x, err = rea_json(target, "xrefs", ad)
        if err: lines.append(f"xrefs {ad}: {err}"); continue
        ids.append(x["evidence_id"])
        refs = x.get("normalized_result") or []
        lines.append(f"xrefs to {ad} ({x['evidence_id']}): {refs}")
        for r in refs[:6]:
            f, err = rea_json(target, "function", r)
            if err:
                lines.append(f"  {r}: not inside a function (data/import table?) -> {err[:200]}"); continue
            ids.append(f["evidence_id"])
            p = (f.get("normalized_result") or {}).get("procedure", {})
            lines.append(f"  call site {r} is inside {p.get('name')} @ {p.get('address')} "
                         f"signature: {p.get('signature')} ({f['evidence_id']})")
    return "\n".join(lines) or "no results", ids


def run_rea(target, a, log):
    cmd = a.get("command")
    if cmd not in ALLOWED:
        return f"ERROR: command must be one of {sorted(ALLOWED)}"
    if cmd != "analyze" and not a.get("arg"):
        return "ERROR: this command needs `arg`"
    t0 = time.time()
    if cmd == "callers":
        out, _ = callers(target, str(a["arg"]))
    else:
        j, err = rea_json(target, cmd, a.get("arg"), a.get("kind"))
        if err:
            out = err
        else:
            body = lean(j)
            if cmd in ("function", "decompile"):
                proc = (j.get("normalized_result") or {})
                if isinstance(proc, dict) and "procedure" in proc:
                    pr = proc["procedure"]
                    body["result"] = {"name": pr.get("name"), "address": pr.get("address"),
                                      "signature": pr.get("signature"),
                                      "pseudocode": pr.get("pseudocode") or proc.get("pseudocode")}
            out = json.dumps(body, ensure_ascii=False, indent=1).replace("\\r\\n", "\n").replace("\\n", "\n")
    off = int(a.get("offset") or 0)
    log.write(json.dumps({"t": "rea", "args": a, "secs": round(time.time() - t0, 1),
                          "chars": len(out), "out": out[:20000]}, ensure_ascii=False) + "\n")
    chunk = out[off:off + MAX_TOOL_CHARS]
    if off + MAX_TOOL_CHARS < len(out):
        chunk += f"\n[cortado: mostrando {off}-{off+MAX_TOOL_CHARS} de {len(out)} chars; repita com offset={off+MAX_TOOL_CHARS}]"
    return chunk


def check_report(report, seen_ids, ok_calls, seen_text=""):
    problems = []
    low = seen_text.lower()
    ghosts = sorted({s for s in SYM_RE.findall(report) if s.lower() not in low})
    if ghosts:
        problems.append("estes nomes/endereços não aparecem em NENHUMA saída do REA (provável confusão entre "
                        "endereço de chamada e nome de função): " + ", ".join(ghosts) +
                        ". Um endereço de xrefs é o local da chamada; use `function <endereço>` para saber o nome da função que o contém.")
    if ok_calls < MIN_CALLS:
        problems.append(f"você fez só {ok_calls} chamadas REA bem-sucedidas; mínimo {MIN_CALLS}. Investigue mais antes de concluir.")
    cited = set(EV_RE.findall(report))
    if not cited:
        problems.append("o relatório não cita nenhum evidence_id.")
    fake = sorted(cited - seen_ids)
    if fake:
        problems.append("estes evidence_id NÃO vieram de nenhuma chamada sua (inventados ou copiados errado): " + ", ".join(fake))
    for s in SECTIONS:
        if s.lower() not in report.lower():
            problems.append(f"falta a seção '{s}'.")
    return problems


def chat(model, messages):
    body = json.dumps({"model": model, "messages": messages, "tools": TOOLS, "stream": False,
                       "options": {"temperature": 0.2}}).encode()
    req = urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--question", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="qwen3-coder-64k")
    ap.add_argument("--max-steps", type=int, default=14)
    a = ap.parse_args()
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    log = open(out.with_suffix(".log.jsonl"), "w", encoding="utf-8")
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Alvo: {a.target}\nPergunta: {a.question}\nComece com uma chamada `rea`."}]
    seen, ok_calls, refusals, t0 = set(), 0, 0, time.time()
    seen_text = a.target + "\n" + a.question
    stats = {"model": a.model, "rea_calls": 0, "llm_calls": 0, "prompt_tokens": 0, "eval_tokens": 0}
    for step in range(a.max_steps + 4):
        r = chat(a.model, messages)
        stats["llm_calls"] += 1
        stats["prompt_tokens"] += r.get("prompt_eval_count", 0)
        stats["eval_tokens"] += r.get("eval_count", 0)
        msg = r["message"]
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        log.write(json.dumps({"t": "llm", "content": msg.get("content", "")[:4000],
                              "tool_calls": calls}, ensure_ascii=False) + "\n"); log.flush()
        if not calls:
            messages.append({"role": "user", "content": "Use uma ferramenta: `rea` para investigar ou `finish` para entregar o relatório."})
            continue
        for c in calls[:1]:  # one action per turn
            fn, args = c["function"]["name"], c["function"].get("arguments") or {}
            if isinstance(args, str):
                try: args = json.loads(args)
                except Exception: args = {}
            if fn == "rea":
                if stats["rea_calls"] >= a.max_steps:
                    res = "ERROR: orçamento de chamadas REA esgotado. Chame `finish` agora com o que tem."
                else:
                    res = run_rea(a.target, args, log)
                    seen_text += "\n" + res
                    stats["rea_calls"] += 1
                    ids = set(EV_RE.findall(res))
                    if ids and "ERROR" not in res[:200]:
                        seen |= ids; ok_calls += 1
                print(f"[{time.time()-t0:6.0f}s] rea {args} -> {len(res)} chars, ids={len(seen)}", flush=True)
                messages.append({"role": "tool", "content": res})
            elif fn == "finish":
                report = args.get("report", "")
                problems = check_report(report, seen, ok_calls, seen_text)
                if not problems:
                    stats.update(secs=round(time.time() - t0), refusals=refusals, verdict="ACCEPTED_BY_HARNESS",
                                 cited_ids=sorted(set(EV_RE.findall(report))))
                    out.write_text(report + "\n\n<!-- harness: " + json.dumps(stats) + " -->\n", encoding="utf-8")
                    log.write(json.dumps({"t": "done", **stats}) + "\n")
                    print(json.dumps(stats, indent=1)); return 0
                refusals += 1
                print(f"[{time.time()-t0:6.0f}s] finish RECUSADO: {problems}", flush=True)
                log.write(json.dumps({"t": "refused", "problems": problems}, ensure_ascii=False) + "\n")
                if refusals >= 3:
                    break
                messages.append({"role": "tool", "content": "RELATÓRIO RECUSADO:\n- " + "\n- ".join(problems)})
            else:
                messages.append({"role": "tool", "content": f"ERROR: ferramenta desconhecida {fn}"})
    stats.update(secs=round(time.time() - t0), refusals=refusals, verdict="FAILED_CONTRACT")
    log.write(json.dumps({"t": "done", **stats}) + "\n")
    out.with_suffix(".FAILED.txt").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    print(json.dumps(stats, indent=1)); return 2


if __name__ == "__main__":
    sys.exit(main())
