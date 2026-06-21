import pygame

from client.constants import BLACK, CYAN, GRAY, RED, WHITE
from client.net.api import ApiClient, ApiError
from client.net.background import BackgroundRequest
from client.scenes.base import Scene
from client.ui.surface import draw_header, draw_panel, draw_status_bar


LIST_STATUS = "R Refresh   C Create room   Enter Join   Esc Menu"
CREATE_STATUS = "Click Password to lock   Tab Switch field   Enter Create"
JOIN_STATUS = "Type password   Enter Join   Esc Back"
MAX_TITLE_LENGTH = 24
MAX_PASSWORD_LENGTH = 16


class OnlineLobbyScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.api = ApiClient()
        self.refresh_request = BackgroundRequest()
        self.create_request = BackgroundRequest()
        self.join_request = BackgroundRequest()
        self.rooms: list[dict] = []
        self.selected = 0
        self.server_online = False
        self.loaded_once = False
        self.loading = False
        self.mode = "list"
        self.create_title = ""
        self.create_password_enabled = False
        self.create_password = ""
        self.create_field = 0
        self.join_password = ""
        self.password_error = ""
        self.ignore_next_text_input = False
        self.composing_text = ""
        self.status = LIST_STATUS

    def on_enter(self) -> None:
        self.mode = "list"
        self.refresh_request = BackgroundRequest()
        self.create_request = BackgroundRequest()
        self.join_request = BackgroundRequest()
        self.refresh()

    def refresh(self, manual: bool = False) -> None:
        if self.refresh_request.running:
            return
        self.loading = True
        if manual:
            self.status = "Refreshing..."
        elif not self.loaded_once:
            self.status = "Loading..."
        self.refresh_request.start(self.api.list_rooms)

    def update(self, dt: float) -> None:
        self.apply_refresh_result()
        self.apply_create_result()
        self.apply_join_result()

    def apply_refresh_result(self) -> None:
        result = self.refresh_request.drain()
        if result is None:
            return
        ok, payload = result
        self.loading = False
        if ok:
            self.server_online = True
            self.loaded_once = True
            self.rooms = payload
            self.selected = min(self.selected, max(len(self.rooms) - 1, 0))
            self.status = LIST_STATUS
        else:
            self.server_online = False
            if not self.loaded_once:
                self.rooms = []
                self.status = "Server unavailable   R Retry   Esc Menu"
            else:
                self.status = "Refresh failed   R Retry   Esc Menu"

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_click(event.pos)
                continue
            if event.type == pygame.TEXTINPUT:
                if self.ignore_next_text_input:
                    self.ignore_next_text_input = False
                    continue
                self.composing_text = ""
                self.handle_text_input(event.text)
                continue
            if event.type == pygame.TEXTEDITING:
                self.handle_text_editing(event.text)
                continue
            if event.type != pygame.KEYDOWN:
                continue
            if self.mode == "create":
                self.handle_create_event(event)
                continue
            if self.mode == "password":
                self.handle_password_event(event)
                continue
            self.handle_list_event(event)

    def handle_list_event(self, event: pygame.event.Event) -> None:
        if event.key in (self.app.key("back"), pygame.K_ESCAPE):
            self.app.change_scene("menu")
        elif event.key in (self.app.key("menu_next"), pygame.K_TAB, pygame.K_DOWN):
            if self.rooms:
                self.selected = (self.selected + 1) % len(self.rooms)
        elif event.key in (pygame.K_UP, pygame.K_LEFT):
            if self.rooms:
                self.selected = (self.selected - 1) % len(self.rooms)
        elif event.key in (self.app.key("retry_ready"), pygame.K_r):
            self.refresh(manual=True)
        elif event.key == pygame.K_c:
            if self.server_online:
                self.open_create_form(ignore_next_text_input=True)
        elif event.key in (self.app.key("confirm"), pygame.K_RETURN) and self.rooms:
            self.join_selected_room()

    def open_create_form(self, ignore_next_text_input: bool = False) -> None:
        self.mode = "create"
        self.create_title = ""
        self.create_password_enabled = False
        self.create_password = ""
        self.create_field = 0
        self.password_error = ""
        self.ignore_next_text_input = ignore_next_text_input
        self.composing_text = ""
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(self.title_rect())
        self.status = CREATE_STATUS

    def handle_create_event(self, event: pygame.event.Event) -> None:
        if event.key in (self.app.key("back"), pygame.K_ESCAPE):
            self.return_to_list()
        elif event.key in (self.app.key("confirm"), pygame.K_RETURN):
            if self.create_field == 1:
                self.toggle_create_password()
            else:
                self.create_room()
        elif event.key in (self.app.key("menu_next"), pygame.K_TAB, pygame.K_DOWN):
            self.create_field = (self.create_field + 1) % self.create_field_count()
        elif event.key in (pygame.K_UP, pygame.K_LEFT):
            self.create_field = (self.create_field - 1) % self.create_field_count()
        elif event.key in (pygame.K_p, pygame.K_SPACE) and self.create_field == 1:
            self.toggle_create_password()
        elif event.key == pygame.K_BACKSPACE:
            if self.create_field == 0:
                self.create_title = self.create_title[:-1]
                self.composing_text = ""
                pygame.key.set_text_input_rect(self.title_rect())
            elif self.create_password_enabled and self.create_field == 2:
                self.create_password = self.create_password[:-1]
                self.composing_text = ""
                pygame.key.set_text_input_rect(self.password_rect())

    def handle_text_input(self, text: str) -> None:
        if self.mode == "create":
            self.append_create_text(text)
        elif self.mode == "password":
            self.append_join_password(text)

    def handle_text_editing(self, text: str) -> None:
        if self.mode not in ("create", "password"):
            self.composing_text = ""
            return
        self.composing_text = text if self.is_text_input(text) else ""

    def append_create_text(self, text: str) -> None:
        if not self.is_text_input(text):
            return
        if self.create_field == 0 and len(self.create_title) < MAX_TITLE_LENGTH:
            self.create_title = (self.create_title + text)[:MAX_TITLE_LENGTH]
            pygame.key.set_text_input_rect(self.title_rect())
        elif self.create_password_enabled and self.create_field == 2 and len(self.create_password) < MAX_PASSWORD_LENGTH:
            self.create_password = (self.create_password + text)[:MAX_PASSWORD_LENGTH]
            pygame.key.set_text_input_rect(self.password_rect())

    def create_room(self) -> None:
        if self.create_request.running:
            return
        title = self.create_title.strip() or "Room"
        password = self.create_password.strip() if self.create_password_enabled else None
        if self.create_password_enabled and not password:
            self.status = "Enter a password or turn password Off"
            return
        if self.create_request.start(self.api.create_room, title, password=password):
            self.status = "Creating..."

    def apply_create_result(self) -> None:
        result = self.create_request.drain()
        if result is None:
            return
        ok, payload = result
        if ok:
            self.app.online_room = payload["room"]
            self.app.online_player = payload["player"]
            pygame.key.stop_text_input()
            self.app.change_scene("online_room")
        else:
            self.status = "Create failed"

    def join_selected_room(self) -> None:
        room = self.rooms[self.selected]
        if room["started"]:
            self.status = "Match already started"
            return
        if room["has_password"]:
            self.mode = "password"
            self.join_password = ""
            self.password_error = ""
            self.ignore_next_text_input = False
            self.composing_text = ""
            pygame.key.start_text_input()
            pygame.key.set_text_input_rect(self.password_rect())
            self.status = JOIN_STATUS
            return
        self.join_room(room, None)

    def handle_password_event(self, event: pygame.event.Event) -> None:
        if event.key in (self.app.key("back"), pygame.K_ESCAPE):
            self.return_to_list()
        elif event.key in (self.app.key("confirm"), pygame.K_RETURN):
            self.join_room(self.rooms[self.selected], self.join_password.strip())
        elif event.key == pygame.K_BACKSPACE:
            self.join_password = self.join_password[:-1]

    def append_join_password(self, text: str) -> None:
        if not self.is_text_input(text):
            return
        self.password_error = ""
        if len(self.join_password) < MAX_PASSWORD_LENGTH:
            self.join_password = (self.join_password + text)[:MAX_PASSWORD_LENGTH]
            pygame.key.set_text_input_rect(self.password_rect())

    def join_room(self, room: dict, password: str | None) -> None:
        if self.join_request.running:
            return
        if self.join_request.start(self.api.join_room, room["id"], password=password):
            self.status = "Joining..."

    def apply_join_result(self) -> None:
        result = self.join_request.drain()
        if result is None:
            return
        ok, payload = result
        if ok:
            self.app.online_room = payload["room"]
            self.app.online_player = payload["player"]
            pygame.key.stop_text_input()
            self.app.change_scene("online_room")
            return
        error = str(payload)
        if "403" in error:
            self.password_error = "Wrong password"
            self.join_password = ""
        elif "409" in error:
            self.password_error = "Room is full"
        else:
            self.password_error = "Join failed"
        self.status = JOIN_STATUS if self.mode == "password" else LIST_STATUS

    def return_to_list(self) -> None:
        self.mode = "list"
        self.join_password = ""
        self.password_error = ""
        self.ignore_next_text_input = False
        self.composing_text = ""
        pygame.key.stop_text_input()
        self.status = LIST_STATUS if self.server_online else "Server offline   R Retry   Esc Menu"

    def toggle_create_password(self) -> None:
        self.create_password_enabled = not self.create_password_enabled
        if self.create_password_enabled:
            self.create_field = 2
            self.composing_text = ""
            pygame.key.set_text_input_rect(self.password_rect())
        else:
            self.create_field = min(self.create_field, 1)
            self.create_password = ""
            self.composing_text = ""
            pygame.key.set_text_input_rect(self.title_rect())

    def create_field_count(self) -> int:
        return 3 if self.create_password_enabled else 2

    def is_text_input(self, text: str) -> bool:
        return bool(text) and all(ord(char) >= 32 for char in text)

    def handle_mouse_click(self, pos: tuple[int, int]) -> None:
        if self.mode == "create":
            self.handle_create_mouse(pos)
        elif self.mode == "password":
            self.handle_password_mouse(pos)
        else:
            self.handle_list_mouse(pos)

    def handle_list_mouse(self, pos: tuple[int, int]) -> None:
        if self.refresh_rect().collidepoint(pos):
            self.refresh(manual=True)
            return
        if self.create_rect().collidepoint(pos) and self.server_online:
            self.open_create_form()
            return
        if self.back_rect().collidepoint(pos):
            self.app.change_scene("menu")
            return
        for index, room in enumerate(self.rooms[:9]):
            if self.room_rect(index).collidepoint(pos):
                self.selected = index
                self.join_selected_room()
                return

    def handle_create_mouse(self, pos: tuple[int, int]) -> None:
        if self.title_rect().collidepoint(pos):
            self.create_field = 0
            self.composing_text = ""
            pygame.key.set_text_input_rect(self.title_rect())
        elif self.password_toggle_rect().collidepoint(pos):
            self.toggle_create_password()
        elif self.create_password_enabled and self.password_rect().collidepoint(pos):
            self.create_field = 2
            self.composing_text = ""
            pygame.key.set_text_input_rect(self.password_rect())
        elif self.form_create_rect().collidepoint(pos):
            self.create_room()
        elif self.form_cancel_rect().collidepoint(pos):
            self.return_to_list()

    def handle_password_mouse(self, pos: tuple[int, int]) -> None:
        if self.password_rect().collidepoint(pos):
            return
        if self.join_rect().collidepoint(pos):
            self.join_room(self.rooms[self.selected], self.join_password.strip())
        elif self.form_cancel_rect().collidepoint(pos):
            self.return_to_list()

    def room_rect(self, index: int) -> pygame.Rect:
        return pygame.Rect(92, 166 + index * 45, 776, 36)

    def refresh_rect(self) -> pygame.Rect:
        return pygame.Rect(575, 112, 120, 34)

    def create_rect(self) -> pygame.Rect:
        return pygame.Rect(705, 112, 150, 34)

    def back_rect(self) -> pygame.Rect:
        return pygame.Rect(70, 112, 110, 34)

    def title_rect(self) -> pygame.Rect:
        return pygame.Rect(125, 190, 710, 48)

    def password_toggle_rect(self) -> pygame.Rect:
        return pygame.Rect(125, 270, 220, 48)

    def password_rect(self) -> pygame.Rect:
        return pygame.Rect(125, 350, 710, 48) if self.mode == "create" else pygame.Rect(125, 235, 710, 48)

    def form_create_rect(self) -> pygame.Rect:
        return pygame.Rect(575, 420, 125, 42)

    def join_rect(self) -> pygame.Rect:
        return pygame.Rect(575, 345, 125, 42)

    def form_cancel_rect(self) -> pygame.Rect:
        y = 420 if self.mode == "create" else 345
        return pygame.Rect(710, y, 125, 42)

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        if self.mode == "create":
            self.draw_create_form(screen)
            return
        if self.mode == "password":
            self.draw_password_form(screen)
            return
        self.draw_room_list(screen)

    def draw_room_list(self, screen: pygame.Surface) -> None:
        draw_header(screen, self.font, "Online")

        list_rect = pygame.Rect(70, 145, 820, 455)
        draw_panel(screen, list_rect)
        if not self.rooms:
            message = "Loading..." if self.loading and not self.loaded_once else "No rooms"
            surface = self.small_font.render(message, True, WHITE)
            screen.blit(surface, surface.get_rect(center=list_rect.center))
        for index, room in enumerate(self.rooms[:9]):
            self.draw_room_row(screen, index, room)
        self.draw_button(screen, self.refresh_rect(), "Refresh", GRAY)
        self.draw_button(screen, self.create_rect(), "Create room", CYAN if self.server_online else GRAY)
        self.draw_button(screen, self.back_rect(), "Menu", GRAY)
        draw_status_bar(screen, self.small_font, self.status)

    def draw_room_row(self, screen: pygame.Surface, index: int, room: dict) -> None:
        locked = "Locked" if room["has_password"] else "Open"
        players = f"{len(room['players'])}/{room['max_players']}"
        state = "Playing" if room["started"] else "Waiting"
        color = CYAN if index == self.selected else WHITE
        row = self.room_rect(index)
        if index == self.selected:
            draw_panel(screen, row, border_color=CYAN, fill_color=(32, 42, 48))
        screen.blit(self.small_font.render(room["title"], True, color), (row.x + 16, row.y + 7))
        screen.blit(self.small_font.render(locked, True, color), (row.x + 390, row.y + 7))
        screen.blit(self.small_font.render(players, True, color), (row.x + 520, row.y + 7))
        screen.blit(self.small_font.render(state, True, color), (row.x + 620, row.y + 7))

    def draw_create_form(self, screen: pygame.Surface) -> None:
        draw_header(screen, self.font, "Create Room")
        panel = pygame.Rect(90, 145, 780, 360)
        draw_panel(screen, panel)

        title_color = CYAN if self.create_field == 0 else WHITE
        password_color = CYAN if self.create_password_enabled and self.create_field == 2 else WHITE
        title_display = self.create_title
        if self.mode == "create" and self.create_field == 0 and self.composing_text:
            title_display = (title_display + self.composing_text)[:MAX_TITLE_LENGTH]
        self.draw_field(screen, "Room name", title_display, (125, 190), title_color)
        toggle_color = CYAN if self.create_field == 1 or self.create_password_enabled else GRAY
        self.draw_button(
            screen,
            self.password_toggle_rect(),
            f"Password {'On' if self.create_password_enabled else 'Off'}",
            toggle_color,
        )
        if self.create_password_enabled:
            hidden_length = len(self.create_password)
            if self.create_field == 2:
                hidden_length += len(self.composing_text)
            hidden = "*" * min(hidden_length, MAX_PASSWORD_LENGTH)
            self.draw_field(screen, "Password", hidden, (125, 350), password_color)

        note = "Password On: locked room" if self.create_password_enabled else "Password Off: open room"
        screen.blit(self.small_font.render(note, True, CYAN if self.create_password_enabled else GRAY), (370, 284))
        self.draw_button(screen, self.form_create_rect(), "Create", CYAN)
        self.draw_button(screen, self.form_cancel_rect(), "Cancel", GRAY)
        draw_status_bar(screen, self.small_font, self.status)

    def draw_password_form(self, screen: pygame.Surface) -> None:
        room = self.rooms[self.selected]
        draw_header(screen, self.font, "Enter Password", room["title"])
        panel = pygame.Rect(90, 165, 780, 230)
        draw_panel(screen, panel)

        hidden = "*" * min(len(self.join_password) + len(self.composing_text), MAX_PASSWORD_LENGTH)
        self.draw_field(screen, "Password", hidden, (125, 235), CYAN)
        if self.password_error:
            color = RED if self.password_error in ("Wrong password", "Join failed") else GRAY
            screen.blit(self.small_font.render(self.password_error, True, color), (125, 320))
        self.draw_button(screen, self.join_rect(), "Join", CYAN)
        self.draw_button(screen, self.form_cancel_rect(), "Cancel", GRAY)
        draw_status_bar(screen, self.small_font, JOIN_STATUS)

    def draw_field(
        self,
        screen: pygame.Surface,
        label: str,
        value: str,
        pos: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        x, y = pos
        screen.blit(self.small_font.render(label, True, GRAY), (x, y - 28))
        rect = pygame.Rect(x, y, 710, 48)
        draw_panel(screen, rect, border_color=color, fill_color=(20, 23, 29))
        display = value + ("_" if color == CYAN else "")
        screen.blit(self.font.render(display, True, WHITE), (rect.x + 16, rect.y + 8))

    def draw_button(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        color: tuple[int, int, int],
    ) -> None:
        draw_panel(screen, rect, border_color=color, fill_color=(24, 28, 35))
        surface = self.small_font.render(label, True, color)
        screen.blit(surface, surface.get_rect(center=rect.center))
