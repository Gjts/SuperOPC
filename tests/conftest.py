from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

scripts_path = str(SCRIPTS_DIR)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)
