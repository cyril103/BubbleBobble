import pygame

from src.settings import (
    PLAYER_COLOR,
    PLAYER_ATTACK_ANIMATION_DURATION,
    PLAYER_COYOTE_TIME,
    PLAYER_HEIGHT,
    PLAYER_JUMP_BUFFER_DURATION,
    PLAYER_JUMP_VELOCITY,
    PLAYER_SPEED,
    PLAYER_WIDTH,
)
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
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0
        self.attack_animation_timer = 0.0

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        horizontal = get_horizontal_intent(keys)
        self.velocity_x = horizontal * PLAYER_SPEED

        if horizontal != 0:
            self.facing = horizontal

    def jump(self) -> None:
        self.jump_buffer_timer = PLAYER_JUMP_BUFFER_DURATION

    def play_attack_animation(self) -> None:
        self.attack_animation_timer = PLAYER_ATTACK_ANIMATION_DURATION

    def _consume_jump_if_possible(self) -> None:
        if self.jump_buffer_timer <= 0 or self.coyote_timer <= 0:
            return

        self.velocity_y = PLAYER_JUMP_VELOCITY
        self.on_ground = False
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0

    def update(self, dt: float, platforms: list[pygame.Rect]) -> None:
        self.attack_animation_timer = max(0.0, self.attack_animation_timer - dt)
        self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        if self.on_ground:
            self.coyote_timer = PLAYER_COYOTE_TIME
        else:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        self._consume_jump_if_possible()
        move_entity(self, dt, platforms)

        if self.on_ground:
            self.coyote_timer = PLAYER_COYOTE_TIME
            self._consume_jump_if_possible()

    def settle(self, dt: float, platforms: list[pygame.Rect]) -> None:
        self.attack_animation_timer = max(0.0, self.attack_animation_timer - dt)
        self.velocity_x = 0.0
        self.jump_buffer_timer = 0.0
        self.coyote_timer = PLAYER_COYOTE_TIME if self.on_ground else 0.0
        settle_entity(self, dt, platforms)

    def draw(self, surface: pygame.Surface, camera, assets, invulnerable: bool = False) -> None:
        if invulnerable and (pygame.time.get_ticks() // 90) % 2 == 1:
            return

        screen_rect = camera.apply_rect(self.rect)
        sprite = assets.get_player_frame(self.facing, self.animation_state(), self.animation_progress())
        if assets.draw_centered(surface, sprite, screen_rect):
            return
        pygame.draw.rect(surface, PLAYER_COLOR, screen_rect, border_radius=8)

    def animation_state(self) -> str:
        if self.attack_animation_timer > 0:
            return "attack"
        if not self.on_ground and self.velocity_y < 0:
            return "jump"
        if not self.on_ground and self.velocity_y > 0:
            return "fall"
        if abs(self.velocity_x) > 0.0:
            return "walk"
        return "idle"

    def animation_progress(self) -> float | None:
        if self.attack_animation_timer <= 0:
            return None
        return 1.0 - (self.attack_animation_timer / PLAYER_ATTACK_ANIMATION_DURATION)

    def draw_death(self, surface: pygame.Surface, camera, assets, progress: float) -> None:
        screen_rect = camera.apply_rect(self.rect)
        sprite = assets.get_player_death_frame(progress, self.facing)
        if assets.draw_scaled(surface, sprite, screen_rect):
            return
        pygame.draw.rect(surface, PLAYER_COLOR, screen_rect, border_radius=8)
