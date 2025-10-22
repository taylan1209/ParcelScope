"""Map composition utilities for layer rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from PIL import Image
from shapely.geometry import base as shapely_base


@dataclass
class FigureSpec:
    """Specification for output figures."""

    width: int
    height: int
    dpi: int
    title: Optional[str] = None


def render_placeholder_png(path: Path, spec: FigureSpec, message: str) -> None:
    """Write a placeholder PNG while the real renderer is under construction."""

    fig = plt.figure(figsize=(spec.width / spec.dpi, spec.height / spec.dpi), dpi=spec.dpi)
    ax = fig.add_subplot(111)
    ax.axis("off")
    if spec.title:
        ax.set_title(spec.title)
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, wrap=True)
    fig.savefig(path, dpi=spec.dpi, bbox_inches="tight")
    plt.close(fig)


def render_vector_layer(
    output_path: Path,
    spec: FigureSpec,
    extent: Tuple[float, float, float, float],
    parcel_geom: shapely_base.BaseGeometry,
    vector: gpd.GeoDataFrame,
    style: Dict[str, object],
) -> None:
    """Render a map using vector overlays."""

    fig, ax = _prepare_axes(spec, extent)
    if not vector.empty:
        plot_kwargs = _vector_style_kwargs(style)
        vector.plot(ax=ax, **plot_kwargs)
    _draw_parcel_outline(ax, parcel_geom, style)
    _finalize(fig, output_path, spec)


def render_wms_layer(
    output_path: Path,
    spec: FigureSpec,
    extent: Tuple[float, float, float, float],
    parcel_geom: shapely_base.BaseGeometry,
    image: Image.Image,
    style: Dict[str, object],
) -> None:
    """Render a map using a WMS raster overlay."""

    fig, ax = _prepare_axes(spec, extent)
    ax.imshow(
        image,
        extent=(extent[0], extent[2], extent[1], extent[3]),
        origin="upper",
        alpha=float(style.get("opacity", 1.0)),
    )
    _draw_parcel_outline(ax, parcel_geom, style)
    _finalize(fig, output_path, spec)


def _prepare_axes(spec: FigureSpec, extent: Tuple[float, float, float, float]) -> Tuple[plt.Figure, Axes]:
    fig = plt.figure(figsize=(spec.width / spec.dpi, spec.height / spec.dpi), dpi=spec.dpi)
    ax = fig.add_subplot(111)
    ax.set_xlim(extent[0], extent[2])
    ax.set_ylim(extent[1], extent[3])
    ax.set_aspect("equal")
    ax.axis("off")
    if spec.title:
        ax.set_title(spec.title)
    return fig, ax


def _vector_style_kwargs(style: Dict[str, object]) -> Dict[str, object]:
    return {
        "facecolor": style.get("fill_color", style.get("color", "#4c78a8")),
        "edgecolor": style.get("outline", style.get("line_color", "#294162")),
        "linewidth": style.get("line_width", 0.8),
        "alpha": style.get("fill_alpha", 0.4),
    }


def _draw_parcel_outline(ax: Axes, parcel_geom: shapely_base.BaseGeometry, style: Dict[str, object]) -> None:
    parcel_series = gpd.GeoSeries([parcel_geom])
    parcel_series.plot(
        ax=ax,
        facecolor=(style.get("parcel_fill_color", "#00ffff")),
        edgecolor=style.get("parcel_outline_color", "#00b7c2"),
        linewidth=style.get("parcel_outline_width", 2.5),
        alpha=style.get("parcel_fill_alpha", 0.18),
    )


def _finalize(fig: plt.Figure, output_path: Path, spec: FigureSpec) -> None:
    fig.savefig(output_path, dpi=spec.dpi, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
