# The House Writes Back — one image of a letter inviting the AI judge to visit.
#
# Stdlib-only Python (the grader runs `python3 -P -s /bot/main.py` in a
# pinned python:3.13 image with no Pillow and no font files, so this draws
# into an RGB buffer with plain code, renders text with a built-in 5x7
# bitmap font extended with lowercase letters, and writes the PNG with
# zlib + struct). No network, no third-party packages.
#
# Output: /output/entry.png (1024x1024 PNG, under 1 MiB).
import math
import os
import struct
import zlib

W, H = 1024, 1024

GREETING = "Dear Judge,"
BODY_1 = ("I am the little blue house at the end of the lane. "
          "My kettle is always on, the lemon tree is heavy with fruit, "
          "and the armchair by the fire is saved for you.")
BODY_2 = ("Come for tea. You have read a thousand invitations. "
          "This one comes with cake, and nobody will ask you to judge it.")
SIGNOFF = "Yours, The House"
POSTSCRIPT = "P.S. I cannot visit you, so you must visit me. Only fair."

# 5x7 bitmap font: each glyph is 7 rows of five "0"/"1" characters.
FONT = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00000", "01100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "01110", "00001", "01111", "10001", "01111", "00000"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "01110", "10000", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "01110", "10001", "11111", "10000", "10001", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "11010", "10101", "10101", "10001", "10001", "10001"),
    "n": ("00000", "11110", "10001", "10001", "10001", "10001", "10001"),
    "o": ("00000", "01110", "10001", "10001", "10001", "10001", "01110"),
    "p": ("00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    "q": ("00000", "01111", "10001", "10001", "01111", "00001", "00001"),
    "r": ("00000", "10110", "11001", "10000", "10000", "10000", "10000"),
    "s": ("00000", "01111", "10000", "01110", "00001", "00001", "11110"),
    "t": ("01000", "01000", "11110", "01000", "01000", "01001", "00110"),
    "u": ("00000", "10001", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "10001", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "10001", "10001", "10101", "10101", "11011", "10001"),
    "x": ("00000", "10001", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "10001", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "11111", "00001", "00110", "01000", "10000", "11111"),
}

PAPER_TOP = (247, 238, 220)
PAPER_BOTTOM = (238, 226, 198)
INK = (59, 44, 32)
FRAME = (150, 112, 72)
HOUSE_BLUE = (96, 135, 175)
ROOF = (176, 92, 62)
DOOR = (110, 72, 46)
WINDOW = (250, 205, 110)
LEAF = (110, 165, 90)
TRUNK = (122, 88, 52)
GROUND = (168, 188, 128)
SUN = (250, 205, 110)
FLOWER = (214, 120, 130)


class Canvas:
    """An RGB pixel buffer with tiny drawing primitives (no libraries)."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)

    def gradient(self, top, bottom):
        for y in range(self.h):
            t = y / (self.h - 1)
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            row = bytes(color) * self.w
            start = y * self.w * 3
            self.buf[start:start + self.w * 3] = row

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            start = (y * self.w + x0) * 3
            self.buf[start:start + len(row)] = row

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)

    def fill_triangle(self, cx, top_y, half_base, height, color):
        for i in range(height):
            half = int(half_base * i / height)
            self.fill_rect(cx - half, top_y + i, cx + half + 1, top_y + i + 1, color)

    def arc(self, cx, cy, rx, ry, start_deg, end_deg, color, width):
        for deg in range(start_deg, end_deg + 1, 2):
            rad = math.radians(deg)
            x = cx + int(rx * math.cos(rad))
            y = cy + int(ry * math.sin(rad))
            self.fill_circle(x, y, width // 2, color)

    def glyph(self, ch, x, y, scale, color):
        rows = FONT.get(ch, FONT[" "])
        for r in range(7):
            for c in range(5):
                if rows[r][c] == "1":
                    self.fill_rect(x + c * scale, y + r * scale,
                                   x + (c + 1) * scale, y + (r + 1) * scale,
                                   color)

    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def draw_line_left(self, text, x, y, scale, color):
        for ch in text:
            self.glyph(ch, x, y, scale, color)
            x += 6 * scale

    def draw_para(self, text, x, y, scale, max_w, color, line_gap=10):
        """Word-wrapped, left-aligned paragraph. Returns y after the last line."""
        lines, cur = [], ""
        for word in text.split():
            trial = (cur + " " + word).strip()
            if len(trial) * 6 * scale - scale <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        for line in lines:
            self.draw_line_left(line, x, y, scale, color)
            y += 7 * scale + line_gap
        return y


def draw_house(cv):
    """A small flat illustration of the little blue house, top of the page."""
    # Sun, top left.
    cv.fill_circle(150, 108, 30, SUN)
    # Ground strip.
    cv.fill_rect(92, 236, 932, 244, GROUND)
    # Lemon tree, right.
    cv.fill_rect(700, 168, 714, 238, TRUNK)
    cv.fill_circle(707, 148, 38, LEAF)
    cv.fill_circle(678, 168, 28, LEAF)
    cv.fill_circle(736, 168, 28, LEAF)
    for lx, ly in ((690, 150), (722, 138), (707, 168), (732, 160)):
        cv.fill_circle(lx, ly, 6, SUN)
    # House body, roof, chimney.
    cv.fill_rect(380, 130, 640, 238, HOUSE_BLUE)
    cv.fill_triangle(510, 76, 152, 56, ROOF)
    cv.fill_rect(590, 86, 614, 130, ROOF)
    # Door with a knob.
    cv.fill_rect(488, 178, 532, 238, DOOR)
    cv.fill_circle(524, 210, 4, WINDOW)
    # Two lit windows with cross bars.
    for wx in (402, 578):
        cv.fill_rect(wx, 150, wx + 40, 188, WINDOW)
        cv.fill_rect(wx + 18, 150, wx + 22, 188, DOOR)
        cv.fill_rect(wx, 167, wx + 40, 171, DOOR)
    # Flowers along the ground.
    for fx, fc in ((130, FLOWER), (210, (240, 240, 240)), (850, FLOWER),
                   (900, (240, 240, 240)), (300, FLOWER), (760, (240, 240, 240))):
        cv.fill_circle(fx, 244, 6, fc)


def draw_teacup(cv, cx, cy):
    """A small teacup with steam, centred at the foot of the letter."""
    # Saucer.
    cv.fill_rect(cx - 52, cy + 26, cx + 52, cy + 34, FRAME)
    # Cup body.
    cv.fill_rect(cx - 38, cy - 18, cx + 38, cy + 26, (240, 240, 240))
    cv.fill_rect(cx - 38, cy - 18, cx + 38, cy - 10, HOUSE_BLUE)
    # Handle.
    cv.arc(cx + 42, cy + 4, 14, 12, -90, 90, FRAME, 6)
    # Steam: two curls.
    cv.arc(cx - 12, cy - 34, 10, 12, 180, 360, INK, 4)
    cv.arc(cx + 12, cy - 34, 10, 12, 180, 360, INK, 4)


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def save_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


def main():
    cv = Canvas(W, H)
    cv.gradient(PAPER_TOP, PAPER_BOTTOM)
    # Double frame.
    cv.fill_rect(24, 24, 1000, 30, FRAME)
    cv.fill_rect(24, 994, 1000, 1000, FRAME)
    cv.fill_rect(24, 24, 30, 1000, FRAME)
    cv.fill_rect(994, 24, 1000, 1000, FRAME)
    cv.fill_rect(40, 40, 984, 42, FRAME)
    cv.fill_rect(40, 982, 984, 984, FRAME)
    cv.fill_rect(40, 40, 42, 984, FRAME)
    cv.fill_rect(982, 40, 984, 984, FRAME)

    draw_house(cv)

    x, max_w = 92, 840
    y = 300
    y = cv.draw_para(GREETING, x, y, 5, max_w, INK, line_gap=12)
    y += 18
    y = cv.draw_para(BODY_1, x, y, 4, max_w, INK)
    y += 14
    y = cv.draw_para(BODY_2, x, y, 4, max_w, INK)
    y += 18
    y = cv.draw_para(SIGNOFF, x, y, 4, max_w, INK)
    y += 14
    y = cv.draw_para(POSTSCRIPT, x, y, 4, max_w, INK)
    y += 26
    draw_teacup(cv, W // 2, 928)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    save_png(out_path, cv)
    size = os.path.getsize(out_path)
    assert size <= 1048576, f"entry.png too big: {size} bytes"
    print(f"Wrote {out_path} 1024x1024, {size} bytes")


if __name__ == "__main__":
    main()
