"""Tests for the render pipeline."""

from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box

from parcelviz.config_loader import SourceConfig
from parcelviz.models import ParcelRecord, RenderRequest
from parcelviz.pipeline import RenderPipeline
from parcelviz.settings import get_settings


class DummyGeocodeService:
    """Test double returning a fixed parcel record."""

    def resolve(self, *, address, apn):
        geometry = {
            "type": "Polygon",
            "coordinates": [
                [
                    (-80.0, 35.0),
                    (-80.0, 35.0005),
                    (-79.9995, 35.0005),
                    (-79.9995, 35.0),
                    (-80.0, 35.0),
                ]
            ],
        }
        return ParcelRecord(
            apn=apn or "123-456-789",
            address=address,
            county="Test County",
            geometry=geometry,
            crs_epsg=4326,
        )


class DummyLayer:
    """Layer adapter that returns a simple square GeoDataFrame."""

    def __init__(self, config, **_):
        self.config = config

    def fetch(self, extent):
        geom = box(extent["xmin"], extent["ymin"], extent["xmax"], extent["ymax"])
        return gpd.GeoDataFrame(
            {"value": [1]},
            geometry=[geom],
            crs=f"EPSG:{self.config.target_epsg}",
        )


def test_pipeline_renders_vector_layer(tmp_path, monkeypatch):
    output_root = tmp_path / "outputs"
    output_root.mkdir()
    cache_path = tmp_path / "cache" / "http_cache.sqlite"

    monkeypatch.setenv("OUTPUT_ROOT", str(output_root))
    monkeypatch.setenv("CACHE_PATH", str(cache_path))

    get_settings.cache_clear()

    config_data = {
        "default_crs": 4326,
        "map": {"width_px": 800, "height_px": 600, "dpi": 150},
        "parcels": {"provider": "dummy", "id_field": "APN", "address_field": "ADDR"},
        "layers": {
            "overlay": {
                "type": "arcgis_feature",
                "target_epsg": 3857,
                "style": {"fill_alpha": 0.3},
            }
        },
    }
    config = SourceConfig(config_data)

    pipeline = RenderPipeline(
        geocode_service=DummyGeocodeService(),
        config=config,
        layer_registry={"arcgis_feature": DummyLayer},
    )
    request = RenderRequest(address="123 Main St", layers=["overlay"], buffer_feet=200, output_dpi=180)

    response = pipeline.run(request)

    assert "overlay" in response.images
    path_str = response.images["overlay"]
    assert path_str.startswith("/outputs/")

    path = output_root / Path(path_str.replace("/outputs/", ""))
    assert path.exists()
    assert path.stat().st_size > 0
    assert response.warnings == []
    assert isinstance(response.created_at, datetime)
