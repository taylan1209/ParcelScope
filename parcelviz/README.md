# ParcelViz

ParcelViz is a modular toolkit for generating parcel-centric map overlays and imagery. It resolves parcels from addresses or APN values, fetches configured GIS layers, and produces crisp PNG exports per layer with optional contact sheets. The project exposes both a command-line interface and a FastAPI service and ships with a lightweight web UI for ad-hoc rendering.

## Purpose

ParcelViz streamlines parcel due diligence workflows by automating parcel lookup, fetching zoning and environmental overlays, and delivering consistent map exports suited for planning reviews, entitlement packages, and client-ready reports.

## Technologies

- Python 3.9+
- FastAPI + Typer for API and CLI interfaces
- GeoPandas, Shapely, and PyProj for spatial data handling
- Matplotlib and Pillow for cartography and image export
- Requests and requests-cache for resilient HTTP access
- Lightweight static web front-end (vanilla JS + CSS)

## Features

- Configurable data sources via `config/sources.yaml` with per-layer CRS, styling, and map canvas settings.
- Parcel resolution through LightBox (LandVision) with fallback geocoders.
- Independent layer adapters for ArcGIS Feature/WMS services, FEMA flood, SSURGO soils, contours, and XYZ tiles.
- Consistent CRS handling, buffered map extents, and parcel highlighting.
- On-disk HTTP caching (requests-cache) to accelerate repeated requests.
- FastAPI `/render` endpoint plus CLI entry point.
- Simple static web front-end for submitting render jobs and browsing outputs.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Update `.env` with your LightBox credentials and adjust `config/sources.yaml` for your target jurisdictions. Launch the API (serves the web UI at `/` and exposes generated imagery under `/outputs`):

```bash
uvicorn parcelviz.api:app --reload
```

Or render directly from the CLI:

```bash
parcelviz render --address "123 Main St, City, NC" --layers zoning flood
```

## Configuration

- `config/sources.yaml` carries parcel service metadata (`parcels`), layer adapters, and the default map canvas (`map.width_px`, `map.height_px`, `map.dpi`). Each layer can specify `style` keys such as `fill_alpha`, `line_color`, or WMS `opacity`.
- Caching defaults to `cache/http_cache.sqlite`; override by editing the config or setting the `CACHE_PATH` environment variable.
- Parcel buffers are supplied in feet via the API/CLI (`buffer_feet`) and automatically converted to the target layer CRS.

## Web UI

Navigate to `http://localhost:8000/` after starting the API. Provide an address or APN, pick layers, and submit. Results display parcel metadata, gallery thumbnails, download links, and inline warnings surfaced by the pipeline.

## Testing

Unit tests rely on adapter stubs to avoid remote calls:

```bash
pytest
```

Ensure dependencies from `.[dev]` are installed before running the suite.
