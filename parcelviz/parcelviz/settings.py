"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Runtime configuration for the ParcelViz service."""

    model_config = SettingsConfigDict(env_file=(".env",), env_file_encoding="utf-8", case_sensitive=False)

    config_path: Path = Path("config/sources.yaml")
    output_root: Path = Path("outputs")
    cache_path: Path = Path("cache/http_cache.sqlite")

    lightbox_api_key: Optional[str] = None
    lightbox_base_url: str = "https://api.lightboxre.com/v1"

    arcgis_token: Optional[str] = None

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    log_level: str = "INFO"


@lru_cache
def get_settings() -> "AppSettings":
    """Return cached settings instance."""

    return AppSettings()
