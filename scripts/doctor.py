#!/usr/bin/env python3
"""Read-only prerequisite inspection, not a runtime verification claim."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from harness.cli import doctor_main
if __name__ == "__main__":
    raise SystemExit(doctor_main())
