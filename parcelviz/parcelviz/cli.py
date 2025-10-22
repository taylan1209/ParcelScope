"""Command-line entry points for ParcelViz."""

from __future__ import annotations

import json
import logging
from typing import List, Optional

import typer

from .models import RenderRequest
from .pipeline import PipelineError, RenderPipeline

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def render(
    address: Optional[str] = typer.Option(None, help="Address to resolve."),
    apn: Optional[str] = typer.Option(None, help="Assessor parcel number."),
    layers: List[str] = typer.Option(..., "--layer", "--layers", help="Layer names to render."),
    buffer_feet: float = typer.Option(250.0, help="Buffer distance beyond parcel geometry."),
    output_dpi: int = typer.Option(220, min=96, max=600, help="Output DPI for generated images."),
) -> None:
    """Run the render pipeline from the command line."""

    pipeline = RenderPipeline()
    request = RenderRequest(address=address, apn=apn, layers=layers, buffer_feet=buffer_feet, output_dpi=output_dpi)
    try:
        response = pipeline.run(request)
    except PipelineError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    if response.warnings:
        typer.secho("Warnings:", fg=typer.colors.YELLOW)
        for warning in response.warnings:
            typer.echo(f"- {warning}")

    typer.secho("Render complete!", fg=typer.colors.GREEN)
    typer.echo(json.dumps(response.model_dump(), indent=2, default=str))


def main() -> None:
    """Entrypoint for python -m parcelviz."""

    logging.basicConfig(level=logging.INFO)
    app()


if __name__ == "__main__":
    main()
