"""Frame statistics for screenshots (stdlib only: zlib PNG decoder, 8-bit RGB/RGBA, non-interlaced).

Usage: frame_stats.py <png>... [--grid N]
Per frame: lit = fraction of pixels with max(r,g,b) > 16; mean = mean luminance (0-255);
uniq = distinct colours in a 64x36 sample (UI-only screens have few, 3D scenes many);
with --grid N, the lit fraction per cell of an N x N grid (where the content is).
Used to judge render changes without looking at the images (phase 4 window gate).
"""
import struct
import sys
import zlib


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat, w = 8, b"", None
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and ctype in (2, 6) and inter == 0, f"unsupported PNG {depth} {ctype} {inter}"
            bpp = 3 if ctype == 2 else 4
        elif typ == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line))
        prev = line
    return w, h, bpp, rows


def stats(path, grid=0):
    w, h, bpp, rows = read_png(path)
    lit = 0
    lum = 0
    cells = [[0] * grid for _ in range(grid)] if grid else None
    step = 4  # sample every 4th pixel in x and y
    n = 0
    for y in range(0, h, step):
        r = rows[y]
        for x in range(0, w, step):
            o = x * bpp
            R, G, B = r[o], r[o + 1], r[o + 2]
            n += 1
            lum += (R * 299 + G * 587 + B * 114) // 1000
            if max(R, G, B) > 16:
                lit += 1
                if grid:
                    cells[y * grid // h][x * grid // w] += 1
    uniq = {rows[y][x * bpp:x * bpp + 3] for y in range(0, h, max(1, h // 36)) for x in range(0, w, max(1, w // 64))}
    out = {"lit": round(lit / n, 3), "mean": round(lum / n, 1), "uniq": len(uniq)}
    if grid:
        per = n / (grid * grid)
        out["grid"] = [[round(v / per, 2) for v in row] for row in cells]
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    grid = 0
    if "--grid" in args:
        k = args.index("--grid")
        grid = int(args[k + 1])
        del args[k:k + 2]
    for p in args:
        try:
            print(p.replace("\\", "/").split("/")[-1], stats(p, grid))
        except Exception as e:  # report and continue
            print(p, "ERROR", e)
