import random

import pygame

from client.audio import sfx
from client.constants import BLACK, CYAN, GRAY, RED, WHITE
from client.game.repeat import GAME_REPEAT, RepeatController
from client.match.countdown import Countdown
from client.net.api import ApiClient, ApiError
from client.net.websocket import RoomSocketClient
from client.player_labels import player_label
from client.scenes.base import Scene
from client.tetris.board import WIDTH
from client.tetris.rules import TetrisGame
from client.tetris.snapshot import game_snapshot
from client.ui.tetris_panel import draw_tetris_panel, empty_grid


LEFT_PANEL_X = 48
RIGHT_PANEL_X = 496
PANEL_Y = 130
STATE_SYNC_INTERVAL = 0.25
HEARTBEAT_INTERVAL = 5.0


class OnlineGameScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.api = ApiClient()
        self.game = TetrisGame()
        self.socket: RoomSocketClient | None = None
        self.remote_states: dict[str, dict] = {}
        self.fall_elapsed = 0.0
        self.send_elapsed = 0.0
        self.heartbeat_elapsed = 0.0
        self.status = "Live match sync"
        self.result: str | None = None
        self.result_sent = False
        self.countdown = Countdown(duration=0.0)
        self.repeat = RepeatController(GAME_REPEAT)

    def on_enter(self) -> None:
        self.game = TetrisGame(seed=self.match_seed())
        self.remote_states = {}
        self.fall_elapsed = 0.0
        self.send_elapsed = 0.0
        self.heartbeat_elapsed = 0.0
        self.result = None
        self.result_sent = False
        self.countdown.reset()
        self.repeat.reset()
        self.status = "Live match sync"
        self.app.audio.play_music("game_theme")
        self.open_socket()
        self.send_state()

    def match_seed(self) -> int | None:
        room = self.app.online_room
        return room.get("match_seed") if room else None

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
            if event.type == pygame.KEYUP:
                self.release_repeat(event.key)
                continue
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == self.app.key("back"):
                self.return_to_room()
                return
            if self.result and event.key == self.app.key("retry_ready"):
                self.ready_for_rematch()
                return
            if self.result:
                continue
            if self.countdown.active:
                continue
            if self.game.game_over:
                continue
            if event.key == self.app.key("move_left"):
                self.repeat.press("move_left")
                self.apply_action("move_left")
            elif event.key == self.app.key("move_right"):
                self.repeat.press("move_right")
                self.apply_action("move_right")
            elif event.key == self.app.key("soft_drop"):
                self.repeat.press("soft_drop")
                self.apply_action("soft_drop")
            elif event.key == self.app.key("rotate_cw"):
                if self.game.rotate(1):
                    self.app.audio.play_sfx(sfx.ROTATE)
                    self.send_input("rotate_cw")
            elif event.key == self.app.key("rotate_ccw"):
                if self.game.rotate(-1):
                    self.app.audio.play_sfx(sfx.ROTATE)
                    self.send_input("rotate_ccw")
            elif event.key == self.app.key("rotate_180"):
                if self.game.rotate(2):
                    self.app.audio.play_sfx(sfx.ROTATE)
                    self.send_input("rotate_180")
            elif event.key == self.app.key("hard_drop"):
                result = self.game.hard_drop()
                self.after_step(result)
                self.app.audio.play_sfx(sfx.HARD_DROP)
                self.send_input("hard_drop")
            elif event.key == self.app.key("hold"):
                self.game.hold()
                self.app.audio.play_sfx(sfx.HOLD)
                self.send_input("hold")

    def return_to_room(self) -> None:
        room = self.app.online_room
        player = self.app.online_player
        if room and player:
            try:
                self.app.online_room = self.api.reset_room(room["id"], player["id"])
            except ApiError as exc:
                self.status = f"Room reset failed: {exc}"
                return
        self.app.change_scene("online_room")

    def ready_for_rematch(self) -> None:
        room = self.app.online_room
        player = self.app.online_player
        if not room or not player:
            self.app.change_scene("online_room")
            return
        try:
            latest = self.api.get_room(room["id"])
            if latest.get("started"):
                latest = self.api.reset_room(room["id"], player["id"])
            self.app.online_room = self.api.set_ready(room["id"], player["id"], True)
        except ApiError as exc:
            self.status = f"Rematch failed: {exc}"
            return
        self.result = None
        self.app.change_scene("online_room")

    def release_repeat(self, key: int) -> None:
        for action in GAME_REPEAT:
            if key == self.app.key(action):
                self.repeat.release(action)

    def apply_action(self, action: str) -> None:
        if action == "move_left":
            if self.game.move(-1, 0):
                self.app.audio.play_sfx(sfx.MOVE)
                self.send_input(action)
        elif action == "move_right":
            if self.game.move(1, 0):
                self.app.audio.play_sfx(sfx.MOVE)
                self.send_input(action)
        elif action == "soft_drop":
            self.after_step(self.game.soft_drop())
            self.send_input(action)

    def update(self, dt: float) -> None:
        self.apply_socket_messages()
        self.heartbeat_elapsed += dt
        if self.heartbeat_elapsed >= HEARTBEAT_INTERVAL:
            self.heartbeat_elapsed = 0.0
            self.send_heartbeat()
        if self.result:
            return
        if self.countdown.active:
            self.countdown.update(dt)
            if not self.countdown.active:
                self.status = "Live match sync"
                self.send_state()
            return
        if not self.game.game_over:
            for action in self.repeat.update(dt):
                self.apply_action(action)
            self.fall_elapsed += dt
            interval = max(0.12, 0.8 - (self.game.level - 1) * 0.06)
            if self.fall_elapsed >= interval:
                self.fall_elapsed = 0.0
                result = self.game.tick()
                self.after_step(result)
                self.send_state()
        self.send_elapsed += dt
        if self.send_elapsed >= STATE_SYNC_INTERVAL:
            self.send_elapsed = 0.0
            self.send_state()

    def send_heartbeat(self) -> None:
        room = self.app.online_room
        player = self.app.online_player
        if not room or not player:
            return
        try:
            self.app.online_room = self.api.heartbeat(room["id"], player["id"])
            if len(self.app.online_room.get("players", [])) < 2 and not self.result:
                self.status = "Opponent disconnected"
                self.result = "WIN"
        except ApiError as exc:
            self.status = f"Heartbeat failed: {exc}"

    def apply_socket_messages(self) -> None:
        if not self.socket:
            return
        for error in self.socket.drain_errors():
            self.status = error
        player = self.app.online_player
        my_id = player["id"] if player else None
        for message in self.socket.drain():
            if message.get("type") == "room.state":
                self.apply_room_state(message["room"])
            elif message.get("type") == "match.input" and message.get("player_id") != my_id:
                self.remote_states[message["player_id"]] = message["state"]
                if message["state"].get("game_over") and not self.game.game_over:
                    self.result = "WIN"
            elif message.get("type") == "match.state" and message.get("player_id") != my_id:
                self.remote_states[message["player_id"]] = message["state"]
                if message["state"].get("game_over") and not self.game.game_over:
                    self.result = "WIN"
            elif message.get("type") == "match.garbage" and message.get("target_id") == my_id:
                self.game.add_garbage(int(message.get("lines", 0)), message.get("hole"))
                self.status = f"Received {message.get('lines', 0)} garbage"
                self.send_state()
                self.maybe_send_result()
            elif message.get("type") == "match.result" and message.get("winner_id") == my_id:
                self.result = "WIN"
            elif message.get("type") == "match.result" and message.get("loser_id") == my_id:
                self.result = "LOSE"

    def apply_room_state(self, room: dict) -> None:
        self.app.online_room = room
        player = self.app.online_player
        if not player:
            return
        player_ids = {room_player["id"] for room_player in room.get("players", [])}
        if player["id"] not in player_ids:
            self.status = "You left the room"
            self.result = "LOSE"
            return
        if len(player_ids) < 2 and not self.result:
            self.status = "Opponent left"
            self.result = "WIN"
            self.result_sent = True
            return
        if not room.get("started") and not self.result:
            self.status = "Match canceled"
            self.app.change_scene("online_room")

    def after_step(self, result=None) -> None:
        if result and result.attack:
            self.send_garbage(result.attack)
            self.status = f"Sent {result.attack} garbage"
        if result and result.lines_cleared:
            self.app.audio.play_sfx(sfx.LINE_CLEAR)
        if result and result.game_over:
            self.app.audio.play_sfx(sfx.GAME_OVER)
        self.maybe_send_result()

    def send_state(self) -> None:
        if not self.socket or not self.app.online_player:
            return
        self.socket.send(
            {
                "type": "match.state",
                "player_id": self.app.online_player["id"],
                "state": self.snapshot(),
            }
        )

    def send_input(self, action: str) -> None:
        if not self.socket or not self.app.online_player:
            return
        self.socket.send(
            {
                "type": "match.input",
                "player_id": self.app.online_player["id"],
                "action": action,
                "state": self.snapshot(),
            }
        )

    def send_garbage(self, lines: int) -> None:
        if not self.socket or not self.app.online_player:
            return
        target_id = self.first_remote_player_id()
        if not target_id:
            return
        self.socket.send(
            {
                "type": "match.garbage",
                "player_id": self.app.online_player["id"],
                "target_id": target_id,
                "lines": lines,
                "hole": random.randrange(WIDTH),
            }
        )

    def maybe_send_result(self) -> None:
        if not self.game.game_over or self.result_sent or not self.socket or not self.app.online_player:
            return
        winner_id = self.first_remote_player_id()
        self.result = "LOSE"
        self.result_sent = True
        self.socket.send(
            {
                "type": "match.result",
                "winner_id": winner_id,
                "loser_id": self.app.online_player["id"],
            }
        )

    def first_remote_player_id(self) -> str | None:
        room = self.app.online_room
        player = self.app.online_player
        if not room or not player:
            return None
        for room_player in room.get("players", []):
            if room_player.get("id") != player["id"]:
                return room_player.get("id")
        return None

    def snapshot(self) -> dict:
        return game_snapshot(self.game)

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        self.draw_text(screen, "Online Match", (80, 70))
        local_state = self.snapshot()
        draw_tetris_panel(screen, self.font, self.small_font, local_state, LEFT_PANEL_X, PANEL_Y, self.local_label())
        self.draw_stats(screen, local_state, LEFT_PANEL_X + 88, 616)

        remote_id, remote = self.first_remote_entry()
        if remote:
            draw_tetris_panel(screen, self.font, self.small_font, remote, RIGHT_PANEL_X, PANEL_Y, self.remote_label(remote_id))
            self.draw_stats(screen, remote, RIGHT_PANEL_X + 88, 616)
            if remote.get("game_over"):
                self.draw_text(screen, "Opponent topped out", (RIGHT_PANEL_X + 88, 96), small=True)
        else:
            empty_state = {"grid": empty_grid(), "ghost": [], "hold": None, "next": []}
            draw_tetris_panel(screen, self.font, self.small_font, empty_state, RIGHT_PANEL_X, PANEL_Y, self.remote_label(remote_id))
            self.draw_text(screen, "Waiting for opponent state...", (RIGHT_PANEL_X + 88, 616), small=True)

        if self.game.game_over:
            self.draw_text(screen, "You topped out", (LEFT_PANEL_X + 88, 96), small=True)
        if self.result:
            self.draw_result_screen(screen)
        elif self.countdown.active:
            surface = self.font.render(self.countdown.label, True, WHITE)
            screen.blit(surface, surface.get_rect(center=(480, 340)))
        if self.status:
            screen.blit(self.small_font.render(self.status, True, GRAY), (380, 94))
        hint_text = "R: Rematch setup   Esc: Back to Room" if self.result else "Esc: Back to Room"
        hint = self.small_font.render(hint_text, True, GRAY)
        screen.blit(hint, (80, 650))

    def draw_result_screen(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 172))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(230, 190, 500, 270)
        pygame.draw.rect(screen, (28, 32, 40), panel, border_radius=8)
        pygame.draw.rect(screen, CYAN if self.result == "WIN" else RED, panel, width=3, border_radius=8)

        title = "YOU WIN" if self.result == "WIN" else "YOU LOSE"
        title_color = CYAN if self.result == "WIN" else RED
        title_surface = self.font.render(title, True, title_color)
        screen.blit(title_surface, title_surface.get_rect(center=(panel.centerx, panel.y + 72)))

        reason = self.result_reason()
        reason_surface = self.small_font.render(reason, True, WHITE)
        screen.blit(reason_surface, reason_surface.get_rect(center=(panel.centerx, panel.y + 130)))

        rematch_surface = self.small_font.render("R: Ready for rematch", True, CYAN)
        screen.blit(rematch_surface, rematch_surface.get_rect(center=(panel.centerx, panel.y + 188)))

        back_surface = self.small_font.render("Esc: Back to room", True, GRAY)
        screen.blit(back_surface, back_surface.get_rect(center=(panel.centerx, panel.y + 224)))

    def result_reason(self) -> str:
        if self.status in {"Opponent left", "Opponent disconnected"}:
            return self.status
        if self.result == "WIN":
            return "Opponent topped out"
        return "You topped out"

    def first_remote_state(self) -> dict | None:
        return next(iter(self.remote_states.values()), None)

    def first_remote_entry(self) -> tuple[str | None, dict | None]:
        return next(iter(self.remote_states.items()), (None, None))

    def local_label(self) -> str:
        room = self.app.online_room
        player = self.app.online_player
        if not room or not player:
            return "P? (You)"
        return f"{player_label(room, player['id'])} (You)"

    def remote_label(self, remote_id: str | None) -> str:
        room = self.app.online_room
        if not room or not remote_id:
            return "P?"
        return player_label(room, remote_id)

    def draw_stats(self, screen: pygame.Surface, state: dict, x: int, y: int) -> None:
        color = RED if state.get("game_over") else CYAN
        combo = max(state.get("combo", -1), 0)
        b2b = " Back-to-Back" if state.get("back_to_back") else ""
        text = f"Score {state['score']}   Lines {state['lines']}   Combo {combo}{b2b}"
        screen.blit(self.small_font.render(text, True, color), (x, y))
