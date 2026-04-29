import pygame


def get_horizontal_intent(keys: pygame.key.ScancodeWrapper) -> int:
    direction = 0

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        direction -= 1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        direction += 1

    return direction
