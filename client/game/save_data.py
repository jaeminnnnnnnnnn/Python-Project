import json
from pathlib import Path

from client.game.settings import Settings


SAVE_PATH = Path("settings.json")


def load_settings() -> Settings:
    if not SAVE_PATH.exists():
        return Settings()
    data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
    settings = Settings()
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    settings.key_bindings = {**Settings().key_bindings, **settings.key_bindings}
    return settings


def save_settings(settings: Settings) -> None:
    SAVE_PATH.write_text(json.dumps(settings.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
