"""Render pipeline orchestration."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from shapely.geometry import shape

from .cache import configure_requests_cache
from .config_loader import ConfigError, SourceConfig, load_source_config
from .crs import buffered_geometry_bounds
from .geocode import GeocodeService, GeocodeError, LightBoxClient
from .layers import LayerRegistry as DEFAULT_LAYER_REGISTRY
from .mapcompose import FigureSpec, render_placeholder_png, render_vector_layer, render_wms_layer
from .models import LayerConfig, LayerResult, ParcelRecord, RenderRequest, RenderResponse
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
        layer_registry: Optional[Dict[str, type]] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.config = config or load_source_config(self.settings.config_path)
        self.geocode_service = geocode_service or self._build_geocode_service()
        self.layer_registry = layer_registry or dict(DEFAULT_LAYER_REGISTRY)
        self._configure_cache()
        self.figure_spec = self._figure_spec_from_config()

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
                layer_config = self.config.get_layer(layer_name)
            except ConfigError as exc:
                LOGGER.error("Layer '%s' not defined: %s", layer_name, exc)
                continue
            try:
                result = self._render_layer(layer_config, parcel, request, output_dir)
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.exception("Layer '%s' failed: %s", layer_name, exc)
                result = self._render_layer_failure(layer_config, parcel, request, output_dir, exc)
            if result:
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
        layer_config: LayerConfig,
        parcel: ParcelRecord,
        request: RenderRequest,
        output_dir: Path,
    ) -> LayerResult:
        """Render a single layer output."""

        parcel_geom = shape(parcel.geometry)
        projected_geom, bounds = buffered_geometry_bounds(
            parcel_geom, parcel.crs_epsg, layer_config.target_epsg, request.buffer_feet
        )
        extent_dict = {
            "xmin": bounds[0],
            "ymin": bounds[1],
            "xmax": bounds[2],
            "ymax": bounds[3],
        }
        spec = FigureSpec(
            width=self.figure_spec.width,
            height=self.figure_spec.height,
            dpi=request.output_dpi,
            title=f"{parcel.apn} – {layer_config.name.title()}",
        )
        output_path = output_dir / f"{layer_config.name}.png"
        adapter = self._build_layer_adapter(layer_config)

        warnings: List[str] = []

        if layer_config.type == "arcgis_feature":
            data = adapter.fetch(extent_dict)
            if data.empty:
                warnings.append("No features returned for extent.")
            render_vector_layer(
                output_path=output_path,
                spec=spec,
                extent=bounds,
                parcel_geom=projected_geom,
                vector=data,
                style=layer_config.params.get("style", {}),
            )
        elif layer_config.type == "wms":
            width_px, height_px = spec.width, spec.height
            image = adapter.fetch(extent_dict, size=(width_px, height_px))
            render_wms_layer(
                output_path=output_path,
                spec=spec,
                extent=bounds,
                parcel_geom=projected_geom,
                image=image,
                style=layer_config.params.get("style", {}),
            )
        else:
            raise PipelineError(f"Unsupported layer type '{layer_config.type}'.")

        return LayerResult(
            name=layer_config.name,
            path=output_path,
            warnings=warnings,
            crs_epsg=layer_config.target_epsg,
            created_at=datetime.utcnow(),
        )

    def _render_layer_failure(
        self,
        layer_config: LayerConfig,
        parcel: ParcelRecord,
        request: RenderRequest,
        output_dir: Path,
        exc: Exception,
    ) -> Optional[LayerResult]:
        output_path = output_dir / f"{layer_config.name}_error.png"
        render_placeholder_png(
            output_path,
            FigureSpec(
                width=self.figure_spec.width,
                height=self.figure_spec.height,
                dpi=request.output_dpi,
                title=f"{parcel.apn} – {layer_config.name.title()}",
            ),
            message=f"Layer failed to render: {exc}",
        )
        return LayerResult(
            name=layer_config.name,
            path=output_path,
            warnings=[f"Layer '{layer_config.name}' failed: {exc}"],
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

    def _configure_cache(self) -> None:
        cache_settings = self.config.cache
        backend = cache_settings.get("backend", "sqlite")
        expire_hours = cache_settings.get("expire_hours")
        cache_path = Path(cache_settings.get("path", self.settings.cache_path))
        if not cache_path.is_absolute():
            cache_path = self.settings.config_path.parent / cache_path
        configure_requests_cache(cache_path, expire_hours=expire_hours, backend=backend)

    def _figure_spec_from_config(self) -> FigureSpec:
        map_spec = self.config.map_spec
        return FigureSpec(
            width=int(map_spec.get("width_px", 1600)),
            height=int(map_spec.get("height_px", 1200)),
            dpi=int(map_spec.get("dpi", 220)),
            title=None,
        )

    def _build_layer_adapter(self, layer_config):
        try:
            layer_cls = self.layer_registry[layer_config.type]
        except KeyError as exc:
            raise PipelineError(f"Layer type '{layer_config.type}' is not registered.") from exc
        kwargs = {}
        if layer_config.type.startswith("arcgis") and self.settings.arcgis_token:
            kwargs["token"] = self.settings.arcgis_token
        return layer_cls(layer_config, **kwargs)
