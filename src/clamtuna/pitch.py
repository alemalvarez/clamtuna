"""YIN pitch detection algorithm (pure numpy)."""

import numpy as np

from clamtuna.constants import SAMPLE_RATE


def yin(signal: np.ndarray, sample_rate: int = SAMPLE_RATE, threshold: float = 0.15) -> float:
    """Detect fundamental frequency using the YIN algorithm.

    Returns detected frequency in Hz, or 0.0 if no pitch detected.
    """
    n = len(signal)
    w = n // 2  # window size / max lag
    if w < 2:
        return 0.0

    x = np.float64(signal)

    # Step 1-2: Difference function d(tau) = sum_{j=0}^{W-1} (x[j] - x[j+tau])^2
    # Use FFT cross-correlation between x[0:W] and x[0:N]
    fft_size = 1
    while fft_size < n:
        fft_size *= 2
    fft_size *= 2

    x1 = np.zeros(fft_size)
    x1[:w] = x[:w]
    x2 = np.zeros(fft_size)
    x2[:n] = x[:n]

    fft1 = np.fft.rfft(x1)
    fft2 = np.fft.rfft(x2)
    # cross-correlation: sum_{j} x1[j] * x2[j+tau]
    xcorr = np.fft.irfft(np.conj(fft1) * fft2)

    # Energy terms
    e1 = np.sum(x[:w] ** 2)  # sum x[j]^2 for j in [0, W-1] — constant for all tau
    # e2(tau) = sum x[j+tau]^2 for j in [0, W-1] = sum x[k]^2 for k in [tau, tau+W-1]
    cumsum = np.cumsum(x**2)
    e2 = np.empty(w)
    e2[0] = cumsum[w - 1]
    for tau in range(1, w):
        end = tau + w - 1
        if end < n:
            e2[tau] = cumsum[end] - cumsum[tau - 1]
        else:
            e2[tau] = cumsum[n - 1] - cumsum[tau - 1]

    diff = e1 + e2 - 2.0 * xcorr[:w]
    diff[0] = 0.0

    # Step 3: Cumulative mean normalized difference
    cmndf = np.ones(w)
    running_sum = 0.0
    for tau in range(1, w):
        running_sum += diff[tau]
        if running_sum == 0:
            cmndf[tau] = 1.0
        else:
            cmndf[tau] = diff[tau] * tau / running_sum

    # Step 4: Absolute threshold — find first dip below threshold, walk to local min
    tau_estimate = 0
    for tau in range(2, w):
        if cmndf[tau] < threshold:
            while tau + 1 < w and cmndf[tau + 1] < cmndf[tau]:
                tau += 1
            tau_estimate = tau
            break

    if tau_estimate == 0:
        return 0.0

    # Step 5: Parabolic interpolation for sub-sample accuracy
    if 0 < tau_estimate < w - 1:
        a = cmndf[tau_estimate - 1]
        b = cmndf[tau_estimate]
        c = cmndf[tau_estimate + 1]
        denom = a - 2 * b + c
        if denom != 0:
            tau_estimate = tau_estimate + (a - c) / (2 * denom)

    freq = sample_rate / tau_estimate
    return float(freq)
