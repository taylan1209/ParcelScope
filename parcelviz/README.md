# ParcelViz

ParcelViz is a modular toolkit for generating parcel-centric map overlays and imagery. It resolves parcels from addresses or APN values, fetches configured GIS layers, and produces crisp PNG exports per layer with optional contact sheets. The project exposes both a command-line interface and a FastAPI service and ships with a lightweight web UI for ad-hoc rendering.

## Features

- Configurable data sources via `config/sources.yaml` with per-layer CRS and styling.
- Parcel resolution through LightBox (LandVision) with fallback geocoders.
- Independent layer adapters for ArcGIS Feature/WMS services, FEMA flood, SSURGO soils, contours, and XYZ tiles.
- Consistent CRS handling and buffered map extents.
- On-disk HTTP caching to accelerate repeated requests.
- FastAPI `/render` endpoint plus CLI entry point.
- Simple React front-end for submitting render jobs and browsing outputs.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Update `.env` with your LightBox credentials and adjust `config/sources.yaml` for your target jurisdictions. Launch the API:

```bash
uvicorn parcelviz.api:app --reload
```

Or run from the CLI:

```bash
parcelviz render --address "123 Main St, City, NC" --layers zoning flood
```

Refer to `docs/` (coming soon) for detailed configuration guidance.
