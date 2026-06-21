import pygame

from client.constants import BLACK, CYAN, GRAY, WHITE
from client.net.api import ApiClient, ApiError
from client.net.websocket import RoomSocketClient
from client.player_labels import player_label
from client.scenes.base import Scene
from client.ui.surface import draw_header, draw_panel, draw_status_bar


HEARTBEAT_INTERVAL = 5.0


class OnlineRoomScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.api = ApiClient()
        self.status = "R 준비   Esc 나가기"
        self.poll_elapsed = 0.0
        self.heartbeat_elapsed = 0.0
        self.socket: RoomSocketClient | None = None
        self.websocket_failed = False

    def on_enter(self) -> None:
        self.poll_elapsed = 0.0
        self.heartbeat_elapsed = 0.0
        self.websocket_failed = False
        self.refresh()
        self.open_socket()

    def on_exit(self) -> None:
        self.socket = None

    def open_socket(self) -> None:
        room = self.app.online_room
        if not room:
            return
        if self.app.online_socket and self.app.online_socket.room_id == room["id"]:
            self.socket = self.app.online_socket
            return
        self.app.close_online_socket()
        self.app.online_socket = RoomSocketClient(room["id"])
        self.app.online_socket.start()
        self.socket = self.app.online_socket

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == self.app.key("back"):
                self.leave_room()
            elif event.key == self.app.key("retry_ready"):
                self.toggle_ready()

    def update(self, dt: float) -> None:
        self.apply_socket_messages()
        self.heartbeat_elapsed += dt
        if self.heartbeat_elapsed >= HEARTBEAT_INTERVAL:
            self.heartbeat_elapsed = 0.0
            self.send_heartbeat()
        self.poll_elapsed += dt
        if self.websocket_failed and self.poll_elapsed >= 1.0:
            self.poll_elapsed = 0.0
            self.refresh()
        room = self.app.online_room
        if room and room.get("started"):
            self.app.change_scene("online_game")

    def send_heartbeat(self) -> None:
        room = self.app.online_room
        player = self.app.online_player
        if not room or not player:
            return
        try:
            self.app.online_room = self.api.heartbeat(room["id"], player["id"])
        except ApiError:
            self.status = "로딩 중"

    def apply_socket_messages(self) -> None:
        if not self.socket:
            return
        for error in self.socket.drain_errors():
            self.websocket_failed = True
            self.status = "로딩 중"
        unhandled = []
        for message in self.socket.drain():
            if message.get("type") == "room.state":
                self.app.online_room = message["room"]
                self.websocket_failed = False
                self.status = "R 준비   Esc 나가기"
            else:
                unhandled.append(message)
        self.socket.put_back(unhandled)

    def refresh(self) -> None:
        room = self.app.online_room
        if not room:
            self.app.change_scene("online_lobby")
            return
        try:
            self.app.online_room = self.api.get_room(room["id"])
            self.status = "R 준비   Esc 나가기"
        except ApiError:
            self.status = "로딩 중"

    def toggle_ready(self) -> None:
        room = self.app.online_room
        player = self.app.online_player
        if not room or not player:
            return
        current = self.current_player_ready()
        try:
            self.app.online_room = self.api.set_ready(room["id"], player["id"], not current)
            self.status = "R 준비   Esc 나가기"
        except ApiError:
            self.status = "준비 실패"

    def leave_room(self) -> None:
        room = self.app.online_room
        player = self.app.online_player
        if room and player:
            try:
                self.api.leave_room(room["id"], player["id"])
            except ApiError:
                pass
        self.app.online_room = None
        self.app.online_player = None
        self.app.close_online_socket()
        self.app.change_scene("online_lobby")

    def current_player_ready(self) -> bool:
        room = self.app.online_room
        player = self.app.online_player
        if not room or not player:
            return False
        for room_player in room["players"]:
            if room_player["id"] == player["id"]:
                return bool(room_player["ready"])
        return False

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        room = self.app.online_room
        player = self.app.online_player
        if not room or not player:
            self.draw_text(screen, "No room selected", (80, 70))
            return
        draw_header(screen, self.font, room["title"])

        panel = pygame.Rect(90, 155, 780, 335)
        draw_panel(screen, panel)
        for index in range(room["max_players"]):
            room_player = room["players"][index] if index < len(room["players"]) else None
            row = pygame.Rect(120, 190 + index * 108, 720, 78)
            is_me = bool(room_player and room_player["id"] == player["id"])
            draw_panel(screen, row, border_color=CYAN if is_me else GRAY, fill_color=(32, 42, 48) if is_me else (28, 32, 40))
            if not room_player:
                screen.blit(self.font.render(f"P{index + 1}", True, GRAY), (row.x + 28, row.y + 20))
                continue
            is_me = room_player["id"] == player["id"]
            name = player_label(room, room_player["id"]) + (" (You)" if is_me else "")
            ready = "준비" if room_player["ready"] else "대기"
            color = CYAN if is_me else WHITE
            screen.blit(self.font.render(name, True, color), (row.x + 28, row.y + 20))
            ready_color = CYAN if room_player["ready"] else GRAY
            ready_surface = self.font.render(ready, True, ready_color)
            screen.blit(ready_surface, ready_surface.get_rect(midright=(row.right - 28, row.centery)))
        slots_left = room["max_players"] - len(room["players"])
        if slots_left:
            self.draw_text(screen, "대기 중", (120, 525), small=True)
        if room["started"]:
            self.draw_text(screen, "시작 중", (120, 560), small=True)
        draw_status_bar(screen, self.small_font, self.status)
