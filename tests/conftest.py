from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
ENGINE_DIR = SCRIPTS_DIR / "engine"

for p in (str(SCRIPTS_DIR), str(ENGINE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
