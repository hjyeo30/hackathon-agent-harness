#!/usr/bin/env python3
"""Run manifest checks; invoke --help for profiles and evidence paths."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from harness.cli import verify_main
if __name__ == "__main__":
    raise SystemExit(verify_main())
