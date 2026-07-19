# clamtuna

A CLI guitar tuner with a chill, minimal terminal aesthetic.

```
┌─────────────────────────────────────────┐
│  [AUTO] [E2] [A2] [D3] [G3] [B3] [E4]  │
├──────────────┬──────────────────────────┤
│   Note: A2   │   ▁▂▃▅▆▇█▇▆▅▃▂▁        │
│  110.02 Hz   │                          │
│  +3.2 cents  │                          │
│              ├──────────────────────────┤
│ FLAT ──●──── │   ▁▃▇▃▁ ▁▂▁ ▁▁         │
│    SHARP     │   110  220 330  Hz       │
└──────────────┴──────────────────────────┘
```

Real-time pitch detection, tuning gauge, waveform, and FFT spectrum — all in your terminal.

## Install & Run

```bash
uv sync
uv run clamtuna
```

Requires Python 3.14+ and a microphone.

## How It Works

- **YIN pitch detection** — pure numpy, no native DSP libs needed
- **FFT spectrum** — log-spaced frequency bins with frequency axis labels
- **Textual TUI** — dark charcoal theme, Unicode block art, color-coded cents

## Controls

| Key | Action |
|-----|--------|
| `a` | Return to auto-detect mode |
| `q` | Quit |

Click any string button (`E2` `A2` `D3` `G3` `B3` `E4`) to lock to that target, or use `AUTO` to detect the nearest string automatically.

## Dev

```bash
uv run pytest          # tests
uv run ruff check .    # lint
uv run ruff format .   # format
```

## License

Apache 2.0
