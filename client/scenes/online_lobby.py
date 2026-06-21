import pygame

from client.constants import BLACK, CYAN, GRAY, WHITE
from client.net.api import ApiClient, ApiError
from client.scenes.base import Scene
from client.ui.surface import draw_header, draw_panel, draw_status_bar


class OnlineLobbyScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.api = ApiClient()
        self.rooms: list[dict] = []
        self.selected = 0
        self.server_online = False
        self.loading = False
        self.mode = "list"
        self.create_title = "방"
        self.create_password_enabled = False
        self.create_password = ""
        self.create_field = 0
        self.join_password = ""
        self.status = "R 새로고침   C 방 만들기   Enter 입장   Esc 뒤로"

    def on_enter(self) -> None:
        self.mode = "list"
        self.refresh()

    def refresh(self) -> None:
        self.loading = True
        self.status = "로딩 중"
        try:
            self.api.health()
            self.server_online = True
            self.rooms = self.api.list_rooms()
            self.selected = min(self.selected, max(len(self.rooms) - 1, 0))
            self.status = "R 새로고침   C 방 만들기   Enter 입장   Esc 뒤로"
        except ApiError:
            self.server_online = False
            self.rooms = []
            self.status = "R 새로고침   Esc 뒤로"
        finally:
            self.loading = False

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
        self.create_title = "방"
        self.create_password_enabled = False
        self.create_password = ""
        self.create_field = 0
        self.status = "Enter 만들기   Tab 항목 이동   P 잠금   Esc 취소"

    def handle_create_event(self, event: pygame.event.Event) -> None:
        if event.key == self.app.key("back"):
            self.mode = "list"
            self.status = "R 새로고침   C 방 만들기   Enter 입장   Esc 뒤로"
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
        title = self.create_title.strip() or "방"
        password = self.create_password if self.create_password_enabled else None
        if self.create_password_enabled and not password:
            self.status = "비밀번호를 입력하세요"
            return
        try:
            payload = self.api.create_room(title, password=password)
            self.app.online_room = payload["room"]
            self.app.online_player = payload["player"]
            self.app.change_scene("online_room")
        except ApiError:
            self.status = "방 만들기 실패"

    def join_selected_room(self) -> None:
        room = self.rooms[self.selected]
        if room["has_password"]:
            self.mode = "password"
            self.join_password = ""
            self.status = "비밀번호 입력"
            return
        self.join_room(room, None)

    def handle_password_event(self, event: pygame.event.Event) -> None:
        if event.key == self.app.key("back"):
            self.mode = "list"
            self.join_password = ""
            self.status = "R 새로고침   C 방 만들기   Enter 입장   Esc 뒤로"
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
        except ApiError:
            self.status = "입장 실패"

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        if self.mode == "create":
            self.draw_create_form(screen)
            return
        if self.mode == "password":
            self.draw_password_form(screen)
            return
        draw_header(screen, self.font, "온라인")

        list_rect = pygame.Rect(70, 145, 820, 455)
        draw_panel(screen, list_rect)
        if not self.rooms:
            message = "로딩 중" if self.loading or not self.server_online else "방 없음"
            surface = self.small_font.render(message, True, WHITE)
            screen.blit(surface, surface.get_rect(center=list_rect.center))
        for index, room in enumerate(self.rooms[:9]):
            lock = "잠김" if room["has_password"] else "공개"
            players = f"{len(room['players'])}/{room['max_players']}"
            started = "진행 중" if room["started"] else "대기 중"
            color = CYAN if index == self.selected else WHITE
            row = pygame.Rect(92, 166 + index * 45, 776, 36)
            if index == self.selected:
                draw_panel(screen, row, border_color=CYAN, fill_color=(32, 42, 48))
            title = self.small_font.render(room["title"], True, color)
            screen.blit(title, (row.x + 16, row.y + 7))
            screen.blit(self.small_font.render(lock, True, color), (row.x + 390, row.y + 7))
            screen.blit(self.small_font.render(players, True, color), (row.x + 500, row.y + 7))
            screen.blit(self.small_font.render(started, True, color), (row.x + 610, row.y + 7))
        draw_status_bar(screen, self.small_font, self.status)

    def draw_create_form(self, screen: pygame.Surface) -> None:
        draw_header(screen, self.font, "방 만들기")
        panel = pygame.Rect(90, 145, 780, 310)
        draw_panel(screen, panel)
        title_color = CYAN if self.create_field == 0 else WHITE
        password_color = CYAN if self.create_field == 1 else WHITE
        screen.blit(self.font.render(f"제목: {self.create_title}", True, title_color), (125, 185))
        password_state = "사용" if self.create_password_enabled else "사용 안 함"
        screen.blit(self.font.render(f"비밀번호: {password_state}", True, WHITE), (125, 250))
        if self.create_password_enabled:
            hidden = "*" * len(self.create_password)
            screen.blit(self.font.render(f"암호: {hidden}", True, password_color), (125, 315))
        draw_status_bar(screen, self.small_font, self.status)

    def draw_password_form(self, screen: pygame.Surface) -> None:
        room = self.rooms[self.selected]
        draw_header(screen, self.font, "비밀번호", room["title"])
        panel = pygame.Rect(90, 165, 780, 210)
        draw_panel(screen, panel)
        hidden = "*" * len(self.join_password)
        screen.blit(self.font.render(f"암호: {hidden}", True, CYAN), (125, 235))
        draw_status_bar(screen, self.small_font, "Enter 입장   Esc 취소")
