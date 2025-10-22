"""XYZ tile helper functions."""

from __future__ import annotations

from typing import Iterable, Tuple

import mercantile


def tiles_for_extent(bounds: Tuple[float, float, float, float], zoom: int) -> Iterable[mercantile.Tile]:
    """Yield tiles covering a bounding box."""

    minx, miny, maxx, maxy = bounds
    for tile in mercantile.tiles(minx, miny, maxx, maxy, [zoom]):
        yield tile
