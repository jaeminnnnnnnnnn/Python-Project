from dataclasses import dataclass
from typing import Any
from urllib import error, request
import json

from client.config import SERVER_URL


class ApiError(Exception):
    pass


@dataclass(frozen=True)
class ApiClient:
    base_url: str = SERVER_URL

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/")

    def list_rooms(self) -> list[dict[str, Any]]:
        return self._request("GET", "/rooms")

    def get_room(self, room_id: str) -> dict[str, Any]:
        return self._request("GET", f"/rooms/{room_id}")

    def create_room(self, title: str, player_name: str = "Player", password: str | None = None) -> dict[str, Any]:
        return self._request(
            "POST",
            "/rooms",
            {"title": title, "player_name": player_name, "password": password},
        )

    def join_room(self, room_id: str, player_name: str = "Player", password: str | None = None) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/rooms/{room_id}/join",
            {"player_name": player_name, "password": password},
        )

    def set_ready(self, room_id: str, player_id: str, ready: bool) -> dict[str, Any]:
        return self._request("POST", f"/rooms/{room_id}/ready", {"player_id": player_id, "ready": ready})

    def leave_room(self, room_id: str, player_id: str) -> dict[str, Any] | None:
        return self._request("POST", f"/rooms/{room_id}/leave", {"player_id": player_id})

    def reset_room(self, room_id: str, player_id: str) -> dict[str, Any]:
        return self._request("POST", f"/rooms/{room_id}/reset", {"player_id": player_id})

    def heartbeat(self, room_id: str, player_id: str) -> dict[str, Any]:
        return self._request("POST", f"/rooms/{room_id}/heartbeat", {"player_id": player_id})

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = self.base_url.rstrip("/") + path
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=body, method=method)
        req.add_header("Accept", "application/json")
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with request.urlopen(req, timeout=5.0) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ApiError(f"{exc.code}: {detail}") from exc
        except OSError as exc:
            raise ApiError("server is not reachable") from exc
        return json.loads(raw) if raw else None
