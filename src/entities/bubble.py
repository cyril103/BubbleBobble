import pygame

from src.settings import (
    BUBBLE_BRAKE_DURATION,
    BUBBLE_CAPTURE_MIN_HORIZONTAL_SPEED,
    BUBBLE_COLOR,
    BUBBLE_LIFETIME,
    BUBBLE_POP_IMPACT_SPEED,
    BUBBLE_RADIUS,
    BUBBLE_RISE_SPEED,
    BUBBLE_SPEED,
    BUBBLE_START_RADIUS,
    HEIGHT,
    WIDTH,
)
from src.systems.vector_field import VectorField


class Bubble:
    def __init__(self, x: int, y: int, direction: int) -> None:
        diameter = BUBBLE_START_RADIUS * 2
        self.rect = pygame.Rect(0, 0, diameter, diameter)
        self.center = pygame.Vector2(x, y)
        self.direction = direction
        self.age = 0.0
        self.growth_progress = 0.0
        self.current_radius = float(BUBBLE_START_RADIUS)
        self.velocity_x = float(BUBBLE_SPEED * direction)
        self.velocity_y = 0.0
        self.blocked_horizontally = False
        self.blocked_at_top = False
        self._sync_rect()

    def _sync_rect(self) -> None:
        diameter = max(2, round(self.current_radius * 2))
        previous_center = (round(self.center.x), round(self.center.y))
        self.rect.size = (diameter, diameter)
        self.rect.center = previous_center

    def _clamp_to_scene(self) -> bool:
        hit_bounds = False

        if self.rect.left < 0:
            self.rect.left = 0
            self.center.x = float(self.rect.centerx)
            self.velocity_x = 0.0
            self.blocked_horizontally = True
            hit_bounds = True
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.center.x = float(self.rect.centerx)
            self.velocity_x = 0.0
            self.blocked_horizontally = True
            hit_bounds = True

        if self.rect.top < 0:
            self.rect.top = 0
            self.center.y = float(self.rect.centery)
            self.velocity_y = 0.0
            self.blocked_at_top = True
            hit_bounds = True
        elif self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
            self.center.y = float(self.rect.centery)
            hit_bounds = True

        return hit_bounds

    def nudge(self, offset: pygame.Vector2) -> None:
        self.center += offset
        self._sync_rect()
        self._clamp_to_scene()

    def update(self, dt: float, vector_field: VectorField | None = None) -> bool:
        self.age += dt
        self.growth_progress = min(1.0, self.age / BUBBLE_BRAKE_DURATION)

        # La bulle garde une bonne vitesse au debut, puis freine fort sur la fin.
        horizontal_factor = max(0.0, 1.0 - self.growth_progress**4)
        if self.blocked_horizontally:
            self.velocity_x = 0.0
        else:
            self.velocity_x = self.direction * BUBBLE_SPEED * horizontal_factor
        self.center.x += self.velocity_x * dt

        eased_growth = 1.0 - (1.0 - self.growth_progress) ** 3
        self.current_radius = BUBBLE_START_RADIUS + (BUBBLE_RADIUS - BUBBLE_START_RADIUS) * eased_growth

        if self.growth_progress >= 1.0:
            idle_direction = vector_field.direction_at(self.center) if vector_field is not None else pygame.Vector2(0, -1)
            if self.blocked_at_top and idle_direction.y < 0:
                idle_direction.y = 0.0
            idle_velocity = idle_direction * BUBBLE_RISE_SPEED
            self.velocity_x = idle_velocity.x
            self.velocity_y = idle_velocity.y
            self.center.x += self.velocity_x * dt
            self.center.y += self.velocity_y * dt
        else:
            self.velocity_y = 0.0

        impact_speed = pygame.Vector2(self.velocity_x, self.velocity_y).length()
        self._sync_rect()
        hit_bounds = self._clamp_to_scene()
        if hit_bounds and impact_speed >= BUBBLE_POP_IMPACT_SPEED:
            return False

        expired = self.age >= BUBBLE_LIFETIME
        return not expired

    def can_capture_enemy(self) -> bool:
        return abs(self.velocity_x) >= BUBBLE_CAPTURE_MIN_HORIZONTAL_SPEED and abs(self.velocity_x) > abs(self.velocity_y)

    def draw(self, surface: pygame.Surface, camera, assets) -> None:
        screen_rect = camera.apply_rect(self.rect)
        sprite = assets.get_bubble_frame(self.growth_progress)
        if assets.draw_scaled(surface, sprite, screen_rect):
            return
        pygame.draw.ellipse(surface, BUBBLE_COLOR, screen_rect, width=3)
