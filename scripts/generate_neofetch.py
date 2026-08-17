#!/usr/bin/env python3
"""
generate_neofetch.py
Generates an animated Neofetch-style terminal info card SVG for GitHub Profile README.
Features staggered fade-in animations, ANSI color chips, and live profile metadata.
"""

import os
import sys
import json
import xml.sax.saxutils as saxutils
from pathlib import Path
from typing import Dict, Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_PROFILE = {
    "username": "johnsikder312-spec",
    "name": "John Sikder",
    "role": "Full-Stack Engineer & AI Systems Architect",
    "bio": "Building resilient distributed systems, agentic AI workflows, and modern web applications.",
    "host": "GitHub Profile Matrix v2.4 (x86_64)",
    "uptime": "99.99% in flow state",
    "shell": "zsh / fish / bash (Antigravity v2)",
    "terminal": "wezterm / tmux / alacritty",
    "stats": {
        "languages": ["Python", "TypeScript", "Go", "Rust", "C++", "SQL"],
        "frameworks": ["React", "Next.js", "Node.js", "FastAPI", "TailwindCSS"],
        "cloud_devops": ["Google Cloud", "AWS", "Docker", "Kubernetes", "GitHub Actions"],
        "specialties": ["Agentic AI Workflows", "Distributed Systems", "High-Performance APIs"]
    },
    "status": "🟢 Available for high-impact engineering & open-source collaboration"
}

def load_profile_data(data_path: Path) -> Dict[str, Any]:
    if data_path.exists():
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error reading {data_path}: {e}")
    return DEFAULT_PROFILE

def generate_neofetch_svg(profile: Dict[str, Any]) -> str:
    username = profile.get("username", "johnsikder312-spec")
    role = profile.get("role", "Full-Stack Engineer & AI Systems Architect")
    host = profile.get("host", "GitHub Profile Matrix v2.4")
    uptime = profile.get("uptime", "99.99% • Flow State")
    stats = profile.get("stats", {})
    languages = ", ".join(stats.get("languages", ["Python", "TypeScript", "Go", "Rust", "C++", "SQL"]))
    frameworks = ", ".join(stats.get("frameworks", ["React", "Next.js", "Node.js", "FastAPI"]))
    cloud = ", ".join(stats.get("cloud_devops", ["Google Cloud", "AWS", "Docker", "Kubernetes", "CI/CD"]))
    specialties = ", ".join(stats.get("specialties", ["Agentic AI", "Distributed Systems", "Cloud Native"]))
    status = profile.get("status", "🟢 Available for collaboration")

    card_width = 540
    card_height = 520
    header_height = 36
    start_x = 24

    # Structured Neofetch lines
    info_items = [
        {"type": "header", "user": username, "host": "GitHub-Matrix"},
        {"type": "sep", "content": "--------------------------------------------------"},
        {"type": "prop", "key": "OS", "val": "GitHub Cloud Linux (x86_64)", "key_color": "#ff7b72"},
        {"type": "prop", "key": "Host", "val": host, "key_color": "#d2a8ff"},
        {"type": "prop", "key": "Role", "val": role, "key_color": "#79c0ff"},
        {"type": "prop", "key": "Languages", "val": languages, "key_color": "#7ee787"},
        {"type": "prop", "key": "Frameworks", "val": frameworks, "key_color": "#ffa657"},
        {"type": "prop", "key": "Cloud/DevOps", "val": cloud, "key_color": "#58a6ff"},
        {"type": "prop", "key": "Specialties", "val": specialties, "key_color": "#d2a8ff"},
        {"type": "prop", "key": "Uptime", "val": uptime, "key_color": "#7ee787"},
        {"type": "prop", "key": "Status", "val": status, "key_color": "#3fb950"},
    ]

    # Staggered CSS Delays
    css_delays = []
    lines_xml = []
    current_y = 80
    line_gap = 26

    for idx, item in enumerate(info_items):
        delay = 0.08 + (idx * 0.07)
        css_delays.append(f".line-{idx} {{ animation-delay: {delay:.3f}s; }}")

        if item["type"] == "header":
            user_esc = saxutils.escape(item["user"])
            host_esc = saxutils.escape(item["host"])
            lines_xml.append(
                f'<g class="neo-line line-{idx}" transform="translate({start_x}, {current_y})">\n'
                f'  <text class="neo-header-user">{user_esc}</text>\n'
                f'  <text x="145" class="neo-header-at">@</text>\n'
                f'  <text x="160" class="neo-header-host">{host_esc}</text>\n'
                f'</g>'
            )
            current_y += 18
        elif item["type"] == "sep":
            lines_xml.append(
                f'<g class="neo-line line-{idx}" transform="translate({start_x}, {current_y})">\n'
                f'  <text class="neo-sep">{saxutils.escape(item["content"])}</text>\n'
                f'</g>'
            )
            current_y += 24
        elif item["type"] == "prop":
            key_esc = saxutils.escape(item["key"])
            val_esc = saxutils.escape(item["val"])
            key_color = item.get("key_color", "#79c0ff")
            lines_xml.append(
                f'<g class="neo-line line-{idx}" transform="translate({start_x}, {current_y})">\n'
                f'  <text class="neo-key" style="fill: {key_color};">{key_esc}:</text>\n'
                f'  <text x="110" class="neo-val">{val_esc}</text>\n'
                f'</g>'
            )
            current_y += line_gap

    delays_css_str = "\n    ".join(css_delays)
    lines_content = "\n    ".join(lines_xml)

    # ANSI Color Palette Blocks
    colors_row1 = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"]
    colors_row2 = ["#6e7681", "#ffa198", "#56d364", "#e3b341", "#79c0ff", "#d2a8ff", "#56d4dd", "#f0f6fc"]
    
    color_blocks_y = current_y + 10
    block_w = 26
    block_h = 13
    block_gap = 6
    block_delay = 0.08 + (len(info_items) * 0.07) + 0.1

    blocks_xml = []
    for i, color in enumerate(colors_row1):
        bx = start_x + (i * (block_w + block_gap))
        blocks_xml.append(f'<rect x="{bx}" y="{color_blocks_y}" width="{block_w}" height="{block_h}" rx="3" fill="{color}" />')
    for i, color in enumerate(colors_row2):
        bx = start_x + (i * (block_w + block_gap))
        blocks_xml.append(f'<rect x="{bx}" y="{color_blocks_y + block_h + 4}" width="{block_w}" height="{block_h}" rx="3" fill="{color}" />')
    
    color_blocks_content = "\n      ".join(blocks_xml)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {card_width} {card_height}" width="{card_width}" height="{card_height}" style="background: transparent;">
  <defs>
    <linearGradient id="neofetchBorderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#30363d" />
      <stop offset="50%" stop-color="#3fb950" stop-opacity="0.7" />
      <stop offset="100%" stop-color="#30363d" />
    </linearGradient>
    <linearGradient id="neoHeaderGrad" x1="0%" y1="0%" x2="100%" y2="0%">
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
      fill: url(#neoHeaderGrad);
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
    .cmd-text {{
      font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
      font-size: 11px;
      fill: #7ee787;
      font-weight: 500;
    }}
    .cmd-prompt {{
      fill: #58a6ff;
    }}
    .cmd-arg {{
      fill: #d2a8ff;
    }}

    @keyframes slideFadeIn {{
      0% {{
        opacity: 0;
        transform: translateX(-10px);
      }}
      100% {{
        opacity: 1;
        transform: translateX(0);
      }}
    }}

    .neo-line {{
      opacity: 0;
      animation: slideFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
      font-size: 11.5px;
    }}

    .neo-header-user {{
      fill: #58a6ff;
      font-weight: 700;
      font-size: 13px;
    }}
    .neo-header-at {{
      fill: #8b949e;
      font-weight: 600;
      font-size: 13px;
    }}
    .neo-header-host {{
      fill: #3fb950;
      font-weight: 700;
      font-size: 13px;
    }}
    .neo-sep {{
      fill: #30363d;
      font-weight: 600;
      font-size: 11px;
    }}
    .neo-key {{
      font-weight: 700;
      letter-spacing: 0.2px;
    }}
    .neo-val {{
      fill: #e6edf3;
      font-weight: 400;
    }}

    @keyframes fadeInPalette {{
      0% {{ opacity: 0; transform: scale(0.95); }}
      100% {{ opacity: 1; transform: scale(1); }}
    }}
    .color-palette-group {{
      opacity: 0;
      animation: fadeInPalette 0.4s ease-out forwards;
      animation-delay: {block_delay:.2f}s;
    }}

    @keyframes cursorBlink {{
      0%, 49% {{ opacity: 1; }}
      50%, 100% {{ opacity: 0; }}
    }}
    .cursor {{
      animation: cursorBlink 1s infinite;
      fill: #3fb950;
    }}

    {delays_css_str}
  </style>

  <!-- Main Card Container -->
  <rect x="1" y="1" width="{card_width - 2}" height="{card_height - 2}" class="terminal-bg" />

  <!-- Window Header Bar -->
  <path d="M 1,11 A 10,10 0 0,1 11,1 L {card_width - 11},1 A 10,10 0 0,1 {card_width - 1},11 L {card_width - 1},{header_height} L 1,{header_height} Z" class="terminal-header" />
  
  <!-- Window Control Buttons -->
  <circle cx="18" cy="18" r="5.5" class="dot-red" />
  <circle cx="34" cy="18" r="5.5" class="dot-yellow" />
  <circle cx="50" cy="18" r="5.5" class="dot-green" />

  <!-- Header Title -->
  <text x="{card_width // 2}" y="22" text-anchor="middle" class="title-text">{username}@terminal: ~ (neofetch)</text>

  <!-- Terminal Command Prompt -->
  <g transform="translate({start_x}, 56)">
    <text y="0" class="cmd-text">
      <tspan class="cmd-prompt">{username}:~$</tspan> neofetch <tspan class="cmd-arg">--system --stats</tspan>
    </text>
  </g>

  <!-- Neofetch Body Lines -->
  {lines_content}

  <!-- ANSI Color Palette Display -->
  <g class="color-palette-group">
      {color_blocks_content}
  </g>
</svg>"""
    return svg

def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "profile_data.json"
    output_svg_path = base_dir / "assets" / "neofetch.svg"

    print(f"[+] Loading profile data from {data_path}...")
    profile = load_profile_data(data_path)

    print(f"[+] Generating Neofetch SVG for {profile.get('username', 'johnsikder312-spec')}...")
    svg_content = generate_neofetch_svg(profile)

    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[OK] Successfully created {output_svg_path} ({len(svg_content)} bytes)")

if __name__ == "__main__":
    main()
