from uuid import uuid4

from server.app.models import Room
from shared.errors import InvalidPasswordError, RoomFullError, RoomNotFoundError
from shared.schemas import Player


class RoomStore:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def list_rooms(self) -> list[Room]:
        return list(self.rooms.values())

    def create_room(self, title: str, password: str | None, player_name: str) -> tuple[Room, Player]:
        room = Room(title=title, password=password)
        player = self._new_player(player_name)
        room.players[player.id] = player
        room.touch(player.id)
        self.rooms[room.id] = room
        return room, player

    def join_room(self, room_id: str, player_name: str, password: str | None) -> tuple[Room, Player]:
        room = self.get(room_id)
        if room.password and room.password != password:
            raise InvalidPasswordError()
        if len(room.players) >= room.max_players:
            raise RoomFullError()
        player = self._new_player(player_name)
        room.players[player.id] = player
        room.touch(player.id)
        return room, player

    def set_ready(self, room_id: str, player_id: str, ready: bool) -> Room:
        room = self.get(room_id)
        if player_id not in room.players:
            if len(room.players) >= room.max_players:
                raise RoomNotFoundError()
            room.players[player_id] = Player(id=player_id, name="Player")
        room.touch(player_id)
        room.players[player_id].ready = ready
        if len(room.players) == room.max_players and all(player.ready for player in room.players.values()):
            if not room.started:
                room.start_match()
        return room

    def leave_room(self, room_id: str, player_id: str) -> Room | None:
        room = self.get(room_id)
        room.players.pop(player_id, None)
        room.last_seen.pop(player_id, None)
        room.started = False
        room.match_seed = None
        if not room.players:
            self.rooms.pop(room_id, None)
            return None
        return room

    def reset_match(self, room_id: str, player_id: str) -> Room:
        room = self.get(room_id)
        if player_id not in room.players:
            raise RoomNotFoundError()
        room.touch(player_id)
        room.started = False
        room.match_seed = None
        for player in room.players.values():
            player.ready = False
        return room

    def heartbeat(self, room_id: str, player_id: str) -> Room:
        room = self.get(room_id)
        if player_id not in room.players:
            raise RoomNotFoundError()
        room.touch(player_id)
        return room

    def get(self, room_id: str) -> Room:
        try:
            room = self.rooms[room_id]
        except KeyError as exc:
            raise RoomNotFoundError() from exc
        return room

    def cleanup_stale_players(self, now: float | None = None) -> list[str]:
        return []

    def cleanup_room(self, room: Room, now: float | None = None) -> bool:
        return False

    def _new_player(self, name: str) -> Player:
        return Player(id=uuid4().hex[:8], name=name)
