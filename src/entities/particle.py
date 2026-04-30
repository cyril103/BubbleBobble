from dataclasses import dataclass

import pygame

from src.settings import POP_EFFECT_DURATION


@dataclass
class Particle:
    center: pygame.Vector2
    lifetime: float = POP_EFFECT_DURATION
    age: float = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface, camera, assets) -> None:
        sprite = assets.get_pop_frame(self.age, self.lifetime)
        rect = pygame.Rect(0, 0, 24, 24)
        rect.center = (round(self.center.x), round(self.center.y))
        screen_rect = camera.apply_rect(rect)
        if assets.draw_scaled(surface, sprite, screen_rect):
            return
        pygame.draw.circle(surface, (180, 220, 255), screen_rect.center, 8, width=2)
