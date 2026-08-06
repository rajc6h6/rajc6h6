#!/usr/bin/env python3
"""
Step 2 — make_ascii_svg.py
Converts source-prepped.png into an animated SVG ASCII portrait.
- 100×53 character grid
- Density ramp: ' .`:-=+*cs#%@'  (bright→sparse, dark→dense)
- Monochrome light-gray fill
- SMIL animation: per-row clip-path wipe left→right, cursor rides edge
- Plays once and freezes (no loop)
Output: raj-ascii.svg
"""

import pathlib
import numpy as np
from PIL import Image

INPUT   = pathlib.Path("source-prepped.png")
OUTPUT  = pathlib.Path("raj-ascii.svg")

COLS    = 100
ROWS    = 53
# char aspect ratio compensation: a character cell is ~2× taller than wide
ASPECT  = 2.0

RAMP    = ' .`:-=+*cs#%@'   # index 0 = bright/blank, last = darkest
FILL_COLOR = "#c8ccd4"      # light gray, monochrome
BG_COLOR   = "#0d1117"      # GitHub dark

FONT_SIZE  = 8              # px, monospace
CHAR_W     = FONT_SIZE * 0.6
CHAR_H     = FONT_SIZE

SVG_W  = int(COLS * CHAR_W) + 8
SVG_H  = int(ROWS * CHAR_H) + 8
PAD_X  = 4
PAD_Y  = 4

# Per-row timing
ROW_DURATION  = 0.06   # seconds each row takes to wipe
ROW_GAP       = 0.04   # stagger delay between rows
CURSOR_W      = CHAR_W * 1.2
FREEZE_EXTRA  = 1.0    # extra hold at end before freeze

total_dur = ROWS * ROW_GAP + ROW_DURATION + FREEZE_EXTRA

def img_to_chars(path: pathlib.Path) -> list[str]:
    img = Image.open(path).convert("L")
    # Resize preserving aspect ratio with char-cell compensation
    target_w = COLS
    target_h = ROWS
    img = img.resize((target_w, int(target_h * ASPECT)), Image.LANCZOS)
    img = img.resize((target_w, target_h), Image.LANCZOS)
    arr = np.array(img)
    rows_out = []
    for row in arr:
        line = ""
        for px in row:
            idx = int(px / 255 * (len(RAMP) - 1))
            line += RAMP[idx]
        rows_out.append(line)
    return rows_out

def escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))

def build_svg(rows: list[str]) -> str:
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg"')
    lines.append(f'     xmlns:xlink="http://www.w3.org/1999/xlink"')
    lines.append(f'     width="{SVG_W}" height="{SVG_H}"')
    lines.append(f'     viewBox="0 0 {SVG_W} {SVG_H}"')
    lines.append(f'     role="img" aria-label="ASCII portrait of raj">')

    # background
    lines.append(f'  <rect width="{SVG_W}" height="{SVG_H}" fill="{BG_COLOR}"/>')

    lines.append('  <defs>')

    # One clipPath per row — animates from 0→full width
    for r in range(len(rows)):
        clip_id = f"clip-r{r}"
        y_top = PAD_Y + r * CHAR_H
        lines.append(f'    <clipPath id="{clip_id}">')
        lines.append(f'      <rect id="cr{r}" x="{PAD_X}" y="{y_top}" width="0" height="{CHAR_H + 1}">')
        delay  = r * ROW_GAP
        # width animates 0 → full_row_width
        row_w  = SVG_W - PAD_X * 2
        begin  = f"{delay:.3f}s"
        end_t  = f"{delay + ROW_DURATION:.3f}s"
        freeze_t = f"{total_dur:.3f}s"
        lines.append(f'        <animate attributeName="width"')
        lines.append(f'                 from="0" to="{row_w}"')
        lines.append(f'                 begin="{begin}" dur="{ROW_DURATION}s"')
        lines.append(f'                 fill="freeze" calcMode="spline"')
        lines.append(f'                 keySplines="0.4 0 0.6 1"/>')
        lines.append(f'      </rect>')
        lines.append(f'    </clipPath>')

    lines.append('  </defs>')

    # Text rows clipped
    lines.append(f'  <g font-family="\'Courier New\', Courier, monospace"')
    lines.append(f'     font-size="{FONT_SIZE}" fill="{FILL_COLOR}"')
    lines.append(f'     xml:space="preserve">')
    for r, row_text in enumerate(rows):
        y  = PAD_Y + (r + 1) * CHAR_H - 1   # text baseline
        xt = PAD_X
        lines.append(f'    <text clip-path="url(#clip-r{r})" x="{xt}" y="{y}">{escape(row_text)}</text>')
    lines.append('  </g>')

    # Cursor — a thin bright rect that rides the wipe edge of the current row
    # Implemented as multiple rects (one per row), each visible only during its row's wipe
    lines.append('  <g id="cursors">')
    for r in range(len(rows)):
        delay   = r * ROW_GAP
        # Show cursor for this row during the row's wipe window
        appear  = f"{delay:.3f}s"
        vanish  = f"{delay + ROW_DURATION + ROW_GAP:.3f}s"
        y_top   = PAD_Y + r * CHAR_H
        cx      = PAD_X  # will animate x alongside the clip
        # cursor x trails the clip edge
        lines.append(f'    <rect id="cur{r}" x="{cx}" y="{y_top}"')
        lines.append(f'          width="{CURSOR_W:.1f}" height="{CHAR_H}"')
        lines.append(f'          fill="#58a6ff" opacity="0">')
        # Fade in at row start
        lines.append(f'      <animate attributeName="opacity"')
        lines.append(f'               values="0;0.85;0"')
        lines.append(f'               keyTimes="0;0.5;1"')
        lines.append(f'               begin="{appear}" dur="{ROW_DURATION + ROW_GAP:.3f}s"')
        lines.append(f'               fill="freeze"/>')
        # Move x across the row
        row_w = SVG_W - PAD_X * 2
        lines.append(f'      <animate attributeName="x"')
        lines.append(f'               from="{PAD_X}" to="{PAD_X + row_w:.1f}"')
        lines.append(f'               begin="{appear}" dur="{ROW_DURATION:.3f}s"')
        lines.append(f'               fill="freeze"/>')
        lines.append(f'    </rect>')
    lines.append('  </g>')

    lines.append('</svg>')
    return '\n'.join(lines)


if __name__ == "__main__":
    if not INPUT.exists():
        raise FileNotFoundError(f"Run prep_photo.py first — {INPUT} not found")
    print(f"[make_ascii_svg] Reading {INPUT} ...")
    rows = img_to_chars(INPUT)
    svg  = build_svg(rows)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"[make_ascii_svg] Saved -> {OUTPUT}  ({COLS}x{ROWS} chars, {len(svg):,} bytes)")
