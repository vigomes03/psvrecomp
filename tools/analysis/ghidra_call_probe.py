"""Direct-Ghidra headless runner that classifies one AArch64 call-site relationship.

Runs the real, installed Ghidra headless analyzer (D:/Tools/ghidra_12.1.4_PUBLIC)
on a caller-supplied raw binary, via CallProbeScript.java (same directory).
This is a standalone verification helper, not part of REA's Windows raw-binary
admission path. The default CallProbeScript entry remains synthetic-only.
The separately validated scoped_function_probe entry reuses this executor for
approved bounded local analysis; private inputs/outputs must stay under ignored lab/.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

ANALYZE_HEADLESS = "D:/Tools/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat"
LANGUAGE_ID = "AARCH64:LE:64:v8A"
COMPILER_SPEC = "default"
SCRIPT_NAME = "CallProbeScript.java"
SCRIPT_DIR = Path(__file__).resolve().parent


class CallProbeError(RuntimeError):
    """Raised whenever the probe cannot produce a trustworthy classification."""


@dataclass(frozen=True)
class CallProbeResult:
    language: str
    image_base: int
    call_site: int
    instruction_present: bool
    is_call: bool
    mnemonic: Optional[str]
    target: Optional[int]
    target_function: Optional[str]
    raw_metadata: Optional[dict] = None


def run_call_probe(
    binary_path: Path,
    base_addr: int,
    call_site_addr: int,
    work_dir: Path,
    timeout_s: int = 120,
    *,
    _script_name: Optional[str] = None,
    _script_args: Sequence[str] = (),
) -> CallProbeResult:
    """Runs the real Ghidra headless analyzer once and classifies call_site_addr.

    Fails closed (raises CallProbeError) on a non-zero exit, a missing or
    unparsable output file, a script-reported error, or metadata that does
    not match what was requested.
    """
    if (type(base_addr) is not int or type(call_site_addr) is not int
            or base_addr < 0 or call_site_addr < base_addr
            or base_addr % 4 or call_site_addr % 4
            or base_addr >= 1 << 64 or call_site_addr >= 1 << 64):
        raise CallProbeError("Expected aligned, unsigned ARM64 base/site addresses")
    if (isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float))
            or timeout_s <= 0):
        raise CallProbeError("Expected a positive subprocess timeout")
    binary_path = Path(binary_path).resolve()
    if not binary_path.is_file():
        raise CallProbeError(f"Input binary does not exist: {binary_path}")
    if call_site_addr - base_addr + 4 > binary_path.stat().st_size:
        raise CallProbeError("Call-site instruction lies outside the input image")
    work_dir = Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:8]
    project_dir = work_dir / f"project-{run_id}"
    project_dir.mkdir(parents=True, exist_ok=True)
    project_name = f"probe-{run_id}"
    output_json = work_dir / f"result-{run_id}.json"
    log_path = work_dir / f"headless-{run_id}.log"
    script_name = SCRIPT_NAME if _script_name is None else _script_name

    command = [
        "cmd", "/d", "/c", ANALYZE_HEADLESS,
        str(project_dir), project_name,
        "-import", str(binary_path),
        "-loader", "BinaryLoader",
        "-loader-baseAddr", "0",
        "-processor", LANGUAGE_ID,
        "-cspec", COMPILER_SPEC,
        "-noanalysis",
        "-scriptPath", str(SCRIPT_DIR),
        "-postScript", script_name, hex(base_addr), hex(call_site_addr), str(output_json),
        *[str(arg) for arg in _script_args],
        "-log", str(log_path),
        "-scriptlog", str(work_dir / f"script-{run_id}.log"),
        "-deleteProject",
    ]

    taskkill = shutil.which("taskkill")
    if taskkill is None:
        raise CallProbeError("Windows taskkill is required to bound the owned JVM process tree")
    stdout_path = work_dir / f"headless-{run_id}.stdout.txt"
    stderr_path = work_dir / f"headless-{run_id}.stderr.txt"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, errors="replace", cwd=work_dir)
    try:
        try:
            stdout, stderr = process.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired as error:
            # Killing only cmd.exe leaves its JVM holding stdout open; run() can
            # then wait past the timeout. Terminate only this owned PID tree.
            killed = subprocess.run([taskkill, "/PID", str(process.pid), "/T", "/F"],
                                    capture_output=True, text=True, errors="replace", timeout=10)
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired as cleanup_error:
                raise CallProbeError(
                    f"Could not reap owned PID {process.pid}: {killed.stderr}"
                ) from cleanup_error
            stdout_path.write_text(stdout, encoding="utf-8")
            stderr_path.write_text(stderr, encoding="utf-8")
            raise CallProbeError(
                f"Ghidra headless run timed out after {timeout_s}s (run_id={run_id}); "
                f"owned process tree reaped, logs: {work_dir}"
            ) from error
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    finally:
        if process.poll() is not None:
            shutil.rmtree(project_dir, ignore_errors=True)

    if completed.returncode != 0:
        raise CallProbeError(
            f"Ghidra headless exited with code {completed.returncode} (run_id={run_id})\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )

    if not output_json.exists():
        raise CallProbeError(
            f"Ghidra headless produced no output JSON (run_id={run_id}); "
            "the post-script likely failed before writing it\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )

    raw_text = output_json.read_text()
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise CallProbeError(
            f"Probe output was not valid JSON (run_id={run_id}): {raw_text!r}"
        ) from error

    if "error" in payload:
        raise CallProbeError(f"CallProbeScript reported an error (run_id={run_id}): {payload['error']}")

    for required in ("language", "image_base", "call_site", "instruction_present", "is_call"):
        if required not in payload:
            raise CallProbeError(f"Probe output missing required field {required!r}: {payload}")

    if payload["language"] != LANGUAGE_ID:
        raise CallProbeError(f"Unexpected language {payload['language']!r}, expected {LANGUAGE_ID!r}")
    if int(payload["image_base"], 16) != base_addr:
        raise CallProbeError(f"Unexpected image base {payload['image_base']!r}, expected {hex(base_addr)}")
    if int(payload["call_site"], 16) != call_site_addr:
        raise CallProbeError(f"Unexpected call_site {payload['call_site']!r}, expected {hex(call_site_addr)}")

    target = payload.get("target")
    return CallProbeResult(
        language=payload["language"],
        image_base=int(payload["image_base"], 16),
        call_site=int(payload["call_site"], 16),
        instruction_present=payload["instruction_present"],
        is_call=payload["is_call"],
        mnemonic=payload.get("mnemonic"),
        target=int(target, 16) if target else None,
        target_function=payload.get("target_function"),
        raw_metadata=payload,
    )
