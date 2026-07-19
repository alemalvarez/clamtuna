"""String selector widget — E2 A2 D3 G3 B3 E4 buttons + AUTO toggle."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

from clamtuna.constants import STANDARD_TUNING


class StringSelector(Widget):
    """Row of string buttons with an AUTO toggle."""

    class StringSelected(Message):
        """Posted when a string is selected."""

        def __init__(self, name: str | None, freq: float | None) -> None:
            super().__init__()
            self.string_name = name
            self.target_freq = freq

    DEFAULT_CSS = """
    StringSelector {
        height: 3;
        layout: horizontal;
        align: center middle;
        padding: 0 1;
        background: #21242b;
        border-bottom: solid #2c313a;
    }
    StringSelector Button {
        min-width: 6;
        margin: 0 1;
        background: #2c313a;
        color: #8b919d;
        border: none;
    }
    StringSelector Button:hover {
        background: #3a3f4b;
        color: #c8ccd4;
    }
    StringSelector Button.-active {
        background: #5c8a7d;
        color: #1a1d23;
        text-style: bold;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.auto_mode = True

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("AUTO", id="btn-auto", classes="-active")
            for name, _ in STANDARD_TUNING:
                yield Button(name, id=f"btn-{name}")

    def select_auto(self) -> None:
        """Switch to auto-detect mode, as if the AUTO button was pressed."""
        self.query_one("#btn-auto", Button).press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Clear all active states
        for button in self.query(Button):
            button.remove_class("-active")
        event.button.add_class("-active")

        if event.button.id == "btn-auto":
            self.auto_mode = True
            self.post_message(self.StringSelected(None, None))
        else:
            name = event.button.id.removeprefix("btn-")
            self.auto_mode = False
            self.post_message(self.StringSelected(name, dict(STANDARD_TUNING)[name]))
