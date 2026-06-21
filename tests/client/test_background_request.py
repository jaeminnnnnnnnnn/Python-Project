from threading import Event

from client.net.background import BackgroundRequest


def test_background_request_returns_result() -> None:
    request = BackgroundRequest()

    assert request.start(lambda: {"status": "ok"})

    while True:
        result = request.drain()
        if result is not None:
            break

    assert result == (True, {"status": "ok"})
    assert not request.running


def test_background_request_rejects_duplicate_while_running() -> None:
    release = Event()
    request = BackgroundRequest()

    assert request.start(release.wait)
    assert not request.start(lambda: None)

    release.set()
    while request.drain() is None:
        pass

    assert not request.running
