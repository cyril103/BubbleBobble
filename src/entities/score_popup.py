from dataclasses import dataclass
import pygame
from src.settings import PLAYER_HEIGHT, SCORE_POPUP_LIFETIME



@dataclass
class ScorePopup:
    x: float
    y: float
    text: str
    lifetime: float = SCORE_POPUP_LIFETIME
    age: float = 0.0

    def __post_init__(self) -> None:
        self.start_y = self.y

    def update(self, dt: float) -> bool:
        self.age += dt
        
        # Smoothly rise over the first 0.8 seconds of the popup's lifetime
        rise_duration = 0.8
        t_rise = min(1.0, self.age / rise_duration)
        
        # Quadratic ease-out to slowly decelerate to a complete stop
        ease = 1.0 - (1.0 - t_rise) ** 2
        
        # Stabilize at exactly 2 times the player height
        max_rise = 2 * PLAYER_HEIGHT
        self.y = self.start_y - max_rise * ease
        
        return self.age < self.lifetime


    def draw(self, surface: pygame.Surface, camera, assets) -> None:
        # Calculate alpha: starts at 255, fades out linearly to 0
        alpha = max(0, min(255, int(255 * (1.0 - self.age / self.lifetime))))
        
        # Get standard retro score font
        font = assets.score_font
        
        # Render the text in a vibrant retro arcade yellow
        text_surf = font.render(self.text, True, (255, 255, 80))
        
        # Apply current fade-out opacity
        text_surf.set_alpha(alpha)
        
        # Center the text at the popup's world coordinates
        rect = text_surf.get_rect(center=(round(self.x), round(self.y)))
        
        # Apply camera viewport transformation
        screen_rect = camera.apply_rect(rect)
        
        # Draw onto the surface
        surface.blit(text_surf, screen_rect)
