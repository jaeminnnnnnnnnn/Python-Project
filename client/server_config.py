from __future__ import annotations

import json
import os
from pathlib import Path

from client.paths import asset_path


DEFAULT_SERVER_URL = "http://127.0.0.1:8000"


def load_server_urls() -> tuple[str, str]:
    server_url = os.getenv("CLIENT_SERVER_URL")
    server_ws_url = os.getenv("CLIENT_SERVER_WS_URL")
    if server_url:
        return server_url, server_ws_url or to_ws_url(server_url)

    config = read_bundled_config()
    server_url = config.get("server_url") or DEFAULT_SERVER_URL
    server_ws_url = config.get("server_ws_url") or to_ws_url(server_url)
    return server_url, server_ws_url


def read_bundled_config() -> dict[str, str]:
    path = asset_path("config", "server.json")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {key: value for key, value in data.items() if isinstance(value, str)}


def to_ws_url(server_url: str) -> str:
    return server_url.replace("https://", "wss://").replace("http://", "ws://")

