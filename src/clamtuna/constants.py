"""Audio config, tuning frequencies, and note math."""

import numpy as np

# Audio config
SAMPLE_RATE = 44100
BUFFER_SIZE = 4096  # ~93ms, enough for E2 at 82 Hz
RING_BUFFER_SECONDS = 2
RING_BUFFER_SIZE = SAMPLE_RATE * RING_BUFFER_SECONDS

# Standard tuning (string number → note name, frequency)
STANDARD_TUNING: list[tuple[str, float]] = [
    ("E2", 82.41),
    ("A2", 110.00),
    ("D3", 146.83),
    ("G3", 196.00),
    ("B3", 246.94),
    ("E4", 329.63),
]

# All 12 note names for chromatic detection
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# A4 reference
A4_FREQ = 440.0
A4_MIDI = 69

# Tuning feedback thresholds (cents)
IN_TUNE_CENTS = 5
CLOSE_CENTS = 20
STRING_SNAP_CENTS = 50  # beyond this, tune against the nearest semitone instead

# Signal levels
SILENCE_RMS = 0.005

# Spectrum analysis range
SPECTRUM_MIN_FREQ = 50.0
SPECTRUM_MAX_FREQ = 5000.0


def freq_to_midi(freq: float) -> float:
    """Convert frequency to MIDI note number (fractional)."""
    if freq <= 0:
        return 0.0
    return 12.0 * np.log2(freq / A4_FREQ) + A4_MIDI


def midi_to_freq(midi: float) -> float:
    """Convert MIDI note number to frequency."""
    return A4_FREQ * 2.0 ** ((midi - A4_MIDI) / 12.0)


def freq_to_note_name(freq: float) -> str:
    """Convert frequency to nearest note name with octave (e.g. 'A4')."""
    if freq <= 0:
        return "--"
    midi = round(freq_to_midi(freq))
    note = NOTE_NAMES[midi % 12]
    octave = (midi // 12) - 1
    return f"{note}{octave}"


def freq_to_cents(freq: float, target_freq: float) -> float:
    """Get cents offset from target frequency. Positive = sharp, negative = flat."""
    if freq <= 0 or target_freq <= 0:
        return 0.0
    return 1200.0 * np.log2(freq / target_freq)


def nearest_note_freq(freq: float) -> float:
    """Return the frequency of the nearest semitone to the given frequency."""
    if freq <= 0:
        return 0.0
    midi = round(freq_to_midi(freq))
    return midi_to_freq(midi)


def nearest_string(freq: float) -> tuple[str, float]:
    """Find the nearest standard tuning string to a frequency."""
    if freq <= 0:
        return STANDARD_TUNING[0]
    return min(STANDARD_TUNING, key=lambda s: abs(freq_to_cents(freq, s[1])))


def resolve_target(freq: float, target: tuple[str, float] | None) -> tuple[str, float, float]:
    """Resolve a detected frequency to (note name, target freq, cents offset).

    With a manual target, tune against it. Otherwise tune against the nearest
    string, falling back to the nearest semitone when the note is more than
    STRING_SNAP_CENTS away from every string.
    """
    if target is not None:
        name, target_freq = target
    else:
        name, target_freq = nearest_string(freq)
        if abs(freq_to_cents(freq, target_freq)) > STRING_SNAP_CENTS:
            name, target_freq = freq_to_note_name(freq), nearest_note_freq(freq)
    return name, target_freq, freq_to_cents(freq, target_freq)
