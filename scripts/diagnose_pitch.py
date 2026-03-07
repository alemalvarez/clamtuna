"""Diagnostic script: record a note, analyze spectrum + YIN pitch detection."""

import sys
import time

import numpy as np
import sounddevice as sd

# Add src to path so we can import clamtuna
sys.path.insert(0, "src")

from clamtuna.constants import SAMPLE_RATE, BUFFER_SIZE
from clamtuna.pitch import yin


RECORD_SECONDS = 2
EXPECTED_FREQ = float(sys.argv[1]) if len(sys.argv) > 1 else 110.0


def record(seconds: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    print(f"Recording {seconds}s at {sr} Hz... Play your note NOW!")
    time.sleep(0.3)  # tiny grace period
    audio = sd.rec(int(seconds * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    print("Done recording.\n")
    return audio[:, 0]


def analyze_spectrum(signal: np.ndarray, sr: int = SAMPLE_RATE):
    """Show top spectral peaks."""
    windowed = signal * np.hanning(len(signal))
    fft_result = np.fft.rfft(windowed)
    magnitudes = np.abs(fft_result)
    freqs = np.fft.rfftfreq(len(signal), 1.0 / sr)

    # Focus on 50-2000 Hz
    mask = (freqs >= 50) & (freqs <= 2000)
    freqs = freqs[mask]
    magnitudes = magnitudes[mask]

    # Find top 10 peaks
    peak_indices = []
    for i in range(1, len(magnitudes) - 1):
        if magnitudes[i] > magnitudes[i - 1] and magnitudes[i] > magnitudes[i + 1]:
            peak_indices.append(i)
    peak_indices.sort(key=lambda i: magnitudes[i], reverse=True)
    peak_indices = peak_indices[:10]

    top_mag = magnitudes[peak_indices[0]] if peak_indices else 1.0
    print("=== FFT Spectrum Peaks (50-2000 Hz) ===")
    print(f"{'Freq (Hz)':>12}  {'Magnitude':>10}  {'Relative':>8}  {'Harmonic?'}")
    print("-" * 55)
    for idx in peak_indices:
        f = freqs[idx]
        m = magnitudes[idx]
        rel = m / top_mag
        # Check if it's a harmonic of the expected fundamental
        ratio = f / EXPECTED_FREQ
        nearest_int = round(ratio)
        is_harmonic = abs(ratio - nearest_int) < 0.08 and nearest_int >= 1
        label = f"~{nearest_int}x fundamental" if is_harmonic else ""
        bar = "#" * int(rel * 30)
        print(f"{f:>12.1f}  {m:>10.1f}  {rel:>8.3f}  {bar} {label}")
    print()


def analyze_yin_detail(signal: np.ndarray, sr: int = SAMPLE_RATE):
    """Run YIN and also show the CMNDF at key lag points."""
    n = len(signal)
    w = n // 2
    x = np.float64(signal)

    # Compute difference function (same as in pitch.py)
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
    xcorr = np.fft.irfft(np.conj(fft1) * fft2)

    e1 = np.sum(x[:w] ** 2)
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

    # CMNDF
    cmndf = np.ones(w)
    running_sum = 0.0
    for tau in range(1, w):
        running_sum += diff[tau]
        if running_sum == 0:
            cmndf[tau] = 1.0
        else:
            cmndf[tau] = diff[tau] * tau / running_sum

    # Show CMNDF values at expected fundamental and its harmonics
    print(f"=== CMNDF at key lag points (expected fundamental: {EXPECTED_FREQ} Hz) ===")
    print(f"{'Harmonic':>10}  {'Freq (Hz)':>10}  {'Lag (samples)':>14}  {'CMNDF value':>12}  {'< 0.15?'}")
    print("-" * 70)
    for h in [1, 2, 3, 4, 5]:
        freq_h = EXPECTED_FREQ * h
        lag = int(round(sr / freq_h))
        if 0 < lag < w:
            val = cmndf[lag]
            # Also find local min near this lag
            search_start = max(2, lag - 5)
            search_end = min(w, lag + 6)
            local_min_lag = search_start + np.argmin(cmndf[search_start:search_end])
            local_min_val = cmndf[local_min_lag]
            below = "YES" if val < 0.15 else "no"
            note = ""
            if h == 1:
                note = "<-- fundamental"
            else:
                note = f"<-- {h}x harmonic (lag = period/{h})"
            print(
                f"{'1/' + str(h) + 'x':>10}  {freq_h:>10.1f}  {lag:>14}  {val:>12.4f}  {below:>7}  {note}"
            )
            if local_min_lag != lag:
                print(f"{'':>10}  {'':>10}  {local_min_lag:>14}  {local_min_val:>12.4f}         (nearby min)")
    print()

    # Show where YIN actually picks its estimate
    threshold = 0.15
    tau_estimate = 0
    for tau in range(2, w):
        if cmndf[tau] < threshold:
            while tau + 1 < w and cmndf[tau + 1] < cmndf[tau]:
                tau += 1
            tau_estimate = tau
            break

    if tau_estimate > 0:
        detected_freq = sr / tau_estimate
        print(f"YIN picks lag={tau_estimate} -> {detected_freq:.2f} Hz")
        ratio = detected_freq / EXPECTED_FREQ
        print(f"Ratio to expected: {ratio:.3f}x", end="")
        nearest = round(ratio)
        if abs(ratio - nearest) < 0.08 and nearest > 1:
            print(f"  ** Locked onto harmonic {nearest}x! **")
        elif abs(ratio - 1) < 0.08:
            print("  (correct)")
        else:
            print()
    else:
        print("YIN: no pitch detected (nothing below threshold)")
    print()


def run_yin_on_chunks(audio: np.ndarray, sr: int = SAMPLE_RATE):
    """Run YIN on BUFFER_SIZE chunks across the recording, like the real tuner does."""
    print(f"=== YIN on {BUFFER_SIZE}-sample chunks across recording ===")
    detections = []
    n_chunks = len(audio) // BUFFER_SIZE
    for i in range(n_chunks):
        chunk = audio[i * BUFFER_SIZE : (i + 1) * BUFFER_SIZE]
        freq = yin(chunk, sr)
        detections.append(freq)
        t = i * BUFFER_SIZE / sr
        if freq > 0:
            ratio = freq / EXPECTED_FREQ
            flag = ""
            nearest = round(ratio)
            if abs(ratio - nearest) < 0.08 and nearest > 1:
                flag = f"  ** {nearest}x harmonic **"
            elif abs(ratio - 1) < 0.08:
                flag = "  (correct)"
            print(f"  t={t:.2f}s  detected={freq:>7.1f} Hz  ratio={ratio:.2f}x{flag}")
        else:
            print(f"  t={t:.2f}s  detected=  --")

    valid = [f for f in detections if f > 0]
    if valid:
        print(f"\nMedian detection: {np.median(valid):.1f} Hz")
        print(f"Mean detection:   {np.mean(valid):.1f} Hz")
    print()


def main():
    print(f"Expected note frequency: {EXPECTED_FREQ} Hz")
    print(f"Sample rate: {SAMPLE_RATE}, Buffer size: {BUFFER_SIZE}\n")

    audio = record(RECORD_SECONDS)

    # Save for re-analysis
    outpath = "scripts/recorded_note.npy"
    np.save(outpath, audio)
    print(f"Saved raw audio to {outpath} ({len(audio)} samples)\n")

    # Use the loudest 4096-sample window for detailed analysis
    # (find the chunk with highest RMS)
    best_start = 0
    best_rms = 0
    for start in range(0, len(audio) - BUFFER_SIZE, BUFFER_SIZE // 4):
        chunk = audio[start : start + BUFFER_SIZE]
        rms = np.sqrt(np.mean(chunk**2))
        if rms > best_rms:
            best_rms = rms
            best_start = start

    best_chunk = audio[best_start : best_start + BUFFER_SIZE]
    print(f"Loudest chunk at sample {best_start} (t={best_start/SAMPLE_RATE:.2f}s, RMS={best_rms:.4f})\n")

    analyze_spectrum(best_chunk)
    analyze_yin_detail(best_chunk)
    run_yin_on_chunks(audio)


if __name__ == "__main__":
    main()
