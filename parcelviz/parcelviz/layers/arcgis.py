"""ArcGIS FeatureServer layer adapter."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import geopandas as gpd
import requests

from ..models import LayerConfig

LOGGER = logging.getLogger(__name__)


class ArcGISLayerError(RuntimeError):
    """Raised when ArcGIS layer operations fail."""


class ArcGISFeatureLayer:
    """Fetch GeoDataFrame data from ArcGIS FeatureServer services."""

    def __init__(self, config: LayerConfig, token: Optional[str] = None) -> None:
        self.config = config
        self.session = requests.Session()
        self.token = token

    def fetch(self, extent: Dict[str, float]) -> gpd.GeoDataFrame:
        """Query features intersecting the provided extent."""

        params = {
            "f": "geojson",
            "geometry": self._extent_to_arcgis(extent, self.config.target_epsg),
            "geometryType": "esriGeometryEnvelope",
            "inSR": self.config.target_epsg,
            "outSR": self.config.target_epsg,
            "spatialRel": "esriSpatialRelIntersects",
            "maxRecordCountFactor": 4,
            "outFields": self.config.params.get("out_fields", "*"),
            "returnGeometry": "true",
        }
        self._apply_token(params)
        url = f"{self.config.params['url']}/query"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if "features" not in payload:
            raise ArcGISLayerError("FeatureServer response missing 'features'.")
        return gpd.GeoDataFrame.from_features(payload["features"], crs=f"EPSG:{self.config.target_epsg}")

    def _extent_to_arcgis(self, extent: Dict[str, float], srid: int) -> str:
        return (
            f"{extent['xmin']},{extent['ymin']},{extent['xmax']},{extent['ymax']}"
            f",{srid}"
        )

    def _apply_token(self, params: Dict[str, object]) -> None:
        if self.token:
            params["token"] = self.token
