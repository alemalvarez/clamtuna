"""Textual App — layout, audio→widget data flow."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer

from clamtuna.audio import AudioStream
from clamtuna.constants import (
    BUFFER_SIZE,
    freq_to_cents,
    freq_to_note_name,
    nearest_note_freq,
    nearest_string,
)
from clamtuna.dsp import compute_spectrum
from clamtuna.pitch import yin
from clamtuna.widgets.gauge import Gauge
from clamtuna.widgets.note_display import NoteDisplay
from clamtuna.widgets.spectrum import Spectrum
from clamtuna.widgets.string_selector import StringSelector
from clamtuna.widgets.waveform import Waveform

import numpy as np


class TunerApp(App):
    """CLI Guitar Tuner."""

    CSS_PATH = "theme.tcss"
    TITLE = "clamtuna"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "toggle_auto", "Auto-detect"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.audio = AudioStream()
        self.target_freq: float | None = None
        self.target_name: str | None = None

    def compose(self) -> ComposeResult:
        yield StringSelector()
        with Horizontal(id="main-panel"):
            with Vertical(id="left-panel"):
                yield NoteDisplay(id="note-display")
                yield Gauge(id="gauge")
            with Vertical(id="right-panel"):
                yield Waveform(id="waveform")
                yield Spectrum(id="spectrum")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.audio.start()
        except Exception as e:
            self.notify(f"Mic error: {e}", severity="error", timeout=5)
            return

        self.set_interval(1 / 20, self._update_pitch)
        self.set_interval(1 / 30, self._update_waveform)
        self.set_interval(1 / 15, self._update_spectrum)

    def on_unmount(self) -> None:
        self.audio.stop()

    def on_string_selector_string_selected(self, event: StringSelector.StringSelected) -> None:
        self.target_name = event.string_name
        self.target_freq = event.target_freq

    def action_toggle_auto(self) -> None:
        selector = self.query_one(StringSelector)
        if not selector.auto_mode:
            # Simulate clicking AUTO
            auto_btn = selector.query_one("#btn-auto")
            auto_btn.press()

    def _update_pitch(self) -> None:
        samples = self.audio.get_samples(BUFFER_SIZE)
        rms = np.sqrt(np.mean(samples**2))
        if rms < 0.005:
            self.query_one(NoteDisplay).update_note("--", 0.0, 0.0)
            self.query_one(Gauge).update_cents(0.0)
            return

        freq = yin(samples)
        if freq <= 0:
            self.query_one(NoteDisplay).update_note("--", 0.0, 0.0)
            self.query_one(Gauge).update_cents(0.0)
            return

        if self.target_freq is not None:
            target = self.target_freq
            name = self.target_name or freq_to_note_name(freq)
        else:
            name, target = nearest_string(freq)
            # If too far from any string, use nearest semitone
            if abs(freq_to_cents(freq, target)) > 50:
                target = nearest_note_freq(freq)
                name = freq_to_note_name(freq)

        cents = freq_to_cents(freq, target)
        self.query_one(NoteDisplay).update_note(name, freq, cents)
        self.query_one(Gauge).update_cents(cents)

    def _update_waveform(self) -> None:
        samples = self.audio.get_samples(BUFFER_SIZE)
        self.query_one(Waveform).update_samples(samples)

    def _update_spectrum(self) -> None:
        samples = self.audio.get_samples(BUFFER_SIZE)
        freqs, mags = compute_spectrum(samples)
        self.query_one(Spectrum).update_spectrum(freqs, mags)
