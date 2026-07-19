"""FFT spectrum analysis and signal-level helpers."""

from functools import lru_cache

import numpy as np

from clamtuna.constants import SAMPLE_RATE, SPECTRUM_MAX_FREQ, SPECTRUM_MIN_FREQ


def rms(signal: np.ndarray) -> float:
    """Root-mean-square level of a signal."""
    if len(signal) == 0:
        return 0.0
    return float(np.sqrt(np.mean(signal.astype(np.float64) ** 2)))


@lru_cache(maxsize=4)
def _spectrum_layout(
    n: int, sample_rate: int, n_bins: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Constants for a given (signal length, sample rate, bin count).

    Returns (window, in-range frequency mask, per-frequency bin index,
    geometric-mean center frequency of each log-spaced bin).
    """
    window = np.hanning(n)
    freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)
    mask = (freqs >= SPECTRUM_MIN_FREQ) & (freqs <= SPECTRUM_MAX_FREQ)
    edges = np.logspace(np.log10(SPECTRUM_MIN_FREQ), np.log10(SPECTRUM_MAX_FREQ), n_bins + 1)
    binned_freqs = np.sqrt(edges[:-1] * edges[1:])
    bin_idx = np.clip(np.digitize(freqs[mask], edges) - 1, 0, n_bins - 1)
    return window, mask, bin_idx, binned_freqs


def compute_spectrum(
    signal: np.ndarray, sample_rate: int = SAMPLE_RATE, n_bins: int = 64
) -> tuple[np.ndarray, np.ndarray]:
    """Compute magnitude spectrum, returns (frequencies, magnitudes).

    Magnitudes are normalized to 0-1 range.
    Results are binned into n_bins logarithmically-spaced frequency bins
    from SPECTRUM_MIN_FREQ to SPECTRUM_MAX_FREQ.
    """
    n = len(signal)
    if n == 0:
        return np.array([]), np.array([])

    window, mask, bin_idx, binned_freqs = _spectrum_layout(n, sample_rate, n_bins)
    magnitudes = (np.abs(np.fft.rfft(signal * window)) / n)[mask]
    if len(magnitudes) == 0:
        return np.array([]), np.array([])

    # Each bin takes the max magnitude of the raw frequencies that fall in it
    binned_mags = np.zeros(n_bins)
    np.maximum.at(binned_mags, bin_idx, magnitudes)

    peak = np.max(binned_mags)
    if peak > 0:
        binned_mags /= peak

    return binned_freqs, binned_mags


def find_peaks(
    freqs: np.ndarray, magnitudes: np.ndarray, threshold: float = 0.2
) -> list[tuple[float, float]]:
    """Find spectral peaks above threshold. Returns (freq, magnitude) pairs, loudest first."""
    if len(magnitudes) < 3:
        return []

    m = magnitudes
    peak_idx = np.flatnonzero((m[1:-1] > m[:-2]) & (m[1:-1] > m[2:]) & (m[1:-1] >= threshold)) + 1
    peaks = [(float(freqs[i]), float(m[i])) for i in peak_idx]
    peaks.sort(key=lambda p: p[1], reverse=True)
    return peaks
