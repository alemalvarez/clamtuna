"""Textual App — layout, audio→widget data flow."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer

from clamtuna.audio import AudioStream
from clamtuna.constants import BUFFER_SIZE, SILENCE_RMS, resolve_target
from clamtuna.dsp import compute_spectrum, rms
from clamtuna.pitch import yin
from clamtuna.widgets.gauge import Gauge
from clamtuna.widgets.note_display import NoteDisplay
from clamtuna.widgets.spectrum import Spectrum
from clamtuna.widgets.string_selector import StringSelector
from clamtuna.widgets.waveform import Waveform

# Widget update rates
PITCH_UPDATE_HZ = 20
WAVEFORM_UPDATE_HZ = 30
SPECTRUM_UPDATE_HZ = 15

# How long (in seconds) to hold the last valid note on screen
NOTE_HOLD_TIME = 1.5
MAX_SILENCE_FRAMES = int(NOTE_HOLD_TIME * PITCH_UPDATE_HZ)

NO_READING = ("--", 0.0, 0.0)


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
        self.target: tuple[str, float] | None = None
        self._last_valid: tuple[str, float, float] = NO_READING
        self._silence_frames = 0

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

        self._note_display = self.query_one(NoteDisplay)
        self._gauge = self.query_one(Gauge)
        self._waveform = self.query_one(Waveform)
        self._spectrum = self.query_one(Spectrum)

        self.set_interval(1 / PITCH_UPDATE_HZ, self._update_pitch)
        self.set_interval(1 / WAVEFORM_UPDATE_HZ, self._update_waveform)
        self.set_interval(1 / SPECTRUM_UPDATE_HZ, self._update_spectrum)

    def on_unmount(self) -> None:
        self.audio.stop()

    def on_string_selector_string_selected(self, event: StringSelector.StringSelected) -> None:
        if event.string_name is None or event.target_freq is None:
            self.target = None
        else:
            self.target = (event.string_name, event.target_freq)

    def action_toggle_auto(self) -> None:
        selector = self.query_one(StringSelector)
        if not selector.auto_mode:
            selector.select_auto()

    def _update_pitch(self) -> None:
        samples = self.audio.get_samples(BUFFER_SIZE)

        if rms(samples) < SILENCE_RMS or (freq := yin(samples)) <= 0:
            # Hold the last valid reading briefly, then clear
            self._silence_frames += 1
            held = self._last_valid if self._silence_frames < MAX_SILENCE_FRAMES else NO_READING
            self._show_reading(*held)
            return

        self._silence_frames = 0
        name, _, cents = resolve_target(freq, self.target)
        self._last_valid = (name, freq, cents)
        self._show_reading(name, freq, cents)

    def _show_reading(self, name: str, freq: float, cents: float) -> None:
        self._note_display.update_note(name, freq, cents)
        self._gauge.update_cents(cents)

    def _update_waveform(self) -> None:
        self._waveform.update_samples(self.audio.get_samples(BUFFER_SIZE))

    def _update_spectrum(self) -> None:
        freqs, mags = compute_spectrum(self.audio.get_samples(BUFFER_SIZE))
        self._spectrum.update_spectrum(freqs, mags)
