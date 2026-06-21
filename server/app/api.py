from fastapi import APIRouter, BackgroundTasks, HTTPException

from server.app.state import room_store
from server.app.websocket import broadcast_room_state
from shared.errors import InvalidPasswordError, RoomFullError, RoomNotFoundError
from shared.schemas import (
    RoomCreateRequest,
    RoomHeartbeatRequest,
    RoomCreateResponse,
    RoomJoinRequest,
    RoomJoinResponse,
    RoomLeaveRequest,
    RoomPublic,
    RoomReadyRequest,
    RoomResetRequest,
)


router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomPublic])
def list_rooms() -> list[RoomPublic]:
    return [room.public() for room in room_store.list_rooms()]


@router.get("/{room_id}", response_model=RoomPublic)
def get_room(room_id: str) -> RoomPublic:
    try:
        return room_store.get(room_id).public()
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail="room not found") from exc


@router.post("", response_model=RoomCreateResponse)
def create_room(payload: RoomCreateRequest, background_tasks: BackgroundTasks) -> RoomCreateResponse:
    room, player = room_store.create_room(payload.title, payload.password, payload.player_name)
    background_tasks.add_task(broadcast_room_state, room.id)
    return RoomCreateResponse(room=room.public(), player=player)


@router.post("/{room_id}/join", response_model=RoomJoinResponse)
def join_room(room_id: str, payload: RoomJoinRequest, background_tasks: BackgroundTasks) -> RoomJoinResponse:
    try:
        room, player = room_store.join_room(room_id, payload.player_name, payload.password)
        background_tasks.add_task(broadcast_room_state, room.id)
        return RoomJoinResponse(room=room.public(), player=player)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail="room not found") from exc
    except InvalidPasswordError as exc:
        raise HTTPException(status_code=403, detail="invalid password") from exc
    except RoomFullError as exc:
        raise HTTPException(status_code=409, detail="room is full") from exc


@router.post("/{room_id}/ready", response_model=RoomPublic)
def ready_room(room_id: str, payload: RoomReadyRequest, background_tasks: BackgroundTasks) -> RoomPublic:
    try:
        room = room_store.set_ready(room_id, payload.player_id, payload.ready)
        background_tasks.add_task(broadcast_room_state, room.id)
        return room.public()
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail="room or player not found") from exc


@router.post("/{room_id}/leave", response_model=RoomPublic | None)
def leave_room(room_id: str, payload: RoomLeaveRequest, background_tasks: BackgroundTasks) -> RoomPublic | None:
    try:
        room = room_store.leave_room(room_id, payload.player_id)
        if room:
            background_tasks.add_task(broadcast_room_state, room.id)
        return room.public() if room else None
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail="room not found") from exc


@router.post("/{room_id}/reset", response_model=RoomPublic)
def reset_room(room_id: str, payload: RoomResetRequest, background_tasks: BackgroundTasks) -> RoomPublic:
    try:
        room = room_store.reset_match(room_id, payload.player_id)
        background_tasks.add_task(broadcast_room_state, room.id)
        return room.public()
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail="room or player not found") from exc


@router.post("/{room_id}/heartbeat", response_model=RoomPublic)
def heartbeat_room(room_id: str, payload: RoomHeartbeatRequest) -> RoomPublic:
    try:
        return room_store.heartbeat(room_id, payload.player_id).public()
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail="room or player not found") from exc
