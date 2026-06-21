from enum import StrEnum


class EventType(StrEnum):
    ROOM_CREATE = "room.create"
    ROOM_LIST = "room.list"
    ROOM_JOIN = "room.join"
    ROOM_LEAVE = "room.leave"
    ROOM_READY = "room.ready"
    MATCH_START = "match.start"
    MATCH_INPUT = "match.input"
    MATCH_STATE = "match.state"
    MATCH_GARBAGE = "match.garbage"
    MATCH_RESULT = "match.result"
    ERROR = "error"

