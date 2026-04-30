from pathlib import Path

import pygame

from src.settings import ASSETS_DIR


SPRITE_LAYOUT = {
    "player": [
        (6, 16, 16, 16),
        (27, 16, 16, 16),
        (48, 16, 16, 16),
        (70, 16, 15, 16),
    ],
    "bubble_attack": [
        (7, 1050, 14, 16),
        (25, 1050, 14, 16),
        (7, 1072, 14, 16),
        (25, 1072, 14, 16),
    ],
    "player_death": [
        (6, 89, 13, 16),
        (26, 89, 15, 16),
        (46, 89, 15, 16),
        (65, 89, 14, 16),
        (85, 89, 14, 16),
        (104, 89, 14, 16),
        (123, 89, 14, 16),
        (145, 89, 14, 16),
        (169, 89, 14, 16),
        (194, 89, 14, 16),
        (230, 92, 14, 13),
        (249, 96, 14, 9),
        (266, 98, 14, 7),
    ],
    "enemy_red": [
        (24, 245, 15, 16),
        (62, 245, 16, 16),
    ],
    "enemy_yellow": [
        (5, 278, 16, 16),
        (24, 278, 16, 16),
    ],
    "enemy_purple": [
        (6, 333, 16, 15),
        (27, 333, 16, 15),
    ],
    "enemy_blue": [
        (6, 363, 16, 16),
        (26, 363, 16, 16),
    ],
    "enemy_ghost": [
        (6, 425, 16, 16),
        (27, 425, 16, 16),
    ],
    "enemy_orange": [
        (9, 507, 15, 16),
        (28, 507, 15, 16),
    ],
    "trapped_red": [
        (283, 245, 16, 16),
        (303, 245, 16, 16),
        (321, 245, 16, 16),
    ],
    "trapped_yellow": [
        (215, 278, 16, 16),
        (236, 278, 16, 16),
        (256, 278, 16, 16),
    ],
    "trapped_purple": [
        (245, 333, 16, 15),
        (268, 333, 14, 16),
        (286, 333, 14, 16),
    ],
    "trapped_blue": [
        (286, 363, 16, 15),
        (306, 363, 15, 16),
        (326, 363, 14, 16),
    ],
    "trapped_ghost": [
        (217, 425, 14, 16),
        (235, 425, 14, 16),
        (253, 425, 14, 16),
    ],
    "trapped_orange": [
        (87, 529, 14, 16),
        (105, 529, 14, 16),
        (123, 529, 14, 16),
    ],
    "pop": [
        (29, 1188, 8, 10),
        (42, 1187, 10, 12),
        (57, 1186, 12, 14),
        (74, 1185, 14, 16),
    ],
    "powerups": [
        (501, 975, 11, 14),
        (515, 975, 11, 14),
        (529, 975, 11, 14),
        (543, 975, 11, 14),
    ],
    "fruit_bonus": [
        (8, 806, 15, 16),
        (27, 804, 14, 18),
        (47, 803, 13, 19),
        (66, 803, 15, 19),
        (86, 804, 16, 18),
        (209, 803, 16, 19),
    ],
}

ENEMY_VARIANTS = (
    "enemy_red",
    "enemy_yellow",
    "enemy_purple",
    "enemy_blue",
    "enemy_ghost",
    "enemy_orange",
)

TRAPPED_VARIANTS = (
    "trapped_red",
    "trapped_yellow",
    "trapped_purple",
    "trapped_blue",
    "trapped_ghost",
    "trapped_orange",
)


class AssetManager:
    def __init__(self) -> None:
        self.font_path = ASSETS_DIR / "fonts" / "emulogic.ttf"
        self.hud_font = self._load_font(5, fallback_size=8)
        self.title_font = self._load_font(10, fallback_size=16)
        self.overlay_font = self._load_font(6, fallback_size=9)

        self.sprite_sheet_path = self._find_sprite_sheet()
        self.sprite_sheet = self._load_sprite_sheet(self.sprite_sheet_path)
        self.player_frames = self._load_sequence("player")
        self.player_death_frames = self._load_sequence("player_death")
        self.bubble_frames = self._load_sequence("bubble_attack")
        self.enemy_frames = {name: self._load_sequence(name) for name in ENEMY_VARIANTS}
        self.trapped_frames = {name: self._load_sequence(name) for name in TRAPPED_VARIANTS}
        self.pop_frames = self._load_sequence("pop")
        self.fruit_bonus_frames = self._load_sequence("fruit_bonus")
        self.powerup_frames = self._load_sequence("powerups")

    def _load_font(self, size: int, fallback_size: int) -> pygame.font.Font:
        if self.font_path.exists():
            return pygame.font.Font(self.font_path, size)
        return pygame.font.SysFont("consolas", fallback_size)

    def _find_sprite_sheet(self) -> Path | None:
        sprites_dir = ASSETS_DIR / "sprites"
        preferred_sheet = sprites_dir / "sprites.png"
        if preferred_sheet.exists():
            return preferred_sheet

        candidates = [path for path in sprites_dir.glob("*.png") if not path.name.startswith("_")]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)

    def _load_sprite_sheet(self, path: Path | None) -> pygame.Surface | None:
        if path is None:
            return None
        return pygame.image.load(path).convert_alpha()

    def _crop_sprite(self, rect: tuple[int, int, int, int]) -> pygame.Surface | None:
        if self.sprite_sheet is None:
            return None

        x, y, width, height = rect
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.blit(self.sprite_sheet, (0, 0), pygame.Rect(x, y, width, height))
        self._clear_connected_background(surface)
        return surface

    def _is_sheet_background_pixel(self, color: pygame.Color) -> bool:
        if color.a == 0:
            return True

        channels = (color.r, color.g, color.b)
        is_neutral = max(channels) - min(channels) <= 18
        return is_neutral and max(channels) <= 90

    def _clear_connected_background(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        visited: set[tuple[int, int]] = set()
        stack: list[tuple[int, int]] = []

        for x in range(width):
            stack.append((x, 0))
            stack.append((x, height - 1))
        for y in range(height):
            stack.append((0, y))
            stack.append((width - 1, y))

        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            if not self._is_sheet_background_pixel(surface.get_at((x, y))):
                continue

            surface.set_at((x, y), (0, 0, 0, 0))

            if x > 0:
                stack.append((x - 1, y))
            if x < width - 1:
                stack.append((x + 1, y))
            if y > 0:
                stack.append((x, y - 1))
            if y < height - 1:
                stack.append((x, y + 1))

    def _load_sequence(self, name: str) -> list[pygame.Surface]:
        frames: list[pygame.Surface] = []
        for rect in SPRITE_LAYOUT.get(name, []):
            sprite = self._crop_sprite(rect)
            if sprite is not None:
                frames.append(sprite)
        return frames

    def get_player_frame(self, facing: int, moving: bool) -> pygame.Surface | None:
        if not self.player_frames:
            return None

        if moving:
            index = (pygame.time.get_ticks() // 140) % len(self.player_frames)
        else:
            index = 0

        frame = self.player_frames[index]
        if facing > 0:
            return pygame.transform.flip(frame, True, False)
        return frame

    def get_player_death_frame(self, progress: float, facing: int) -> pygame.Surface | None:
        if not self.player_death_frames:
            return None

        progress = min(0.999, max(0.0, progress))
        index = int(progress * len(self.player_death_frames))
        frame = self.player_death_frames[index]
        if facing > 0:
            return pygame.transform.flip(frame, True, False)
        return frame

    def get_bubble_frame(self, growth_progress: float) -> pygame.Surface | None:
        if not self.bubble_frames:
            return None

        if len(self.bubble_frames) == 1:
            return self.bubble_frames[0]

        progress = min(0.999, max(0.0, growth_progress))
        index = int(progress * len(self.bubble_frames))
        return self.bubble_frames[index]

    def get_enemy_frame(self, variant: int, trapped: bool) -> pygame.Surface | None:
        if trapped:
            family = TRAPPED_VARIANTS[variant % len(TRAPPED_VARIANTS)]
            frames = self.trapped_frames.get(family, [])
            if not frames:
                return None
            index = (pygame.time.get_ticks() // 180) % len(frames)
            return frames[index]

        family = ENEMY_VARIANTS[variant % len(ENEMY_VARIANTS)]
        frames = self.enemy_frames.get(family, [])
        if not frames:
            return None

        index = (pygame.time.get_ticks() // 220) % len(frames)
        return frames[index]

    def get_collectable_frame(self, variant: int) -> pygame.Surface | None:
        if not self.fruit_bonus_frames:
            return None
        return self.fruit_bonus_frames[variant % len(self.fruit_bonus_frames)]

    def get_pop_frame(self, age: float, lifetime: float) -> pygame.Surface | None:
        if not self.pop_frames:
            return None
        if len(self.pop_frames) == 1:
            return self.pop_frames[0]

        progress = min(0.999, max(0.0, age / lifetime))
        index = int(progress * len(self.pop_frames))
        return self.pop_frames[index]

    def draw_scaled(
        self,
        surface: pygame.Surface,
        sprite: pygame.Surface | None,
        target_rect: pygame.Rect,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
    ) -> bool:
        if sprite is None:
            return False

        width = max(1, round(target_rect.width * scale_x))
        height = max(1, round(target_rect.height * scale_y))
        scaled = pygame.transform.scale(sprite, (width, height))
        render_rect = scaled.get_rect(center=target_rect.center)
        surface.blit(scaled, render_rect)
        return True
