"""Tuning gauge widget — horizontal needle from -50 to +50 cents."""

from textual.widget import Widget
from textual.reactive import reactive


class Gauge(Widget):
    """Horizontal tuning gauge showing cents offset as a needle position."""

    cents: reactive[float] = reactive(0.0)

    DEFAULT_CSS = """
    Gauge {
        height: 5;
        padding: 1 0;
    }
    """

    GAUGE_WIDTH = 41  # odd number for center alignment

    def render(self) -> str:
        w = self.GAUGE_WIDTH
        center = w // 2

        # Map cents (-50 to +50) to position (0 to w-1)
        clamped = max(-50.0, min(50.0, self.cents))
        pos = int(center + (clamped / 50.0) * center)
        pos = max(0, min(w - 1, pos))

        abs_cents = abs(self.cents)
        if abs_cents < 5:
            color = "#5c8a7d"
        elif abs_cents < 20:
            color = "#c9a94e"
        else:
            color = "#c45c5c"

        # Build gauge bar
        bar = list("─" * w)
        bar[center] = "│"
        bar[0] = "╶"
        bar[-1] = "╴"

        # Place needle
        needle_line = list(" " * w)
        needle_line[pos] = "●"

        gauge_str = "".join(bar)
        needle_str = "".join(needle_line)

        flat_label = "FLAT" if self.cents < -5 else "    "
        sharp_label = "SHARP" if self.cents > 5 else "     "

        return (
            f"  [{color}]{needle_str}[/]\n"
            f"  [dim]{gauge_str}[/]\n"
            f"  [dim]{flat_label}{'':^{w - 10}}{sharp_label}[/]"
        )

    def update_cents(self, cents: float) -> None:
        self.cents = cents

    def watch_cents(self) -> None:
        self.refresh()
