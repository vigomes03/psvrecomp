"""Builds the synthetic AArch64 call-probe fixture used by ghidra_call_probe tests.

Assembles a tiny known program with the verified project compiler
(D:/msys64/ucrt64/bin/clang.exe, cross-assembling for aarch64-none-elf) and
extracts the raw .text bytes for Ghidra's BinaryLoader. Addresses are read
back from the assembler's own symbol table rather than hard-coded, so a
change to the assembly keeps the computed addresses correct.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .elf_min import ElfObject

CLANG = "D:/msys64/ucrt64/bin/clang.exe"

# entry: mov/bl/mov/ret, callee: mov/ret. The bl at entry+4 is the only call;
# entry+0 is a plain data-processing instruction for the negative control.
ASSEMBLY = """\
.text
.global entry
entry:
    mov x0, #1
    bl callee
    mov x1, #2
    ret
callee:
    mov x2, #3
    ret
"""

BASE_ADDR = 0x00100000


@dataclass(frozen=True)
class ProbeFixture:
    bin_path: Path
    base_addr: int
    entry_addr: int
    call_site_addr: int
    non_call_addr: int
    callee_addr: int


def build_probe_fixture(out_dir: Path) -> ProbeFixture:
    out_dir.mkdir(parents=True, exist_ok=True)
    asm_path = out_dir / "probe.s"
    obj_path = out_dir / "probe.o"
    bin_path = out_dir / "probe.bin"

    asm_path.write_text(ASSEMBLY)
    subprocess.run(
        [CLANG, "--target=aarch64-none-elf", "-c", str(asm_path), "-o", str(obj_path)],
        check=True, capture_output=True, text=True, timeout=60,
    )

    obj = ElfObject(obj_path.read_bytes())
    text = obj.section_bytes(".text")
    symbols = obj.symbols()
    text_shndx = obj.section_names.index(".text")

    entry_value, entry_shndx = symbols["entry"]
    callee_value, callee_shndx = symbols["callee"]
    if entry_shndx != text_shndx or callee_shndx != text_shndx:
        raise ValueError("expected entry/callee symbols inside .text")

    bin_path.write_bytes(text)
    entry_addr = BASE_ADDR + entry_value
    return ProbeFixture(
        bin_path=bin_path,
        base_addr=BASE_ADDR,
        entry_addr=entry_addr,
        call_site_addr=entry_addr + 4,
        non_call_addr=entry_addr,
        callee_addr=BASE_ADDR + callee_value,
    )
