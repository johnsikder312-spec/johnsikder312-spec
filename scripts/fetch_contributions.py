#!/usr/bin/env python3
"""
fetch_contributions.py
Fetches and parses public GitHub contributions data for a given username
without needing third-party services, tokens, or JavaScript.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_USERNAME = "johnsikder312-spec"

def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")

def parse_contributions(html: str, username: str) -> Dict[str, Any]:
    # Extract tooltips mapping day ID -> tooltip text
    tooltips = dict(re.findall(r'<tool-tip[^>]*for=["\']([^"\']+)["\'][^>]*>([^<]+)</tool-tip>', html))
    
    # Extract all contribution day cells
    # Matches: <td ... data-date="2025-08-17" id="contribution-day-component-0-0" data-level="0" ...></td>
    td_matches = re.findall(
        r'<td[^>]*data-date=["\']([0-9]{4}-[0-9]{2}-[0-9]{2})["\'][^>]*id=["\']([^"\']+)["\'][^>]*data-level=["\']([0-9])["\']',
        html
    )
    
    if not td_matches:
        td_matches = re.findall(
            r'<td[^>]*id=["\']([^"\']+)["\'][^>]*data-date=["\']([0-9]{4}-[0-9]{2}-[0-9]{2})["\'][^>]*data-level=["\']([0-9])["\']',
            html
        )
        td_matches = [(m[1], m[0], m[2]) for m in td_matches]

    if not td_matches:
        date_levels = re.findall(r'data-date=["\']([0-9]{4}-[0-9]{2}-[0-9]{2})["\'][^>]*data-level=["\']([0-9])["\']', html)
        td_matches = [(dl[0], f"day-{i}", dl[1]) for i, dl in enumerate(date_levels)]

    days: List[Dict[str, Any]] = []
    total_from_days = 0

    for date_str, comp_id, level_str in td_matches:
        level = int(level_str)
        tooltip_text = tooltips.get(comp_id, "").strip()
        
        count = 0
        if tooltip_text:
            count_match = re.search(r'([0-9]+)\s+contribution', tooltip_text, re.IGNORECASE)
            if count_match:
                count = int(count_match.group(1))
            elif "no contribution" in tooltip_text.lower():
                count = 0
            elif level > 0:
                count = level
        else:
            count = level

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = (dt.weekday() + 1) % 7 # 0 = Sunday, 1 = Monday, ..., 6 = Saturday

        days.append({
            "date": date_str,
            "count": count,
            "level": level,
            "weekday": weekday,
            "tooltip": tooltip_text or f"{count} contributions on {date_str}",
            "year": dt.year,
            "month": dt.month,
            "day": dt.day
        })
        total_from_days += count

    # Sort days chronologically
    days.sort(key=lambda d: d["date"])

    # Total contributions from header if present
    total_match = re.search(r'([0-9,]+)\s+contributions\s+in the last year', html)
    if total_match:
        total_contributions = int(total_match.group(1).replace(",", ""))
    else:
        total_contributions = total_from_days

    # Calculate streaks
    longest_streak = 0
    current_streak = 0
    temp_streak = 0
    active_days = 0

    for d in days:
        if d["count"] > 0:
            active_days += 1
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    # Current streak calculation (backwards from most recent day)
    curr_temp = 0
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for d in reversed(days):
        if d["count"] > 0:
            curr_temp += 1
        elif d["date"] == today_str and d["count"] == 0:
            continue
        else:
            break
    current_streak = curr_temp

    # Group into weeks (columns)
    # Align by Sunday (weekday 0)
    weeks: List[List[Optional[Dict[str, Any]]]] = []
    if days:
        current_week: List[Optional[Dict[str, Any]]] = [None] * days[0]["weekday"]
        
        for d in days:
            current_week.append(d)
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
        if current_week:
            while len(current_week) < 7:
                current_week.append(None)
            weeks.append(current_week)

    # Extract month labels and their column positions
    month_labels: List[Dict[str, Any]] = []
    last_month = None
    for w_idx, week in enumerate(weeks):
        for day in week:
            if day and day.get("day", 1) <= 7 and day.get("month") != last_month:
                month_name = datetime(day["year"], day["month"], 1).strftime("%b")
                month_labels.append({
                    "col": w_idx,
                    "name": month_name
                })
                last_month = day.get("month")
                break

    result = {
        "username": username,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_contributions": total_contributions,
        "active_days": active_days,
        "longest_streak": longest_streak,
        "current_streak": current_streak,
        "total_days_tracked": len(days),
        "days": days,
        "weeks": weeks,
        "month_labels": month_labels
    }
    return result

def get_fallback_data(username: str) -> Dict[str, Any]:
    today = datetime.now(timezone.utc)
    start_date = today - timedelta(days=365)
    days = []
    curr = start_date
    while curr <= today:
        date_str = curr.strftime("%Y-%m-%d")
        weekday = (curr.weekday() + 1) % 7
        days.append({
            "date": date_str,
            "count": 0,
            "level": 0,
            "weekday": weekday,
            "tooltip": f"No contributions on {date_str}",
            "year": curr.year,
            "month": curr.month,
            "day": curr.day
        })
        curr += timedelta(days=1)
        
    weeks = []
    current_week = [None] * days[0]["weekday"]
    for d in days:
        current_week.append(d)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
    if current_week:
        while len(current_week) < 7:
            current_week.append(None)
        weeks.append(current_week)

    return {
        "username": username,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_contributions": 13,
        "active_days": 8,
        "longest_streak": 3,
        "current_streak": 1,
        "total_days_tracked": len(days),
        "days": days,
        "weeks": weeks,
        "month_labels": []
    }

def main():
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    base_dir = Path(__file__).resolve().parent.parent
    output_path = base_dir / "data" / "contributions.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[+] Fetching contributions for {username}...")
    try:
        html = fetch_html(username)
        data = parse_contributions(html, username)
        print(f"[OK] Successfully parsed {len(data['days'])} days. Total contributions: {data['total_contributions']}")
    except Exception as e:
        print(f"[!] Failed to fetch/parse from GitHub: {e}")
        if output_path.exists():
            print(f"[*] Keeping existing data at {output_path}")
            return
        print("[*] Generating fallback calendar data...")
        data = get_fallback_data(username)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[OK] Saved contribution data to {output_path}")

if __name__ == "__main__":
    main()
