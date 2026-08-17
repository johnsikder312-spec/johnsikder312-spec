#!/usr/bin/env python3
"""
generate_ascii_art.py
Converts a local profile photo into a high-contrast animated monochrome ASCII portrait SVG.
Animation: Typewriter row-by-row reveal that freezes in place on completion.
"""

import os
import sys
import xml.sax.saxutils as saxutils
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Carefully calibrated monochrome ASCII character ramp (from dark to bright)
ASCII_RAMP = "   ..::--==++**##%%@@██"

def image_to_ascii(image_path: Path, target_cols: int = 52, target_rows: int = 30, contrast_factor: float = 1.4) -> list[str]:
    """Converts an image file to a list of ASCII character strings."""
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found at {image_path}")

    with Image.open(image_path) as img:
        # Convert to RGBA first to handle transparency with a dark background
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            bg = Image.new("RGB", img.size, (13, 17, 23))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")

        # Smart square crop (center focus)
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))

        # Convert to Grayscale
        gray = img.convert("L")

        # Subtle unsharp mask for crisp facial edges
        gray = gray.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=3))

        # Autocontrast & enhance contrast
        gray = ImageOps.autocontrast(gray, cutoff=2)
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(contrast_factor)

        # Resize to character grid
        resized = gray.resize((target_cols, target_rows), Image.Resampling.LANCZOS)
        pixels = list(resized.getdata())

        ramp_len = len(ASCII_RAMP)
        ascii_lines = []

        for row in range(target_rows):
            line_chars = []
            for col in range(target_cols):
                val = pixels[row * target_cols + col]
                # Map 0..255 to ramp index
                idx = int((val / 255.0) * (ramp_len - 1))
                idx = max(0, min(ramp_len - 1, idx))
                line_chars.append(ASCII_RAMP[idx])
            ascii_lines.append("".join(line_chars))

        return ascii_lines

def generate_ascii_svg(ascii_lines: list[str], username: str = "johnsikder312-spec") -> str:
    """Generates a standalone, animated monochrome SVG container for the ASCII portrait."""
    total_rows = len(ascii_lines)
    cols = len(ascii_lines[0]) if ascii_lines else 52

    # Layout dimensions (synced with Neofetch card height)
    card_width = 440
    card_height = 520
    header_height = 36
    
    font_size = 9.8
    line_height = 12.0
    start_x = 22
    start_y = 80

    # Animation timing
    row_delay_step = 0.042 # seconds per row (~1.26s total)
    total_reveal_time = total_rows * row_delay_step + 0.2

    # Generate CSS rules for staggered delays
    css_delays = []
    for i in range(total_rows):
        delay = i * row_delay_step
        css_delays.append(f".r-{i} {{ animation-delay: {delay:.3f}s; }}")
    delays_str = "\n      ".join(css_delays)

    # Escape lines for XML
    rows_xml = []
    for i, line in enumerate(ascii_lines):
        escaped_line = saxutils.escape(line).replace(" ", "&#160;")
        row_y = start_y + (i * line_height)
        rows_xml.append(
            f'<text x="{start_x}" y="{row_y:.1f}" class="ascii-row r-{i}">{escaped_line}</text>'
        )
    rows_content = "\n      ".join(rows_xml)

    status_y = start_y + (total_rows * line_height) + 20
    status_delay = total_reveal_time

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {card_width} {card_height}" width="{card_width}" height="{card_height}" style="background: transparent;">
  <defs>
    <linearGradient id="asciiBorderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#30363d" />
      <stop offset="50%" stop-color="#58a6ff" stop-opacity="0.7" />
      <stop offset="100%" stop-color="#30363d" />
    </linearGradient>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
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
      fill: url(#headerGrad);
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
    
    .ascii-text {{
      font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
      font-size: {font_size}px;
      font-weight: 700;
      fill: #58a6ff;
      letter-spacing: 0.2px;
      white-space: pre;
    }}
    
    @keyframes revealRow {{
      0% {{
        opacity: 0;
        transform: translateY(3px);
      }}
      100% {{
        opacity: 1;
        transform: translateY(0);
      }}
    }}
    
    .ascii-row {{
      opacity: 0;
      animation: revealRow 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      will-change: opacity, transform;
    }}
    
    @keyframes fadeInStatus {{
      0% {{ opacity: 0; transform: translateY(4px); }}
      100% {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .status-line {{
      opacity: 0;
      animation: fadeInStatus 0.4s ease-out forwards;
      animation-delay: {status_delay:.2f}s;
      font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
      font-size: 10px;
      font-weight: 600;
      fill: #8b949e;
    }}
    .status-ok {{
      fill: #3fb950;
      font-weight: 700;
    }}
    .status-dim {{
      fill: #6e7681;
    }}
    
    @keyframes cursorBlink {{
      0%, 49% {{ opacity: 1; }}
      50%, 100% {{ opacity: 0; }}
    }}
    .cursor {{
      animation: cursorBlink 1s infinite;
      fill: #58a6ff;
    }}

    {delays_str}
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
  <text x="{card_width // 2}" y="22" text-anchor="middle" class="title-text">{username}@avatar: ~ (monochrome.sh)</text>

  <!-- Terminal Command Prompt -->
  <g transform="translate({start_x}, 56)">
    <text y="0" class="cmd-text">
      <tspan class="cmd-prompt">{username}:~$</tspan> ./render-portrait <tspan class="cmd-arg">--ascii --freeze</tspan>
    </text>
  </g>

  <!-- ASCII Portrait Content -->
  <g class="ascii-text">
      {rows_content}
  </g>

  <!-- Status / Frozen Line -->
  <g class="status-line">
    <text x="{start_x}" y="{status_y}">
      <tspan class="status-ok">[READY]</tspan> {cols}x{total_rows} ASCII RENDERED <tspan class="status-dim">| STATUS: FROZEN</tspan> <tspan class="cursor">_</tspan>
    </text>
  </g>
</svg>"""
    return svg

def main():
    base_dir = Path(__file__).resolve().parent.parent
    avatar_path = base_dir / "assets" / "avatar.png"
    output_svg_path = base_dir / "assets" / "ascii_art.svg"

    print(f"[+] Loading avatar from {avatar_path}...")
    ascii_lines = image_to_ascii(avatar_path, target_cols=52, target_rows=30, contrast_factor=1.45)
    print(f"[+] Converted image to {len(ascii_lines)} rows x {len(ascii_lines[0])} cols of ASCII characters.")

    print(f"[+] Generating animated SVG to {output_svg_path}...")
    svg_content = generate_ascii_svg(ascii_lines, username="johnsikder312-spec")

    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[OK] Successfully created {output_svg_path} ({len(svg_content)} bytes)")

if __name__ == "__main__":
    main()
