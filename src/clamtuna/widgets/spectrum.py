"""FFT spectrum bar chart with frequency labels."""

import numpy as np
from textual.widget import Widget

from clamtuna.widgets.render import GREEN, downsample, render_block_rows


class Spectrum(Widget):
    """Displays FFT spectrum as a vertical bar chart."""

    DEFAULT_CSS = """
    Spectrum {
        height: 1fr;
        padding: 0 1;
    }
    """

    LABEL_TARGETS = [100, 200, 500, 1000, 2000, 5000]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._freqs: np.ndarray = np.zeros(0)
        self._magnitudes: np.ndarray = np.zeros(0)

    def update_spectrum(self, freqs: np.ndarray, magnitudes: np.ndarray) -> None:
        self._freqs = freqs
        self._magnitudes = magnitudes
        self.refresh()

    def render(self) -> str:
        content_width = self.size.width - 2
        content_height = self.size.height - 1  # leave room for freq labels
        if content_width <= 0 or content_height <= 0 or len(self._magnitudes) == 0:
            return ""

        n_bars = min(content_width, len(self._magnitudes))
        mags = downsample(self._magnitudes, n_bars)
        freqs = downsample(self._freqs, n_bars)

        rows = [f"[{GREEN}]{row}[/]" for row in render_block_rows(mags, content_height)]
        rows.append(f"[dim]{self._label_row(freqs, n_bars)}[/]")
        return "\n".join(rows)

    def _label_row(self, freqs: np.ndarray, n_bars: int) -> str:
        """Frequency labels placed under the bars closest to each target."""
        label_line = list(" " * n_bars)
        for target in self.LABEL_TARGETS:
            if len(freqs) == 0:
                break
            idx = int(np.argmin(np.abs(freqs - target)))
            if 0 <= idx < n_bars:
                label = f"{target // 1000}k" if target >= 1000 else str(target)
                start = max(0, idx - len(label) // 2)
                end = min(n_bars, start + len(label))
                label_line[start:end] = label[: end - start]
        return "".join(label_line)
