"""Parcel data access helpers."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import requests

from .models import ParcelRecord

LOGGER = logging.getLogger(__name__)


class ParcelServiceError(RuntimeError):
    """Raised when parcel service operations fail."""


class ParcelService:
    """Fetch parcels from configured services (e.g., ArcGIS FeatureServer)."""

    def __init__(
        self,
        url: str,
        id_field: str,
        address_field: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.id_field = id_field
        self.address_field = address_field
        self.token = token
        self.session = requests.Session()

    def fetch_parcel_by_apn(self, apn: str, out_sr: int) -> ParcelRecord:
        """Query a parcel FeatureServer using an APN."""

        params = {
            "where": f"{self.id_field}='{apn}'",
            "outFields": "*",
            "f": "geojson",
            "outSR": out_sr,
            "returnGeometry": "true",
        }
        self._apply_token(params)
        response = self.session.get(f"{self.url}/query", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        features = data.get("features", [])
        if not features:
            raise ParcelServiceError(f"No parcel found for APN '{apn}'.")
        feature = features[0]
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})
        return ParcelRecord(
            apn=properties.get(self.id_field, apn),
            address=properties.get(self.address_field) if self.address_field else None,
            county=properties.get("COUNTY"),
            geometry=geometry,
            crs_epsg=out_sr,
        )

    def _apply_token(self, params: Dict[str, object]) -> None:
        if self.token:
            params["token"] = self.token
