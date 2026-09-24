#!/usr/bin/env python3
"""
Generate a high-accuracy ASCII portrait + biometric-HUD block for the
GitHub profile README.

Outputs (all under ./assets):
  siddharth-face.txt              raw ASCII portrait
  siddharth-face-hud.txt          HUD block (face + profile panel) for README
  siddharth-face-scan-preview.png styled preview render
  siddharth-face-scan.gif         animated scan-line GIF (README hero)

Usage:
  python tools/generate_face_ascii.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SRC = ASSETS / "sidd image.jpeg"

# crop of the bust (x0, y0, x1, y1) on the 960x1280 source photo
# (tight on head+shoulders, excludes the plant on the right)
CROP = (170, 130, 800, 1040)

FACE_COLS = 78          # width of the ASCII portrait in characters
GAMMA = 0.85            # <1 brightens midtones (skin) so features stay open
AUTOCONTRAST_CUTOFF = 2 # ignore extreme % when stretching levels

# light -> dark ramp: LIGHT pixels map to DENSE chars (index 0 = brightest),
# so on a dark terminal background the portrait reads like the real photo
# (bright skin/wall, dark hair/features carved out) — the video look.
RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,\"^`'. "

# HUD / render styling
FG = (69, 245, 199)         # #45F5C7 terminal green
FG_DIM = (46, 130, 110)
BG = (8, 12, 14)
PANEL_W = 34                # width of the right-hand profile panel

IDENTITY = "SIDDHARTH KUMAR RAI"
ROLE = "PRODUCT ENGINEER"
FOCUS = "AGENTIC AI / FULL-STACK"
STACK = "NEXT.JS · NODE · PYTHON"
STATUS = "OPEN TO WORK"
GITHUB = "github.com/siddharthkumarrai"
LOCATION = "DELHI, INDIA"

PANEL_ROWS = [
    ("IDENTITY", IDENTITY),
    ("ROLE", ROLE),
    ("FOCUS", FOCUS),
    ("STACK", STACK),
    ("STATUS", STATUS),
    ("GITHUB", GITHUB),
    ("LOCATION", LOCATION),
]



# --------------------------------------------------------------------------
# ascii generation
# --------------------------------------------------------------------------
def to_ascii(img: Image.Image, cols: int) -> list[str]:
    """Map a grayscale image to ASCII rows with aspect-ratio correction."""
    w, h = img.size
    rows = max(1, round(h / w * cols * 0.5))  # chars are ~2x taller than wide
    small = img.resize((cols, rows), Image.LANCZOS)
    px = list(small.tobytes())          # L-mode: one byte per pixel
    n = len(RAMP)
    lines = []
    for r in range(rows):
        band = px[r * cols:(r + 1) * cols]
        lines.append("".join(RAMP[min(n - 1, v * n // 256)] for v in band))
    return lines


def prepare(src: Image.Image) -> Image.Image:
    """Crop + normalize the photo for maximum feature contrast."""
    g = src.convert("L").crop(CROP)
    g = ImageOps.autocontrast(g, cutoff=AUTOCONTRAST_CUTOFF)
    # smooth wall/sensor grain, then re-sharpen the big features
    # (eyes, nose, beard line) so they survive the downscale to 78 cols
    g = g.filter(ImageFilter.GaussianBlur(0.8))
    g = g.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=2))
    # gamma correction
    lut = [min(255, round(255 * ((i / 255) ** GAMMA))) for i in range(256)]
    return g.point(lut)


# --------------------------------------------------------------------------
# hud composition
# --------------------------------------------------------------------------
def wrap_panel(value: str, width: int) -> list[str]:
    return textwrap.wrap(value, width=width) or [""]


def build_hud(face: list[str]) -> str:
    """Compose the biometric HUD: ASCII face left, profile panel right."""
    face_w = FACE_COLS
    inner = face_w + 3 + PANEL_W
    sep = "+" + "-" * (inner + 2) + "+"

    def row(left: str = "", right: str = "") -> str:
        return "| " + left.ljust(face_w + 2) + right.ljust(PANEL_W) + " |"

    lines = [sep]
    title = " PROFILE // BIOMETRIC ASCII SCAN"
    lines.append("| " + title.ljust(inner - len("SIDDHARTH_KUMAR_RAI") - 2)
                 + "SIDDHARTH_KUMAR_RAI |")
    lines.append(sep)

    # build panel column: header, then labelled fields
    panel: list[str] = [" PROFILE DATA".ljust(PANEL_W), ""]
    for i, (label, value) in enumerate(PANEL_ROWS):
        if i:
            panel.append("")
        panel.append((" " + label).ljust(PANEL_W))
        for j, chunk in enumerate(wrap_panel(value, PANEL_W - 2)):
            panel.append(("  " + chunk if j == 0 else "    " + chunk).ljust(PANEL_W))

    # left column: subject header + scan bar + face
    # NOTE: every left chunk must stay <= face_w + 2 so the right panel
    # always starts on the same column.
    left = [(" SUBJECT: FACE_ASCII").ljust(face_w - 7) + " [ LIVE ]",
            (" " + "█" * (face_w - 1)).ljust(face_w + 2)]
    left += [" " + ln for ln in face]
    left.append("")
    left.append((" SCAN 100%   SIGNAL " + "████████").ljust(face_w + 2))

    height = max(len(left), len(panel))
    left += [""] * (height - len(left))
    panel += [""] * (height - len(panel))

    for l, p in zip(left, panel):
        lines.append(row(l, p))
    lines.append(sep)
    return "\n".join(lines)



# --------------------------------------------------------------------------
# preview rendering (PNG / GIF)
# --------------------------------------------------------------------------
def _font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("consola.ttf", "cour.ttf", "C:/Windows/Fonts/consola.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _measure(hud_lines: list[str], font: ImageFont.FreeTypeFont, pad: int):
    sample = "M" * len(hud_lines[0])
    bbox = font.getbbox(sample)
    cw = (bbox[2] - bbox[0]) / len(sample)
    ch = font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + 5
    w = int(len(hud_lines[0]) * cw + pad * 2)
    h = int(len(hud_lines) * ch + pad * 2)
    return cw, ch, w, h


def render_hud_png(hud: str, path: Path) -> None:
    font = _font(15)
    pad = 24
    lines = hud.split("\n")
    _, ch, w, h = _measure(lines, font, pad)

    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    y = pad
    for line in lines:
        color = FG if line.startswith("+") or "BIOMETRIC" in line else FG_DIM
        d.text((pad, y), line, font=font, fill=color)
        y += ch
    for yy in range(0, h, 4):          # CRT scanline texture
        d.line([(0, yy), (w, yy)], fill=(6, 10, 12))
    img.save(path)


def render_gif(hud: str, path: Path, frames: int = 24) -> None:
    """Animated scan-line sweep over the HUD, like the reference video."""
    font = _font(15)
    pad = 24
    lines = hud.split("\n")
    _, ch, w, h = _measure(lines, font, pad)

    frames_img: list[Image.Image] = []
    for f in range(frames):
        img = Image.new("RGB", (w, h), BG)
        d = ImageDraw.Draw(img)
        scan_y = int(h * f / frames)
        y = pad
        for line in lines:
            if scan_y <= y <= scan_y + ch:
                color = (180, 255, 235)          # highlighted by scan bar
            elif line.startswith("+") or "BIOMETRIC" in line:
                color = FG
            else:
                color = FG_DIM
            d.text((pad, y), line, font=font, fill=color)
            y += ch
        d.rectangle([pad, scan_y, w - pad, scan_y + 3], fill=(120, 255, 220))
        for yy in range(0, h, 4):
            d.line([(0, yy), (w, yy)], fill=(6, 10, 12))
        frames_img.append(img.convert("P", palette=Image.ADAPTIVE, colors=48))

    frames_img[0].save(
        path,
        save_all=True,
        append_images=frames_img[1:],
        duration=100,
        loop=0,
        optimize=True,
    )


# --------------------------------------------------------------------------
def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    src = Image.open(SRC)
    face = to_ascii(prepare(src), FACE_COLS)

    (ASSETS / "siddharth-face.txt").write_text("\n".join(face), encoding="utf-8")

    hud = build_hud(face)
    (ASSETS / "siddharth-face-hud.txt").write_text(hud, encoding="utf-8")

    render_hud_png(hud, ASSETS / "siddharth-face-scan-preview.png")
    render_gif(hud, ASSETS / "siddharth-face-scan.gif", frames=18)

    print(f"face : {FACE_COLS}x{len(face)} chars")
    print(f"hud  : {len(hud.splitlines()[0])} cols x {len(hud.splitlines())} rows")
    print("wrote:", ", ".join(p.name for p in sorted(ASSETS.iterdir())))


if __name__ == "__main__":
    main()
