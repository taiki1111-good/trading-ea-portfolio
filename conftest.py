"""Pytest bootstrap for stable imports from repo root.

Ensures `src` and `scripts` can be imported when running `pytest -q`
without requiring an explicit PYTHONPATH setting.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)
