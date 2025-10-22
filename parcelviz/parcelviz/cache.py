"""HTTP cache management utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import requests_cache


def configure_requests_cache(path: Path, expire_hours: Optional[int] = None, backend: str = "sqlite") -> None:
    """Configure global requests-cache."""

    path.parent.mkdir(parents=True, exist_ok=True)
    requests_cache.install_cache(
        cache_name=str(path.with_suffix("")),
        backend=backend,
        expire_after=None if expire_hours is None else expire_hours * 3600,
    )
