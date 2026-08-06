#!/usr/bin/env python3
"""
Step 3 — make_info_card.py
Generates a neofetch-style SVG info card with animated row fade+slide-in.
Set STATIC=1 env var for a frozen frame (local preview).
Output: info-card.svg
"""

import os
import pathlib

OUTPUT = pathlib.Path("info-card.svg")
STATIC = os.environ.get("STATIC", "0") == "1"

# ── Design tokens ──────────────────────────────────────────────
W           = 490
BG          = "#0d1117"
BORDER      = "#30363d"
TITLE_BG    = "#161b22"
TITLE_FG    = "#c9d1d9"
KEY_FG      = "#58a6ff"   # blue
VAL_FG      = "#c9d1d9"   # light gray
DIM_FG      = "#8b949e"   # dim gray for secondary lines
GREEN       = "#3fb950"
ORANGE      = "#e3b341"
PINK        = "#f78166"

FONT        = "'Courier New', Courier, monospace"
FONT_SIZE   = 12
LINE_H      = 19
PAD_X       = 16
PAD_Y       = 14
TITLE_H     = 32
CORNER      = 6

# Row stagger timing
ROW_DUR     = 0.25   # seconds per row animation
ROW_GAP     = 0.07   # stagger between rows
SLIDE_PX    = 12     # pixels to slide from left

# ── Content rows ───────────────────────────────────────────────
# Each entry: (key, value, value_color, is_continuation)
ROWS = [
    ("User",       "raj@github",                                                   GREEN,   False),
    ("OS",         "B.Arch, IIT Roorkee (2024–2029)",                              VAL_FG,  False),
    ("Host",       "Founder & AI Systems Engineer, Synlitics",                     ORANGE,  False),
    ("Now",        "GSoC 2026 @ KolibriOS · Building agentic AI systems",          VAL_FG,  False),
    ("Prev",       "AI Product Intern, OkCredit Future Founders (ranked 7th/1032)",VAL_FG,  False),
    ("Stack",      "LangGraph · PydanticAI · FastMCP · pgvector · FastAPI · Logfire", KEY_FG, False),
    ("Highlights", "Contract Intelligence Engine (LangGraph + pgvector hybrid RAG)", VAL_FG, False),
    ("",           "Dependency Drift Sentinel (CVE auditor, CI-gated)",            DIM_FG,  True),
    ("",           "Shadow-Mode AI Deployment Proxy (74% cost ↓ via caching)",     DIM_FG,  True),
    ("Location",   "India  (Open to remote)",                                      VAL_FG,  False),
]

def esc(s):
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&apos;"))

def build_svg() -> str:
    # Calculate total height
    n_rows = len(ROWS)
    body_h = PAD_Y + n_rows * LINE_H + PAD_Y
    total_h = TITLE_H + body_h + 2  # +2 for bottom border

    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg"')
    out.append(f'     width="{W}" height="{total_h}"')
    out.append(f'     viewBox="0 0 {W} {total_h}"')
    out.append(f'     role="img" aria-label="raj profile info card">')

    # ── Styles (CSS keyframes for animation) ──
    if not STATIC:
        animations_css = ""
        for i in range(n_rows):
            delay = i * ROW_GAP
            animations_css += f"""
        @keyframes rowIn{i} {{
          0%   {{ opacity: 0; transform: translateX(-{SLIDE_PX}px); }}
          100% {{ opacity: 1; transform: translateX(0); }}
        }}
        .row{i} {{
          animation: rowIn{i} {ROW_DUR}s ease-out {delay:.3f}s both;
          animation-fill-mode: forwards;
        }}"""
    else:
        animations_css = ""
        for i in range(n_rows):
            animations_css += f"\n        .row{i} {{ opacity: 1; }}"

    out.append(f'  <style>')
    out.append(f'    text {{ dominant-baseline: middle; }}')
    out.append(animations_css)
    out.append(f'  </style>')

    # ── Background + border ──
    out.append(f'  <rect width="{W}" height="{total_h}"')
    out.append(f'        rx="{CORNER}" ry="{CORNER}"')
    out.append(f'        fill="{BG}" stroke="{BORDER}" stroke-width="1"/>')

    # ── Title bar ──
    out.append(f'  <rect width="{W}" height="{TITLE_H}"')
    out.append(f'        rx="{CORNER}" ry="{CORNER}" fill="{TITLE_BG}"/>')
    out.append(f'  <rect y="{TITLE_H - CORNER}" width="{W}" height="{CORNER}" fill="{TITLE_BG}"/>')
    out.append(f'  <rect y="{TITLE_H}" width="{W}" height="1" fill="{BORDER}"/>')

    # Traffic-light dots
    for xi, color in [(14, PINK), (32, ORANGE), (50, GREEN)]:
        out.append(f'  <circle cx="{xi}" cy="{TITLE_H // 2}" r="5" fill="{color}"/>')

    # Title text
    title_txt = "raj@github: ~/info"
    out.append(f'  <text x="{W // 2}" y="{TITLE_H // 2}"')
    out.append(f'        font-family={FONT!r} font-size="12"')
    out.append(f'        fill="{TITLE_FG}" text-anchor="middle">{esc(title_txt)}</text>')

    # ── Info rows ──
    KEY_W = 70   # fixed key column width
    COLON_W = 10

    for i, (key, val, val_color, is_cont) in enumerate(ROWS):
        y = TITLE_H + PAD_Y + i * LINE_H + LINE_H // 2
        cls = f"row{i}"

        out.append(f'  <g class="{cls}">')
        if is_cont:
            # Continuation line: indented value only
            x_val = PAD_X + KEY_W + COLON_W
            out.append(f'    <text x="{x_val}" y="{y}"')
            out.append(f'          font-family={FONT!r} font-size="{FONT_SIZE}"')
            out.append(f'          fill="{val_color}">{esc(val)}</text>')
        else:
            # Key
            out.append(f'    <text x="{PAD_X}" y="{y}"')
            out.append(f'          font-family={FONT!r} font-size="{FONT_SIZE}"')
            out.append(f'          fill="{KEY_FG}" font-weight="bold">{esc(key)}</text>')
            # Colon
            colon_x = PAD_X + KEY_W
            out.append(f'    <text x="{colon_x}" y="{y}"')
            out.append(f'          font-family={FONT!r} font-size="{FONT_SIZE}"')
            out.append(f'          fill="{DIM_FG}">:</text>')
            # Value
            val_x = colon_x + COLON_W
            out.append(f'    <text x="{val_x}" y="{y}"')
            out.append(f'          font-family={FONT!r} font-size="{FONT_SIZE}"')
            out.append(f'          fill="{val_color}">{esc(val)}</text>')
        out.append(f'  </g>')

    out.append('</svg>')
    return '\n'.join(out)


if __name__ == "__main__":
    svg = build_svg()
    OUTPUT.write_text(svg, encoding="utf-8")
    mode = "static" if STATIC else "animated"
    print(f"[make_info_card] Saved -> {OUTPUT}  ({mode}, {len(svg):,} bytes)")
