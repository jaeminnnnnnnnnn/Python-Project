from client.server_config import to_ws_url


def test_to_ws_url() -> None:
    assert to_ws_url("https://example.fly.dev") == "wss://example.fly.dev"
    assert to_ws_url("http://127.0.0.1:8000") == "ws://127.0.0.1:8000"

