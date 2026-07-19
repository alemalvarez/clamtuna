# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLI-based guitar tuner with a retro terminal aesthetic. Built with Python 3.14 and managed with `uv`.

## Commands

```bash
# Setup
uv sync

# Run the tuner
uv run clamtuna

# Run tests
uv run pytest
uv run pytest tests/test_pitch.py::test_yin_standard_tuning -v  # single test

# Lint & format
uv run ruff check .
uv run ruff format .
```

## Architecture

Data flows microphone → DSP → widgets, with audio processing and UI rendering in separate modules:

- `audio.py` — `sounddevice` input stream (PortAudio) feeding a thread-safe ring buffer
- `pitch.py` — custom YIN pitch detector in pure vectorized NumPy, exposed as composable steps (`cmndf` → `pick_tau` → `yin`)
- `dsp.py` — FFT magnitude spectrum with log-spaced bins, peak finding, `rms`
- `constants.py` — audio config, tuning table, note math, and the note-resolution policy (`resolve_target`)
- `app.py` — Textual `App`; timers poll the ring buffer and push readings into the widgets
- `widgets/` — one module per widget (note display, cents gauge, waveform, spectrum, string selector); shared block-character rendering and color palette live in `widgets/render.py`
- **Package manager**: `uv` with `pyproject.toml` — no `requirements.txt` or `setup.py`
- **Python version**: 3.14 (specified in `pyproject.toml` via `requires-python`)

## Conventions

- Target the standard tuning frequencies: E2=82.41, A2=110.00, D3=146.83, G3=196.00, B3=246.94, E4=329.63 Hz
- Keep audio processing and UI rendering in separate modules
- Use `ruff` for linting and formatting
- Entry point defined as a script in `pyproject.toml` (`[project.scripts]`)
