"""Create a small plx.learnSQL .ico (32x32) without extra dependencies."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

SIZE = 32
BG = (7, 11, 20, 255)
ACCENT = (62, 224, 197, 255)
INK = (4, 37, 30, 255)


def pixel(x: int, y: int) -> tuple[int, int, int, int]:
    # dark rounded tile
    dx = min(x, SIZE - 1 - x)
    dy = min(y, SIZE - 1 - y)
    if dx < 2 or dy < 2:
        return (0, 0, 0, 0)
    if dx < 4 or dy < 4:
        return ACCENT
    color = BG
    # elephant-ish blob
    if 8 <= x <= 23 and 9 <= y <= 22:
        color = ACCENT
    if 20 <= x <= 26 and 14 <= y <= 18:
        color = ACCENT
    if 24 <= x <= 28 and 17 <= y <= 22:
        color = ACCENT
    # eye
    if 12 <= x <= 14 and 13 <= y <= 15:
        color = INK
    return color


def build_ico() -> bytes:
    # 32bpp XOR bitmap, bottom-up, plus AND mask
    header = struct.pack("<IIIHHIIIIII", 40, SIZE, SIZE * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    xor = bytearray()
    for y in range(SIZE - 1, -1, -1):
        for x in range(SIZE):
            r, g, b, a = pixel(x, y)
            xor += struct.pack("BBBB", b, g, r, a)
    # AND mask: 1 bit per pixel, 32-bit padded rows
    mask = bytearray()
    for y in range(SIZE - 1, -1, -1):
        row = 0
        for x in range(SIZE):
            r, g, b, a = pixel(x, y)
            bit = 1 if a == 0 else 0
            row = (row << 1) | bit
        mask += struct.pack(">I", row)
    image = header + xor + mask
    # ICONDIR + ICONDIRENTRY
    reserved = 0
    ico_type = 1
    count = 1
    planes = 1
    bitcount = 32
    offset = 6 + 16
    entry = struct.pack(
        "<BBBBHHII",
        SIZE,
        SIZE,
        0,
        0,
        planes,
        bitcount,
        len(image),
        offset,
    )
    return struct.pack("<HHH", reserved, ico_type, count) + entry + image


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "flowapp.ico")
    out.write_bytes(build_ico())
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
