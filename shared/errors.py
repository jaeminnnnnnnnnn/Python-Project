class RoomError(Exception):
    pass


class RoomFullError(RoomError):
    pass


class RoomNotFoundError(RoomError):
    pass


class InvalidPasswordError(RoomError):
    pass

