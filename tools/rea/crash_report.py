#!/usr/bin/env python3
"""Readable crash report from a PSV Recomp log (window.log, psvrecomp.log or crashes/crash_*.log).

usage: crash_report.py <log> [--host-dir D:/Dev/REA/lab/host-vk]

Prints the error line, the host backtrace with each frame named (pvgame.dll+off -> generated function f_<guest addr>,
psvrecomp/pvhost+off -> runtime function), the guest backtrace the runtime already resolved, and the last lines the game
logged before the crash (scene, frame rate, input). Symbols come from nm on pvgame.dll / pvhost.exe of --host-dir, so
use the same build that crashed.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpuprof_report as cp  # noqa: E402  (nm-based symbol tables)


def main():
    a = sys.argv[1:]
    host = "D:/Dev/REA/lab/host-vk"
    if "--host-dir" in a:
        i = a.index("--host-dir"); host = a[i + 1]; del a[i:i + 2]
    log = a[0]
    text = open(log, encoding="utf-8", errors="replace").read()
    lines = text.splitlines()
    idx = None
    for i, l in enumerate(lines):
        if l.startswith("FATAL: ") or l.startswith("*** "):
            idx = i
            break
    if idx is None:
        print("no FATAL / exception line in", log)
        return 1
    print("== error")
    print(lines[idx])
    for l in lines[idx + 1:idx + 3]:
        if l.startswith("    host "):
            print(l)
    game = cp.symbols(os.path.join(host, "pvgame.dll"))
    hostsyms = cp.symbols(os.path.join(host, "pvhost.exe"))
    print("\n== host backtrace (named)")
    for l in lines[idx:idx + 60]:
        m = re.match(r"\s*#(\d+)\s+[0-9a-f]+\s+(\S+)\+([0-9a-f]+)", l)
        if not m:
            continue
        mod, off = m.group(2), int(m.group(3), 16)
        if mod.lower().startswith("pvgame"):
            name = cp.lookup(game, off)
        elif mod.lower() in ("psvrecomp", "pvhost", "pvhost.exe", "psvrecomp.exe"):
            name = "host:" + cp.lookup(hostsyms, off)
        else:
            name = mod
        print(f"  #{m.group(1):<3} {mod}+{off:x}  {name}")
    g = [l for l in lines[max(0, idx - 40):idx + 80] if l.strip().startswith("guest #")]
    if g:
        print("\n== guest backtrace (from the log)")
        for l in g:
            print(" ", l.strip())
    print("\n== last log lines before the error")
    ctx = [l for l in lines[max(0, idx - 400):idx]
           if l.startswith(("[vk] t=", "[input] t=", "[frametime]", "[diag]", "[lm]", "[kernel]")) or "ERROR" in l]
    for l in ctx[-12:]:
        print(" ", l[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
