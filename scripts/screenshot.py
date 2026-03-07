"""Take an SVG screenshot of the tuner app after a brief delay."""

import sys
sys.path.insert(0, "src")

from clamtuna.app import TunerApp

app = TunerApp()

async def take_screenshot():
    await app.run_async()

# Use Textual's built-in screenshot on press of a key,
# or we can just export directly.
# Simpler: use textual's --screenshot flag via CLI

if __name__ == "__main__":
    app.run()
