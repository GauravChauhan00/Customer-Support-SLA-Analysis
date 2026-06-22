"""Run the complete beginner-friendly analytics workflow."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

steps = [
    ROOT / "src" / "clean_data.py",
    ROOT / "src" / "analyze_data.py",
    ROOT / "src" / "run_sql_demo.py",
]

for step in steps:
    print(f"\n>>> Running {step.name}")
    subprocess.run([sys.executable, str(step)], check=True, cwd=ROOT)

print("\nProject completed successfully. Check data/processed and reports folders.")
