"""Shared test helpers."""

import numpy as np

from clamtuna.constants import BUFFER_SIZE, SAMPLE_RATE


def make_sine(
    freq: float, duration_samples: int = BUFFER_SIZE, sr: int = SAMPLE_RATE
) -> np.ndarray:
    """Generate a pure sine wave at the given frequency."""
    t = np.arange(duration_samples) / sr
    return (0.8 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
