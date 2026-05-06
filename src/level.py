import json
from dataclasses import dataclass
from pathlib import Path

import pygame

from src.settings import BASE_HEIGHT, BASE_WIDTH, HEIGHT, WIDTH, NATIVE_RESOLUTION_SCALE


@dataclass
class Level:
    name: str
    player_spawn: tuple[int, int]
    platforms: list[pygame.Rect]
    enemy_spawns: list[tuple[int, int, int]]

    @classmethod
    def from_file(cls, path: Path) -> "Level":
        data = json.loads(path.read_text(encoding="utf-8"))
        coordinate_scale = _coordinate_scale(data)
        platforms = [pygame.Rect(*_scale_values(platform, coordinate_scale)) for platform in data["platforms"]]
        enemy_spawns: list[tuple[int, int, int]] = []
        for index, spawn in enumerate(data["enemy_spawns"]):
            x, y = spawn[:2]
            variant = spawn[2] if len(spawn) >= 3 else index
            enemy_spawns.append((*_scale_point((x, y), coordinate_scale), variant))
        return cls(
            name=data["name"],
            player_spawn=_scale_point(data["player_spawn"], coordinate_scale),
            platforms=platforms,
            enemy_spawns=enemy_spawns,
        )


def _coordinate_scale(data: dict[str, object]) -> float:
    native_width = data.get("native_width")
    native_height = data.get("native_height")
    if _is_positive_number(native_width):
        width_scale = WIDTH / native_width
        if _is_positive_number(native_height):
            height_scale = HEIGHT / native_height
            if round(width_scale, 6) != round(height_scale, 6):
                raise ValueError(
                    "Les dimensions natives du niveau ne correspondent pas "
                    f"au ratio attendu: {native_width}x{native_height}."
                )
        return width_scale

    if _looks_like_legacy_level(data):
        return NATIVE_RESOLUTION_SCALE

    return 1.0


def _is_positive_number(value: object) -> bool:
    return isinstance(value, int | float) and value > 0


def _looks_like_legacy_level(data: dict[str, object]) -> bool:
    platforms = data.get("platforms", [])
    if not isinstance(platforms, list):
        return False

    max_right = 0
    max_bottom = 0
    for platform in platforms:
        if not isinstance(platform, list | tuple) or len(platform) < 4:
            continue
        x, y, width, height = platform[:4]
        max_right = max(max_right, int(x) + int(width))
        max_bottom = max(max_bottom, int(y) + int(height))

    return max_right <= BASE_WIDTH and max_bottom <= BASE_HEIGHT and (WIDTH, HEIGHT) != (BASE_WIDTH, BASE_HEIGHT)


def _scale_values(values: list[int] | tuple[int, ...], coordinate_scale: float) -> tuple[int, ...]:
    return tuple(round(value * coordinate_scale) for value in values)


def _scale_point(values: list[int] | tuple[int, int], coordinate_scale: float) -> tuple[int, int]:
    x, y = values[:2]
    return round(x * coordinate_scale), round(y * coordinate_scale)


def discover_level_paths(levels_dir: Path) -> list[Path]:
    return sorted(levels_dir.glob("level_*.json"))
