"""Note display widget — detected note name, Hz, cents."""

from textual.reactive import reactive
from textual.widget import Widget

from clamtuna.widgets.render import cents_status


class NoteDisplay(Widget):
    """Shows the currently detected note, frequency, and cents offset."""

    note_name: reactive[str] = reactive("--")
    frequency: reactive[float] = reactive(0.0)
    cents: reactive[float] = reactive(0.0)

    DEFAULT_CSS = """
    NoteDisplay {
        height: auto;
        min-height: 7;
        padding: 1 0;
    }
    """

    def render(self) -> str:
        if self.frequency <= 0:
            return "  [bold dim]--[/]\n\n  --- Hz\n  --- cents"

        color, status = cents_status(self.cents)
        symbol = f"  {status}" if status else ""
        sign = "+" if self.cents >= 0 else ""
        return (
            f"  [bold {color}]{self.note_name}[/]\n\n"
            f"  [{color}]{self.frequency:.1f} Hz[/]\n"
            f"  [{color}]{sign}{self.cents:.1f} cents[/]{symbol}"
        )

    def update_note(self, name: str, freq: float, cents: float) -> None:
        self.note_name = name
        self.frequency = freq
        self.cents = cents
