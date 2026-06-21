import time
from uuid import uuid4

from server.app.models import Room
from shared.errors import InvalidPasswordError, RoomFullError, RoomNotFoundError
from shared.schemas import Player


class RoomStore:
    stale_timeout_seconds = 45.0

    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def list_rooms(self) -> list[Room]:
        self.cleanup_stale_players()
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
        self.cleanup_room(room)
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
        self.cleanup_room(room)
        if player_id not in room.players:
            raise RoomNotFoundError()
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
        self.cleanup_room(room)
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
        self.cleanup_room(room)
        if player_id not in room.players:
            raise RoomNotFoundError()
        room.touch(player_id)
        return room

    def get(self, room_id: str) -> Room:
        try:
            room = self.rooms[room_id]
        except KeyError as exc:
            raise RoomNotFoundError() from exc
        self.cleanup_room(room)
        if room_id not in self.rooms:
            raise RoomNotFoundError()
        return room

    def cleanup_stale_players(self, now: float | None = None) -> list[str]:
        removed_rooms: list[str] = []
        for room in list(self.rooms.values()):
            if self.cleanup_room(room, now):
                removed_rooms.append(room.id)
        return removed_rooms

    def cleanup_room(self, room: Room, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        stale_ids = [
            player_id
            for player_id in room.players
            if now - room.last_seen.get(player_id, now) > self.stale_timeout_seconds
        ]
        for player_id in stale_ids:
            room.players.pop(player_id, None)
            room.last_seen.pop(player_id, None)
        if stale_ids:
            room.started = False
            room.match_seed = None
            for player in room.players.values():
                player.ready = False
        if not room.players and room.id in self.rooms:
            self.rooms.pop(room.id, None)
            return True
        return False

    def _new_player(self, name: str) -> Player:
        return Player(id=uuid4().hex[:8], name=name)
