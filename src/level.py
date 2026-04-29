import json
from dataclasses import dataclass
from pathlib import Path

import pygame


@dataclass
class Level:
    name: str
    player_spawn: tuple[int, int]
    platforms: list[pygame.Rect]
    enemy_spawns: list[tuple[int, int]]

    @classmethod
    def from_file(cls, path: Path) -> "Level":
        data = json.loads(path.read_text(encoding="utf-8"))
        platforms = [pygame.Rect(*platform) for platform in data["platforms"]]
        enemy_spawns = [tuple(spawn) for spawn in data["enemy_spawns"]]
        return cls(
            name=data["name"],
            player_spawn=tuple(data["player_spawn"]),
            platforms=platforms,
            enemy_spawns=enemy_spawns,
        )


def discover_level_paths(levels_dir: Path) -> list[Path]:
    return sorted(levels_dir.glob("level_*.json"))
