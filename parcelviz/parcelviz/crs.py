"""Coordinate reference system helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import geopandas as gpd
from pyproj import CRS, Transformer
from shapely.geometry.base import BaseGeometry


@dataclass(frozen=True)
class CRSInfo:
    """Metadata about a coordinate reference system."""

    epsg: int
    name: str
    units: str


def describe_crs(epsg: int) -> CRSInfo:
    """Return human-readable CRS metadata."""

    crs = CRS.from_epsg(epsg)
    return CRSInfo(epsg=epsg, name=crs.name, units=crs.axis_info[0].unit_name)


def reproject_geometry(geometry: BaseGeometry, src_epsg: int, dst_epsg: int) -> BaseGeometry:
    """Reproject a geometry between CRS definitions."""

    if src_epsg == dst_epsg:
        return geometry
    transformer = Transformer.from_crs(src_epsg, dst_epsg, always_xy=True)
    return shapely_transform(transformer.transform, geometry)


def shapely_transform(func, geometry: BaseGeometry) -> BaseGeometry:
    """Apply coordinate transformation to a shapely geometry."""

    # Import locally to avoid optional dependency at module import time.
    from shapely.ops import transform as shapely_transform_op

    return shapely_transform_op(func, geometry)


def reproject_gdf(gdf: gpd.GeoDataFrame, dst_epsg: int) -> gpd.GeoDataFrame:
    """Reproject a GeoDataFrame to a different CRS."""

    if gdf.crs is None:
        raise ValueError("GeoDataFrame CRS is undefined.")
    if int(gdf.crs.to_epsg()) == dst_epsg:
        return gdf
    return gdf.to_crs(epsg=dst_epsg)


def buffer_extent(bounds: Tuple[float, float, float, float], buffer_distance: float) -> Tuple[float, float, float, float]:
    """Expand a bounding box by the provided buffer distance."""

    minx, miny, maxx, maxy = bounds
    return (minx - buffer_distance, miny - buffer_distance, maxx + buffer_distance, maxy + buffer_distance)
