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
uv run pytest tests/test_audio.py::test_pitch_detection -v  # single test

# Lint & format
uv run ruff check .
uv run ruff format .
```

## Architecture

- **Audio capture**: Use `sounddevice` for real-time microphone input via PortAudio
- **Pitch detection**: Use `aubio` or a custom YIN/autocorrelation algorithm on NumPy arrays
- **Terminal UI**: Use `rich` or `textual` for the retro-styled TUI (ASCII art, color gauges, etc.)
- **Package manager**: `uv` with `pyproject.toml` — no `requirements.txt` or `setup.py`
- **Python version**: 3.14 (specified in `pyproject.toml` via `requires-python`)

## Conventions

- Target the standard tuning frequencies: E2=82.41, A2=110.00, D3=146.83, G3=196.00, B3=246.94, E4=329.63 Hz
- Keep audio processing and UI rendering in separate modules
- Use `ruff` for linting and formatting
- Entry point defined as a script in `pyproject.toml` (`[project.scripts]`)
