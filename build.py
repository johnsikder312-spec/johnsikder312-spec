#!/usr/bin/env python3
"""
build.py
Master build script to refresh public GitHub contributions and regenerate
all animated SVGs (Monochrome ASCII portrait, Neofetch card, and Contribution Heatmap).
"""

import os
import sys
import subprocess
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_step(script_name: str, base_dir: Path) -> bool:
    script_path = base_dir / "scripts" / script_name
    print(f"\n========================================================")
    print(f">> Executing: {script_name}")
    print(f"========================================================")
    
    result = subprocess.run([sys.executable, str(script_path)], cwd=str(base_dir))
    if result.returncode != 0:
        print(f"[ERROR] Step {script_name} failed with exit code {result.returncode}")
        return False
    return True

def main():
    base_dir = Path(__file__).resolve().parent
    steps = [
        "fetch_contributions.py",
        "generate_ascii_art.py",
        "generate_neofetch.py",
        "generate_heatmap.py",
    ]

    print("=" * 60)
    print("🚀 Starting GitHub Profile Art & Metrics Build Pipeline")
    print(f"Target Username: johnsikder312-spec")
    print(f"Working Directory: {base_dir}")
    print("=" * 60)

    for step in steps:
        if not run_step(step, base_dir):
            print("\n❌ Build pipeline encountered errors.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("🎉 All SVGs and Contribution Data generated successfully!")
    print(f"1. assets/ascii_art.svg")
    print(f"2. assets/neofetch.svg")
    print(f"3. assets/contribution_heatmap.svg")
    print("=" * 60)

if __name__ == "__main__":
    main()
