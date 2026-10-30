#!/usr/bin/env python3
"""Preview/install selected skills and a namespaced reference kit."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from harness.cli import bootstrap_main
if __name__ == "__main__":
    raise SystemExit(bootstrap_main())
