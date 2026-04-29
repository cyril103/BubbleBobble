from pathlib import Path

import pygame

from src.settings import ASSETS_DIR


SPRITE_LAYOUT = {
    "player": [
        (21, 89, 159, 174),
        (207, 89, 148, 174),
        (381, 94, 138, 169),
        (546, 90, 135, 173),
    ],
    "bubble_attack": [
        (735, 171, 41, 41),
        (824, 152, 70, 71),
        (935, 123, 102, 103),
        (1082, 89, 143, 142),
    ],
    "enemy_red": [
        (37, 356, 166, 140),
        (235, 354, 168, 143),
    ],
    "enemy_yellow": [
        (466, 362, 166, 128),
        (642, 362, 136, 132),
    ],
    "enemy_purple": [
        (840, 360, 149, 133),
        (1028, 357, 152, 132),
    ],
    "enemy_blue": [
        (42, 537, 154, 136),
        (241, 537, 153, 138),
    ],
    "enemy_ghost": [
        (479, 541, 144, 134),
        (642, 541, 136, 134),
    ],
    "enemy_orange": [
        (841, 537, 169, 141),
        (1032, 537, 173, 141),
    ],
    "trapped": [
        (21, 788, 143, 153),
        (175, 788, 142, 153),
        (330, 790, 141, 151),
        (483, 788, 144, 153),
    ],
    "pop": [
        (30, 1049, 118, 121),
        (185, 1056, 102, 113),
        (253, 1053, 200, 97),
        (506, 1044, 116, 125),
    ],
    "powerups": [
        (657, 1054, 143, 115),
        (834, 1054, 119, 122),
        (972, 1051, 121, 125),
        (1106, 1045, 123, 127),
    ],
    "fruit_bonus": [
        (657, 823, 96, 94),
        (758, 822, 90, 98),
        (854, 827, 91, 96),
        (962, 830, 93, 92),
        (1064, 827, 83, 85),
        (1155, 814, 78, 111),
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


class AssetManager:
    def __init__(self) -> None:
        self.font_path = ASSETS_DIR / "fonts" / "emulogic.ttf"
        self.hud_font = self._load_font(14, fallback_size=20)
        self.title_font = self._load_font(24, fallback_size=40)
        self.overlay_font = self._load_font(14, fallback_size=20)

        self.sprite_sheet_path = self._find_sprite_sheet()
        self.sprite_sheet = self._load_sprite_sheet(self.sprite_sheet_path)
        self.player_frames = self._load_sequence("player")
        self.bubble_frames = self._load_sequence("bubble_attack")
        self.enemy_frames = {name: self._load_sequence(name) for name in ENEMY_VARIANTS}
        self.trapped_frames = self._load_sequence("trapped")
        self.pop_frames = self._load_sequence("pop")
        self.fruit_bonus_frames = self._load_sequence("fruit_bonus")
        self.powerup_frames = self._load_sequence("powerups")

    def _load_font(self, size: int, fallback_size: int) -> pygame.font.Font:
        if self.font_path.exists():
            return pygame.font.Font(self.font_path, size)
        return pygame.font.SysFont("consolas", fallback_size)

    def _find_sprite_sheet(self) -> Path | None:
        sprites_dir = ASSETS_DIR / "sprites"
        candidates = [path for path in sprites_dir.glob("*.png") if not path.name.startswith("_")]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_size)

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
        return surface

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
        if facing < 0:
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
            if not self.trapped_frames:
                return None
            return self.trapped_frames[variant % len(self.trapped_frames)]

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
