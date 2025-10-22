"""Geocoding and parcel resolution utilities."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import requests
from shapely.geometry import shape

from .models import ParcelRecord

LOGGER = logging.getLogger(__name__)


class GeocodeError(RuntimeError):
    """Raised when a geocode lookup fails."""


class LightBoxClient:
    """Thin wrapper around the LightBox (LandVision) API."""

    def __init__(self, api_key: str, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def address_to_parcel(self, address: str) -> ParcelRecord:
        """Resolve an address to a parcel record."""

        search_payload = {"address": address, "limit": 1}
        response = self.session.post(f"{self.base_url}/geocode", json=search_payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        if not data.get("results"):
            raise GeocodeError(f"No results returned for address: {address}")
        candidate = data["results"][0]

        parcel_info = self._lookup_parcel(candidate["parcelId"])
        geometry = shape(parcel_info["geometry"])
        return ParcelRecord(
            apn=parcel_info.get("apn", candidate.get("parcelId", "")),
            address=parcel_info.get("siteAddress", address),
            county=parcel_info.get("county"),
            geometry=geometry.__geo_interface__,
            crs_epsg=4326,
        )

    def _lookup_parcel(self, parcel_id: str) -> Dict[str, object]:
        response = self.session.get(f"{self.base_url}/parcels/{parcel_id}", timeout=20)
        response.raise_for_status()
        return response.json()


class GeocodeService:
    """Facade encapsulating all geocoding strategies."""

    def __init__(self, lightbox_client: Optional[LightBoxClient] = None):
        self.lightbox_client = lightbox_client

    def resolve(self, *, address: Optional[str], apn: Optional[str]) -> ParcelRecord:
        """Return a parcel record from an address or APN."""

        if apn:
            raise GeocodeError("APN resolution not yet implemented.")
        if not address:
            raise GeocodeError("Either address or APN must be provided.")
        if self.lightbox_client is None:
            raise GeocodeError("LightBox client not configured for address lookups.")
        return self.lightbox_client.address_to_parcel(address)
