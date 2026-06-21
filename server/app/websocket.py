from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.app.state import room_store


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

    async def broadcast(self, room_id: str, message: dict) -> None:
        for websocket in list(self.rooms.get(room_id, ())):
            await websocket.send_json(message)


manager = ConnectionManager()


async def broadcast_room_state(room_id: str) -> None:
    room = room_store.get(room_id)
    await manager.broadcast(room_id, {"type": "room.state", "room": room.public().model_dump()})


@router.websocket("/ws/rooms/{room_id}")
async def room_socket(websocket: WebSocket, room_id: str) -> None:
    await manager.connect(room_id, websocket)
    try:
        room = room_store.get(room_id)
        await websocket.send_json({"type": "room.state", "room": room.public().model_dump()})
        while True:
            message = await websocket.receive_json()
            await manager.broadcast(room_id, message)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
    except Exception:
        manager.disconnect(room_id, websocket)
        await websocket.close(code=1011)
