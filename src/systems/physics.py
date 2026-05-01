import pygame

from src.settings import GRAVITY, WIDTH


def _apply_vertical_physics(entity, dt: float, platforms: list[pygame.Rect]) -> pygame.Rect | None:
    previous_bottom = entity.rect.bottom

    entity.y += entity.velocity_y * dt
    entity.rect.y = round(entity.y)
    entity.on_ground = False
    support_platform = None

    for platform in platforms:
        overlaps_x = entity.rect.right > platform.left and entity.rect.left < platform.right
        lands_on_platform = previous_bottom <= platform.top and entity.rect.bottom >= platform.top
        if overlaps_x and lands_on_platform:
            entity.rect.bottom = platform.top
            entity.y = float(entity.rect.y)
            entity.velocity_y = 0.0
            entity.on_ground = True
            support_platform = platform
            break

    entity.x = float(entity.rect.x)
    entity.y = float(entity.rect.y)
    return support_platform


def move_entity(entity, dt: float, platforms: list[pygame.Rect], gravity: float = GRAVITY) -> pygame.Rect | None:
    entity.velocity_y += gravity * dt

    entity.x += entity.velocity_x * dt
    entity.rect.x = round(entity.x)
    entity.rect.x = max(0, min(entity.rect.x, WIDTH - entity.rect.width))
    entity.x = float(entity.rect.x)

    return _apply_vertical_physics(entity, dt, platforms)


def settle_entity(entity, dt: float, platforms: list[pygame.Rect], gravity: float = GRAVITY) -> pygame.Rect | None:
    entity.velocity_y += gravity * dt
    return _apply_vertical_physics(entity, dt, platforms)
