import pygame

from client.constants import BLACK, CYAN, GRAY, WHITE
from client.game.input import ACTION_LABELS, CONTROL_GROUPS
from client.game.save_data import load_settings, save_settings
from client.scenes.base import Scene


class OptionsScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.settings = load_settings()
        self.items = ["music_enabled", "sfx_enabled", "controls", "quit"]
        self.control_items = [action for _, actions in CONTROL_GROUPS for action in actions]
        self.selected = 0
        self.control_selected = 0
        self.mode = "main"
        self.waiting_action: str | None = None

    def on_enter(self) -> None:
        self.settings = self.app.settings

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if self.waiting_action:
                self.set_key_binding(event.key)
                continue
            if self.mode == "controls":
                self.handle_control_event(event)
                continue
            if event.key in (self.app.key("menu_next"), pygame.K_DOWN):
                self.selected = (self.selected + 1) % len(self.items)
            elif event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.items)
            elif event.key in (self.app.key("confirm"), pygame.K_RETURN):
                self.activate_main_item()
            elif event.key in (self.app.key("back"), pygame.K_ESCAPE):
                self.app.change_scene("menu")

    def activate_main_item(self) -> None:
        name = self.items[self.selected]
        if name in ("music_enabled", "sfx_enabled"):
            setattr(self.settings, name, not getattr(self.settings, name))
            self.save()
        elif name == "controls":
            self.mode = "controls"
        elif name == "quit":
            self.app.quit()

    def handle_control_event(self, event: pygame.event.Event) -> None:
        if event.key in (self.app.key("menu_next"), pygame.K_DOWN):
            self.control_selected = (self.control_selected + 1) % len(self.control_items)
        elif event.key == pygame.K_UP:
            self.control_selected = (self.control_selected - 1) % len(self.control_items)
        elif event.key in (self.app.key("confirm"), pygame.K_RETURN):
            self.waiting_action = self.control_items[self.control_selected]
        elif event.key == pygame.K_BACKSPACE:
            self.settings.key_bindings = dict(self.app.settings.key_bindings)
            from client.game.input import DEFAULT_KEY_BINDINGS

            self.settings.key_bindings.update(DEFAULT_KEY_BINDINGS)
            self.save()
        elif event.key in (self.app.key("back"), pygame.K_ESCAPE):
            self.mode = "main"

    def set_key_binding(self, key: int) -> None:
        if key in (self.app.key("back"), pygame.K_ESCAPE):
            self.waiting_action = None
            return
        self.settings.key_bindings[self.waiting_action] = key
        self.waiting_action = None
        self.save()

    def save(self) -> None:
        save_settings(self.settings)
        self.app.settings = self.settings
        self.app.audio.apply_settings(self.settings)

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BLACK)
        if self.mode == "controls":
            self.draw_controls(screen)
            return
        self.draw_text(screen, "Options", (80, 70))
        rows = [
            ("Background Music", "ON" if self.settings.music_enabled else "OFF"),
            ("Sound Effects", "ON" if self.settings.sfx_enabled else "OFF"),
            ("Change Controls", ""),
            ("Exit Game", ""),
        ]
        for index, (label, value) in enumerate(rows):
            color = CYAN if index == self.selected else WHITE
            suffix = f": {value}" if value else ""
            surface = self.font.render(f"{'> ' if index == self.selected else '  '}{label}{suffix}", True, color)
            screen.blit(surface, (110, 170 + index * 58))
        hint = self.small_font.render("Enter: Select   Esc: Back", True, GRAY)
        screen.blit(hint, (80, 650))

    def draw_controls(self, screen: pygame.Surface) -> None:
        self.draw_text(screen, "Controls", (80, 70))
        if self.waiting_action:
            label = ACTION_LABELS[self.waiting_action]
            self.draw_text(screen, f"Press a key for {label}", (110, 150), small=True)
            self.draw_text(screen, "Esc: Cancel", (110, 190), small=True)
            return
        y = 125
        for group_name, actions in CONTROL_GROUPS:
            screen.blit(self.small_font.render(group_name, True, GRAY), (110, y))
            y += 30
            for action in actions:
                index = self.control_items.index(action)
                color = CYAN if index == self.control_selected else WHITE
                key_name = pygame.key.name(self.settings.key_bindings[action]).upper()
                label = ACTION_LABELS[action]
                surface = self.small_font.render(
                    f"{'> ' if index == self.control_selected else '  '}{label}: {key_name}",
                    True,
                    color,
                )
                screen.blit(surface, (130, y))
                y += 34
            y += 10
        hint = self.small_font.render("Enter: Change   Backspace: Defaults   Esc: Back", True, GRAY)
        screen.blit(hint, (80, 650))
