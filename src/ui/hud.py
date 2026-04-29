from src.settings import HUD_COLOR


def draw_hud(screen, font, score: int, lives: int, level_name: str, message: str) -> None:
    score_surface = font.render(f"Score: {score}", False, HUD_COLOR)
    lives_surface = font.render(f"Vies: {lives}", False, HUD_COLOR)
    level_surface = font.render(f"Niveau: {level_name}", False, HUD_COLOR)
    message_surface = font.render(message, False, HUD_COLOR)
    screen.blit(score_surface, (20, 16))
    screen.blit(lives_surface, (20, 38))
    screen.blit(level_surface, (20, 60))
    screen.blit(message_surface, (20, 84))
