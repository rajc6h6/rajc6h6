#!/usr/bin/env python3
"""
Step 4 — fetch_contributions.py
Fetches the public GitHub contribution graph for rajc6h6 (no token needed),
parses day cells, and writes data/contributions.json with raw days + stats.
"""

import json
import pathlib
import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

USERNAME   = "rajc6h6"
URL        = f"https://github.com/users/{USERNAME}/contributions"
OUTPUT     = pathlib.Path("data/contributions.json")
OUTPUT.parent.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; profile-art-bot/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "X-Requested-With": "XMLHttpRequest",
}

def fetch_days() -> list[dict]:
    print(f"[fetch_contributions] GET {URL}")
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Build a map from cell-id -> exact count using <tool-tip for="cell-id"> text
    tooltip_map: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        cell_id = tip.get("for", "")
        text = tip.get_text(strip=True)
        m = re.search(r"(\d+)\s+contribution", text)
        if m:
            tooltip_map[cell_id] = int(m.group(1))
        elif "No contributions" in text:
            tooltip_map[cell_id] = 0

    days = []
    cells = soup.select("td[data-date]")
    if not cells:
        cells = soup.select("rect[data-date]")  # older SVG-based graph

    for cell in cells:
        d = cell.get("data-date", "")
        if not re.match(r"\d{4}-\d{2}-\d{2}", d):
            continue
        level = int(cell.get("data-level", 0))
        cell_id = cell.get("id", "")

        if cell_id in tooltip_map:
            count = tooltip_map[cell_id]
        else:
            # Fallback: infer from aria-label on the cell itself
            label = cell.get("aria-label", "") or cell.get("data-tooltip", "")
            m2 = re.search(r"(\d+)\s+contribution", label)
            count = int(m2.group(1)) if m2 else 0

        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days

def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {}

    total = sum(d["count"] for d in days)

    # Current streak (from today backwards)
    today = date.today().isoformat()
    day_map = {d["date"]: d["count"] for d in days}

    # Walk backwards from today
    streak = 0
    cur = date.today()
    while cur.isoformat() in day_map:
        if day_map[cur.isoformat()] > 0:
            streak += 1
            cur -= timedelta(days=1)
        else:
            # Allow today to be 0 (it's early in the day) and keep going
            if cur.isoformat() == today:
                cur -= timedelta(days=1)
            else:
                break

    # Longest streak
    longest = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    # Best day
    best = max(days, key=lambda x: x["count"])

    # Monthly totals
    monthly: dict[str, int] = {}
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "total_contributions": total,
        "current_streak": streak,
        "longest_streak": longest,
        "best_day": best,
        "monthly_totals": monthly,
    }

def main():
    days = fetch_days()
    if not days:
        print("[fetch_contributions] WARNING: no contribution cells found — check HTML structure")
    stats = compute_stats(days)
    payload = {"days": days, "stats": stats}
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[fetch_contributions] {len(days)} days written -> {OUTPUT}")
    print(f"  total: {stats.get('total_contributions',0)}")
    print(f"  current streak: {stats.get('current_streak',0)}")
    print(f"  longest streak: {stats.get('longest_streak',0)}")

if __name__ == "__main__":
    main()
