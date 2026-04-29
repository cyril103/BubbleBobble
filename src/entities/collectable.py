import math
from dataclasses import dataclass

import pygame

from src.settings import (
    COLLECTABLE_BOUNCE_VELOCITY,
    COLLECTABLE_GRAVITY,
    COLLECTABLE_HORIZONTAL_VELOCITY,
    COLLECTABLE_LIFETIME,
    COLLECTABLE_PICKUP_DELAY,
    COLLECTABLE_SIZE,
    WIDTH,
)


@dataclass
class Collectable:
    x: float
    y: float
    variant: int
    score: int
    kind: str = "fruit"
    lifetime: float = COLLECTABLE_LIFETIME
    age: float = 0.0
    velocity_y: float = COLLECTABLE_BOUNCE_VELOCITY
    launch_direction: int = 1
    pickup_delay: float = COLLECTABLE_PICKUP_DELAY

    def __post_init__(self) -> None:
        self.rect = pygame.Rect(round(self.x), round(self.y), COLLECTABLE_SIZE, COLLECTABLE_SIZE)
        self.on_ground = False
        self.velocity_x = COLLECTABLE_HORIZONTAL_VELOCITY * self.launch_direction

    def update(self, dt: float, platforms: list[pygame.Rect]) -> bool:
        self.age += dt
        self.pickup_delay = max(0.0, self.pickup_delay - dt)

        self.x += self.velocity_x * dt
        self.rect.x = round(self.x)
        self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))
        self.x = float(self.rect.x)

        self.velocity_y += COLLECTABLE_GRAVITY * dt
        previous_bottom = self.rect.bottom
        self.y += self.velocity_y * dt
        self.rect.y = round(self.y)
        self.on_ground = False

        for platform in platforms:
            if self.rect.colliderect(platform) and previous_bottom <= platform.top:
                self.rect.bottom = platform.top
                self.y = float(self.rect.y)
                self.velocity_y = 0.0
                self.velocity_x *= 0.92
                self.on_ground = True
                break

        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface, camera, assets) -> None:
        bob_offset = round(3 * math.sin(self.age * 4.0)) if self.on_ground else 0
        screen_rect = camera.apply_rect(self.rect).move(0, bob_offset)
        sprite = assets.get_collectable_frame(self.variant)
        if assets.draw_scaled(surface, sprite, screen_rect, scale_x=1.15, scale_y=1.15):
            return
        pygame.draw.rect(surface, (255, 220, 120), screen_rect, border_radius=8)
