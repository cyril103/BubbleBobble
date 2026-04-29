import pygame

from src.settings import PLAYER_COLOR, PLAYER_HEIGHT, PLAYER_JUMP_VELOCITY, PLAYER_SPEED, PLAYER_WIDTH
from src.systems.input import get_horizontal_intent
from src.systems.physics import move_entity, settle_entity


class Player:
    def __init__(self, spawn_x: int, spawn_y: int) -> None:
        self.rect = pygame.Rect(spawn_x, spawn_y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = False
        self.facing = 1

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        horizontal = get_horizontal_intent(keys)
        self.velocity_x = horizontal * PLAYER_SPEED

        if horizontal != 0:
            self.facing = horizontal

    def jump(self) -> None:
        if self.on_ground:
            self.velocity_y = PLAYER_JUMP_VELOCITY
            self.on_ground = False

    def update(self, dt: float, platforms: list[pygame.Rect]) -> None:
        move_entity(self, dt, platforms)

    def settle(self, dt: float, platforms: list[pygame.Rect]) -> None:
        self.velocity_x = 0.0
        settle_entity(self, dt, platforms)

    def draw(self, surface: pygame.Surface, camera, assets, invulnerable: bool = False) -> None:
        if invulnerable and (pygame.time.get_ticks() // 90) % 2 == 1:
            return

        screen_rect = camera.apply_rect(self.rect)
        sprite = assets.get_player_frame(self.facing, moving=abs(self.velocity_x) > 0.0)
        if assets.draw_scaled(surface, sprite, screen_rect, scale_x=1.55, scale_y=1.35):
            return
        pygame.draw.rect(surface, PLAYER_COLOR, screen_rect, border_radius=8)
