import pygame

from src.settings import HUD_COLOR
from src.ui.menu import Menu


def draw_overlay(screen: pygame.Surface, title_font, body_font, title: str, lines: list[str]) -> None:
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((5, 8, 14, 180))
    screen.blit(overlay, (0, 0))

    title_surface = title_font.render(title, False, HUD_COLOR)
    title_x = Menu.center_x(screen, title_surface.get_width())
    screen.blit(title_surface, (title_x, 78))

    y = 120
    for line in lines:
        line_surface = body_font.render(line, False, HUD_COLOR)
        line_x = Menu.center_x(screen, line_surface.get_width())
        screen.blit(line_surface, (line_x, y))
        y += body_font.get_height() + 6


def draw_title_screen(screen: pygame.Surface, title_font, body_font, blink_on: bool) -> None:
    title = title_font.render("BUBBLE DUNGEON", False, HUD_COLOR)
    subtitle = body_font.render("ARCADE PROTOTYPE", False, HUD_COLOR)
    prompt = body_font.render("PRESS ENTER", False, HUD_COLOR)
    controls = [
        "A-D / LEFT-RIGHT  MOVE",
        "SPACE / W / UP    JUMP",
        "F / CTRL          BUBBLE",
    ]

    title_x = Menu.center_x(screen, title.get_width())
    subtitle_x = Menu.center_x(screen, subtitle.get_width())
    screen.blit(title, (title_x, 66))
    screen.blit(subtitle, (subtitle_x, 93))

    if blink_on:
        prompt_x = Menu.center_x(screen, prompt.get_width())
        screen.blit(prompt, (prompt_x, 132))

    y = 172
    for line in controls:
        rendered = body_font.render(line, False, HUD_COLOR)
        screen.blit(rendered, (Menu.center_x(screen, rendered.get_width()), y))
        y += body_font.get_height() + 5


def draw_ready_overlay(screen: pygame.Surface, title_font, body_font, level_name: str) -> None:
    title_surface = title_font.render("READY", False, HUD_COLOR)
    subtitle_surface = body_font.render(level_name.upper(), False, HUD_COLOR)

    screen.blit(title_surface, (Menu.center_x(screen, title_surface.get_width()), 92))
    screen.blit(subtitle_surface, (Menu.center_x(screen, subtitle_surface.get_width()), 124))
