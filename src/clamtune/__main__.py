"""Entry point for the clamtune CLI."""

from clamtune.app import TunerApp


def main() -> None:
    app = TunerApp()
    app.run()


if __name__ == "__main__":
    main()
