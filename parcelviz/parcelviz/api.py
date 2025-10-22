"""FastAPI application exposing the render pipeline and static front-end."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .models import RenderRequest, RenderResponse
from .pipeline import PipelineError, RenderPipeline
from .settings import AppSettings, get_settings

LOGGER = logging.getLogger(__name__)
WEB_DIR = Path(__file__).resolve().parent / "web"
OUTPUT_DIR = get_settings().output_root
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ParcelViz API", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR, html=False), name="outputs")


def get_pipeline(settings: AppSettings = Depends(get_settings)) -> RenderPipeline:
    """Provide a RenderPipeline instance for FastAPI dependency injection."""

    return RenderPipeline(settings=settings)


@app.get("/health")
async def health() -> dict:
    """Lightweight health check endpoint."""

    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the simple front-end."""

    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    html = html.replace('href="styles.css"', 'href="/static/styles.css"')
    html = html.replace('src="main.js"', 'src="/static/main.js"')
    return HTMLResponse(content=html)


@app.post("/render", response_model=RenderResponse)
async def render(request: RenderRequest, pipeline: RenderPipeline = Depends(get_pipeline)) -> RenderResponse:
    """Render layers for a parcel."""

    try:
        return pipeline.run(request)
    except PipelineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Unhandled exception during render: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
