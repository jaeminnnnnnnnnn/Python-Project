from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any
import json
import time

from client.config import SERVER_WS_URL


@dataclass(frozen=True)
class WebSocketEndpoint:
    url: str


@dataclass
class RoomSocketClient:
    room_id: str
    base_url: str = SERVER_WS_URL
    messages: Queue[dict[str, Any]] = field(default_factory=Queue)
    errors: Queue[str] = field(default_factory=Queue)
    outgoing: Queue[dict[str, Any]] = field(default_factory=Queue)
    _stop: Event = field(default_factory=Event)
    _thread: Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(target=self._run, name=f"room-ws-{self.room_id}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def send(self, message: dict[str, Any]) -> None:
        self.outgoing.put(message)

    def drain(self) -> list[dict[str, Any]]:
        drained: list[dict[str, Any]] = []
        while True:
            try:
                drained.append(self.messages.get_nowait())
            except Empty:
                return drained

    def drain_errors(self) -> list[str]:
        drained: list[str] = []
        while True:
            try:
                drained.append(self.errors.get_nowait())
            except Empty:
                return drained

    def _run(self) -> None:
        try:
            from websockets.sync.client import connect
        except Exception as exc:
            self.errors.put(f"websocket package unavailable: {exc}")
            return

        url = f"{self.base_url.rstrip('/')}/ws/rooms/{self.room_id}"
        while not self._stop.is_set():
            try:
                with connect(url, open_timeout=2, close_timeout=1) as websocket:
                    while not self._stop.is_set():
                        while True:
                            try:
                                websocket.send(json.dumps(self.outgoing.get_nowait()))
                            except Empty:
                                break
                        raw = websocket.recv(timeout=0.2)
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8")
                        self.messages.put(json.loads(raw))
            except TimeoutError:
                continue
            except Exception as exc:
                if not self._stop.is_set():
                    self.errors.put(f"websocket disconnected: {exc}")
                    time.sleep(1.0)
