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


def feet_to_crs_units(buffer_feet: float, epsg: int) -> float:
    """Convert a distance in feet to the units of the provided CRS."""

    crs = CRS.from_epsg(epsg)
    unit_name = crs.axis_info[0].unit_name.lower()
    if "metre" in unit_name:
        return buffer_feet * 0.3048
    if "foot" in unit_name or "feet" in unit_name:
        return buffer_feet
    if "degree" in unit_name:
        # Approximate feet to degrees conversion (1 degree ≈ 364000 feet at equator).
        return buffer_feet / 364000.0
    raise ValueError(f"Unsupported CRS unit '{unit_name}' for EPSG:{epsg}.")


def buffered_geometry_bounds(
    geometry: BaseGeometry,
    src_epsg: int,
    dst_epsg: int,
    buffer_feet: float,
) -> Tuple[BaseGeometry, Tuple[float, float, float, float]]:
    """Return parcel geometry reprojected to dst_epsg and buffered extent bounds."""

    projected_geom = reproject_geometry(geometry, src_epsg, dst_epsg)
    buffer_distance = feet_to_crs_units(buffer_feet, dst_epsg)
    buffered = projected_geom.buffer(buffer_distance)
    return projected_geom, buffered.bounds
