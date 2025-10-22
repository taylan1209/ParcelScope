"""Utilities for loading application YAML configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping

import yaml

from .models import LayerConfig


class ConfigError(RuntimeError):
    """Raised when the configuration file is invalid."""


class SourceConfig:
    """Container for strongly-typed access to configuration data."""

    def __init__(self, raw: Mapping[str, Any]) -> None:
        self._raw = dict(raw)

    @property
    def default_crs(self) -> int:
        return int(self._raw.get("default_crs", 4326))

    @property
    def buffer_feet(self) -> float:
        return float(self._raw.get("buffer_feet", 200))

    @property
    def cache(self) -> Mapping[str, Any]:
        return self._raw.get("cache", {})

    @property
    def map_spec(self) -> Mapping[str, Any]:
        return self._raw.get(
            "map",
            {
                "width_px": 1600,
                "height_px": 1200,
                "dpi": 220,
            },
        )

    @property
    def parcels(self) -> Mapping[str, Any]:
        parcels = self._raw.get("parcels")
        if not parcels:
            raise ConfigError("Missing 'parcels' configuration.")
        return parcels

    @property
    def layers(self) -> Iterable[LayerConfig]:
        layers = self._raw.get("layers", {})
        for name, params in layers.items():
            if "type" not in params:
                raise ConfigError(f"Layer '{name}' missing 'type'.")
            target_epsg = int(params.get("target_epsg", self.default_crs))
            yield LayerConfig(
                name=name,
                type=str(params["type"]),
                target_epsg=target_epsg,
                params={k: v for k, v in params.items() if k not in ("type", "target_epsg")},
            )

    def get_layer(self, name: str) -> LayerConfig:
        for layer in self.layers:
            if layer.name == name:
                return layer
        raise ConfigError(f"Layer '{name}' not defined in configuration.")

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(self._raw))


def load_source_config(path: Path) -> SourceConfig:
    """Load configuration file and return a `SourceConfig` instance."""

    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}
    if not isinstance(data, MutableMapping):
        raise ConfigError("Configuration root must be a mapping.")
    return SourceConfig(data)
