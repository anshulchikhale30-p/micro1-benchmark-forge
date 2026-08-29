from __future__ import annotations

import sys
from pathlib import Path

from agents.llm_client import build_llm  # noqa: F401  (re-export for baseline imports)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
