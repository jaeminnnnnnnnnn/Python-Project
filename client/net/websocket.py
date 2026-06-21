from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any, Iterable
import json
import time

from client.config import SERVER_WS_URL


VISUAL_SYNC_TYPES = {"match.input", "match.state"}


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
        if message.get("type") in VISUAL_SYNC_TYPES:
            self._drop_queued_visual_sync_messages()
        self.outgoing.put(message)

    def _drop_queued_visual_sync_messages(self) -> None:
        retained: list[dict[str, Any]] = []
        while True:
            try:
                queued = self.outgoing.get_nowait()
            except Empty:
                break
            if queued.get("type") not in VISUAL_SYNC_TYPES:
                retained.append(queued)
        for queued in retained:
            self.outgoing.put(queued)

    def drain(self) -> list[dict[str, Any]]:
        drained: list[dict[str, Any]] = []
        while True:
            try:
                drained.append(self.messages.get_nowait())
            except Empty:
                return drained

    def put_back(self, messages: Iterable[dict[str, Any]]) -> None:
        pending = list(messages)
        if not pending:
            return
        while True:
            try:
                pending.append(self.messages.get_nowait())
            except Empty:
                break
        for message in pending:
            self.messages.put(message)

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
                with connect(url, open_timeout=10, close_timeout=1, ping_interval=20, ping_timeout=20) as websocket:
                    while not self._stop.is_set():
                        while True:
                            try:
                                websocket.send(json.dumps(self.outgoing.get_nowait()))
                            except Empty:
                                break
                        try:
                            raw = websocket.recv(timeout=0.01)
                        except TimeoutError:
                            continue
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8")
                        self.messages.put(json.loads(raw))
            except Exception as exc:
                if not self._stop.is_set():
                    self.errors.put(f"websocket disconnected: {exc}")
                    time.sleep(1.0)
