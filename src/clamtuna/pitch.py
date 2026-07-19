"""YIN pitch detection algorithm (pure numpy)."""

import numpy as np

from clamtuna.constants import SAMPLE_RATE

DEFAULT_THRESHOLD = 0.15


def cmndf(signal: np.ndarray) -> np.ndarray:
    """Cumulative mean normalized difference function (YIN steps 1-3).

    Returns one value per lag tau in [0, len(signal) // 2).
    """
    n = len(signal)
    w = n // 2  # window size / max lag
    x = signal.astype(np.float64)

    # Difference function d(tau) = sum_{j=0}^{W-1} (x[j] - x[j+tau])^2
    # Use FFT cross-correlation between x[0:W] and x[0:N]
    fft_size = 1 << ((n - 1).bit_length() + 1)
    x1 = np.zeros(fft_size)
    x1[:w] = x[:w]
    x2 = np.zeros(fft_size)
    x2[:n] = x
    xcorr = np.fft.irfft(np.conj(np.fft.rfft(x1)) * np.fft.rfft(x2))

    # Energy terms: e1 is constant, e2(tau) is a sliding-window sum
    e1 = np.sum(x[:w] ** 2)
    cs = np.concatenate(([0.0], np.cumsum(x**2)))
    taus = np.arange(w)
    e2 = cs[np.minimum(taus + w, n)] - cs[taus]

    diff = e1 + e2 - 2.0 * xcorr[:w]
    diff[0] = 0.0

    # Cumulative mean normalization: cmndf(tau) = d(tau) * tau / sum_{1..tau} d
    result = np.ones(w)
    running = np.cumsum(diff[1:])
    np.divide(diff[1:] * np.arange(1, w), running, out=result[1:], where=running != 0)
    return result


def pick_tau(curve: np.ndarray, threshold: float = DEFAULT_THRESHOLD) -> int:
    """YIN step 4: first dip below threshold, walked to its local minimum.

    Returns the chosen lag, or 0 if nothing dips below the threshold.
    """
    w = len(curve)
    dips = np.flatnonzero(curve[2:] < threshold)
    if len(dips) == 0:
        return 0
    tau = int(dips[0]) + 2
    while tau + 1 < w and curve[tau + 1] < curve[tau]:
        tau += 1
    return tau


def yin(
    signal: np.ndarray, sample_rate: int = SAMPLE_RATE, threshold: float = DEFAULT_THRESHOLD
) -> float:
    """Detect fundamental frequency using the YIN algorithm.

    Returns detected frequency in Hz, or 0.0 if no pitch detected.
    """
    n = len(signal)
    w = n // 2
    if w < 2:
        return 0.0

    curve = cmndf(signal)
    tau = pick_tau(curve, threshold)
    if tau == 0:
        return 0.0

    # Step 5: Parabolic interpolation for sub-sample accuracy
    tau_estimate = float(tau)
    if 0 < tau < w - 1:
        a, b, c = curve[tau - 1], curve[tau], curve[tau + 1]
        denom = a - 2 * b + c
        if denom != 0:
            tau_estimate = tau + (a - c) / (2 * denom)

    return float(sample_rate / tau_estimate)
