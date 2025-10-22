"""Render pipeline orchestration."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from shapely.geometry import shape

from .config_loader import SourceConfig, load_source_config
from .geocode import GeocodeService, GeocodeError, LightBoxClient
from .mapcompose import FigureSpec, render_placeholder_png
from .models import LayerResult, ParcelRecord, RenderRequest, RenderResponse
from .settings import AppSettings, get_settings
from .utils import ensure_directory

LOGGER = logging.getLogger(__name__)


class PipelineError(RuntimeError):
    """Raised when the pipeline cannot complete."""


class RenderPipeline:
    """High-level orchestrator translating requests into rendered outputs."""

    def __init__(
        self,
        *,
        settings: Optional[AppSettings] = None,
        geocode_service: Optional[GeocodeService] = None,
        config: Optional[SourceConfig] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.config = config or load_source_config(self.settings.config_path)
        self.geocode_service = geocode_service or self._build_geocode_service()

    def run(self, request: RenderRequest) -> RenderResponse:
        """Execute the full render flow for a request."""

        try:
            parcel = self._resolve_parcel(request)
        except GeocodeError as exc:
            raise PipelineError(str(exc)) from exc

        output_dir = ensure_directory(self._output_dir(parcel))
        layer_results: List[LayerResult] = []
        for layer_name in request.layers:
            try:
                result = self._render_layer(layer_name, parcel, request, output_dir)
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.exception("Layer '%s' failed: %s", layer_name, exc)
                continue
            layer_results.append(result)

        images = {result.name: self._to_public_url(result.path) for result in layer_results}
        warnings = [warn for result in layer_results for warn in result.warnings]
        return RenderResponse(
            parcel={
                "apn": parcel.apn,
                "address": parcel.address,
                "county": parcel.county,
                "crs": f"EPSG:{parcel.crs_epsg}",
            },
            images=images,
            contact_sheet=None,
            created_at=datetime.utcnow(),
            warnings=warnings,
        )

    def _resolve_parcel(self, request: RenderRequest) -> ParcelRecord:
        return self.geocode_service.resolve(address=request.address, apn=request.apn)

    def _render_layer(
        self,
        layer_name: str,
        parcel: ParcelRecord,
        request: RenderRequest,
        output_dir: Path,
    ) -> LayerResult:
        """Render a single layer output."""

        layer_config = self.config.get_layer(layer_name)
        parcel_geom = shape(parcel.geometry)
        output_path = output_dir / f"{layer_name}.png"

        render_placeholder_png(
            output_path,
            FigureSpec(width=1600, height=1200, dpi=request.output_dpi, title=f"{parcel.apn} – {layer_name.title()}"),
            message="Rendering pipeline not yet implemented.",
        )

        return LayerResult(
            name=layer_name,
            path=output_path,
            warnings=["Rendering not yet implemented."],
            crs_epsg=layer_config.target_epsg,
            created_at=datetime.utcnow(),
        )

    def _output_dir(self, parcel: ParcelRecord) -> Path:
        root = self.settings.output_root
        return root / parcel.apn.replace("/", "_")

    def _to_public_url(self, path: Path) -> str:
        try:
            relative = path.relative_to(self.settings.output_root)
        except ValueError:
            return str(path)
        return f"/outputs/{relative.as_posix()}"

    def _build_geocode_service(self) -> GeocodeService:
        settings = self.settings
        if settings.lightbox_api_key:
            client = LightBoxClient(settings.lightbox_api_key, settings.lightbox_base_url)
        else:
            client = None
        return GeocodeService(lightbox_client=client)
