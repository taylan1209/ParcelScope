"""Miscellaneous helper routines."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


def extent_hash(extent: Dict[str, Any]) -> str:
    """Return a deterministic hash for an extent dictionary."""

    normalized = json.dumps(extent, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def ensure_directory(path: Path) -> Path:
    """Ensure that a directory exists."""

    path.mkdir(parents=True, exist_ok=True)
    return path
