"""Web Map Service layer adapter."""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Dict

import requests
from PIL import Image

from ..models import LayerConfig

LOGGER = logging.getLogger(__name__)


class WMSLayerError(RuntimeError):
    """Raised when WMS requests fail."""


class WMSLayer:
    """Fetch transparent PNG imagery from WMS/WMTS services."""

    def __init__(self, config: LayerConfig) -> None:
        self.config = config
        self.session = requests.Session()

    def fetch(self, bbox: Dict[str, float], size: int = 1024) -> Image.Image:
        """Return an image for the requested bounding box."""

        params = {
            "service": "WMS",
            "request": "GetMap",
            "format": "image/png",
            "transparent": "true",
            "version": self.config.params.get("version", "1.3.0"),
            "layers": self.config.params["layers"],
            "styles": self.config.params.get("styles", ""),
            "crs": f"EPSG:{self.config.target_epsg}",
            "bbox": ",".join(str(bbox[k]) for k in ("xmin", "ymin", "xmax", "ymax")),
            "width": size,
            "height": size,
        }
        response = self.session.get(self.config.params["url"], params=params, timeout=30)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
