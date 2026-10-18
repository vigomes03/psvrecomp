"""Direct-Ghidra headless runner that creates two explicitly bounded candidate
functions (a caller and a callee) and decompiles both.

Runs the real, installed Ghidra headless analyzer (D:/Tools/ghidra_12.1.4_PUBLIC)
via ScopedFunctionProbe.java (same directory), reusing run_call_probe's
subprocess/timeout/freshness handling. Validate on our own synthetic fixtures
first. Approved R-01 experiments may use hash-bound private images under lab/targets,
with all decompiler output kept local under ignored lab/. No private C belongs in stdout.
"""
from __future__ import annotations

from pathlib import Path

from .ghidra_call_probe import CallProbeError, run_call_probe

ROOT = Path(__file__).resolve().parents[2]
SCOPED_SCRIPT_NAME = "ScopedFunctionProbe.java"
MAX_INTERVAL_BYTES = 16384
ALLOWED_INPUT_DIRS = (ROOT / "lab/targets", ROOT / "lab/analysis-probe-tests")
ALLOWED_OUTPUT_DIR = ROOT / "lab"


def _require_aligned_u64(name, value):
    if type(value) is not int or value < 0 or value >= 1 << 64:
        raise CallProbeError(f"Expected a non-negative unsigned 64-bit integer for {name}")
    if value % 4:
        raise CallProbeError(f"Expected {name} to be 4-byte aligned")
    return value


def _require_interval(label, start, end):
    _require_aligned_u64(f"{label}_start", start)
    if type(end) is not int or end < start or end >= 1 << 64:
        raise CallProbeError(f"Expected {label}_end >= {label}_start")
    size = end - start + 1
    if size % 4:
        raise CallProbeError(f"Expected {label} interval size to be a multiple of 4")
    if size > MAX_INTERVAL_BYTES:
        raise CallProbeError(f"{label} interval exceeds {MAX_INTERVAL_BYTES} bytes")
    return size


def _require_under(path: Path, allowed_roots, description):
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT):
        raise CallProbeError(f"{description} resolves outside the project")
    for allowed in allowed_roots:
        allowed_resolved = allowed.resolve()
        if resolved == allowed_resolved or allowed_resolved in resolved.parents:
            return resolved
    raise CallProbeError(f"{description} must be under one of {allowed_roots}, got {resolved}")


def run_scoped_probe(
    binary_path,
    base_addr: int,
    call_site_addr: int,
    caller_start: int,
    caller_end: int,
    callee_start: int,
    callee_end: int,
    work_dir,
    timeout_s: int = 120,
) -> dict:
    """Creates and decompiles two supplied-bound candidate functions, fail-closed.

    Rejects invalid or out-of-bounds input before launching Ghidra. The
    underlying script verifies call_site_addr is a direct call whose only
    target equals callee_start before creating/decompiling anything.
    """
    binary_path = Path(binary_path)
    work_dir = Path(work_dir)

    _require_aligned_u64("base_addr", base_addr)
    _require_aligned_u64("call_site_addr", call_site_addr)
    caller_size = _require_interval("caller", caller_start, caller_end)
    callee_size = _require_interval("callee", callee_start, callee_end)

    if caller_start <= callee_end and callee_start <= caller_end:
        raise CallProbeError("caller and callee intervals must not overlap")
    if not (caller_start <= call_site_addr and call_site_addr + 3 <= caller_end):
        raise CallProbeError("call_site_addr must lie inside the caller interval")

    resolved_binary = _require_under(binary_path, ALLOWED_INPUT_DIRS, "binary_path")
    if not resolved_binary.is_file():
        raise CallProbeError(f"Input binary does not exist: {resolved_binary}")
    _require_under(work_dir, (ALLOWED_OUTPUT_DIR,), "work_dir")

    image_size = resolved_binary.stat().st_size
    image_start, image_end = base_addr, base_addr + image_size - 1
    if not (image_start <= caller_start and caller_end <= image_end):
        raise CallProbeError("caller interval lies outside the input image")
    if not (image_start <= callee_start and callee_end <= image_end):
        raise CallProbeError("callee interval lies outside the input image")

    result = run_call_probe(
        resolved_binary, base_addr, call_site_addr, work_dir, timeout_s,
        _script_name=SCOPED_SCRIPT_NAME,
        _script_args=(hex(caller_start), hex(caller_end), hex(callee_start), hex(callee_end)),
    )
    payload = result.raw_metadata
    if not isinstance(payload, dict):
        raise CallProbeError("Missing actual scoped metadata")
    count = payload.get("decoded_instruction_count")
    if type(count) is not int or not 0 < count <= (caller_size + callee_size) // 4:
        raise CallProbeError("Decoded instruction count exceeds the supplied byte budget")
    for key, expected in (("caller_start", caller_start), ("caller_end", caller_end),
                          ("callee_start", callee_start), ("callee_end", callee_end)):
        if payload.get(key) != hex(expected):
            raise CallProbeError(f"Returned bound differs from request: {key}")

    if not payload.get("is_call") or result.target != callee_start:
        raise CallProbeError(
            f"Call site did not resolve to the supplied callee entry: {payload}"
        )
    if payload.get("function_count") != 2:
        raise CallProbeError(f"Expected exactly 2 candidate functions, got: {payload}")
    if payload.get("function_provenance") != "supplied-symbol-intervals":
        raise CallProbeError(f"Unexpected function provenance: {payload}")
    if payload.get("auto_analysis_disabled") is not True:
        raise CallProbeError(f"Expected auto-analysis to stay disabled: {payload}")
    if payload.get("caller_decompiled") is not True or payload.get("callee_decompiled") is not True:
        raise CallProbeError(f"Expected both candidate functions to decompile: {payload}")

    work_dir_resolved = work_dir.resolve()
    for key in ("caller_pseudocode", "callee_pseudocode"):
        raw_path = payload.get(key)
        if not raw_path:
            raise CallProbeError(f"Missing {key} in probe output: {payload}")
        pseudocode_path = Path(raw_path)
        if not pseudocode_path.is_absolute():
            raise CallProbeError(f"Expected {key} to be an absolute path, got {raw_path!r}")
        resolved_pseudocode = pseudocode_path.resolve()
        if resolved_pseudocode != work_dir_resolved and work_dir_resolved not in resolved_pseudocode.parents:
            raise CallProbeError(f"{key} escaped work_dir: {resolved_pseudocode}")
        if not resolved_pseudocode.is_file() or resolved_pseudocode.stat().st_size == 0:
            raise CallProbeError(f"{key} is missing or empty: {resolved_pseudocode}")

    return payload
