"""Minimal ELF64 little-endian section/symbol reader.

Only reads what build_probe_fixture.py needs from our own clang-assembled
object files. Not a general-purpose ELF library.
"""
from __future__ import annotations

import struct


class ElfObject:
    def __init__(self, data: bytes):
        if data[:4] != b"\x7fELF":
            raise ValueError("not an ELF file")
        if data[4] != 2:
            raise ValueError("expected ELFCLASS64")
        if data[5] != 1:
            raise ValueError("expected little-endian ELF")
        (e_shoff,) = struct.unpack_from("<Q", data, 0x28)
        (e_shentsize,) = struct.unpack_from("<H", data, 0x3A)
        (e_shnum,) = struct.unpack_from("<H", data, 0x3C)
        (e_shstrndx,) = struct.unpack_from("<H", data, 0x3E)
        self.data = data
        # Elf64_Shdr: name,type,flags,addr,offset,size,link,info,addralign,entsize
        self.sections = [
            struct.unpack_from("<IIQQQQIIQQ", data, e_shoff + i * e_shentsize)
            for i in range(e_shnum)
        ]
        shstr_off = self.sections[e_shstrndx][4]
        self.section_names = [self._name_at(shstr_off, s[0]) for s in self.sections]

    def _name_at(self, strtab_off: int, name_off: int) -> str:
        end = self.data.index(b"\x00", strtab_off + name_off)
        return self.data[strtab_off + name_off : end].decode()

    def section_bytes(self, name: str) -> bytes:
        idx = self.section_names.index(name)
        sh_offset, sh_size = self.sections[idx][4], self.sections[idx][5]
        return self.data[sh_offset : sh_offset + sh_size]

    def symbols(self) -> dict[str, tuple[int, int]]:
        """Returns {symbol_name: (value, section_index)}."""
        symtab_idx = self.section_names.index(".symtab")
        _, _, _, symtab_off, symtab_size, strtab_idx, _, _, entsize = self.sections[symtab_idx][1:]
        strtab_off = self.sections[strtab_idx][4]
        result: dict[str, tuple[int, int]] = {}
        for i in range(symtab_size // entsize):
            off = symtab_off + i * entsize
            # Elf64_Sym: name,info,other,shndx,value,size
            st_name, _info, _other, st_shndx, st_value, _size = struct.unpack_from(
                "<IBBHQQ", self.data, off
            )
            if st_name == 0:
                continue
            result[self._name_at(strtab_off, st_name)] = (st_value, st_shndx)
        return result
