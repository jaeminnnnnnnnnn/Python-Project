from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.app.state import room_store
from shared.errors import RoomNotFoundError


router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms[room_id].add(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        self.rooms[room_id].discard(websocket)
        if not self.rooms[room_id]:
            self.rooms.pop(room_id, None)

    async def broadcast(self, room_id: str, message: dict, exclude: WebSocket | None = None) -> None:
        for websocket in list(self.rooms.get(room_id, ())):
            if websocket is exclude:
                continue
            await websocket.send_json(message)


manager = ConnectionManager()


async def broadcast_room_state(room_id: str) -> None:
    room = room_store.get(room_id)
    await manager.broadcast(room_id, {"type": "room.state", "room": room.public().model_dump()})


async def disconnect_room_socket(room_id: str, websocket: WebSocket, player_id: str | None) -> None:
    manager.disconnect(room_id, websocket)
    if not player_id:
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


@router.websocket("/ws/rooms/{room_id}")
async def room_socket(websocket: WebSocket, room_id: str, player_id: str | None = None) -> None:
    await manager.connect(room_id, websocket)
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
