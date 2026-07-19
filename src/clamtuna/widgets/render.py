"""Shared widget rendering helpers: color palette and block-character columns."""

import numpy as np

from clamtuna.constants import CLOSE_CENTS, IN_TUNE_CENTS

BLOCKS = " ▁▂▃▄▅▆▇█"

# Palette
GREEN = "#5c8a7d"
YELLOW = "#c9a94e"
RED = "#c45c5c"
DIM = "#3a3f4b"


def cents_status(cents: float) -> tuple[str, str]:
    """Map a cents offset to its (color, label): in tune, close, or off."""
    if abs(cents) < IN_TUNE_CENTS:
        return GREEN, "IN TUNE"
    if abs(cents) < CLOSE_CENTS:
        return YELLOW, "CLOSE"
    return RED, ""


def downsample(values: np.ndarray, width: int) -> np.ndarray:
    """Pick evenly-spaced samples so values fit in width columns."""
    if len(values) <= width:
        return values
    return values[np.linspace(0, len(values) - 1, width, dtype=int)]


def render_block_rows(values: np.ndarray, height: int) -> list[str]:
    """Render 0-1 values as columns of block characters, one string per row (top-down)."""
    rows = []
    for row in range(height):
        top = 1.0 - row / height
        bottom = 1.0 - (row + 1) / height
        # Fraction of this row's band that each column fills, in eighths
        idx = np.clip(((values - bottom) * height * 8).astype(int), 0, 8)
        idx[values >= top] = 8
        idx[values <= bottom] = 0
        rows.append("".join(BLOCKS[i] for i in idx))
    return rows
