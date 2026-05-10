import math

import pygame

from src.settings import (
    BUBBLE_RADIUS,
    BUBBLE_RISE_SPEED,
    ENEMY_COLOR,
    ENEMY_DEATH_ANIMATION_DURATION,
    ENEMY_DEATH_BOUNCE_VELOCITY,
    ENEMY_DEATH_GRAVITY,
    ENEMY_DEATH_HORIZONTAL_VELOCITY,
    ENEMY_HEIGHT,
    ENEMY_SPEED,
    ENEMY_TRAPPED_COLOR,
    ENEMY_WIDTH,
    FPS,
    HEIGHT,
    TRAP_DURATION,
    WIDTH,
)
from src.systems.physics import move_entity, settle_entity
from src.systems.vector_field import VectorField


class Enemy:
    def __init__(self, x: int, y: int, variant: int = 0) -> None:
        self.rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.velocity_x = -ENEMY_SPEED
        self.velocity_y = 0.0
        self.on_ground = False
        self.trapped = False
        self.trap_timer = 0.0
        self.alive = True
        self.variant = variant
        self.dying = False
        self.death_age = 0.0
        self.collectable_ready = False
        self.collectable_launch_origin_x = float(self.rect.centerx)

    @property
    def center(self) -> pygame.Vector2:
        return pygame.Vector2(self.rect.center)

    @property
    def current_radius(self) -> float:
        return float(BUBBLE_RADIUS)

    def _set_center(self, center: pygame.Vector2) -> None:
        self.rect.center = (round(center.x), round(center.y))
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

    def _clamp_trapped_bubble(self) -> None:
        center = self.center
        center.x = max(BUBBLE_RADIUS, min(center.x, WIDTH - BUBBLE_RADIUS))
        center.y = max(BUBBLE_RADIUS, min(center.y, HEIGHT - BUBBLE_RADIUS))
        self._set_center(center)

    def nudge(self, offset: pygame.Vector2) -> None:
        if not self.trapped:
            return
        self._set_center(self.center + offset)
        self._clamp_trapped_bubble()

    def trap(self) -> None:
        self.trapped = True
        self.trap_timer = TRAP_DURATION
        self.velocity_x = 0.0
        self.velocity_y = -BUBBLE_RISE_SPEED

    def release(self) -> None:
        self.trapped = False
        self.velocity_x = ENEMY_SPEED
        self.velocity_y = 0.0

    def start_death(self, launch_origin_x: float | None = None) -> None:
        self.trapped = False
        self.dying = True
        self.death_age = 0.0
        self.collectable_ready = False
        self.collectable_launch_origin_x = (
            float(self.rect.centerx) if launch_origin_x is None else float(launch_origin_x)
        )
        launch_direction = 1 if self.collectable_launch_origin_x <= self.rect.centerx else -1
        self.velocity_x = ENEMY_DEATH_HORIZONTAL_VELOCITY * launch_direction
        self.velocity_y = ENEMY_DEATH_BOUNCE_VELOCITY

    def finish_death(self) -> None:
        self.alive = False
        self.dying = False
        self.collectable_ready = False

    def update(self, dt: float, platforms: list[pygame.Rect], vector_field: VectorField | None = None) -> None:
        if not self.alive:
            return

        if self.dying:
            self.death_age += dt
            support_platform = move_entity(self, dt, platforms, gravity=ENEMY_DEATH_GRAVITY)
            if self.rect.left <= 0 or self.rect.right >= WIDTH:
                self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))
                self.x = float(self.rect.x)
                self.velocity_x *= -1
            self.collectable_ready = support_platform is not None
            return

        if self.trapped:
            self.trap_timer -= dt
            idle_direction = vector_field.direction_at(self.center) if vector_field is not None else pygame.Vector2(0, -1)
            if self.rect.centery <= BUBBLE_RADIUS and idle_direction.y < 0:
                idle_direction.y = 0.0
            if idle_direction.length_squared() > 0:
                idle_velocity = idle_direction.normalize() * BUBBLE_RISE_SPEED
                self.velocity_x = idle_velocity.x
                self.velocity_y = idle_velocity.y
                self._set_center(self.center + idle_velocity * dt)
                self._clamp_trapped_bubble()
            else:
                self.velocity_x = 0.0
                self.velocity_y = 0.0
            if self.trap_timer <= 0:
                self.release()
            return

        support_platform = move_entity(self, dt, platforms)

        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.velocity_x *= -1
            self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))
            self.x = float(self.rect.x)

        if support_platform is not None:
            next_left = self.rect.left + (self.velocity_x / FPS)
            next_right = self.rect.right + (self.velocity_x / FPS)
            if next_left < support_platform.left or next_right > support_platform.right:
                self.velocity_x *= -1

    def settle(self, dt: float, platforms: list[pygame.Rect]) -> None:
        if not self.alive:
            return
        if self.trapped or self.dying:
            return
        settle_entity(self, dt, platforms)

    def draw(self, surface: pygame.Surface, camera, assets) -> None:
        screen_rect = camera.apply_rect(self.rect)
        if self.dying:
            sprite = assets.get_enemy_death_frame(self.variant, self.death_age, self.facing)
            if assets.draw_centered(surface, sprite, screen_rect):
                return
            pygame.draw.rect(surface, ENEMY_COLOR, screen_rect, border_radius=10)
            return

        if self.trapped:
            screen_rect = screen_rect.move(0, round(math.sin(pygame.time.get_ticks() / 140 + self.variant) * 4))
        sprite = assets.get_enemy_frame(self.variant, self.trapped, self.facing)
        if assets.draw_scaled(surface, sprite, screen_rect):
            return
        color = ENEMY_TRAPPED_COLOR if self.trapped else ENEMY_COLOR
        pygame.draw.rect(surface, color, screen_rect, border_radius=10)

    @property
    def facing(self) -> int:
        return 1 if self.velocity_x > 0 else -1
