"""Entry point for the clamtuna CLI."""

from clamtuna.app import TunerApp


def main() -> None:
    app = TunerApp()
    app.run()


if __name__ == "__main__":
    main()
