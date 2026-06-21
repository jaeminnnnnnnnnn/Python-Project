import pygame

from client.constants import BLACK, CYAN, GRAY, WHITE
from client.net.api import ApiClient, ApiError
from client.scenes.base import Scene


class OnlineLobbyScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.api = ApiClient()
        self.rooms: list[dict] = []
        self.selected = 0
        self.server_online = False
        self.server_message = "Checking server..."
        self.mode = "list"
        self.create_title = "Room"
        self.create_password_enabled = False
        self.create_password = ""
        self.create_field = 0
        self.join_password = ""
        self.status = "R: Refresh   C: Create Room   Enter: Join   Esc: Back"

    def on_enter(self) -> None:
        self.mode = "list"
        self.refresh()

    def refresh(self) -> None:
        try:
            self.api.health()
            self.server_online = True
            self.server_message = "Server Online"
            self.rooms = self.api.list_rooms()
            self.selected = min(self.selected, max(len(self.rooms) - 1, 0))
            self.status = "R: Refresh   C: Create Room   Enter: Join   Esc: Back"
        except ApiError as exc:
            self.server_online = False
            self.server_message = "Server Offline"
            self.rooms = []
            self.status = f"Cannot connect. Press R to retry. ({exc})"

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if self.mode == "create":
                self.handle_create_event(event)
                continue
            if self.mode == "password":
                self.handle_password_event(event)
                continue
            if event.key == self.app.key("back"):
                self.app.change_scene("menu")
            elif event.key in (self.app.key("menu_next"), pygame.K_DOWN):
                if self.rooms:
                    self.selected = (self.selected + 1) % len(self.rooms)
            elif event.key == pygame.K_UP:
                if self.rooms:
                    self.selected = (self.selected - 1) % len(self.rooms)
            elif event.key == self.app.key("retry_ready"):
                self.refresh()
            elif event.key == pygame.K_c:
                if self.server_online:
                    self.open_create_form()
            elif event.key == self.app.key("confirm") and self.rooms:
                self.join_selected_room()

    def open_create_form(self) -> None:
        self.mode = "create"
        self.create_title = "Room"
        self.create_password_enabled = False
        self.create_password = ""
        self.create_field = 0
        self.status = "Enter: Create   Tab: Field   P: Password On/Off   Esc: Cancel"

    def handle_create_event(self, event: pygame.event.Event) -> None:
        if event.key == self.app.key("back"):
            self.mode = "list"
            self.status = "R: Refresh   C: Create Room   Enter: Join   Esc: Back"
        elif event.key == self.app.key("confirm"):
            self.create_room()
        elif event.key == self.app.key("menu_next"):
            self.create_field = (self.create_field + 1) % (2 if self.create_password_enabled else 1)
        elif event.key == pygame.K_p:
            self.create_password_enabled = not self.create_password_enabled
            if not self.create_password_enabled:
                self.create_password = ""
                self.create_field = 0
        elif event.key == pygame.K_BACKSPACE:
            if self.create_field == 0:
                self.create_title = self.create_title[:-1]
            else:
                self.create_password = self.create_password[:-1]
        else:
            self.append_text(event)

    def append_text(self, event: pygame.event.Event) -> None:
        char = event.unicode
        if not char or ord(char) < 32:
            return
        if self.create_field == 0:
            if len(self.create_title) < 24:
                self.create_title += char
        elif len(self.create_password) < 16:
            self.create_password += char

    def create_room(self) -> None:
        title = self.create_title.strip() or "Room"
        password = self.create_password if self.create_password_enabled else None
        if self.create_password_enabled and not password:
            self.status = "Password is empty."
            return
        try:
            payload = self.api.create_room(title, password=password)
            self.app.online_room = payload["room"]
            self.app.online_player = payload["player"]
            self.app.change_scene("online_room")
        except ApiError as exc:
            self.status = f"Create failed: {exc}"

    def join_selected_room(self) -> None:
        room = self.rooms[self.selected]
        if room["has_password"]:
            self.mode = "password"
            self.join_password = ""
            self.status = "Enter password"
            return
        self.join_room(room, None)

    def handle_password_event(self, event: pygame.event.Event) -> None:
        if event.key == self.app.key("back"):
            self.mode = "list"
            self.join_password = ""
            self.status = "R: Refresh   C: Create Room   Enter: Join   Esc: Back"
        elif event.key == self.app.key("confirm"):
            self.join_room(self.rooms[self.selected], self.join_password)
        elif event.key == pygame.K_BACKSPACE:
            self.join_password = self.join_password[:-1]
        elif event.unicode and ord(event.unicode) >= 32 and len(self.join_password) < 16:
            self.join_password += event.unicode

    def join_room(self, room: dict, password: str | None) -> None:
        try:
            payload = self.api.join_room(room["id"], password=password)
            self.app.online_room = payload["room"]
            self.app.online_player = payload["player"]
            self.app.change_scene("online_room")
        except ApiError as exc:
            self.status = f"Join failed: {exc}"

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        if self.mode == "create":
            self.draw_create_form(screen)
            return
        if self.mode == "password":
            self.draw_password_form(screen)
            return
        self.draw_text(screen, "Online Lobby", (80, 70))
        state_color = CYAN if self.server_online else GRAY
        screen.blit(self.small_font.render(self.server_message, True, state_color), (80, 112))
        screen.blit(self.small_font.render(self.api.base_url, True, GRAY), (80, 615))
        if not self.rooms:
            message = "No rooms. Press C to create one." if self.server_online else "Server is not reachable."
            self.draw_text(screen, message, (90, 160), small=True)
        for index, room in enumerate(self.rooms[:9]):
            marker = "> " if index == self.selected else "  "
            lock = "LOCK" if room["has_password"] else "OPEN"
            players = f"{len(room['players'])}/{room['max_players']}"
            started = "STARTED" if room["started"] else "WAITING"
            color = CYAN if index == self.selected else WHITE
            text = f"{marker}{room['title']}  [{lock}]  {players}  {started}"
            screen.blit(self.small_font.render(text, True, color), (90, 145 + index * 36))
        hint = self.small_font.render(self.status, True, GRAY)
        screen.blit(hint, (80, 650))

    def draw_create_form(self, screen: pygame.Surface) -> None:
        self.draw_text(screen, "Create Room", (80, 70))
        title_color = CYAN if self.create_field == 0 else WHITE
        password_color = CYAN if self.create_field == 1 else WHITE
        screen.blit(self.font.render(f"Title: {self.create_title}", True, title_color), (110, 165))
        password_state = "ON" if self.create_password_enabled else "OFF"
        screen.blit(self.font.render(f"Password: {password_state}", True, WHITE), (110, 230))
        if self.create_password_enabled:
            hidden = "*" * len(self.create_password)
            screen.blit(self.font.render(f"Code: {hidden}", True, password_color), (110, 295))
        hint = self.small_font.render(self.status, True, GRAY)
        screen.blit(hint, (80, 650))

    def draw_password_form(self, screen: pygame.Surface) -> None:
        room = self.rooms[self.selected]
        self.draw_text(screen, "Enter Password", (80, 70))
        self.draw_text(screen, room["title"], (110, 145), small=True)
        hidden = "*" * len(self.join_password)
        screen.blit(self.font.render(f"Password: {hidden}", True, CYAN), (110, 215))
        hint = self.small_font.render("Enter: Join   Esc: Cancel", True, GRAY)
        screen.blit(hint, (80, 650))
