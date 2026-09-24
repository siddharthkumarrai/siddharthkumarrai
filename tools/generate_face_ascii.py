#!/usr/bin/env python3
"""
Generate a high-accuracy ASCII portrait + biometric-HUD block for the
GitHub profile README.

Outputs (all under ./assets):
  siddharth-face.txt              raw ASCII portrait
  siddharth-face-hud.txt          HUD block (framed face only) for README
  siddharth-face-scan-preview.png styled preview render
  siddharth-face-scan.gif         animated scan-line GIF (README hero)

Usage:
  python tools/generate_face_ascii.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SRC = ASSETS / "sidd image.jpeg"

# crop of the head (x0, y0, x1, y1) on the 960x1280 source photo
# (tight portrait: hair-top -> beard bottom; the face fills the grid so
#  no rows are wasted on torso, and the block stays ~25% shorter)
CROP = (206, 135, 784, 785)

FACE_COLS = 78          # width of the ASCII portrait in characters
# rendered cell aspect for Consola 15px (advance 8px, line height 18px):
# rows = h/w * cols * CELL — chars are 2.25x taller than wide, so using
# 0.5 here would stretch the face ~12% vertically
CELL = 8.0 / 18.0
GAMMA = 0.85            # <1 brightens midtones (skin) so features stay open
AUTOCONTRAST_CUTOFF = 2 # ignore extreme % when stretching levels
HI_GAIN = 1.6           # grid-space local-contrast gain (eyes/lips/nostrils)
HI_CLIP_SIGMA = 2.2     # contrast limit on the high-pass (no background speckle)

# light -> dark ramp: LIGHT pixels map to DENSE chars (index 0 = brightest),
# so on a dark terminal background the portrait reads like the real photo
# (bright skin/wall, dark hair/features carved out) — the video look.
RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,\"^`'. "

# HUD / render styling
FG = (69, 245, 199)         # #45F5C7 terminal green
FG_DIM = (46, 130, 110)
BG = (8, 12, 14)

NAME = "SIDDHARTH KUMAR RAI"



# --------------------------------------------------------------------------
# ascii generation
# --------------------------------------------------------------------------
def to_ascii(img: Image.Image, cols: int) -> list[str]:
    """Map a grayscale image to ASCII rows with aspect-ratio correction."""
    w, h = img.size
    rows = max(1, round(h / w * cols * CELL))  # true rendered cell aspect
    small = img.resize((cols, rows), Image.LANCZOS)
    small = enhance_grid(small)                # contrast where 1 px = 1 cell
    px = list(small.tobytes())          # L-mode: one byte per pixel
    n = len(RAMP)
    lines = []
    for r in range(rows):
        band = px[r * cols:(r + 1) * cols]
        lines.append("".join(RAMP[min(n - 1, (255 - v) * n // 256)] for v in band))
    return lines


def prepare(src: Image.Image) -> Image.Image:
    """Crop + denoise the photo; contrast is enhanced later, on the grid."""
    g = src.convert("L").crop(CROP)
    g = ImageOps.autocontrast(g, cutoff=AUTOCONTRAST_CUTOFF)
    # smooth wall/sensor grain before the downscale turns it into blotches
    return g.filter(ImageFilter.GaussianBlur(0.8))


def enhance_grid(grid: Image.Image) -> Image.Image:
    """Carve fine features (eyes, nostrils, lips, beard line) at grid scale.

    Sharpening at full resolution vanishes in the downscale to ~78 cols, so
    every contrast step runs here instead, where one pixel == one ASCII cell.
    """
    a = np.asarray(grid, dtype=np.float32)
    lo = np.asarray(grid.filter(ImageFilter.GaussianBlur(2.0)), dtype=np.float32)
    hi = a - lo
    limit = HI_CLIP_SIGMA * float(hi.std()) + 1e-6   # contrast-limited: no speckle
    hi = np.clip(hi, -limit, limit)
    out = lo + HI_GAIN * hi                          # amplify local details
    p_lo, p_hi = np.percentile(out, (1, 99))         # full ramp gets used
    out = (out - p_lo) * (255.0 / max(p_hi - p_lo, 1e-6))
    g = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "L")
    # crisp cell-level edges + gamma so skin midtones stay open
    g = g.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=0))
    lut = [min(255, round(255 * ((i / 255) ** GAMMA))) for i in range(256)]
    return g.point(lut)


# --------------------------------------------------------------------------
# hud composition
# --------------------------------------------------------------------------
def build_hud(face: list[str]) -> str:
    """Compose the biometric HUD: ASCII face only, inside a terminal frame."""
    face_w = FACE_COLS
    inner = face_w + 2
    sep = "+" + "-" * (inner + 2) + "+"

    def row(text: str = "") -> str:
        return "| " + text.ljust(inner) + " |"

    lines = [sep]
    title = " PROFILE // BIOMETRIC ASCII SCAN"
    name = NAME.replace(" ", "_")
    lines.append("| " + title.ljust(inner - len(name)) + name + " |")
    lines.append(sep)

    # left column: subject header + scan bar + face
    # NOTE: every left chunk must stay <= inner so the frame edge aligns.
    left = [(" SUBJECT: FACE_ASCII").ljust(face_w - 7) + " [ LIVE ]",
            (" " + "█" * (face_w - 1)).ljust(face_w + 2)]
    left += [" " + ln for ln in face]
    left.append("")
    left.append((" SCAN 100%   SIGNAL " + "████████").ljust(face_w + 2))

    for l in left:
        lines.append(row(l))
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
