"""Real-time waveform display using Unicode block elements."""

import numpy as np
from textual.widget import Widget

from clamtuna.widgets.render import GREEN, downsample, render_block_rows


class Waveform(Widget):
    """Displays audio waveform using Unicode block characters."""

    DEFAULT_CSS = """
    Waveform {
        height: 1fr;
        padding: 0 1;
        border-bottom: solid #2c313a;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._samples: np.ndarray = np.zeros(0)

    def update_samples(self, samples: np.ndarray) -> None:
        self._samples = samples
        self.refresh()

    def render(self) -> str:
        content_width = self.size.width - 2
        content_height = self.size.height
        if content_width <= 0 or content_height <= 0 or len(self._samples) == 0:
            return ""

        samples = downsample(self._samples, content_width)

        # Normalize to 0-1 range (from -1..1 audio)
        peak = np.max(np.abs(samples))
        if peak > 0:
            normalized = (samples / peak + 1.0) / 2.0
        else:
            normalized = np.full(len(samples), 0.5)

        rows = render_block_rows(normalized, content_height)
        return "\n".join(f"[{GREEN}]{row}[/]" for row in rows)
