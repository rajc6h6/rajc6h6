#!/usr/bin/env python3
"""
Step 5 — render_heatmap_svg.py
Renders data/contributions.json as an animated 53-week × 7-day contribution
heatmap SVG (GitHub-style).

Animation: diagonal line-after-line slide-down reveal, CSS keyframes, plays
once and freezes (animation-fill-mode: forwards, no iteration-count repeat).

Output: contrib-heatmap.svg
"""

import json
import math
import pathlib
from datetime import date, timedelta

INPUT  = pathlib.Path("data/contributions.json")
OUTPUT = pathlib.Path("contrib-heatmap.svg")

# ── Palette (index = data-level 0–5) ──────────────────────────
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG      = "#0d1117"
BORDER  = "#30363d"
FG      = "#8b949e"
FG_HI   = "#c9d1d9"

# ── Layout ─────────────────────────────────────────────────────
CELL     = 12    # px square
CELL_GAP = 3     # px gap between cells
CELL_R   = 2     # corner radius
COLS     = 53    # weeks
ROWS     = 7     # days per week

MARGIN_TOP    = 28   # for month labels
MARGIN_LEFT   = 30   # for day-of-week labels
MARGIN_BOTTOM = 40   # for legend + stats
MARGIN_RIGHT  = 10

GRID_W = COLS * (CELL + CELL_GAP) - CELL_GAP
GRID_H = ROWS * (CELL + CELL_GAP) - CELL_GAP

W = MARGIN_LEFT + GRID_W + MARGIN_RIGHT
H = MARGIN_TOP  + GRID_H + MARGIN_BOTTOM

FONT = "'Segoe UI', system-ui, sans-serif"
MONO = "'Courier New', Courier, monospace"

# ── Animation ─────────────────────────────────────────────────
# Diagonal reveal: each diagonal d = col + row gets a staggered delay.
# Total diagonals = (COLS-1) + (ROWS-1) = 58
TOTAL_DIAGS  = COLS + ROWS - 1
DIAG_DUR     = 0.18   # seconds per diagonal to fade/slide in
DIAG_GAP     = 0.03   # stagger between diagonals

SLIDE_PX = 6   # pixels cell slides down on reveal

def load_data():
    data  = json.loads(INPUT.read_text())
    days  = data["days"]
    stats = data["stats"]
    day_map = {d["date"]: d for d in days}
    return day_map, stats

def build_week_grid(day_map):
    """
    Returns list of 53 weeks, each a list of 7 cells (Sun→Sat):
      {"date": "YYYY-MM-DD", "count": N, "level": 0-5}
    Fills missing dates with level=0.
    """
    # Find last date in data
    dates = sorted(day_map.keys())
    if not dates:
        last = date.today()
    else:
        last = date.fromisoformat(dates[-1])

    # Back up to end of the current week (Saturday)
    while last.weekday() != 5:   # 5 = Saturday
        last += timedelta(days=1)

    # Start: 53 weeks back, aligned to Sunday
    first = last - timedelta(weeks=COLS) + timedelta(days=1)
    while first.weekday() != 6:  # 6 = Sunday
        first -= timedelta(days=1)

    weeks = []
    cur = first
    for _ in range(COLS):
        week = []
        for _ in range(ROWS):
            ds = cur.isoformat()
            d  = day_map.get(ds, {"date": ds, "count": 0, "level": 0})
            # If level is missing or 0 but count > 0, infer level
            if d["count"] > 0 and d.get("level", 0) == 0:
                c = d["count"]
                d["level"] = 1 if c < 3 else 2 if c < 7 else 3 if c < 12 else 4 if c < 20 else 5
            week.append(d)
            cur += timedelta(days=1)
        weeks.append(week)
    return weeks, first

def month_labels(weeks, first_date):
    """Returns list of (label_text, x_position) for month headers."""
    labels = []
    seen_months = set()
    for col, week in enumerate(weeks):
        d = date.fromisoformat(week[0]["date"])
        ym = (d.year, d.month)
        if ym not in seen_months:
            seen_months.add(ym)
            x = MARGIN_LEFT + col * (CELL + CELL_GAP)
            labels.append((d.strftime("%b"), x))
    return labels

def build_svg(weeks, stats, first_date) -> str:
    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg"')
    out.append(f'     width="{W}" height="{H}"')
    out.append(f'     viewBox="0 0 {W} {H}"')
    out.append(f'     role="img" aria-label="Contribution heatmap for rajc6h6">')

    # ── CSS ───────────────────────────────────────────────────
    css_lines = ['  <style>']
    css_lines.append('    rect.cell { shape-rendering: crispEdges; }')

    for d in range(TOTAL_DIAGS):
        delay = d * DIAG_GAP
        css_lines.append(f'    @keyframes diagIn{d} {{')
        css_lines.append(f'      0%   {{ opacity: 0; transform: translateY({SLIDE_PX}px); }}')
        css_lines.append(f'      100% {{ opacity: 1; transform: translateY(0); }}')
        css_lines.append(f'    }}')
        css_lines.append(f'    .diag{d} {{')
        css_lines.append(f'      opacity: 0;')
        css_lines.append(f'      animation: diagIn{d} {DIAG_DUR}s ease-out {delay:.3f}s forwards;')
        css_lines.append(f'    }}')

    css_lines.append('  </style>')
    out.extend(css_lines)

    # ── Background ───────────────────────────────────────────
    out.append(f'  <rect width="{W}" height="{H}" fill="{BG}"/>')

    # ── Month labels ─────────────────────────────────────────
    for label, x in month_labels(weeks, first_date):
        out.append(f'  <text x="{x}" y="{MARGIN_TOP - 8}"')
        out.append(f'        font-family={FONT!r} font-size="10" fill="{FG}">{label}</text>')

    # ── Day-of-week labels (Mon/Wed/Fri) ─────────────────────
    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for row, lbl in day_labels.items():
        y = MARGIN_TOP + row * (CELL + CELL_GAP) + CELL // 2
        out.append(f'  <text x="{MARGIN_LEFT - 4}" y="{y}"')
        out.append(f'        font-family={FONT!r} font-size="9" fill="{FG}"')
        out.append(f'        text-anchor="end" dominant-baseline="middle">{lbl}</text>')

    # ── Grid cells ───────────────────────────────────────────
    out.append(f'  <g>')
    for col, week in enumerate(weeks):
        x = MARGIN_LEFT + col * (CELL + CELL_GAP)
        for row, day in enumerate(week):
            y    = MARGIN_TOP + row * (CELL + CELL_GAP)
            lvl  = min(day.get("level", 0), 5)
            fill = PALETTE[lvl]
            diag = col + row   # diagonal index
            tip  = f"{day['date']}: {day['count']} contribution{'s' if day['count'] != 1 else ''}"
            out.append(f'    <rect class="cell diag{diag}" x="{x}" y="{y}"')
            out.append(f'          width="{CELL}" height="{CELL}" rx="{CELL_R}" ry="{CELL_R}"')
            out.append(f'          fill="{fill}">')
            out.append(f'      <title>{tip}</title>')
            out.append(f'    </rect>')
    out.append(f'  </g>')

    # ── Legend ───────────────────────────────────────────────
    legend_y    = MARGIN_TOP + GRID_H + 14
    legend_x    = MARGIN_LEFT
    out.append(f'  <text x="{legend_x}" y="{legend_y + CELL}"')
    out.append(f'        font-family={FONT!r} font-size="10" fill="{FG}"')
    out.append(f'        dominant-baseline="middle">Less</text>')
    lx = legend_x + 30
    for lvl in range(6):
        fill = PALETTE[lvl]
        out.append(f'  <rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}"')
        out.append(f'        rx="{CELL_R}" ry="{CELL_R}" fill="{fill}"/>')
        lx += CELL + 3
    out.append(f'  <text x="{lx + 2}" y="{legend_y + CELL}"')
    out.append(f'        font-family={FONT!r} font-size="10" fill="{FG}"')
    out.append(f'        dominant-baseline="middle">More</text>')

    # ── Stats footer ─────────────────────────────────────────
    total = stats.get("total_contributions", 0)
    streak_cur  = stats.get("current_streak", 0)
    streak_long = stats.get("longest_streak", 0)
    best        = stats.get("best_day", {})
    best_str    = f"best day {best.get('date','—')} ({best.get('count',0)})" if best else ""

    footer_txt  = (
        f"{total:,} contributions in the last year  ·  "
        f"current streak {streak_cur}d  ·  longest {streak_long}d  ·  {best_str}"
    )
    stats_y = legend_y + CELL + 12
    out.append(f'  <text x="{MARGIN_LEFT}" y="{stats_y}"')
    out.append(f'        font-family={MONO!r} font-size="9" fill="{FG}">{footer_txt}</text>')

    out.append('</svg>')
    return '\n'.join(out)


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Run fetch_contributions.py first — {INPUT} not found")
    day_map, stats = load_data()
    weeks, first_date = build_week_grid(day_map)
    svg = build_svg(weeks, stats, first_date)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"[render_heatmap_svg] Saved -> {OUTPUT}  ({W}x{H}px, {len(svg):,} bytes)")

if __name__ == "__main__":
    main()
