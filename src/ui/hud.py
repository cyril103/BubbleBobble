from src.settings import HUD_COLOR, scale_px


def draw_hud(screen, font, score: int, lives: int, level_name: str, message: str) -> None:
    score_surface = font.render(f"{score:06d}", False, HUD_COLOR)
    lives_surface = font.render(f"L{lives}", False, HUD_COLOR)
    level_surface = font.render(level_name.upper(), False, HUD_COLOR)
    message_surface = font.render(message[:32], False, HUD_COLOR)
    screen.blit(score_surface, (scale_px(6), scale_px(5)))
    screen.blit(lives_surface, (screen.get_width() - lives_surface.get_width() - scale_px(6), scale_px(5)))
    screen.blit(level_surface, (scale_px(6), scale_px(14)))
    screen.blit(message_surface, (scale_px(6), screen.get_height() - message_surface.get_height() - scale_px(4)))
