from pathlib import Path

import pygame

from src.settings import ASSETS_DIR, ENEMY_DEATH_FRAME_DURATION, ENEMY_HEIGHT, PLAYER_HEIGHT


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
        self.player_animation_frames = self._load_player_animation_frames()
        self.player_death_frames = self._load_player_death_frames() or self._load_sequence("player_death")
        self.bubble_frames = self._load_sequence("bubble_attack")
        self.bubble_animation_frames = self._load_bubble_animation_frames()
        self.enemy_frames = {name: self._load_sequence(name) for name in ENEMY_VARIANTS}
        self.trapped_frames = {name: self._load_sequence(name) for name in TRAPPED_VARIANTS}
        self.zen_chan_frames = self._load_zen_chan_frames()
        self.mighta_frames = self._load_mighta_frames()
        self.pop_frames = self._load_bubble_pop_frames() or self._load_sequence("pop")
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
        if color.a <= 8:
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

    def _load_player_animation_frames(self) -> dict[str, list[pygame.Surface]]:
        animation_dir = ASSETS_DIR / "sprites" / "player_animations"
        sequences = {
            "idle": ["idle"],
            "walk": [f"walk_{index}" for index in range(1, 7)],
            "jump": [f"jump_up_{index}" for index in range(1, 3)],
            "fall": [f"fall_down_{index}" for index in range(1, 3)],
            "attack": [f"bubble_attack_{index}" for index in range(1, 6)],
        }

        loaded: dict[str, list[pygame.Surface]] = {}
        for name, stems in sequences.items():
            frames: list[pygame.Surface] = []
            for stem in stems:
                path = animation_dir / f"{stem}.png"
                if not path.exists():
                    continue

                frame = pygame.image.load(path).convert_alpha()
                self._clear_connected_background(frame)
                frame = self._scale_player_animation_frame(frame)
                frames.append(frame)
            loaded[name] = frames

        return loaded

    def _load_player_death_frames(self) -> list[pygame.Surface]:
        animation_dir = ASSETS_DIR / "sprites" / "player_animations"
        paths = sorted(animation_dir.glob("death*.png"), key=self._frame_number)
        frames: list[pygame.Surface] = []

        for path in paths:
            frame = pygame.image.load(path).convert_alpha()
            self._clear_connected_background(frame)
            frame = self._scale_player_animation_frame(frame)
            frames.append(frame)

        return frames

    def _frame_number(self, path: Path) -> int:
        digits = "".join(char for char in path.stem if char.isdigit())
        return int(digits) if digits else 0

    def _load_bubble_animation_frames(self) -> dict[str, list[pygame.Surface]]:
        animation_dir = ASSETS_DIR / "sprites" / "bobbles_animations"
        sequences = {
            "attack": [
                animation_dir / "bulle_attack_1.png",
                animation_dir / "bulle_attack_2.png",
                animation_dir / "bulle_attack_3.png",
                animation_dir / "bulles" / "bulle_attack4.png",
                animation_dir / "bulles" / "bulle_attack5.png",
                animation_dir / "bulles" / "bulle_attack6.png",
            ],
            "idle": [
                animation_dir / "bulle_idle.png",
                *[animation_dir / f"bulle_idle_{index}.png" for index in range(1, 4)],
            ],
        }

        loaded: dict[str, list[pygame.Surface]] = {}
        for name, paths in sequences.items():
            frames: list[pygame.Surface] = []
            for path in paths:
                if not path.exists():
                    continue

                frame = pygame.image.load(path).convert_alpha()
                self._clear_connected_background(frame)
                frames.append(frame)
            loaded[name] = frames

        return loaded

    def _load_bubble_pop_frames(self) -> list[pygame.Surface]:
        animation_dir = ASSETS_DIR / "sprites" / "bobbles_animations"
        paths = sorted(animation_dir.glob("bubble_explode_*.png"), key=self._frame_number)
        frames: list[pygame.Surface] = []

        for path in paths:
            frame = pygame.image.load(path).convert_alpha()
            self._clear_connected_background(frame)
            frames.append(frame)

        return frames

    def _load_zen_chan_frames(self) -> dict[str, list[pygame.Surface]]:
        animation_dir = ASSETS_DIR / "sprites" / "zen_chan"
        sequences = {
            "walk": sorted(animation_dir.glob("zen-chan[0-9]*.png"), key=self._frame_number),
            "trapped": sorted(animation_dir.glob("zen-chan_trapped*.png"), key=self._frame_number),
            "death": sorted(animation_dir.glob("zen-chan_death*.png"), key=self._frame_number),
        }

        loaded: dict[str, list[pygame.Surface]] = {}
        for name, paths in sequences.items():
            frames: list[pygame.Surface] = []
            for path in paths:
                frame = pygame.image.load(path).convert_alpha()
                self._clear_connected_background(frame)
                frame = self._scale_to_height(frame, ENEMY_HEIGHT)
                frames.append(frame)
            loaded[name] = frames

        return loaded

    def _load_mighta_frames(self) -> dict[str, list[pygame.Surface]]:
        animation_dir = ASSETS_DIR / "sprites" / "mighta"
        sequences = {
            "walk": sorted(animation_dir.glob("mighta_[0-9]*.png"), key=self._frame_number),
            "trapped": sorted(animation_dir.glob("mighta_trapped_*.png"), key=self._frame_number),
            "death": sorted(animation_dir.glob("mighta_death_*.png"), key=self._frame_number),
        }

        loaded: dict[str, list[pygame.Surface]] = {}
        for name, paths in sequences.items():
            frames: list[pygame.Surface] = []
            for path in paths:
                frame = pygame.image.load(path).convert_alpha()
                self._clear_connected_background(frame)
                frame = self._scale_to_height(frame, ENEMY_HEIGHT)
                frames.append(frame)
            loaded[name] = frames

        return loaded

    def _scale_player_animation_frame(self, frame: pygame.Surface) -> pygame.Surface:
        return self._scale_to_height(frame, PLAYER_HEIGHT)

    def _scale_to_height(self, frame: pygame.Surface, target_height: int) -> pygame.Surface:
        width, height = frame.get_size()
        if height <= 0:
            return frame

        target_width = max(1, round(width * (target_height / height)))
        return pygame.transform.scale(frame, (target_width, target_height))

    def _get_player_animation_frame(self, state: str, progress: float | None = None) -> pygame.Surface | None:
        frames = self.player_animation_frames.get(state, [])
        if not frames:
            return None

        frame_duration_ms = {
            "walk": 95,
            "jump": 120,
            "fall": 140,
            "attack": 68,
        }.get(state, 160)

        if len(frames) == 1:
            return frames[0]

        if progress is None:
            index = (pygame.time.get_ticks() // frame_duration_ms) % len(frames)
        else:
            progress = min(0.999, max(0.0, progress))
            index = int(progress * len(frames))
        return frames[index]

    def get_player_frame(self, facing: int, state: str = "idle", progress: float | None = None) -> pygame.Surface | None:
        frame = self._get_player_animation_frame(state, progress)
        if frame is None and state == "attack":
            frame = self._get_player_animation_frame("idle")
        if frame is not None:
            if facing > 0:
                return pygame.transform.flip(frame, True, False)
            return frame

        if not self.player_frames:
            return None

        if state == "walk":
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
        attack_frames = self.bubble_animation_frames.get("attack", [])
        idle_frames = self.bubble_animation_frames.get("idle", [])
        if attack_frames or idle_frames:
            if growth_progress < 1.0 and attack_frames:
                progress = min(0.999, max(0.0, growth_progress))
                index = int(progress * len(attack_frames))
                return attack_frames[index]

            frames = idle_frames or attack_frames
            if len(frames) == 1:
                return frames[0]
            index = (pygame.time.get_ticks() // 160) % len(frames)
            return frames[index]

        if not self.bubble_frames:
            return None

        if len(self.bubble_frames) == 1:
            return self.bubble_frames[0]

        progress = min(0.999, max(0.0, growth_progress))
        index = int(progress * len(self.bubble_frames))
        return self.bubble_frames[index]

    def get_enemy_frame(self, variant: int, trapped: bool, facing: int = -1) -> pygame.Surface | None:
        if variant in (0, 1):
            character_frames = self.zen_chan_frames if variant == 0 else self.mighta_frames
            state = "trapped" if trapped else "walk"
            frames = character_frames.get(state, [])
            if frames:
                frame_duration = 180 if trapped else 130
                index = (pygame.time.get_ticks() // frame_duration) % len(frames)
                frame = frames[index]
                if facing > 0:
                    return pygame.transform.flip(frame, True, False)
                return frame

        if trapped:
            family = TRAPPED_VARIANTS[variant % len(TRAPPED_VARIANTS)]
            frames = self.trapped_frames.get(family, [])
            if not frames:
                return None
            index = (pygame.time.get_ticks() // 180) % len(frames)
            frame = frames[index]
            if facing > 0:
                return pygame.transform.flip(frame, True, False)
            return frame

        family = ENEMY_VARIANTS[variant % len(ENEMY_VARIANTS)]
        frames = self.enemy_frames.get(family, [])
        if not frames:
            return None

        index = (pygame.time.get_ticks() // 220) % len(frames)
        frame = frames[index]
        if facing > 0:
            return pygame.transform.flip(frame, True, False)
        return frame

    def get_enemy_death_frame(self, variant: int, age: float, facing: int = -1) -> pygame.Surface | None:
        if variant in (0, 1):
            character_frames = self.zen_chan_frames if variant == 0 else self.mighta_frames
            frames = character_frames.get("death", [])
            if frames:
                index = int(age / ENEMY_DEATH_FRAME_DURATION) % len(frames)
                frame = frames[index]
                if facing > 0:
                    return pygame.transform.flip(frame, True, False)
                return frame

        return self.get_enemy_frame(variant, trapped=False, facing=facing)

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

    def draw_centered(
        self,
        surface: pygame.Surface,
        sprite: pygame.Surface | None,
        target_rect: pygame.Rect,
    ) -> bool:
        if sprite is None:
            return False

        render_rect = sprite.get_rect(center=target_rect.center)
        surface.blit(sprite, render_rect)
        return True
