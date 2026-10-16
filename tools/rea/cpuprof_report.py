#!/usr/bin/env python3
"""Report for runtime/cpuprof.c (PVR_CPUPROF=<from>:<to>): where the game threads spend CPU time.

usage: cpuprof_report.py <cpuprof.txt> <pvgame.dll> <pvhost.exe> [--top N]

Samples in pvgame.dll are named by the generated function (f_<guest addr>); samples in pvhost.exe by runtime
function; anything else (ntdll waits, CRT memcpy, vulkan driver) by module. For samples outside pvgame.dll the
guest caller (x30 at sample time, resolved to its f_<addr>) is shown too.
"""
import bisect
import collections
import re
import subprocess
import sys

NM = r"D:\msys64\ucrt64\bin\nm.exe"
OBJDUMP = r"D:\msys64\ucrt64\bin\objdump.exe"


def image_base(path):
    out = subprocess.run([OBJDUMP, "-p", path], capture_output=True, text=True).stdout
    m = re.search(r"^ImageBase\s+([0-9a-fA-F]+)", out, re.M)
    return int(m.group(1), 16)


def symbols(path):
    """sorted (rva, name) of text symbols"""
    base = image_base(path)
    out = subprocess.run([NM, "--defined-only", path], capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        p = line.split()
        if len(p) == 3 and p[1] in "tT" and not p[2].startswith("."):
            rows.append((int(p[0], 16) - base, p[2]))
    rows.sort()
    return [r[0] for r in rows], [r[1] for r in rows]


def lookup(tab, rva):
    addrs, names = tab
    i = bisect.bisect_right(addrs, rva) - 1
    return names[i] if i >= 0 else "?"


def main():
    a = sys.argv[1:]
    top = 25
    if "--top" in a:
        i = a.index("--top"); top = int(a[i + 1]); del a[i:i + 2]
    prof, game_dll, host_exe = a
    game, host = symbols(game_dll), symbols(host_exe)
    guest_fns = sorted(int(n[2:], 16) for n in game[1] if re.fullmatch(r"f_[0-9a-f]+", n))

    def guest_name(lr):
        if not lr:
            return ""
        i = bisect.bisect_right(guest_fns, lr - 4) - 1
        return f"f_{guest_fns[i]:x}" if i >= 0 else f"?{lr:x}"

    threads, per_t, per_fn, per_helper = {}, collections.Counter(), collections.Counter(), collections.Counter()
    per_t_fn = collections.defaultdict(collections.Counter)
    for line in open(prof):
        p = line.split()
        if p[0] == "T":
            threads[int(p[1])] = " ".join(p[2:])
            continue
        t, mod, rva, lr, n = int(p[1]), p[2], int(p[3], 16), int(p[4], 16), int(p[5])
        if mod.lower() == "pvgame.dll":
            fn = lookup(game, rva)
        elif mod.lower() == "pvhost.exe":
            fn = "host:" + lookup(host, rva)
        else:
            fn = mod
        per_t[t] += n
        per_fn[fn] += n
        per_t_fn[t][fn] += n
        if mod.lower() != "pvgame.dll":
            per_helper[(fn, guest_name(lr))] += n
    total = sum(per_t.values()) or 1
    print(f"{total} samples")
    print("\n== threads (samples ~ ms of CPU or wait; 'ntdll/KERNELBASE' = blocked)")
    for t, n in per_t.most_common():
        busy = n - sum(v for k, v in per_t_fn[t].items() if k.lower() in ("ntdll.dll", "kernelbase.dll", "win32u.dll"))
        top3 = ", ".join(f"{k} {100 * v / n:.0f}%" for k, v in per_t_fn[t].most_common(3))
        print(f"T{t:<3} {threads.get(t, '')}  running {100 * busy / n:5.1f}%  | {top3}")
    print(f"\n== top {top} functions (all threads)")
    for fn, n in per_fn.most_common(top):
        print(f"{100 * n / total:6.2f}%  {n:7d}  {fn}")
    print(f"\n== top {top} runtime/library samples by guest caller")
    for (fn, caller), n in per_helper.most_common(top):
        print(f"{100 * n / total:6.2f}%  {n:7d}  {fn}  <- {caller}")


if __name__ == "__main__":
    main()
