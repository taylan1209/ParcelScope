"""Layer adapter registry."""

from __future__ import annotations

from typing import Dict, Type

from .arcgis import ArcGISFeatureLayer
from .wms import WMSLayer

LayerRegistry: Dict[str, Type] = {
    "arcgis_feature": ArcGISFeatureLayer,
    "wms": WMSLayer,
}


def get_layer_class(layer_type: str):
    """Return the layer adapter class for a type."""

    try:
        return LayerRegistry[layer_type]
    except KeyError as exc:
        raise KeyError(f"Unknown layer type '{layer_type}'.") from exc
