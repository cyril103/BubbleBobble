import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

try:
    import pygame  # noqa: F401
except ModuleNotFoundError:
    class Rect:
        def __init__(self, x: int, y: int, width: int, height: int) -> None:
            self.x = x
            self.y = y
            self.width = width
            self.height = height

        @property
        def size(self) -> tuple[int, int]:
            return self.width, self.height

        @property
        def topleft(self) -> tuple[int, int]:
            return self.x, self.y

    sys.modules["pygame"] = types.SimpleNamespace(Rect=Rect)

from src.level import Level
from src.settings import HEIGHT, WIDTH


class LevelScalingTest(unittest.TestCase):
    def write_level(self, data: dict[str, object]) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "level_01.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_legacy_224x256_level_scales_to_native_resolution(self) -> None:
        level = Level.from_file(
            self.write_level(
                {
                    "name": "Legacy",
                    "player_spawn": [18, 230],
                    "platforms": [[0, 246, 224, 10], [216, 0, 8, 256]],
                    "enemy_spawns": [[104, 8, 1], [120, 16]],
                }
            )
        )

        self.assertEqual((WIDTH, HEIGHT), (672, 768))
        self.assertEqual(level.player_spawn, (54, 690))
        self.assertEqual(level.platforms[0].size, (672, 30))
        self.assertEqual(level.platforms[1].topleft, (648, 0))
        self.assertEqual(level.enemy_spawns, [(312, 24, 1), (360, 48, 1)])

    def test_native_level_metadata_keeps_coordinates_unchanged(self) -> None:
        level = Level.from_file(
            self.write_level(
                {
                    "name": "Native",
                    "native_width": WIDTH,
                    "native_height": HEIGHT,
                    "player_spawn": [54, 690],
                    "platforms": [[0, 738, 672, 30]],
                    "enemy_spawns": [[312, 24, 0]],
                }
            )
        )

        self.assertEqual(level.player_spawn, (54, 690))
        self.assertEqual(level.platforms[0].size, (672, 30))
        self.assertEqual(level.enemy_spawns, [(312, 24, 0)])

    def test_mismatched_native_metadata_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Level.from_file(
                self.write_level(
                    {
                        "name": "Broken metadata",
                        "native_width": WIDTH,
                        "native_height": 256,
                        "player_spawn": [54, 690],
                        "platforms": [[0, 738, 672, 30]],
                        "enemy_spawns": [],
                    }
                )
            )


if __name__ == "__main__":
    unittest.main()
