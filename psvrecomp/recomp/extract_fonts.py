"""Extract open replacement shared fonts (TTF) from a local Eden source tree into a font dir for pl:u.

Eden/yuzu embed open-licensed fonts as C++ byte arrays (src/core/file_sys/system_archive/data/font_*.cpp). We only
read the bytes at build time into lab/sysfont/<type>.ttf (private, git-ignored); no Eden code enters the project.
Prefer the console's own system fonts (title 0100000000000810.. dumped with nxdumptool) when available.

Usage: extract_fonts.py <eden_src_dir> <out_dir>
"""
import os
import re
import sys

TYPES = ['font_standard', 'font_chinese_simplified', 'font_extended_chinese_simplified',
         'font_chinese_traditional', 'font_korean', 'font_nintendo_extended']
src, out = sys.argv[1], sys.argv[2]
d = os.path.join(src, 'core', 'file_sys', 'system_archive', 'data')
os.makedirs(out, exist_ok=True)
for i, name in enumerate(TYPES):
    text = open(os.path.join(d, name + '.cpp'), encoding='utf-8').read()
    m = re.search(r'std::array<unsigned char, (\d+)>\s+\w+\{\{(.*?)\}\};', text, re.S)
    size, body = int(m.group(1)), m.group(2)
    data = bytes(int(x, 16) for x in re.findall(r'0x([0-9a-fA-F]{2})', body))
    assert len(data) == size, (name, len(data), size)
    open(os.path.join(out, f'{i}.ttf'), 'wb').write(data)
    print(f'{i}.ttf  {name}  {size} bytes  sfnt={data[:4].hex()}')
