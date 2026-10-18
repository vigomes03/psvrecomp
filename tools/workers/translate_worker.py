"""Chunked PT-BR -> English translation worker (local Ollama) with invariant checks enforced in code.

Why: one-shot whole-file translation by qwen truncated files (W22 t1/t2). This harness splits a text file into small
chunks (never inside a code fence), sends only the chunks that contain Portuguese, and accepts a chunk only if:
  * the line count is identical (keeps tables/lists aligned and makes review a line-by-line diff);
  * every inline-code span without Portuguese, every URL/link target and every number survives;
  * no Portuguese markers remain outside inline code.
Failed chunks are retried with the exact errors (max 3 attempts), then kept verbatim and listed in the report so
Claude finishes them. Output goes to --out; nothing is written over the source unless --out points at it.

Usage:
  python tools/workers/translate_worker.py --src docs/x.md --out lab/translate/docs/x.md [--model qwen3.8:27b]
Prints one JSON line: chunks, translated, failed (with line ranges and last errors), seconds.
"""
import argparse, json, re, sys, time, urllib.request
from collections import Counter
from pathlib import Path

PT_WORDS = (r"não|nao|também|então|está|estão|são|já|só|até|após|além|porém|através|você|vocês|é|à|às|ao|aos|"
            r"para|pelo|pela|pelos|pelas|com|uma|umas|uns|um|que|quando|onde|como|mas|ou|se|sem|nem|ainda|depois|"
            r"antes|cada|todo|toda|todos|todas|isso|isto|esse|essa|este|esta|aqui|ali|nosso|nossa|deve|precisa|"
            r"fica|ficam|tem|têm|foi|vai|ser|ter|fazer|feito|pronto|nunca|sempre|agora|mesmo|mesma|outro|outra|"
            r"da|dos|das|na|nos|nas|em|de|os")
PT_RE = re.compile(rf"\b({PT_WORDS})\b", re.I)
PT_STRONG = re.compile(r"ção|ções|ões|ãe|ão\b|[ãõç]|\b(não|também|então|está|são|já|só|até|após|você|pela|pelo|"
                       r"uma|para|quando|onde|depois|ainda|cada|todos|nosso|nossa|deve|precisa|fica|isso)\b", re.I)
ALLOW = re.compile(r"Pokémon|Pokemon|Pokédex|Violet|Scarlet", re.I)
CODE_SPAN = re.compile(r"`[^`\n]+`")
URL = re.compile(r"https?://[^\s)>\]]+|\]\(([^)\s]+)\)")
NUM = re.compile(r"\d+")

SYSTEM = (
    "You translate Brazilian Portuguese technical text (Markdown docs about reverse engineering, static recompilation "
    "and emulation) into clear US technical English. Rules: translate every Portuguese word of prose, headings, table "
    "cells and comments. Every input line starts with a tag like [7]; answer with exactly one output line per tag, "
    "starting with the same tag, in the same order. Never merge or split tagged lines, even when a sentence "
    "continues on the next tag. "
    "keep Markdown syntax, table pipes, list markers, indentation, emoji, code fences and their contents, inline code "
    "in backticks, paths, URLs, identifiers, environment variables, hex values, run_id values and every number exactly "
    "as written (do not reformat dates or decimal commas). Inline code that is itself Portuguese prose may be "
    "translated. Placeholders such as [USER] stay as they are. Do not add, drop, summarize or explain anything. "
    "Reply with the translation only, between the lines <<<BEGIN>>> and <<<END>>>."
)


def bare(line):
    return ALLOW.sub("", URL.sub("", CODE_SPAN.sub("", line)))


def pt_score(line):
    bare_ = bare(line)
    return len(PT_STRONG.findall(bare_)) * 2 + len(PT_RE.findall(bare_))


def has_pt(text):
    return any(pt_score(l) >= 3 or PT_STRONG.search(bare(l)) for l in text.splitlines())


def chunks(lines, max_lines=20, max_chars=3000):
    """Split into chunks at blank lines / headings, never inside a ``` fence."""
    out, cur, size, fence = [], [], 0, False
    for l in lines:
        boundary = not fence and (not l.strip() or l.startswith("#"))
        if cur and boundary and (len(cur) >= max_lines or size >= max_chars):
            out.append(cur); cur, size = [], 0
        elif cur and not fence and size + len(l) > max_chars * 1.6:
            out.append(cur); cur, size = [], 0
        cur.append(l); size += len(l)
        if l.lstrip().startswith("```"):
            fence = not fence
    if cur:
        out.append(cur)
    return out


def check(src, dst):
    errs = []
    s, d = src.split("\n"), dst.split("\n")
    if len(s) != len(d):
        errs.append(f"line count {len(d)} but the input has {len(s)}; return exactly one line per input line")
    keep = [c for c in CODE_SPAN.findall(src) if not PT_STRONG.search(c)]
    missing = [c for c in keep if c not in dst]
    if missing:
        errs.append("inline code changed or dropped (copy verbatim): " + ", ".join(missing[:8]))
    urls = [m.group(0) for m in URL.finditer(src)]
    gone = [u for u in urls if u not in dst]
    if gone:
        errs.append("link/URL targets changed: " + ", ".join(gone[:6]))
    ns, nd = Counter(NUM.findall(src)), Counter(NUM.findall(dst))
    lost = ns - nd
    if lost:
        errs.append("numbers dropped or changed: " + ", ".join(list(lost.elements())[:10]))
    if len(s) == len(d):
        left = [i + 1 for i, l in enumerate(d) if pt_score(l) >= 3 or PT_STRONG.search(bare(l))]
        if left:
            errs.append("Portuguese still present on chunk lines " + ", ".join(map(str, left[:10])) + ": " +
                        " | ".join(d[i - 1].strip()[:80] for i in left[:3]))
        for i, (a, b) in enumerate(zip(s, d), 1):
            if a.strip().startswith("|") != b.strip().startswith("|") or a.count("|") != b.count("|") and a.strip().startswith("|"):
                errs.append(f"line {i}: table structure changed (pipes {a.count('|')} -> {b.count('|')})"); break
    return errs


TAG = re.compile(r"^\s*\[(\d+)\] ?(.*)$")


def tag(lines):
    return "\n".join(f"[{i}] {l.strip()}" for i, l in enumerate(lines, 1) if l.strip())


def untag(lines, reply):
    """Rebuild the chunk from tagged reply lines; returns (text, errors)."""
    got = {}
    for l in reply.split("\n"):
        m = TAG.match(l)
        if m:
            got.setdefault(int(m.group(1)), m.group(2))
    want = [i for i, l in enumerate(lines, 1) if l.strip()]
    missing = [i for i in want if i not in got]
    extra = sorted(set(got) - set(want))
    errs = []
    if missing:
        errs.append("missing tags " + ", ".join(f"[{i}]" for i in missing[:15]) + ": answer every tag exactly once")
    if extra:
        errs.append("unknown tags " + ", ".join(f"[{i}]" for i in extra[:10]))
    out = [(l[:len(l) - len(l.lstrip())] + got.get(i, l).strip()) if l.strip() else l for i, l in enumerate(lines, 1)]
    return "\n".join(out), errs


def ask(host, model, num_ctx, text, errs, prev):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Translate these tagged lines:\n<<<BEGIN>>>\n{text}\n<<<END>>>"}]
    if errs:
        msgs += [{"role": "assistant", "content": f"<<<BEGIN>>>\n{prev}\n<<<END>>>"},
                 {"role": "user", "content": "REJECTED. Fix exactly these problems and resend the full chunk:\n- " +
                  "\n- ".join(errs)}]
    body = {"model": model, "stream": False, "keep_alive": "10m", "think": False,
            "options": {"num_ctx": num_ctx, "temperature": 0.1, "repeat_penalty": 1.05}, "messages": msgs}
    req = urllib.request.Request(host + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        out = json.loads(r.read())["message"]["content"]
    m = re.search(r"<<<BEGIN>>>\n?(.*?)\n?<<<END>>>", out, re.S)
    body = m.group(1) if m else re.sub(r"^<<<BEGIN>>>\n?", "", out.strip())
    return body.strip("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="qwen3.8:27b")
    ap.add_argument("--num-ctx", type=int, default=16384)
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--tries", type=int, default=3)
    a = ap.parse_args()

    raw = Path(a.src).read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    t0, done, failed, out, pos = time.time(), 0, [], [], 1
    parts = chunks(lines)
    for part in parts:
        first, pos = pos, pos + len(part)
        lead = next((i for i, l in enumerate(part) if l.strip()), len(part))
        trail = next((i for i, l in enumerate(reversed(part)) if l.strip()), 0)
        core = part[lead:len(part) - trail]
        text = "\n".join(core)
        pad = lambda t: "\n".join([""] * lead + ([t] if core else []) + [""] * trail)
        if not core or not has_pt(text):
            out.append("\n".join(part)); continue
        prev, errs, reply = "", [], ""
        for _ in range(a.tries):
            reply = ask(a.host, a.model, a.num_ctx, tag(core), errs, reply)
            prev, errs = untag(core, reply)
            errs += check(text, prev)
            if not errs:
                break
        if errs:
            failed.append({"lines": f"{first}-{pos - 1}", "errors": errs})
            out.append("\n".join(part))
        else:
            done += 1
            out.append(pad(prev))
        print(f"  chunk {first}-{pos - 1}: {'ok' if not errs else 'FAILED'}", file=sys.stderr, flush=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_bytes("\n".join(out).replace("\n", nl).encode("utf-8"))
    print(json.dumps({"src": a.src, "out": a.out, "chunks": len(parts), "translated": done, "failed": failed,
                      "seconds": round(time.time() - t0, 1), "model": a.model}, ensure_ascii=False))
    return 0 if not failed else 3


if __name__ == "__main__":
    sys.exit(main())
