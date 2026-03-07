"""FFT spectrum bar chart with frequency labels."""

import numpy as np
from textual.widget import Widget

BLOCKS = " ▁▂▃▄▅▆▇█"


class Spectrum(Widget):
    """Displays FFT spectrum as a vertical bar chart."""

    DEFAULT_CSS = """
    Spectrum {
        height: 1fr;
        padding: 0 1;
    }
    """

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

        freqs = self._freqs
        mags = self._magnitudes

        # Resample to fit width
        n_bars = min(content_width, len(mags))
        if n_bars < len(mags):
            indices = np.linspace(0, len(mags) - 1, n_bars, dtype=int)
            mags = mags[indices]
            freqs = freqs[indices]

        # Build rows top-down
        rows = []
        for row in range(content_height):
            threshold = 1.0 - (row + 1) / content_height
            threshold_top = 1.0 - row / content_height
            line = []
            for mag in mags:
                if mag >= threshold_top:
                    line.append(BLOCKS[8])
                elif mag <= threshold:
                    line.append(" ")
                else:
                    frac = (mag - threshold) / (threshold_top - threshold)
                    idx = int(frac * 8)
                    idx = max(0, min(8, idx))
                    line.append(BLOCKS[idx])
            rows.append(f"[#5c8a7d]{''.join(line)}[/]")

        # Frequency label row
        label_line = list(" " * n_bars)
        label_targets = [100, 200, 500, 1000, 2000, 5000]
        for target in label_targets:
            if len(freqs) == 0:
                break
            idx = int(np.argmin(np.abs(freqs - target)))
            if 0 <= idx < n_bars:
                if target >= 1000:
                    label = f"{target // 1000}k"
                else:
                    label = str(target)
                start = max(0, idx - len(label) // 2)
                end = min(n_bars, start + len(label))
                for i, ch in enumerate(label):
                    pos = start + i
                    if pos < end:
                        label_line[pos] = ch

        rows.append(f"[dim]{''.join(label_line)}[/]")
        return "\n".join(rows)
