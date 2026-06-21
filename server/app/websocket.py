from collections import defaultdict
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.app.state import room_store
from shared.errors import RoomNotFoundError


router = APIRouter(tags=["websocket"])
DISCONNECT_GRACE_SECONDS = 3.0


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self.socket_players: dict[WebSocket, tuple[str, str | None]] = {}
        self.player_counts: dict[tuple[str, str], int] = defaultdict(int)

    async def connect(self, room_id: str, websocket: WebSocket, player_id: str | None = None) -> None:
        await websocket.accept()
        self.rooms[room_id].add(websocket)
        self.socket_players[websocket] = (room_id, player_id)
        if player_id:
            self.player_counts[(room_id, player_id)] += 1

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        self.rooms[room_id].discard(websocket)
        if not self.rooms[room_id]:
            self.rooms.pop(room_id, None)
        tracked_room_id, player_id = self.socket_players.pop(websocket, (room_id, None))
        if player_id:
            key = (tracked_room_id, player_id)
            self.player_counts[key] -= 1
            if self.player_counts[key] <= 0:
                self.player_counts.pop(key, None)

    def is_player_connected(self, room_id: str, player_id: str) -> bool:
        return self.player_counts.get((room_id, player_id), 0) > 0

    async def broadcast(self, room_id: str, message: dict, exclude: WebSocket | None = None) -> None:
        for websocket in list(self.rooms.get(room_id, ())):
            if websocket is exclude:
                continue
            await websocket.send_json(message)


manager = ConnectionManager()


async def broadcast_room_state(room_id: str) -> None:
    room = room_store.get(room_id)
    await manager.broadcast(room_id, {"type": "room.state", "room": room.public().model_dump()})


async def remove_disconnected_player_after_grace(room_id: str, player_id: str) -> None:
    await asyncio.sleep(DISCONNECT_GRACE_SECONDS)
    if manager.is_player_connected(room_id, player_id):
        return
    try:
        existing = room_store.get(room_id)
        if not existing.started:
            return
        room = room_store.leave_room(room_id, player_id)
    except RoomNotFoundError:
        return
    if room:
        await manager.broadcast(room_id, {"type": "room.state", "room": room.public().model_dump()})


async def disconnect_room_socket(room_id: str, websocket: WebSocket, player_id: str | None) -> None:
    manager.disconnect(room_id, websocket)
    if not player_id:
        return
    try:
        existing = room_store.get(room_id)
        if not existing.started:
            return
    except RoomNotFoundError:
        return
    asyncio.create_task(remove_disconnected_player_after_grace(room_id, player_id))


@router.websocket("/ws/rooms/{room_id}")
async def room_socket(websocket: WebSocket, room_id: str, player_id: str | None = None) -> None:
    await manager.connect(room_id, websocket, player_id)
    try:
        room = room_store.get(room_id)
        await websocket.send_json({"type": "room.state", "room": room.public().model_dump()})
        while True:
            message = await websocket.receive_json()
            exclude = websocket if str(message.get("type", "")).startswith("match.") else None
            await manager.broadcast(room_id, message, exclude=exclude)
    except WebSocketDisconnect:
        await disconnect_room_socket(room_id, websocket, player_id)
    except Exception:
        await disconnect_room_socket(room_id, websocket, player_id)
        await websocket.close(code=1011)
