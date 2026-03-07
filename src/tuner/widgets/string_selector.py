"""String selector widget — E2 A2 D3 G3 B3 E4 buttons + AUTO toggle."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

from tuner.constants import STANDARD_TUNING


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
        self.selected: str | None = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("AUTO", id="btn-auto", classes="-active")
            for name, _ in STANDARD_TUNING:
                yield Button(name, id=f"btn-{name}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        # Clear all active states
        for button in self.query(Button):
            button.remove_class("-active")
        event.button.add_class("-active")

        if btn_id == "btn-auto":
            self.auto_mode = True
            self.selected = None
            self.post_message(self.StringSelected(None, None))
        else:
            self.auto_mode = False
            for name, freq in STANDARD_TUNING:
                if btn_id == f"btn-{name}":
                    self.selected = name
                    self.post_message(self.StringSelected(name, freq))
                    break
