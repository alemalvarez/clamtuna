"""FFT spectrum analysis."""

import numpy as np

from clamtuna.constants import SAMPLE_RATE


def compute_spectrum(
    signal: np.ndarray, sample_rate: int = SAMPLE_RATE, n_bins: int = 64
) -> tuple[np.ndarray, np.ndarray]:
    """Compute magnitude spectrum, returns (frequencies, magnitudes).

    Magnitudes are normalized to 0-1 range.
    Results are binned into n_bins logarithmically-spaced frequency bins
    from ~50Hz to ~5000Hz.
    """
    n = len(signal)
    if n == 0:
        return np.array([]), np.array([])

    windowed = signal * np.hanning(n)
    fft_result = np.fft.rfft(windowed)
    magnitudes = np.abs(fft_result) / n
    freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)

    # Limit to 50-5000 Hz range
    min_freq, max_freq = 50.0, 5000.0
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    freqs = freqs[mask]
    magnitudes = magnitudes[mask]

    if len(freqs) == 0:
        return np.array([]), np.array([])

    # Log-spaced bins
    log_bin_edges = np.logspace(np.log10(min_freq), np.log10(max_freq), n_bins + 1)
    binned_freqs = np.zeros(n_bins)
    binned_mags = np.zeros(n_bins)

    for i in range(n_bins):
        bin_mask = (freqs >= log_bin_edges[i]) & (freqs < log_bin_edges[i + 1])
        if np.any(bin_mask):
            binned_mags[i] = np.max(magnitudes[bin_mask])
            binned_freqs[i] = np.sqrt(log_bin_edges[i] * log_bin_edges[i + 1])  # geometric mean
        else:
            binned_freqs[i] = np.sqrt(log_bin_edges[i] * log_bin_edges[i + 1])

    # Normalize
    peak = np.max(binned_mags)
    if peak > 0:
        binned_mags = binned_mags / peak

    return binned_freqs, binned_mags


def find_peaks(
    freqs: np.ndarray, magnitudes: np.ndarray, threshold: float = 0.2
) -> list[tuple[float, float]]:
    """Find spectral peaks above threshold. Returns list of (freq, magnitude)."""
    if len(magnitudes) < 3:
        return []

    peaks = []
    for i in range(1, len(magnitudes) - 1):
        if (
            magnitudes[i] > magnitudes[i - 1]
            and magnitudes[i] > magnitudes[i + 1]
            and magnitudes[i] >= threshold
        ):
            peaks.append((float(freqs[i]), float(magnitudes[i])))

    peaks.sort(key=lambda p: p[1], reverse=True)
    return peaks
