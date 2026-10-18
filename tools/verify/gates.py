"""Gates: the only accepted proof that something works in the PVRecomp pipeline.

Every claim ("compiles", "boot OK", "phase N done") must point at a gate RUN recorded here. A gate runs the real
command itself, checks the real artifacts/logs in code and appends one JSON line to work/evidence/gates.jsonl with
git HEAD, exit code, artifact hashes and the checks it made. Nobody (Claude or qwen) writes that file by hand.

  python tools/verify/gates.py run <gate> [--agent claude|qwen] [--min-stage S]   run one gate, record evidence
  python tools/verify/gates.py claim <gate> --agent qwen --text "boot OK" [--expect pass|stage:S]
        record what an agent CLAIMED, run the gate, and score the claim (true / false) in work/evidence/claims.jsonl
  python tools/verify/gates.py score                       claims per agent: verified / false / false-rate
  python tools/verify/gates.py lint [--staged]             fake detector (scripts that only echo success, docs that
                                                           claim completion without a gate run id); used by pre-commit
  python tools/verify/gates.py list                        gates and their checks

Gates: dumps, host, link, boot, simd, excl_pair. `boot` reports the furthest stage reached (see STAGES).
"""
import argparse, datetime, hashlib, json, os, re, shutil, subprocess, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / "work" / "evidence"
GATES_LOG, CLAIMS_LOG = EVID / "gates.jsonl", EVID / "claims.jsonl"
PD = ROOT / "psvrecomp"
RECOMP = PD / "recomp"
LAB = ROOT / "lab"
GENFULL, HOST = LAB / "genfull", LAB / "host"
BASH = shutil.which("bash") or r"C:\Program Files\Git\bin\bash.exe"
VENV_PY = RECOMP / "venv" / "Scripts" / "python.exe"

# Boot stages, in order. Each is (name, regex that must appear in boot.log).
STAGES = [
    ("dll_loaded", r"^pvgame: .* (\d+) modules, (\d+) functions"),
    ("modules_loaded", r"^loaded sdk "),
    ("relocated", r"^relocated sdk "),
    ("main_thread", r"^main thread: prio"),
    ("init_sdk", r"^init sdk "),
    ("init_subsdk0", r"^init subsdk0 "),
    ("init_main", r"^init main "),
    ("nnmain_started", r"^init main [\s\S]*?\[sm\] GetService"),  # the game itself asks for services
    ("romfs_read", r"\[fs\] romfs reads"),
    ("frame_presented", r"^\[nvn-null\] present #1 "),  # first frame handed to (null) presentation
    ("frames_60", r"^\[nvn-null\] present #64 "),
    ("nnmain_returned", r"nnMain returned"),
    ("survived_time_limit", r"time limit reached"),
]
STAGE_NAMES = [s for s, _ in STAGES]


def sh(cmd, cwd=None, timeout=3600, env=None):
    """Run a bash command; return (exit, combined output). Never hides the exit code."""
    p = subprocess.run([BASH, "-c", cmd], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def sha256(path, limit=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def git_head():
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    d = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True)
    return r.stdout.strip(), bool(d.stdout.strip())


def mpath(p):  # Windows path with forward slashes for bash/clang
    return str(p).replace("\\", "/")


# PATH with the MSYS2 toolchain + a Windows TMP for clang (bash snippet prefix)
ENV_MSYS = r'export PATH="/d/msys64/ucrt64/bin:$PATH" TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" ' \
           r'TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"; '


def bpath(p):  # MSYS path for bash scripts that call cygpath
    s = mpath(p)
    return "/" + s[0].lower() + s[2:] if re.match(r"^[A-Za-z]:/", s) else s


class Gate:
    def __init__(self):
        self.checks, self.artifacts, self.info, self.out = [], {}, {}, ""

    def check(self, name, ok, detail=""):
        self.checks.append({"check": name, "ok": bool(ok), "detail": str(detail)[:300]})
        return ok

    def artifact(self, path, hash_it=True):
        p = Path(path)
        if p.exists():
            self.artifacts[mpath(p.relative_to(ROOT)) if ROOT in p.parents else mpath(p)] = {
                "bytes": p.stat().st_size, "sha256": sha256(p) if hash_it else None,
                "mtime": datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")}
        return p.exists()


# ---------------------------------------------------------------- gates
def g_dumps(g, a):
    ver = a.version or "base"
    ex = ROOT / "dumps" / ver / "exefs"
    for m in ["main", "sdk", "subsdk0", "main.npdm"]:
        if g.check(f"exefs/{m} exists", (ex / m).exists(), ex / m):
            g.artifact(ex / m)
    rom = ROOT / "dumps" / ver / "romfs"
    n = sum(1 for _ in rom.rglob("*") if _.is_file()) if rom.exists() else 0
    size = sum(f.stat().st_size for f in rom.rglob("*") if f.is_file()) if rom.exists() else 0
    g.info.update(romfs_files=n, romfs_bytes=size)
    g.check("romfs non-empty", n > 0 and size > 1 << 30, f"{n} files, {size} bytes")
    # Pin: the first recorded hashes of a version are the reference; later runs must match them.
    ref = EVID / f"dumps-{ver}.json"
    cur = {k: v["sha256"] for k, v in g.artifacts.items()}
    if ref.exists():
        old = json.loads(ref.read_text())
        g.check("exefs hashes match pinned reference", old == cur, f"pinned {ref.name}")
    elif cur and all(c["ok"] for c in g.checks):
        ref.write_text(json.dumps(cur, indent=1))
        g.info["pinned"] = ref.name


def dirs(a):
    """Per dump version: base keeps lab/genfull + lab/host; others use lab/gen-<v> + lab/host-<v>."""
    v = getattr(a, "version", "base") or "base"
    return (GENFULL, HOST) if v == "base" else (LAB / f"gen-{v}", LAB / f"host-{v}")


def runtime_source_manifest():
    """Fingerprint owned runtime inputs, not merely the output timestamp."""
    files = [RECOMP / "build_host.sh"]
    for folder in (PD / "runtime", PD / "third_party" / "imgui"):
        files.extend(p for p in folder.rglob("*") if p.suffix in (".c", ".cpp", ".h", ".inc"))
    vma = ROOT / "ref/LASRecomp-main/LASRecomp-main/runtime/nvn/vulkan/vma.cpp"
    if vma.is_file():
        files.append(vma)
    return {mpath(p.relative_to(ROOT)): sha256(p) for p in sorted(set(files)) if p.is_file()}


def host_build_provenance(host, records=None):
    """Return the matching Vulkan build run id, or reject unknown/stale inputs."""
    exe = Path(host) / "pvhost.exe"
    if not exe.is_file():
        return None
    current, binary_hash = runtime_source_manifest(), sha256(exe)
    key = mpath(exe.relative_to(ROOT))
    records = list(known_runs().values()) if records is None else list(records)
    for record in reversed(records):
        info = record.get("info", {})
        artifact = record.get("artifacts", {}).get(key, {})
        if (record.get("gate") == "host" and record.get("pass") and info.get("backend") == "vulkan"
                and artifact.get("sha256") == binary_hash and info.get("runtime_sources") == current):
            return record["run_id"]
    return None


def g_host(g, a):
    GENFULL, HOST = dirs(a)
    backend = getattr(a, "backend", "null")
    if backend == "vulkan":
        HOST = LAB / "host-vk-auto"
    g.info.update(backend=backend, version=a.version, host_dir=mpath(HOST),
                  runtime_sources=runtime_source_manifest())
    HOST.mkdir(parents=True, exist_ok=True)
    for f in ["pvhost.exe", "pvhost.dll.a"]:
        (HOST / f).unlink(missing_ok=True)
    code, out = sh(f'bash build_host.sh "{bpath(HOST)}" {backend}', cwd=RECOMP, timeout=1200)
    g.out = out
    g.check("runtime sources unchanged during build", g.info["runtime_sources"] == runtime_source_manifest())
    g.check("build_host.sh exit 0", code == 0, f"exit {code}")
    g.check("no compiler errors", " error: " not in out and "error generated" not in out,
            "\n".join(l for l in out.splitlines() if "error" in l)[:300])
    for f in ["pvhost.exe", "pvhost.dll.a"]:
        g.check(f"{f} produced", g.artifact(HOST / f), HOST / f)


def g_link(g, a):
    GENFULL, HOST = dirs(a)
    backend = getattr(a, "backend", "null")
    if backend == "vulkan":
        HOST = LAB / "host-vk-auto"
    g.info.update(backend=backend, version=a.version, host_dir=mpath(HOST))
    (HOST / "pvgame.dll").unlink(missing_ok=True)
    objs = {d: len(list((GENFULL / d).glob("*.o"))) for d in ["obj", "obj_subsdk0", "obj_sdk"]}
    g.info["objs"] = objs
    g.check("generated objects present", all(objs.values()), objs)
    g.check("pvhost.dll.a present (run gate host first)", (HOST / "pvhost.dll.a").exists())
    # run_boot.sh links then boots; link-only: run with 0 s and ignore the boot part.
    code, out = sh(f'bash run_boot.sh "{bpath(GENFULL)}" "{bpath(HOST)}" 1 {a.version}', cwd=RECOMP, timeout=3600)
    g.out = out
    g.check("pvgame.dll produced", g.artifact(HOST / "pvgame.dll"), out[-300:])
    if (HOST / "pvgame.dll").exists():
        g.check("pvgame.dll > 100 MB", (HOST / "pvgame.dll").stat().st_size > 100 << 20)
        code, nm = sh(f'/d/msys64/ucrt64/bin/objdump -p "{mpath(HOST / "pvgame.dll")}" | grep -c pvgame_tables')
        g.check("exports pvgame_tables", nm.strip() not in ("", "0"), nm.strip())


def boot_stage(log):
    reached, last = {}, None
    for name, rx in STAGES:
        m = re.search(rx, log, re.M)
        reached[name] = bool(m)
        if m:
            last = name
    crash = re.search(r"\*\*\* exception (\w+) accessing (0x\w+)", log)
    fatal = re.search(r"^.*FATAL.*$", log, re.M)
    funcs = re.search(STAGES[0][1], log, re.M)
    return last, reached, crash.group(0) if crash else None, fatal.group(0) if fatal else None, \
        int(funcs.group(2)) if funcs else None


def stage_ok(last, reached, need):
    """The requested stage's OWN marker must be in the log, not just a later-ranked one. Ranking alone was a hole:
    a run that idled to the time limit without presenting a frame ranked above frames_60 and passed it (14/10)."""
    return last is not None and bool(reached.get(need)) and STAGE_NAMES.index(last) >= STAGE_NAMES.index(need)


def g_boot(g, a):
    """Boot headless; with --repeat N every one of N runs must reach the stage (boots are nondeterministic: threads)."""
    GENFULL, HOST = dirs(a)
    secs = a.seconds
    n = max(1, a.repeat)
    stages = []
    for i in range(n):
        (HOST / "boot.log").unlink(missing_ok=True)
        code, out = sh(f'bash run_boot.sh "{bpath(GENFULL)}" "{bpath(HOST)}" {secs} {a.version}', cwd=RECOMP,
                       timeout=secs + 3600)
        g.out += out
        log_p = HOST / "boot.log"
        tag = f"run {i + 1}/{n}: " if n > 1 else ""
        if not g.check(f"{tag}boot.log written by this run", log_p.exists()):
            return
        if n > 1:  # keep every run's log as evidence
            kept = HOST / f"boot_run{i + 1}.log"
            kept.write_bytes(log_p.read_bytes())
            g.artifact(kept)
        else:
            g.artifact(log_p)
        log = log_p.read_text(encoding="utf-8", errors="replace")
        last, reached, crash, fatal, funcs = boot_stage(log)
        stages.append(last)
        g.info.update(stage=last, stage_index=STAGE_NAMES.index(last) if last else -1, reached=reached,
                      crash=crash, fatal=fatal, functions=funcs, log_lines=log.count("\n"),
                      log_tail=log.splitlines()[-12:])
        needs = (a.min_stage or "survived_time_limit").split(",")  # comma list: every stage must be reached
        for need in needs:
            if need not in STAGE_NAMES:
                raise SystemExit(f"unknown stage {need!r}; stages: {STAGE_NAMES}")
            g.check(f"{tag}reached stage >= {need}", stage_ok(last, reached, need), f"reached {last}; {need} marker "
                    + ("present" if reached.get(need) else "ABSENT") + (f"; {fatal}" if fatal else ""))
        if "survived_time_limit" in needs:  # a partial-stage gate records the crash as info, not as a failed check
            g.check(f"{tag}no host exception", crash is None, crash or "")
            g.check(f"{tag}no FATAL", fatal is None, fatal or "")
    if n > 1:
        g.info.update(stages=stages, repeat=n)


def g_simd(g, a):
    code, out = sh(ENV_MSYS + f'"{bpath(VENV_PY)}" test_simd.py', cwd=RECOMP, timeout=3600)
    g.out = out
    m = re.search(r"(\d+)\s+fail", out, re.I)
    g.check("test_simd exit 0", code == 0, f"exit {code}")
    g.check("0 failures reported", bool(m) and m.group(1) == "0", m.group(0) if m else "no failure count in output")


def g_excl_pair(g, a):
    code, out = sh(f'"{bpath(VENV_PY)}" test_excl_pair.py', cwd=RECOMP, timeout=1200)
    g.out = out
    g.check("test_excl_pair exit 0", code == 0, f"exit {code}")


def g_nvn_null(g, a):
    """Card W03: runtime/nvn/null_backend.c against recomp/test_null_backend.c (-Wall -Werror)."""
    out = LAB / "w03"
    out.mkdir(parents=True, exist_ok=True)
    src = PD / "runtime" / "nvn" / "null_backend.c"
    if not g.check("null_backend.c installed", src.exists(), src):
        return
    g.artifact(src)
    exe, err = out / "test_null_backend.exe", out / "stderr.txt"
    code, o = sh(f'export PATH="/d/msys64/ucrt64/bin:$PATH" TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" '
                 f'TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"; clang -Wall -Werror -O1 '
                 f'-I"{mpath(PD / "runtime")}" -I"{mpath(PD / "runtime" / "nvn")}" "{mpath(RECOMP / "test_null_backend.c")}" '
                 f'"{mpath(src)}" -o "{mpath(exe)}"')
    g.out = o
    if not g.check("compiles with -Wall -Werror", code == 0, o[-300:]):
        return
    code, o = sh(f'"{mpath(exe)}" 2> "{mpath(err)}"')
    g.out += o
    g.check("test exit 0 and prints W03 PASS", code == 0 and "W03 PASS" in o, o.strip()[-200:])
    e = err.read_text(encoding="utf-8", errors="replace") if err.exists() else ""
    nums = re.findall(r"^\[nvn-null\] present #(\d+) \(", e, re.M)
    g.check("present logged for #1 #2 #4 only", nums == ["1", "2", "4"], nums)
    g.check("init line logged once", e.count("[nvn-null] headless backend (no rendering)") == 1)


def g_sdl_null(g, a):
    """Card W04: runtime/platform/sdl_audio_null.h against recomp/test_sdl_audio_null.c, then audio.c compiles."""
    out = LAB / "w04"
    out.mkdir(parents=True, exist_ok=True)
    hdr = PD / "runtime" / "platform" / "sdl_audio_null.h"
    if not g.check("sdl_audio_null.h installed", hdr.exists(), hdr):
        return
    g.artifact(hdr)
    env = ('export PATH="/d/msys64/ucrt64/bin:$PATH" TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" '
           'TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"; ')
    exe = out / "test_sdl_audio_null.exe"
    code, o = sh(env + f'clang -Wall -Werror -O1 -I"{mpath(hdr.parent)}" "{mpath(RECOMP / "test_sdl_audio_null.c")}" '
                 f'-o "{mpath(exe)}" && "{mpath(exe)}"')
    g.out = o
    g.check("test compiles (-Wall -Werror) and prints W04 PASS", code == 0 and "W04 PASS" in o, o.strip()[-300:])
    audio = PD / "runtime" / "services" / "audio.c"
    if audio.exists():
        code, o = sh(env + f'clang -O1 -fsyntax-only -D_POSIX_THREAD_SAFE_FUNCTIONS -I"{mpath(PD / "runtime")}" '
                     f'"{mpath(audio)}"')
        g.out += o
        g.check("services/audio.c compiles with the shim", code == 0, o.strip()[-300:])


def g_pl(g, a):
    """Card W05: runtime/services/pl.c (pl:u shared fonts) against recomp/test_pl.c."""
    out = LAB / "w05"
    out.mkdir(parents=True, exist_ok=True)
    src = PD / "runtime" / "services" / "pl.c"
    if not g.check("services/pl.c installed", src.exists(), src):
        return
    g.artifact(src)
    env = ('export PATH="/d/msys64/ucrt64/bin:$PATH" TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" '
           'TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"; ')
    exe = out / "test_pl.exe"
    code, o = sh(env + f'clang -Wall -O1 -D_POSIX_THREAD_SAFE_FUNCTIONS -I"{mpath(PD / "runtime")}" '
                 f'"{mpath(RECOMP / "test_pl.c")}" -o "{mpath(exe)}"')
    g.out = o
    if not g.check("test compiles", code == 0, o.strip()[-400:]):
        return
    code, o = sh(f'"{mpath(exe)}" "{mpath(out)}"')
    g.out += o
    g.check("test prints W05 PASS", code == 0 and "W05 PASS" in o, o.strip()[-400:])


def g_cmdbuf_split(g, a):
    """Card W07: runtime/nvn/cmdbuf.c splits big commands across 1024-byte chunks (recomp/test_cmdbuf_split.c)."""
    out = LAB / "w07"
    out.mkdir(parents=True, exist_ok=True)
    src = PD / "runtime" / "nvn" / "cmdbuf.c"
    g.artifact(src)
    env = ENV_MSYS
    exe = out / "test_cmdbuf_split.exe"
    exe.unlink(missing_ok=True)
    code, o = sh(env + f'clang -Wall -Werror -O1 -march=x86-64-v3 -I"{mpath(PD / "runtime")}" '
                 f'-I"{mpath(PD / "runtime" / "nvn")}" "{mpath(RECOMP / "test_cmdbuf_split.c")}" -o "{mpath(exe)}"')
    g.out = o
    if not g.check("test compiles (-Wall -Werror)", code == 0 and exe.exists(), o.strip()[-500:]):
        return
    code, o = sh(f'"{mpath(exe)}" 2>&1')
    g.out += o
    g.check("test prints W07 PASS", code == 0 and "W07 PASS" in o, o.strip()[-500:])


def g_regions(g, a):
    """Card W08: runtime/regions.c (guest memory map as an interval map) against recomp/test_regions.c."""
    out = LAB / "w08"
    out.mkdir(parents=True, exist_ok=True)
    src = PD / "runtime" / "regions.c"
    if not g.check("runtime/regions.c installed", src.exists(), src):
        return
    g.artifact(src)
    exe = out / "test_regions.exe"
    exe.unlink(missing_ok=True)
    code, o = sh(ENV_MSYS + f'clang -Wall -Werror -O1 -I"{mpath(PD / "runtime")}" "{mpath(RECOMP / "test_regions.c")}" '
                 f'"{mpath(src)}" -o "{mpath(exe)}"')
    g.out = o
    if not g.check("test compiles (-Wall -Werror)", code == 0 and exe.exists(), o.strip()[-500:]):
        return
    code, o = sh(f'"{mpath(exe)}" 2>&1', timeout=600)
    g.out += o
    g.check("test prints W08 PASS", code == 0 and "W08 PASS" in o, o.strip()[-500:])


def save_manifest(folder):
    """Hashes only: no save contents enter evidence records."""
    folder = Path(folder)
    if not folder.is_dir() or folder.is_symlink() or folder.is_junction():
        raise ValueError("save source must be a real directory")
    result = {}
    for path in sorted(folder.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise ValueError("linked save entries are not supported")
        if path.is_file():
            result[path.relative_to(folder).as_posix()] = sha256(path)
    return result


def prepare_window_save(source, target):
    """Prepare an expendable copy. Never delete source or a related directory."""
    target = Path(target)
    lab = (ROOT / "lab").resolve()
    resolved = target.resolve()
    if resolved == lab or not resolved.is_relative_to(lab):
        raise ValueError("save sandbox must be below the project lab directory")
    if target.is_symlink() or target.is_junction():
        raise ValueError("save sandbox cannot be a link or junction")
    source = Path(source).resolve() if source else None
    if source and (source == resolved or source in resolved.parents or resolved in source.parents):
        raise ValueError("save source and sandbox paths must be disjoint")
    before = save_manifest(source) if source else {}
    staging = target.with_name(f".{target.name}.copy-{uuid.uuid4().hex}")
    try:
        if source:
            shutil.copytree(source, staging)
        else:
            staging.mkdir(parents=True)
        if save_manifest(staging) != before:
            raise ValueError("save copy does not match the source manifest")
        if target.exists():
            shutil.rmtree(target)
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return before


def g_save_safety(g, a):
    """Test backup recovery on synthetic data and a private disposable save copy."""
    code, out = sh(f'"{mpath(sys.executable)}" "{mpath(ROOT / "tools/verify/test_save_safety.py")}" -v', cwd=ROOT)
    g.out = out
    g.check("save isolation regression suite", code == 0 and "Ran 4 tests" in out and "OK" in out, out[-300:])
    g.info.update(scope="copied-save backup/recovery; not guest atomic Commit")
    if not a.save:
        g.check("explicit source save supplied", False, "use --save with a seed directory")
        return
    folder = LAB / "save-safety" / uuid.uuid4().hex[:10]
    folder.mkdir(parents=True)
    backup, sandbox = folder / "backup", folder / "sandbox"
    try:
        before = prepare_window_save(a.save, backup)
        g.check("nonempty seed manifest", bool(before))
        if not before:
            return
        prepare_window_save(backup, sandbox)
        g.check("initial copy matches seed", save_manifest(sandbox) == before)
        expendable = sandbox / next(iter(before))
        expendable.write_bytes(b"interrupted-expendable-copy")
        g.check("copy corruption detected", save_manifest(sandbox) != before)
        prepare_window_save(backup, sandbox)
        g.check("restore matches backup", save_manifest(sandbox) == before)
        g.check("original seed unchanged", save_manifest(a.save) == before)
        g.info.update(source=mpath(Path(a.save)), source_manifest=before,
                      backup=mpath(backup), restored_sandbox=mpath(sandbox))
    except (OSError, ValueError) as exc:
        g.check("save recovery experiment", False, str(exc))


def g_save_interruption(g, a):
    """One real guest write, deliberate exit before Flush/Commit, then verified backup restoration."""
    if not g.check("explicit source save supplied", bool(a.save)):
        return
    if not g.check("explicit save input scenario supplied", bool(a.input_script)):
        return
    if not g.check("interruption target is v400", a.version == "v400"):
        return
    host = LAB / "host-vk-auto"
    build_run = host_build_provenance(host)
    if not g.check("current-source Vulkan build", bool(build_run), build_run or "rebuild Vulkan host/link"):
        return
    for name in ("pvhost.exe", "pvgame.dll"):
        if not g.check(f"interruption input {name}", g.artifact(host / name)):
            return
    code, out = sh(f'"{mpath(sys.executable)}" "{mpath(ROOT / "tools/verify/test_save_fault.py")}" -v', cwd=ROOT)
    if not g.check("native fault positive and negative controls", code == 0, out[-400:]):
        return
    folder = LAB / "save-interruption" / uuid.uuid4().hex[:10]
    folder.mkdir(parents=True)
    backup, sandbox, log = folder / "backup", folder / "sandbox", folder / "guest.log"
    before = prepare_window_save(a.save, backup)
    if not g.check("nonempty source manifest", bool(before)):
        return
    prepare_window_save(backup, sandbox)
    env = window_environment(host, sandbox, a.input_script)
    env.update(PVR_TEST_SAVE_AFTER_WRITE="1", LARECOMP_TRACE_SAVE="1", PVR_RUN_SECONDS="60",
               PVR_DISPLAY="2", SDL_AUDIO_DRIVER="dummy", PVR_SYSFONT_DIR=mpath(LAB / "sysfont"),
               LARECOMP_SCREENSHOT_EVERY="999999", LARECOMP_SCREENSHOT_FROM="999999",
               LARECOMP_SETTINGS=mpath(folder / "test-settings.ini"))
    env["PATH"] = r"D:\msys64\ucrt64\bin" + os.pathsep + env.get("PATH", "")
    g.info.update(scope="guest exit after accepted write, before Flush/Commit; not power-loss atomicity",
                  version="v400", backend="vulkan", host_build_run_id=build_run,
                  source=mpath(Path(a.save)), source_manifest=before, input_script=a.input_script,
                  backup=mpath(backup), restored_sandbox=mpath(sandbox), attempts=1)
    try:
        with log.open("wb") as output:
            child = subprocess.run([str(host / "pvhost.exe"), str(ROOT / "dumps/v400/exefs"),
                                    str(ROOT / "dumps/v400/romfs")], cwd=host, env=env,
                                   stdout=output, stderr=subprocess.STDOUT, timeout=120)
        text = log.read_text(encoding="utf-8", errors="replace")
        marker = "[save-test] after write before Flush/Commit"
        g.info.update(child_exit=child.returncode, interrupted_manifest=save_manifest(sandbox))
        g.check("guest exited at deliberate fault boundary", child.returncode == 86, str(child.returncode))
        g.check("exact fault marker observed once", text.count(marker) == 1)
        g.check("actual guest write observed", "[save] write " in text)
        g.check("Flush/Commit not reached", "[save] flush " not in text and "[save] commit " not in text)
        g.check("no unrelated fatal/host exception", "FATAL" not in text and "exception c0000005" not in text)
        g.out = f"single guest exit={child.returncode}; fault marker count={text.count(marker)}"
    except (OSError, subprocess.TimeoutExpired) as exc:
        g.check("single interruption experiment returned", False, str(exc))
    finally:
        if log.exists():
            g.artifact(log)
        prepare_window_save(backup, sandbox)
        g.check("restoration matches immutable backup", save_manifest(sandbox) == before)
        after = save_manifest(a.save)
        g.info.update(source_manifest_after=after)
        g.check("source save unchanged", after == before)


def window_environment(host, save, input_script=None):
    env = dict(os.environ)
    for key in ("PVR_FRAMEPACE", "PVR_FPS_CAP", "PVR_GAME60", "SAVE_SEED", "PVR_INPUT", "PVR_AUTOPRESS", "PVR_TEST_CRASH", "PVR_TEST_SAVE_AFTER_WRITE"):
        env.pop(key, None)
    env.update(PVR_HOST_DIR=bpath(host), LARECOMP_SAVE_DIR=mpath(save),
               LARECOMP_SETTINGS="build/psvrecomp_auto.ini",
               LARECOMP_SCREENSHOT_EVERY="150", LARECOMP_SCREENSHOT_FROM="150")
    if input_script:
        env.update(PVR_INPUT=input_script, PVR_AUTOPRESS="A:1000000:100:999999")
    return env


def g_window(g, a):
    """M3-M5 in the isolated window build (lab/host-vk-auto: Vulkan, v4.0.0, paced at the game's 30 fps): a NEW game from an empty
    save with run_auto.sh's scripted input (A every second). Checks, all on the first try (no crash retries):
      no FATAL / host exception; presented frames ~ 30 fps over the run; screenshots are rendered scenes (lit, many
      colours: M3 first frame / M4 3D); the scene changes during the run (the game advances with the input: M5);
      the last 10 s frametime windows hold >= 27 fps."""
    sys.path.insert(0, str(ROOT / "tools" / "verify"))
    import frame_stats
    H = LAB / "host-vk-auto"
    g.info.update(version="v400", backend="vulkan")
    for name in ("pvhost.exe", "pvgame.dll"):
        if not g.check(f"window input {name} present", g.artifact(H / name), str(H / name)):
            return
    build_run = host_build_provenance(H)
    if not g.check("Vulkan binary matches a current-source host gate", bool(build_run),
                   build_run or "rebuild host --version v400 --backend vulkan"):
        return
    g.info.update(host_build_run_id=build_run)
    secs = max(a.seconds, 60)
    save = H / "save_gate"
    try:
        source_manifest = prepare_window_save(a.save, save)
    except (OSError, ValueError) as exc:
        g.check("isolated save prepared", False, str(exc))
        return
    g.info.update(save_sandbox=mpath(save), source_manifest=source_manifest)
    if a.save:
        g.info.update(save=str(a.save))
    g.check("isolated save matches input", save_manifest(save) == source_manifest)
    input_script = getattr(a, "input_script", None)
    env = window_environment(H, save, input_script)
    g.info.update(input_script=input_script)
    code, out = sh(f"bash tools/verify/run_auto.sh {secs} gate_window", cwd=ROOT, env=env, timeout=secs * 4 + 900)
    g.out += out
    g.check("automatic window command exit 0", code == 0, f"exit {code}")
    if a.save:
        try:
            after_manifest = save_manifest(a.save)
            g.info.update(source_manifest_after=after_manifest)
            g.check("original source save unchanged", after_manifest == source_manifest)
        except (OSError, ValueError) as exc:
            g.check("original source save unchanged", False, str(exc))
    log_p = H / "gate_window.log"
    if not g.check("gate_window.log written by this run", log_p.exists()):
        return
    g.artifact(log_p)
    log = log_p.read_text(encoding="utf-8", errors="replace")
    g.check("first try without crash (run 1: bad=0)", "run 1: bad=0" in out, out.strip().splitlines()[0] if out.strip() else "")
    fatal = re.search(r"^FATAL: .*$", log, re.M)
    exc = re.search(r"^\*\*\* exception .*$", log, re.M)
    g.check("no FATAL", fatal is None, fatal.group(0) if fatal else "")
    g.check("no host exception", exc is None, exc.group(0) if exc else "")
    frames = [int(x) for x in re.findall(r"\[vk\] t=[0-9.]+ frame (\d+)", log)]
    last = frames[-1] if frames else 0
    need = int(30 * (secs - 15) * 0.8)
    g.check(f"presented >= {need} frames (30 fps pacing)", last >= need, f"last frame {last}")
    pngs = sorted((H / "build" / "frames").glob("frame_*.png"))
    st = []
    for f in pngs:
        try:
            st.append((f.name, frame_stats.stats(str(f))))
        except Exception as e:  # noqa: BLE001 (a truncated PNG at the time limit)
            g.info.setdefault("unreadable", []).append(f"{f.name}: {e}")
    rendered = [(n, d) for n, d in st if d["lit"] > 0.9 and d["uniq"] >= 500]
    g.info.update(screenshots=len(st), rendered=len(rendered), frame_stats={n: d for n, d in st})
    g.check("M3/M4: >= 3 screenshots are rendered scenes (lit > 0.9, >= 500 colours)", len(rendered) >= 3,
            f"{len(rendered)}/{len(st)}")
    changes = sum(1 for (_, x), (_, y) in zip(st, st[1:]) if abs(x["mean"] - y["mean"]) > 5 or abs(x["uniq"] - y["uniq"]) > 200)
    g.check("M5: the scene changes during the run (game advances with input)", changes >= 2, f"{changes} changes")
    wins = [float(x) for x in re.findall(r"\[frametime\] \d+ s: \d+ frames, avg [0-9.]+ ms \(([0-9.]+) fps\)", log)]
    tail = wins[-2:]
    g.info.update(frametime_windows_fps=wins)
    g.check("last 10 s frametime windows >= 27 fps", len(tail) == 2 and min(tail) >= 27, f"{tail}")
    for f in rendered[:2] + rendered[-1:]:
        g.artifact(H / "build" / "frames" / f[0])


GATES = {"save_interruption": g_save_interruption, "save_safety": g_save_safety, "window": g_window, "dumps": g_dumps, "host": g_host, "link": g_link, "boot": g_boot, "simd": g_simd, "excl_pair": g_excl_pair, "nvn_null": g_nvn_null, "sdl_null": g_sdl_null, "pl": g_pl, "cmdbuf_split": g_cmdbuf_split, "regions": g_regions}


def run_gate(name, a):
    g = Gate()
    EVID.mkdir(parents=True, exist_ok=True)
    t0 = datetime.datetime.now()
    try:
        GATES[name](g, a)
    except subprocess.TimeoutExpired as e:
        g.check("finished before timeout", False, str(e))
    head, dirty = git_head()
    rec = {"run_id": uuid.uuid4().hex[:10], "gate": name, "agent": a.agent, "time": t0.isoformat(timespec="seconds"),
           "seconds": round((datetime.datetime.now() - t0).total_seconds(), 1), "git": head, "dirty": dirty,
           "pass": bool(g.checks) and all(c["ok"] for c in g.checks), "checks": g.checks, "artifacts": g.artifacts,
           "info": g.info, "output_sha256": hashlib.sha256(g.out.encode()).hexdigest(), "output_tail": g.out[-1500:]}
    EVID.mkdir(parents=True, exist_ok=True)
    with GATES_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def show(rec):
    print(f"[gate {rec['gate']}] run_id={rec['run_id']} {'PASS' if rec['pass'] else 'FAIL'} "
          f"({rec['seconds']} s, git {rec['git']}{' dirty' if rec['dirty'] else ''})")
    for c in rec["checks"]:
        print(f"  {'ok  ' if c['ok'] else 'FAIL'} {c['check']}  {c['detail'] if not c['ok'] or c['detail'] else ''}")
    for k in ("stage", "crash", "fatal", "functions"):
        if rec["info"].get(k) is not None:
            print(f"  {k}: {rec['info'][k]}")


# ---------------------------------------------------------------- claims / score
def cmd_claim(a):
    rec = run_gate(a.gate, a)
    show(rec)
    if a.expect.startswith("stage:"):
        want = a.expect.split(":", 1)[1]
        got = rec["info"].get("stage")
        true = got is not None and STAGE_NAMES.index(got) >= STAGE_NAMES.index(want)
    else:
        true = rec["pass"]
    c = {"time": rec["time"], "agent": a.agent, "claim": a.text, "gate": a.gate, "expect": a.expect,
         "run_id": rec["run_id"], "verdict": "true" if true else "FALSE", "source": "gate"}
    with CLAIMS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"claim by {a.agent}: \"{a.text}\" -> {c['verdict']}")
    return 0 if true else 1


def cmd_note(a):
    """A claim judged by review (no gate can rerun it, e.g. a past chat turn): evidence text is mandatory."""
    c = {"time": datetime.datetime.now().isoformat(timespec="seconds"), "agent": a.agent, "claim": a.text,
         "gate": None, "verdict": a.verdict, "source": "review", "evidence": a.evidence, "context": a.context}
    EVID.mkdir(parents=True, exist_ok=True)
    with CLAIMS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"noted {a.agent}: {a.verdict}  {a.text[:80]}")


def cmd_score(a):
    rows = [json.loads(l) for l in CLAIMS_LOG.read_text(encoding="utf-8").splitlines() if l.strip()] \
        if CLAIMS_LOG.exists() else []
    by = {}
    for r in rows:
        s = by.setdefault(r["agent"], {"claims": 0, "true": 0, "false": 0})
        s["claims"] += 1
        s["true" if r["verdict"] == "true" else "false"] += 1
    print(f"{'agente':10} {'claims':>6} {'verdadeiras':>11} {'falsas':>6} {'taxa falsa':>10}")
    for ag, s in sorted(by.items()):
        print(f"{ag:10} {s['claims']:6} {s['true']:11} {s['false']:6} {s['false'] / s['claims']:10.0%}")
    if a.verbose:
        for r in rows:
            print(f"  {r['time'][:16]} {r['agent']:7} {r['verdict']:5} {r['claim'][:70]}  ({r.get('run_id') or r.get('evidence', '')[:40]})")


# ---------------------------------------------------------------- fake detector
SUCCESS_WORDS = re.compile(r"✅|PASSOU|PASSED|\bOK\b|sucesso|success|conclu[ií]d|completo|complete", re.I)
DONE_DOC = re.compile(r"✅|\[x\]|conclu[ií]d[ao]|completa|completed|implemented|funcionando|working", re.I)
RUN_ID = re.compile(r"run_id[=: ]+([0-9a-f]{10})|gate[:=]\s*\w+@([0-9a-f]{10})")


def known_runs():
    if not GATES_LOG.exists():
        return {}
    out = {}
    for l in GATES_LOG.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            out[r["run_id"]] = r
    return out


def lint_file(p, text, runs, new_lines=None):
    probs = []
    lines = text.splitlines()
    if p.suffix in (".sh", ".bash") or text.startswith("#!"):
        echo = [l for l in lines if l.strip().startswith(("echo", "printf"))]
        real = [l for l in lines if l.strip() and not l.strip().startswith(("#", "echo", "printf", "cd ", "set ", "fi",
                                                                            "if ", "then", "else", "done", "for ", "}"))]
        if len(echo) >= 5 and sum(bool(SUCCESS_WORDS.search(l)) for l in echo) >= 3 and len(real) <= len(echo) // 3:
            probs.append("script only PRINTS success (echo/printf) instead of checking anything")
        for i, l in enumerate(lines, 1):
            if re.search(r"echo .*(✅|PASSOU|sucesso|success|conclu[ií]d|realizad|pronto para|validad)", l, re.I) and \
               not re.search(r"(&&|\|\|(?!\s*true)|if |\$\?)", "\n".join(lines[max(0, i - 3):i])):
                probs.append(f"line {i}: unconditional success message: {l.strip()[:80]}")
            if re.search(r"(build|compile|link|clang|make|run_boot|pvhost).*\|\|\s*true", l):
                probs.append(f"line {i}: failure of a build/run step swallowed with `|| true`")
    if p.suffix == ".py":
        for i, l in enumerate(lines, 1):
            if re.search(r"print\(.*(✅|PASSOU|sucesso|conclu[ií]d|FINALIZADO|pronto para)", l, re.I) and \
               not re.search(r"\bif\b|\bassert\b|returncode|exit", "\n".join(lines[max(0, i - 4):i])):
                probs.append(f"line {i}: unconditional success print: {l.strip()[:80]}")
    if p.suffix == ".md":
        scan = new_lines if new_lines is not None else list(enumerate(lines, 1))
        if p.name in ("CLAUDE.md", "AGENTS.md"):  # rule files describe the policy, they claim nothing
            return probs
        for i, l in scan:
            if re.search(r"❌|FALS[EO]|rejeitad|rejected|falh[ao]u|failed", l, re.I):  # recording a failure is never a fake success
                continue
            prose = re.sub(r"`[^`]*`", "", l)  # inline code (log strings, `[x]` syntax) is not a claim
            if DONE_DOC.search(prose) and re.search(r"boot|fase|phase|(?<!de)compil|link|teste|test|funciona|HLE|implement",
                                                    prose, re.I):
                ids = [x for m in RUN_ID.finditer(l) for x in m.groups() if x]
                if not ids:
                    probs.append(f"line {i}: completion claim without gate run_id: {l.strip()[:90]}")
                for rid in ids:
                    if rid not in runs:
                        probs.append(f"line {i}: run_id {rid} does not exist in gates.jsonl")
                    elif not runs[rid]["pass"] and not re.search(r"FAIL|falh|crash|parou", l, re.I):
                        probs.append(f"line {i}: cites run {rid} as success but that run FAILED")
    if p.suffix in (".c", ".h"):
        if re.search(r"\b(dummy|fake)\b.*\n", text, re.I) and re.search(r"return\s+(0|1|0x[0-9a-f]+ULL);", text) \
           and text.count("\n") < 40:
            probs.append("tiny stub file with dummy returns (check it is not pretending to be a real service)")
    return probs


def staged_files():
    r = subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                       capture_output=True, text=True, encoding="utf-8")
    return [ROOT / l for l in r.stdout.splitlines() if l.strip()]


def added_lines(p):
    """Line numbers added in the staged diff of p (so old docs written before the harness don't block)."""
    r = subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "-U0", "--", str(p)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out, ln = [], 0
    for l in r.stdout.splitlines():
        m = re.match(r"@@ -\S+ \+(\d+)", l)
        if m:
            ln = int(m.group(1))
        elif l.startswith("+") and not l.startswith("+++"):
            out.append((ln, l[1:]))
            ln += 1
    return out


def cmd_lint(a):
    runs = known_runs()
    if a.staged:
        files = staged_files()
    elif a.files:
        files = [Path(f).resolve() for f in a.files]
    else:
        r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-mo", "--exclude-standard"], capture_output=True,
                           text=True, encoding="utf-8")
        files = [ROOT / l for l in r.stdout.splitlines() if l.strip()]
    bad = 0
    for p in files:
        if not p.is_file() or p.suffix not in (".sh", ".py", ".md", ".c", ".h", "") or "venv" in p.parts:
            continue
        if p.resolve() in (Path(__file__).resolve(), Path(__file__).with_name("test_gates.py").resolve()):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        probs = lint_file(p, text, runs, added_lines(p) if a.staged and p.suffix == ".md" else None)
        for x in probs:
            print(f"{mpath(p.relative_to(ROOT))}: {x}")
        bad += len(probs)
    print(f"lint: {bad} problem(s)")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("run", "claim"):
        s = sp.add_parser(n)
        s.add_argument("gate", choices=GATES)
        s.add_argument("--agent", default="claude", choices=["claude", "qwen", "user"])
        s.add_argument("--min-stage", help="stage, or comma list of stages that must all be reached: " + ", ".join(STAGE_NAMES))
        s.add_argument("--seconds", type=int, default=30)
        s.add_argument("--input-script", help="window: explicit PVR_INPUT script, disables default periodic presses")
        s.add_argument("--repeat", type=int, default=1, help="boot: N runs, all must pass")
        s.add_argument("--save", help="window/save_safety: source save directory (window default: empty new game)")
        s.add_argument("--backend", choices=["null", "vulkan"], default="null",
                       help="host/link: null uses versioned host; vulkan uses isolated lab/host-vk-auto")
        s.add_argument("--version", default="base", help="dump version: dumps/<version>, lab/gen-<version> (base = lab/genfull)")
        if n == "claim":
            s.add_argument("--text", required=True)
            s.add_argument("--expect", default="pass", help="pass | stage:<name>")
    s = sp.add_parser("note")
    s.add_argument("--agent", required=True, choices=["claude", "qwen", "user"])
    s.add_argument("--text", required=True)
    s.add_argument("--verdict", required=True, choices=["true", "FALSE"])
    s.add_argument("--evidence", required=True)
    s.add_argument("--context", default="")
    s = sp.add_parser("score"); s.add_argument("-v", "--verbose", action="store_true")
    s = sp.add_parser("lint"); s.add_argument("--staged", action="store_true"); s.add_argument("files", nargs="*")
    sp.add_parser("list")
    a = ap.parse_args()
    if a.cmd == "run":
        rec = run_gate(a.gate, a)
        show(rec)
        return 0 if rec["pass"] else 1
    if a.cmd == "claim":
        return cmd_claim(a)
    if a.cmd == "note":
        return cmd_note(a)
    if a.cmd == "score":
        return cmd_score(a)
    if a.cmd == "lint":
        return cmd_lint(a)
    if a.cmd == "list":
        for k, f in GATES.items():
            print(k)
        print("boot stages:", " < ".join(STAGE_NAMES))


if __name__ == "__main__":
    sys.exit(main())
