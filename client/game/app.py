from __future__ import annotations

import pygame

from client import config
from client.audio.manager import AudioManager
from client.game.save_data import load_settings
from client.net.websocket import RoomSocketClient
from client.scenes.intro import IntroScene
from client.scenes.menu import MenuScene
from client.scenes.online_game import OnlineGameScene
from client.scenes.online_lobby import OnlineLobbyScene
from client.scenes.online_room import OnlineRoomScene
from client.scenes.options import OptionsScene
from client.scenes.single import SingleScene


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(config.TITLE)
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.settings = load_settings()
        self.audio = AudioManager()
        self.audio.apply_settings(self.settings)
        self.online_room: dict | None = None
        self.online_player: dict | None = None
        self.online_socket: RoomSocketClient | None = None
        self.scenes = {
            "intro": IntroScene(self),
            "menu": MenuScene(self),
            "single": SingleScene(self),
            "online_lobby": OnlineLobbyScene(self),
            "online_room": OnlineRoomScene(self),
            "online_game": OnlineGameScene(self),
            "options": OptionsScene(self),
        }
        self.scene = self.scenes["intro"]

    def change_scene(self, name: str) -> None:
        self.scene.on_exit()
        self.scene = self.scenes[name]
        self.scene.on_enter()

    def quit(self) -> None:
        self.close_online_socket()
        self.running = False

    def close_online_socket(self) -> None:
        if self.online_socket:
            self.online_socket.stop()
            self.online_socket = None

    def key(self, action: str) -> int:
        return self.settings.key_bindings[action]

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit()

            self.scene.handle_events(events)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
