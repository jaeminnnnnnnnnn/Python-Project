from pydantic import BaseModel, Field


class Player(BaseModel):
    id: str
    name: str
    ready: bool = False


class RoomCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=40)
    password: str | None = Field(default=None, max_length=40)
    player_name: str = Field(default="Player", min_length=1, max_length=20)


class RoomJoinRequest(BaseModel):
    player_name: str = Field(default="Player", min_length=1, max_length=20)
    password: str | None = None


class RoomReadyRequest(BaseModel):
    player_id: str
    ready: bool


class RoomLeaveRequest(BaseModel):
    player_id: str


class RoomResetRequest(BaseModel):
    player_id: str


class RoomHeartbeatRequest(BaseModel):
    player_id: str


class RoomPublic(BaseModel):
    id: str
    title: str
    has_password: bool
    players: list[Player]
    max_players: int = 2
    started: bool = False
    match_seed: int | None = None


class RoomCreateResponse(BaseModel):
    room: RoomPublic
    player: Player


class RoomJoinResponse(BaseModel):
    room: RoomPublic
    player: Player
