"""Tuning gauge widget — dot row from -50 to +50 cents."""

from textual.reactive import reactive
from textual.widget import Widget

from clamtuna.constants import IN_TUNE_CENTS
from clamtuna.widgets.render import DIM, GREEN, RED, cents_status


class Gauge(Widget):
    """Horizontal tuning gauge showing cents offset as a lit dot in a row."""

    cents: reactive[float] = reactive(0.0)

    DEFAULT_CSS = """
    Gauge {
        height: 5;
        padding: 1 0;
    }
    """

    NUM_DOTS = 9  # odd number so there's a center dot

    def render(self) -> str:
        n = self.NUM_DOTS
        center = n // 2
        content_width = self.size.width - 4  # account for padding

        # Map cents (-50 to +50) to dot index (0 to n-1)
        clamped = max(-50.0, min(50.0, self.cents))
        pos = int(round(center + (clamped / 50.0) * center))
        pos = max(0, min(n - 1, pos))

        active_color, _ = cents_status(self.cents)

        # Build the dot row, centered in the available width
        dots = []
        for i in range(n):
            if i == pos:
                dots.append(f"[{active_color}]●[/]")
            elif i == center:
                dots.append(f"[{GREEN}]○[/]")
            else:
                dots.append(f"[{DIM}]○[/]")

        dot_row = " ".join(dots)

        # Labels
        flat_label = f"[{RED}]♭[/]" if self.cents < -IN_TUNE_CENTS else f"[{DIM}]♭[/]"
        sharp_label = f"[{RED}]♯[/]" if self.cents > IN_TUNE_CENTS else f"[{DIM}]♯[/]"

        # Center everything
        # Dot row is n dots + (n-1) spaces = 2n-1 visible chars
        row_width = 2 * n - 1
        label_width = row_width + 4  # flat + space + dots + space + sharp
        pad = max(0, (content_width - label_width) // 2)
        indent = " " * pad

        # Marker line above/below pointing to center dot
        # Center dot is at char position: 2 * center (each dot + space = 2 chars)
        marker_offset = 2 * center
        marker_line = " " * marker_offset + f"[{GREEN}]▼[/]"
        bottom_line = " " * marker_offset + f"[{GREEN}]▲[/]"

        return (
            f"{indent}   {marker_line}\n"
            f"{indent} {flat_label} {dot_row} {sharp_label}\n"
            f"{indent}   {bottom_line}"
        )

    def update_cents(self, cents: float) -> None:
        self.cents = cents
