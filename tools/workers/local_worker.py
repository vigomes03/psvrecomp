"""Local code worker (Ollama) for the REA project: Claude writes a task card, a local qwen produces ONE file.

Claude writes a card (markdown) with a verifiable contract; this script sends card + context files to the local
model and writes the produced file. Claude then verifies (compiler / tests / differential check) and accepts,
retries with the exact errors (max 3), or finishes it editorially. Never install a worker file unverified.

Usage:
  python tools/workers/local_worker.py --task work/cards/W01-x.md --out path/to/file.py \
      [--ctx a.py b.h] [--lang python] [--model qwen3.8:27b] [--num-ctx 32768]
Output: writes --out and prints JSON stats (tokens, tok/s, seconds). Exit 0 = a code block was found.
"""
import argparse, json, re, sys, time, urllib.request
from pathlib import Path

SYSTEM = (
    "You are a senior systems programmer (C, C++, Python, AArch64, reverse engineering) working as a worker in a "
    "pipeline supervised by another engineer who will compile, test and review your output. Follow the task card "
    "exactly. Use only the APIs, types and functions shown in the card or the context files, or the language's "
    "standard library; never invent helpers, addresses, offsets, symbols or file formats. If something you need is "
    "missing, write `TODO(worker): <what is missing>` at that spot instead of guessing. "
    "Reply with exactly ONE complete file inside a single fenced code block in the language the card asks for. "
    "No explanations outside the code block."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ctx", nargs="*", default=[])
    ap.add_argument("--lang", default="", help="hint appended to the prompt, e.g. python / c / cpp")
    ap.add_argument("--model", default="qwen3.8:27b")
    ap.add_argument("--num-ctx", type=int, default=32768)
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--repeat-penalty", type=float, default=1.1)
    a = ap.parse_args()

    parts = [Path(a.task).read_text(encoding="utf-8")]
    for c in a.ctx:
        parts.append(f"\n--- CONTEXT FILE: {c} ---\n" + Path(c).read_text(encoding="utf-8", errors="replace"))
    if a.lang:
        parts.append(f"\nAnswer with one ```{a.lang} code block.")
    body = {
        "model": a.model, "stream": False, "keep_alive": "5m", "think": False,
        "options": {"num_ctx": a.num_ctx, "temperature": a.temperature, "repeat_penalty": a.repeat_penalty},
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "\n".join(parts)}],
    }
    t0 = time.time()
    req = urllib.request.Request(a.host + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        resp = json.loads(r.read())
    dt = time.time() - t0
    text = resp["message"]["content"]
    m = re.findall(r"```[a-zA-Z0-9#+_-]*\n(.*?)```", text, re.S)
    code = max(m, key=len) if m else text
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(code.strip() + "\n", encoding="utf-8")
    ev = resp.get("eval_count", 0)
    evd = resp.get("eval_duration", 1) / 1e9
    print(json.dumps({"ok": bool(m), "out": a.out, "lines": code.count("\n") + 1,
                      "todo_markers": code.count("TODO(worker)"),
                      "prompt_tokens": resp.get("prompt_eval_count"), "gen_tokens": ev,
                      "gen_tok_s": round(ev / evd, 1) if evd else None, "seconds": round(dt, 1),
                      "model": a.model}))
    return 0 if m else 2


if __name__ == "__main__":
    sys.exit(main())
