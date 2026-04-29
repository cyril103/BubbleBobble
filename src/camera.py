import pygame


class Camera:
    def __init__(self) -> None:
        self.offset = pygame.Vector2(0, 0)

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        return rect.move(-round(self.offset.x), -round(self.offset.y))
