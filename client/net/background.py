from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import Thread
from typing import Any, Callable


@dataclass
class BackgroundRequest:
    results: Queue[tuple[bool, Any]] = field(default_factory=Queue)
    running: bool = False

    def start(self, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        if self.running:
            return False
        self.running = True
        thread = Thread(target=self._run, args=(callback, args, kwargs), daemon=True)
        thread.start()
        return True

    def drain(self) -> tuple[bool, Any] | None:
        try:
            result = self.results.get_nowait()
        except Empty:
            return None
        self.running = False
        return result

    def _run(self, callback: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        try:
            self.results.put((True, callback(*args, **kwargs)))
        except Exception as exc:
            self.results.put((False, exc))
