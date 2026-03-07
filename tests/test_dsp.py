"""Tests for FFT spectrum analysis."""

import numpy as np
import pytest

from clamtune.dsp import compute_spectrum, find_peaks
from clamtune.constants import SAMPLE_RATE, BUFFER_SIZE


def make_sine(
    freq: float, duration_samples: int = BUFFER_SIZE, sr: int = SAMPLE_RATE
) -> np.ndarray:
    t = np.arange(duration_samples) / sr
    return (0.8 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_spectrum_shape():
    signal = make_sine(440.0)
    freqs, mags = compute_spectrum(signal, n_bins=64)
    assert len(freqs) == 64
    assert len(mags) == 64


def test_spectrum_peak_at_fundamental():
    signal = make_sine(440.0)
    freqs, mags = compute_spectrum(signal, n_bins=64)
    peak_idx = np.argmax(mags)
    peak_freq = freqs[peak_idx]
    assert peak_freq == pytest.approx(440.0, rel=0.15)


def test_spectrum_normalized():
    signal = make_sine(440.0)
    _, mags = compute_spectrum(signal)
    assert np.max(mags) == pytest.approx(1.0)
    assert np.min(mags) >= 0.0


def test_find_peaks_single_sine():
    signal = make_sine(440.0)
    freqs, mags = compute_spectrum(signal, n_bins=64)
    peaks = find_peaks(freqs, mags, threshold=0.3)
    assert len(peaks) >= 1
    assert peaks[0][0] == pytest.approx(440.0, rel=0.15)


def test_find_peaks_harmonics():
    freq = 110.0
    t = np.arange(BUFFER_SIZE) / SAMPLE_RATE
    signal = (0.8 * np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * 2 * freq * t)).astype(
        np.float32
    )
    freqs, mags = compute_spectrum(signal, n_bins=64)
    peaks = find_peaks(freqs, mags, threshold=0.2)
    peak_freqs = [p[0] for p in peaks]
    # Should detect both fundamental and harmonic
    assert any(abs(f - 110.0) / 110.0 < 0.2 for f in peak_freqs)
    assert any(abs(f - 220.0) / 220.0 < 0.2 for f in peak_freqs)


def test_spectrum_empty():
    freqs, mags = compute_spectrum(np.array([]))
    assert len(freqs) == 0
    assert len(mags) == 0
