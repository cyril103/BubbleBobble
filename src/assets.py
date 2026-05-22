from dataclasses import dataclass
from pathlib import Path
import re

import pygame

from src.settings import ASSETS_DIR, ENEMY_DEATH_FRAME_DURATION, ENEMY_HEIGHT, PLAYER_HEIGHT


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


@dataclass(frozen=True)
class CollectableItem:
    name: str
    score: int
    frame: pygame.Surface


class AssetManager:
    def __init__(self) -> None:
        self.font_path = ASSETS_DIR / "fonts" / "emulogic.ttf"
        self.hud_font = self._load_font(15, fallback_size=24)
        self.title_font = self._load_font(30, fallback_size=48)
        self.overlay_font = self._load_font(18, fallback_size=27)
        self.score_font = self._load_font(30, fallback_size=45)



        self.player_animation_frames = self._load_player_animation_frames()
        self.player_death_frames = self._load_player_death_frames()
        self.bubble_animation_frames = self._load_bubble_animation_frames()
        self.enemy_frames: dict[str, list[pygame.Surface]] = {}
        self.trapped_frames: dict[str, list[pygame.Surface]] = {}
        self.zen_chan_frames = self._load_zen_chan_frames()
        self.mighta_frames = self._load_mighta_frames()
        self.pop_frames = self._load_bubble_pop_frames()
        self.collectable_items = self._load_collectable_items()
        self.collectable_frames = [item.frame for item in self.collectable_items]

    def _load_font(self, size: int, fallback_size: int) -> pygame.font.Font:
        if self.font_path.exists():
            return pygame.font.Font(self.font_path, size)
        return pygame.font.SysFont("consolas", fallback_size)

    def _is_connected_background_pixel(self, color: pygame.Color) -> bool:
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

            if not self._is_connected_background_pixel(surface.get_at((x, y))):
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

    def _load_collectable_items(self) -> list[CollectableItem]:
        items_dir = ASSETS_DIR / "sprites" / "items"
        items: list[CollectableItem] = []

        for path in sorted(items_dir.glob("*.png")):
            match = re.search(r"_(\d+)$", path.stem)
            if match is None:
                continue

            frame = pygame.image.load(path).convert_alpha()
            self._clear_connected_background(frame)
            items.append(CollectableItem(path.stem[: match.start()], int(match.group(1)), frame))

        return sorted(items, key=lambda item: item.score)

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

        return None

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

        return None

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
        if not self.collectable_frames:
            return None
        return self.collectable_frames[variant % len(self.collectable_frames)]

    def get_collectable_score(self, variant: int) -> int:
        if not self.collectable_items:
            return 0
        item = self.collectable_items[variant % len(self.collectable_items)]
        return item.score

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
