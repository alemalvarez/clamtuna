"""Entry point for the tuner CLI."""

from tuner.app import TunerApp


def main() -> None:
    app = TunerApp()
    app.run()


if __name__ == "__main__":
    main()
