"""Real-time waveform display using Unicode block elements."""

import numpy as np
from textual.widget import Widget

BLOCKS = " ▁▂▃▄▅▆▇█"


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

        samples = self._samples
        # Downsample to fit width
        n = len(samples)
        if n > content_width:
            indices = np.linspace(0, n - 1, content_width, dtype=int)
            samples = samples[indices]

        # Normalize to 0-1 range (from -1..1 audio)
        peak = np.max(np.abs(samples))
        if peak > 0:
            normalized = (samples / peak + 1.0) / 2.0
        else:
            normalized = np.full(len(samples), 0.5)

        # Map to block characters across available height
        # Each row represents a vertical slice
        rows = []
        for row in range(content_height):
            # Row 0 = top, row content_height-1 = bottom
            row_bottom = 1.0 - (row + 1) / content_height
            row_top = 1.0 - row / content_height
            line = []
            for val in normalized:
                if val >= row_top:
                    line.append(BLOCKS[8])  # full block
                elif val <= row_bottom:
                    line.append(" ")
                else:
                    # Partial block
                    frac = (val - row_bottom) / (row_top - row_bottom)
                    idx = int(frac * 8)
                    idx = max(0, min(8, idx))
                    line.append(BLOCKS[idx])
            rows.append(f"[#5c8a7d]{''.join(line)}[/]")

        return "\n".join(rows)
