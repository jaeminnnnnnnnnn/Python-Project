from pathlib import Path
import sys


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1]


def asset_path(*parts: str) -> Path:
    return app_root().joinpath("client", "assets", *parts)

