"""Tests for the render pipeline."""

from datetime import datetime
from pathlib import Path

import pytest

from parcelviz.models import ParcelRecord, RenderRequest
from parcelviz.pipeline import RenderPipeline


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


@pytest.fixture()
def tmp_outputs(tmp_path):
    root = tmp_path / "outputs"
    root.mkdir()
    return root


def test_pipeline_creates_placeholder_images(tmp_outputs, monkeypatch):
    monkeypatch.setenv("OUTPUT_ROOT", str(tmp_outputs))
    pipeline = RenderPipeline(geocode_service=DummyGeocodeService())
    request = RenderRequest(address="123 Main St", layers=["zoning"], buffer_feet=250, output_dpi=200)

    response = pipeline.run(request)

    assert response.images, "Expected at least one image path."
    for path_str in response.images.values():
        assert path_str.startswith("/outputs/")
        path = tmp_outputs / Path(path_str.replace("/outputs/", ""))
        assert path.exists()
        assert path.suffix == ".png"
    assert isinstance(response.created_at, datetime)
