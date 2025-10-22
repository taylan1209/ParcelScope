"""Map composition utilities for layer rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt


@dataclass
class FigureSpec:
    """Specification for output figures."""

    width: int
    height: int
    dpi: int
    title: Optional[str] = None


def render_placeholder_png(path: Path, spec: FigureSpec, message: str) -> None:
    """Write a placeholder PNG while the real renderer is under construction."""

    fig = plt.figure(figsize=(spec.width / spec.dpi, spec.height / spec.dpi), dpi=spec.dpi)
    ax = fig.add_subplot(111)
    ax.axis("off")
    if spec.title:
        ax.set_title(spec.title)
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, wrap=True)
    fig.savefig(path, dpi=spec.dpi, bbox_inches="tight")
    plt.close(fig)
