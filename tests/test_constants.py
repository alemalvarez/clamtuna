"""Tests for note math and tuning helpers."""

import pytest

from clamtuna.constants import (
    freq_to_cents,
    freq_to_midi,
    freq_to_note_name,
    midi_to_freq,
    nearest_note_freq,
    nearest_string,
)


def test_a4_midi():
    assert freq_to_midi(440.0) == pytest.approx(69.0)


def test_midi_to_freq_a4():
    assert midi_to_freq(69) == pytest.approx(440.0)


def test_roundtrip_midi():
    for freq in [82.41, 110.0, 220.0, 440.0, 880.0]:
        midi = freq_to_midi(freq)
        assert midi_to_freq(midi) == pytest.approx(freq, rel=1e-4)


def test_freq_to_note_name():
    assert freq_to_note_name(440.0) == "A4"
    assert freq_to_note_name(261.63) == "C4"
    assert freq_to_note_name(82.41) == "E2"


def test_freq_to_cents_exact():
    assert freq_to_cents(440.0, 440.0) == pytest.approx(0.0)


def test_freq_to_cents_semitone():
    # One semitone up from A4 is A#4 = 466.16 Hz → 100 cents
    assert freq_to_cents(466.16, 440.0) == pytest.approx(100.0, abs=1.0)


def test_freq_to_cents_sharp_flat():
    assert freq_to_cents(442.0, 440.0) > 0  # sharp
    assert freq_to_cents(438.0, 440.0) < 0  # flat


def test_nearest_note_freq():
    # Slightly sharp A4 should snap to 440
    result = nearest_note_freq(442.0)
    assert result == pytest.approx(440.0, rel=1e-2)


def test_nearest_string():
    name, freq = nearest_string(112.0)  # close to A2=110
    assert name == "A2"
    assert freq == 110.0


def test_nearest_string_low():
    name, freq = nearest_string(85.0)  # close to E2=82.41
    assert name == "E2"


def test_zero_freq_handling():
    assert freq_to_midi(0) == 0.0
    assert freq_to_note_name(0) == "--"
    assert freq_to_cents(0, 440.0) == 0.0
    assert nearest_note_freq(0) == 0.0
