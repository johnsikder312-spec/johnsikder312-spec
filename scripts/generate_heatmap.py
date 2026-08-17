#!/usr/bin/env python3
"""
generate_heatmap.py
Renders a self-contained, animated GitHub Contribution Heatmap SVG
directly from parsed contributions data without third-party services or tokens.
"""

import os
import sys
import json
import xml.sax.saxutils as saxutils
from pathlib import Path
from typing import Dict, Any, List

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

LEVEL_COLORS = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}

LEVEL_BORDER_COLORS = {
    0: "#21262d",
    1: "#1b4d32",
    2: "#197c3f",
    3: "#2ebc4f",
    4: "#56e66e",
}

def generate_heatmap_svg(data: Dict[str, Any]) -> str:
    username = data.get("username", "johnsikder312-spec")
    total_contribs = data.get("total_contributions", 0)
    active_days = data.get("active_days", 0)
    longest_streak = data.get("longest_streak", 0)
    current_streak = data.get("current_streak", 0)
    weeks = data.get("weeks", [])
    month_labels = data.get("month_labels", [])

    svg_width = 880
    svg_height = 230
    header_height = 36

    # Grid layout
    cell_size = 10.5
    cell_gap = 3.5
    step = cell_size + cell_gap # 14px per column/row

    grid_start_x = 56
    grid_start_y = 86

    # Day labels
    day_labels_xml = [
        f'<text x="{grid_start_x - 10}" y="{grid_start_y + step * 1 + 8}" class="axis-label" text-anchor="end">Mon</text>',
        f'<text x="{grid_start_x - 10}" y="{grid_start_y + step * 3 + 8}" class="axis-label" text-anchor="end">Wed</text>',
        f'<text x="{grid_start_x - 10}" y="{grid_start_y + step * 5 + 8}" class="axis-label" text-anchor="end">Fri</text>',
    ]

    # Month labels
    month_labels_xml = []
    for ml in month_labels:
        col_x = grid_start_x + (ml["col"] * step)
        month_labels_xml.append(
            f'<text x="{col_x}" y="{grid_start_y - 8}" class="axis-label">{saxutils.escape(ml["name"])}</text>'
        )

    # Grid cells and animations
    cells_xml = []
    css_col_delays = []
    
    for col_idx, week in enumerate(weeks):
        delay = 0.015 * col_idx
        css_col_delays.append(f".col-{col_idx} {{ animation-delay: {delay:.3f}s; }}")

        col_x = grid_start_x + (col_idx * step)
        for row_idx, day in enumerate(week):
            if day is None:
                continue
            row_y = grid_start_y + (row_idx * step)
            level = day.get("level", 0)
            fill_color = LEVEL_COLORS.get(level, LEVEL_COLORS[0])
            border_color = LEVEL_BORDER_COLORS.get(level, LEVEL_BORDER_COLORS[0])
            count = day.get("count", 0)
            date_str = day.get("date", "")
            tooltip_raw = day.get("tooltip", f"{count} contributions on {date_str}")
            tooltip_esc = saxutils.escape(tooltip_raw)

            extra_cls = ""
            if level > 0:
                extra_cls = " cell-active"

            cell = (
                f'<rect x="{col_x}" y="{row_y}" width="{cell_size}" height="{cell_size}" rx="2.5" '
                f'fill="{fill_color}" stroke="{border_color}" stroke-width="0.7" '
                f'class="cal-cell col-{col_idx}{extra_cls}">\n'
                f'  <title>{tooltip_esc}</title>\n'
                f'</rect>'
            )
            cells_xml.append(cell)

    delays_str = "\n    ".join(css_col_delays)
    cells_content = "\n  ".join(cells_xml)
    day_labels_content = "\n  ".join(day_labels_xml)
    month_labels_content = "\n  ".join(month_labels_xml)

    # Legend calculation
    legend_start_x = svg_width - 190
    legend_y = svg_height - 20
    legend_cells = []
    for lvl in range(5):
        lx = legend_start_x + 40 + (lvl * 15)
        legend_cells.append(
            f'<rect x="{lx}" y="{legend_y - 9}" width="10.5" height="10.5" rx="2" '
            f'fill="{LEVEL_COLORS[lvl]}" stroke="{LEVEL_BORDER_COLORS[lvl]}" stroke-width="0.7" />'
        )
    legend_content = "\n    ".join(legend_cells)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}" style="background: transparent;">
  <defs>
    <linearGradient id="heatBorderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#30363d" />
      <stop offset="50%" stop-color="#238636" stop-opacity="0.8" />
      <stop offset="100%" stop-color="#30363d" />
    </linearGradient>
    <linearGradient id="heatHeaderGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#161b22" />
      <stop offset="100%" stop-color="#0d1117" />
    </linearGradient>
  </defs>

  <style>
    .terminal-bg {{
      fill: #0d1117;
      stroke: #30363d;
      stroke-width: 1.2px;
      rx: 10px;
    }}
    .terminal-header {{
      fill: url(#heatHeaderGrad);
      stroke: #30363d;
      stroke-width: 1px;
    }}
    .dot-red {{ fill: #ff5f56; }}
    .dot-yellow {{ fill: #ffbd2e; }}
    .dot-green {{ fill: #27c93f; }}

    .title-text {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
      font-size: 12px;
      font-weight: 600;
      fill: #8b949e;
      letter-spacing: 0.3px;
    }}

    .axis-label {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
      font-size: 10px;
      fill: #7d8590;
      font-weight: 500;
    }}

    .legend-text {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
      font-size: 10px;
      fill: #7d8590;
      font-weight: 500;
    }}

    .stat-pill {{
      font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
      font-size: 10.5px;
      font-weight: 600;
    }}

    @keyframes cellPop {{
      0% {{
        opacity: 0;
        transform: scale(0.6);
      }}
      70% {{
        transform: scale(1.1);
      }}
      100% {{
        opacity: 1;
        transform: scale(1);
      }}
    }}

    .cal-cell {{
      opacity: 0;
      animation: cellPop 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      transform-box: fill-box;
      transform-origin: center;
      transition: transform 0.15s ease, stroke-width 0.15s ease;
    }}

    .cal-cell:hover {{
      transform: scale(1.35);
      stroke: #ffffff !important;
      stroke-width: 1.5px !important;
      cursor: pointer;
    }}

    @keyframes activePulse {{
      0%, 100% {{ filter: drop-shadow(0 0 0px #39d353); }}
      50% {{ filter: drop-shadow(0 0 2.5px #39d353); }}
    }}

    .cell-active {{
      animation: cellPop 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards, activePulse 3s infinite ease-in-out 1.2s;
    }}

    {delays_str}
  </style>

  <!-- Container -->
  <rect x="1" y="1" width="{svg_width - 2}" height="{svg_height - 2}" class="terminal-bg" />

  <!-- Header Bar -->
  <path d="M 1,11 A 10,10 0 0,1 11,1 L {svg_width - 11},1 A 10,10 0 0,1 {svg_width - 1},11 L {svg_width - 1},{header_height} L 1,{header_height} Z" class="terminal-header" />
  
  <!-- Window Control Buttons -->
  <circle cx="18" cy="18" r="5.5" class="dot-red" />
  <circle cx="34" cy="18" r="5.5" class="dot-yellow" />
  <circle cx="50" cy="18" r="5.5" class="dot-green" />

  <!-- Title -->
  <text x="75" y="22" class="title-text">{username} / contribution-heatmap (last 12 months)</text>

  <!-- Live Stats Badges in Top Bar -->
  <g transform="translate({svg_width - 430}, 12)">
    <!-- Total Contributions -->
    <rect x="0" y="0" width="130" height="20" rx="4" fill="#238636" fill-opacity="0.2" stroke="#238636" stroke-width="0.8" />
    <text x="65" y="14" text-anchor="middle" class="stat-pill" fill="#3fb950">Contributions: {total_contribs}</text>

    <!-- Active Days -->
    <rect x="138" y="0" width="105" height="20" rx="4" fill="#1f6feb" fill-opacity="0.2" stroke="#1f6feb" stroke-width="0.8" />
    <text x="190" y="14" text-anchor="middle" class="stat-pill" fill="#58a6ff">Active: {active_days}d</text>

    <!-- Max Streak -->
    <rect x="251" y="0" width="165" height="20" rx="4" fill="#a371f7" fill-opacity="0.2" stroke="#a371f7" stroke-width="0.8" />
    <text x="333" y="14" text-anchor="middle" class="stat-pill" fill="#d2a8ff">Max Streak: {longest_streak}d | Cur: {current_streak}d</text>
  </g>

  <!-- Month Labels -->
  {month_labels_content}

  <!-- Day of Week Labels -->
  {day_labels_content}

  <!-- Calendar Grid Cells -->
  {cells_content}

  <!-- Footer Info & Legend -->
  <g transform="translate({grid_start_x}, {legend_y})">
    <text x="0" y="0" class="legend-text" fill="#484f58">Live data synced directly from public GitHub profile • No external tokens</text>
  </g>

  <g>
    <text x="{legend_start_x + 10}" y="{legend_y}" class="legend-text" text-anchor="end">Less</text>
    {legend_content}
    <text x="{legend_start_x + 122}" y="{legend_y}" class="legend-text">More</text>
  </g>
</svg>"""
    return svg

def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "contributions.json"
    output_svg_path = base_dir / "assets" / "contribution_heatmap.svg"

    if not data_path.exists():
        print(f"[!] {data_path} not found. Running fetch_contributions.py first...")
        from fetch_contributions import main as fetch_main
        fetch_main()

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[+] Generating Heatmap SVG for {data.get('username', 'johnsikder312-spec')}...")
    svg_content = generate_heatmap_svg(data)

    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[OK] Successfully created {output_svg_path} ({len(svg_content)} bytes)")

if __name__ == "__main__":
    main()
