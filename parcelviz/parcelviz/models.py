"""Shared domain models for parcel visualization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from pydantic import BaseModel, Field, validator

GeometryLike = Dict[str, object]


class RenderRequest(BaseModel):
    """Input payload for the render pipeline and API."""

    address: Optional[str] = Field(None, description="Mailing or site address to resolve.")
    apn: Optional[str] = Field(None, description="Assessor parcel number.")
    layers: List[str] = Field(default_factory=list, description="Layer names requested for rendering.")
    buffer_feet: float = Field(250, ge=0, description="Buffer distance beyond parcel geometry.")
    output_dpi: int = Field(220, ge=96, le=600, description="Target DPI for exported images.")

    @validator("layers")
    def _ensure_layers(cls, value: Iterable[str]) -> List[str]:
        items = [layer.strip() for layer in value if layer.strip()]
        if not items:
            raise ValueError("At least one layer must be specified.")
        return items

    @validator("apn", always=True)
    def _require_identifier(cls, v: Optional[str], values: Dict[str, object]) -> Optional[str]:
        address = values.get("address")
        if not v and not address:
            raise ValueError("Provide either an address or an APN.")
        return v


@dataclass(slots=True)
class ParcelRecord:
    """Normalized parcel representation used by downstream components."""

    apn: str
    address: Optional[str]
    county: Optional[str]
    geometry: GeometryLike
    crs_epsg: int


@dataclass(slots=True)
class LayerConfig:
    """Subset of layer configuration resolved from YAML."""

    name: str
    type: str
    target_epsg: int
    params: Dict[str, object]


@dataclass(slots=True)
class LayerResult:
    """Metadata for a rendered layer output."""

    name: str
    path: Path
    warnings: List[str]
    crs_epsg: int
    created_at: datetime


class RenderResponse(BaseModel):
    """Structured API response for render jobs."""

    parcel: Dict[str, object]
    images: Dict[str, str]
    contact_sheet: Optional[str] = None
    created_at: datetime
    warnings: List[str] = Field(default_factory=list)
