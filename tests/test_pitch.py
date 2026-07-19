"""Tests for YIN pitch detection with synthetic sine waves."""

import numpy as np
import pytest

from clamtuna.pitch import yin
from clamtuna.constants import SAMPLE_RATE, BUFFER_SIZE, STANDARD_TUNING

from tests.conftest import make_sine

TUNING_CASES = [*STANDARD_TUNING, ("A4", 440.0)]


@pytest.mark.parametrize(("name", "freq"), TUNING_CASES, ids=[name for name, _ in TUNING_CASES])
def test_yin_standard_tuning(name, freq):
    signal = make_sine(freq)
    detected = yin(signal)
    assert detected == pytest.approx(freq, rel=0.02), f"Expected ~{freq}, got {detected}"


def test_yin_silence():
    signal = np.zeros(BUFFER_SIZE, dtype=np.float32)
    detected = yin(signal)
    assert detected == 0.0


def test_yin_noise():
    rng = np.random.default_rng(42)
    signal = (rng.standard_normal(BUFFER_SIZE) * 0.01).astype(np.float32)
    detected = yin(signal)
    # Should either return 0 or some unreliable value — just shouldn't crash
    assert isinstance(detected, float)


def test_yin_with_harmonics():
    """Test detection with a signal containing harmonics (more realistic guitar tone)."""
    freq = 110.0  # A2
    t = np.arange(BUFFER_SIZE) / SAMPLE_RATE
    signal = (
        0.8 * np.sin(2 * np.pi * freq * t)
        + 0.4 * np.sin(2 * np.pi * 2 * freq * t)
        + 0.2 * np.sin(2 * np.pi * 3 * freq * t)
    ).astype(np.float32)
    detected = yin(signal)
    assert detected == pytest.approx(freq, rel=0.02)
