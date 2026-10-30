#!/usr/bin/env python3
"""Check required files and current, complete evidence without submission."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from harness.cli import final_main
if __name__ == "__main__":
    raise SystemExit(final_main())
