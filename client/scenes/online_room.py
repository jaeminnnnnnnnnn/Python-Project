import pygame

from client.constants import BLACK, CYAN, GRAY, WHITE
from client.net.api import ApiClient, ApiError
from client.net.background import BackgroundRequest
from client.net.websocket import RoomSocketClient
from client.player_labels import player_label
from client.scenes.base import Scene
from client.ui.surface import draw_header, draw_panel, draw_status_bar


HEARTBEAT_INTERVAL = 5.0


class OnlineRoomScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.api = ApiClient()
        self.status = "Click Ready   Esc Leave"
        self.poll_elapsed = 0.0
        self.heartbeat_elapsed = 0.0
        self.socket: RoomSocketClient | None = None
        self.websocket_failed = False
        self.heartbeat_request = BackgroundRequest()

    def on_enter(self) -> None:
        self.poll_elapsed = 0.0
        self.heartbeat_elapsed = 0.0
        self.websocket_failed = False
        self.heartbeat_request = BackgroundRequest()
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
        player = self.app.online_player
        self.app.online_socket = RoomSocketClient(room["id"], player_id=player["id"] if player else None)
        self.app.online_socket.start()
        self.socket = self.app.online_socket

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.ready_rect().collidepoint(event.pos):
                    self.toggle_ready()
                elif self.leave_rect().collidepoint(event.pos):
                    self.leave_room()
                continue
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (self.app.key("back"), pygame.K_ESCAPE):
                self.leave_room()
            elif event.key in (self.app.key("retry_ready"), pygame.K_r, pygame.K_RETURN):
                self.toggle_ready()

    def update(self, dt: float) -> None:
        self.apply_socket_messages()
        self.apply_heartbeat_result()
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
        self.heartbeat_request.start(self.api.heartbeat, room["id"], player["id"])

    def apply_heartbeat_result(self) -> None:
        result = self.heartbeat_request.drain()
        if result is None:
            return
        ok, payload = result
        if not ok:
            self.status = "Loading..."
            return
        room = self.app.online_room
        if room and payload.get("id") == room.get("id"):
            self.app.online_room = payload

    def apply_socket_messages(self) -> None:
        if not self.socket:
            return
        for _ in self.socket.drain_errors():
            self.websocket_failed = True
            self.status = "Reconnecting..."
        unhandled = []
        for message in self.socket.drain():
            if message.get("type") == "room.state":
                self.app.online_room = message["room"]
                self.websocket_failed = False
                self.status = "Click Ready   Esc Leave"
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
            self.status = "Click Ready   Esc Leave"
        except ApiError:
            self.status = "Loading..."

    def toggle_ready(self) -> None:
        room = self.app.online_room
        player = self.app.online_player
        if not room or not player:
            return
        current = self.current_player_ready()
        try:
            self.app.online_room = self.api.set_ready(room["id"], player["id"], not current)
            self.status = "Click Ready   Esc Leave"
        except ApiError:
            self.status = "Ready failed"

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

    def ready_rect(self) -> pygame.Rect:
        return pygame.Rect(610, 540, 120, 44)

    def leave_rect(self) -> pygame.Rect:
        return pygame.Rect(750, 540, 120, 44)

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
            name = player_label(room, room_player["id"]) + (" (You)" if is_me else "")
            ready = "Ready" if room_player["ready"] else "Waiting"
            color = CYAN if is_me else WHITE
            screen.blit(self.font.render(name, True, color), (row.x + 28, row.y + 20))
            ready_color = CYAN if room_player["ready"] else GRAY
            ready_surface = self.font.render(ready, True, ready_color)
            screen.blit(ready_surface, ready_surface.get_rect(midright=(row.right - 28, row.centery)))
        slots_left = room["max_players"] - len(room["players"])
        if slots_left:
            self.draw_text(screen, "Waiting for player...", (120, 525), small=True)
        if room["started"]:
            self.draw_text(screen, "Starting...", (120, 560), small=True)
        self.draw_button(screen, self.ready_rect(), "Ready", CYAN)
        self.draw_button(screen, self.leave_rect(), "Leave", GRAY)
        draw_status_bar(screen, self.small_font, self.status)

    def draw_button(self, screen: pygame.Surface, rect: pygame.Rect, label: str, color: tuple[int, int, int]) -> None:
        draw_panel(screen, rect, border_color=color, fill_color=(24, 28, 35))
        surface = self.small_font.render(label, True, color)
        screen.blit(surface, surface.get_rect(center=rect.center))
