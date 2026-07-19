"""Diagnostic script: record a note, analyze spectrum + YIN pitch detection."""

import sys
import time

import numpy as np
import sounddevice as sd

from clamtuna.constants import BUFFER_SIZE, SAMPLE_RATE
from clamtuna.dsp import find_peaks, rms
from clamtuna.pitch import DEFAULT_THRESHOLD, cmndf, pick_tau, yin

RECORD_SECONDS = 2
EXPECTED_FREQ = float(sys.argv[1]) if len(sys.argv) > 1 else 110.0


def harmonic_of(freq: float, fundamental: float, tol: float = 0.08) -> int | None:
    """Which harmonic of fundamental this freq is (1 = the fundamental itself), or None."""
    ratio = freq / fundamental
    nearest = round(ratio)
    return nearest if nearest >= 1 and abs(ratio - nearest) < tol else None


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
    magnitudes = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(signal), 1.0 / sr)

    # Focus on 50-2000 Hz, top 10 peaks
    mask = (freqs >= 50) & (freqs <= 2000)
    peaks = find_peaks(freqs[mask], magnitudes[mask], threshold=0.0)[:10]

    top_mag = peaks[0][1] if peaks else 1.0
    print("=== FFT Spectrum Peaks (50-2000 Hz) ===")
    print(f"{'Freq (Hz)':>12}  {'Magnitude':>10}  {'Relative':>8}  {'Harmonic?'}")
    print("-" * 55)
    for f, m in peaks:
        rel = m / top_mag
        h = harmonic_of(f, EXPECTED_FREQ)
        label = f"~{h}x fundamental" if h else ""
        bar = "#" * int(rel * 30)
        print(f"{f:>12.1f}  {m:>10.1f}  {rel:>8.3f}  {bar} {label}")
    print()


def analyze_yin_detail(signal: np.ndarray, sr: int = SAMPLE_RATE):
    """Run YIN and also show the CMNDF at key lag points."""
    w = len(signal) // 2
    curve = cmndf(signal)

    # Show CMNDF values at expected fundamental and its harmonics
    print(f"=== CMNDF at key lag points (expected fundamental: {EXPECTED_FREQ} Hz) ===")
    print(
        f"{'Harmonic':>10}  {'Freq (Hz)':>10}  {'Lag (samples)':>14}  {'CMNDF value':>12}"
        f"  {'< ' + str(DEFAULT_THRESHOLD) + '?'}"
    )
    print("-" * 70)
    for h in [1, 2, 3, 4, 5]:
        freq_h = EXPECTED_FREQ * h
        lag = int(round(sr / freq_h))
        if 0 < lag < w:
            val = curve[lag]
            # Also find local min near this lag
            search_start = max(2, lag - 5)
            search_end = min(w, lag + 6)
            local_min_lag = search_start + np.argmin(curve[search_start:search_end])
            local_min_val = curve[local_min_lag]
            below = "YES" if val < DEFAULT_THRESHOLD else "no"
            note = "<-- fundamental" if h == 1 else f"<-- {h}x harmonic (lag = period/{h})"
            print(
                f"{'1/' + str(h) + 'x':>10}  {freq_h:>10.1f}  {lag:>14}  {val:>12.4f}  {below:>7}  {note}"
            )
            if local_min_lag != lag:
                print(
                    f"{'':>10}  {'':>10}  {local_min_lag:>14}  {local_min_val:>12.4f}         (nearby min)"
                )
    print()

    # Show where YIN actually picks its estimate
    tau = pick_tau(curve)
    if tau > 0:
        detected_freq = sr / tau
        print(f"YIN picks lag={tau} -> {detected_freq:.2f} Hz")
        ratio = detected_freq / EXPECTED_FREQ
        print(f"Ratio to expected: {ratio:.3f}x", end="")
        h = harmonic_of(detected_freq, EXPECTED_FREQ)
        if h is not None and h > 1:
            print(f"  ** Locked onto harmonic {h}x! **")
        elif h == 1:
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
            h = harmonic_of(freq, EXPECTED_FREQ)
            if h is not None and h > 1:
                flag = f"  ** {h}x harmonic **"
            elif h == 1:
                flag = "  (correct)"
            else:
                flag = ""
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

    # Use the loudest BUFFER_SIZE-sample window for detailed analysis
    starts = range(0, len(audio) - BUFFER_SIZE, BUFFER_SIZE // 4)
    best_start = max(starts, key=lambda s: rms(audio[s : s + BUFFER_SIZE]))
    best_chunk = audio[best_start : best_start + BUFFER_SIZE]
    print(
        f"Loudest chunk at sample {best_start} "
        f"(t={best_start / SAMPLE_RATE:.2f}s, RMS={rms(best_chunk):.4f})\n"
    )

    analyze_spectrum(best_chunk)
    analyze_yin_detail(best_chunk)
    run_yin_on_chunks(audio)


if __name__ == "__main__":
    main()
