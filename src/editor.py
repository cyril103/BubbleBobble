import json
from dataclasses import dataclass
from pathlib import Path

import pygame

from src.assets import AssetManager
from src.assets import ENEMY_VARIANTS
from src.camera import Camera
from src.entities.enemy import Enemy
from src.entities.player import Player
from src.level import Level, discover_level_paths
from src.settings import (
    BACKGROUND_COLOR,
    ENEMY_HEIGHT,
    ENEMY_WIDTH,
    FPS,
    HEIGHT,
    LEVELS_DIR,
    PLATFORM_COLOR,
    PLAYER_HEIGHT,
    PLAYER_WIDTH,
    WIDTH,
    WINDOW_SCALE,
)


GRID_SIZE = 8
PANEL_HEIGHT = 72
EDITOR_WIDTH = WIDTH
EDITOR_HEIGHT = HEIGHT + PANEL_HEIGHT
HANDLE_SIZE = 6
PALETTE_CELL_SIZE = 22
PALETTE_TOP = HEIGHT + 47

GRID_COLOR = (42, 47, 62)
TEXT_COLOR = (240, 244, 248)
MUTED_TEXT_COLOR = (168, 178, 190)
SELECTED_COLOR = (255, 220, 120)
PLAYER_MARKER_COLOR = (245, 196, 87)
ENEMY_MARKER_COLOR = (221, 95, 98)
PANEL_COLOR = (18, 21, 31)
SAVE_FLASH_COLOR = (88, 210, 150)


@dataclass
class EditableLevel:
    path: Path
    name: str
    player_spawn: tuple[int, int]
    platforms: list[pygame.Rect]
    enemy_spawns: list[tuple[int, int, int]]

    @classmethod
    def from_path(cls, path: Path) -> "EditableLevel":
        level = Level.from_file(path)
        return cls(
            path=path,
            name=level.name,
            player_spawn=level.player_spawn,
            platforms=[platform.copy() for platform in level.platforms],
            enemy_spawns=list(level.enemy_spawns),
        )

    def to_json_data(self) -> dict[str, object]:
        return {
            "name": self.name,
            "player_spawn": list(self.player_spawn),
            "platforms": [[rect.x, rect.y, rect.width, rect.height] for rect in self.platforms],
            "enemy_spawns": [[x, y, variant] for x, y, variant in self.enemy_spawns],
        }

    def save(self) -> None:
        content = json.dumps(self.to_json_data(), indent=2, ensure_ascii=True)
        self.path.write_text(content + "\n", encoding="utf-8")


class LevelEditor:
    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((EDITOR_WIDTH * WINDOW_SCALE, EDITOR_HEIGHT * WINDOW_SCALE))
        self.canvas = pygame.Surface((EDITOR_WIDTH, EDITOR_HEIGHT))
        pygame.display.set_caption("Bubble Dungeon - Level Editor")
        self.clock = pygame.time.Clock()
        self.assets = AssetManager()
        self.camera = Camera()
        self.font = self.assets._load_font(5, fallback_size=8)
        self.small_font = self.assets._load_font(4, fallback_size=7)

        self.level_paths = discover_level_paths(LEVELS_DIR)
        if not self.level_paths:
            raise RuntimeError("Aucun fichier de niveau trouve dans levels/.")

        self.level_index = 0
        self.level = EditableLevel.from_path(self.level_paths[self.level_index])
        self.dirty = False
        self.running = True
        self.mode = "platform"
        self.selected_platform_index: int | None = None
        self.selected_enemy_index: int | None = None
        self.drag_action: str | None = None
        self.drag_offset = pygame.Vector2()
        self.drag_start = pygame.Vector2()
        self.drag_origin_rect: pygame.Rect | None = None
        self.save_flash_timer = 0.0
        self.selected_enemy_variant = 0
        self.message = "1 Plateformes  2 Joueur  3 Ennemis"

    def run(self) -> int:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        return 0

    def update(self, dt: float) -> None:
        self.save_flash_timer = max(0.0, self.save_flash_timer - dt)

    def load_level(self, index: int, *, force: bool = False) -> None:
        if self.dirty and not force:
            self.message = "Sauvegarde avec Ctrl+S ou recharge avec Ctrl+R avant de changer de niveau"
            return

        self.level_index = index % len(self.level_paths)
        self.level = EditableLevel.from_path(self.level_paths[self.level_index])
        self.dirty = False
        self.clear_selection()
        self.message = f"Niveau charge: {self.level.path.name}"

    def save_level(self) -> None:
        self.level.save()
        self.dirty = False
        self.save_flash_timer = 1.2
        self.message = f"Sauvegarde: {self.level.path.name}"

    def reload_level(self) -> None:
        self.load_level(self.level_index, force=True)
        self.message = f"Niveau recharge: {self.level.path.name}"

    def mark_dirty(self, message: str | None = None) -> None:
        self.dirty = True
        if message is not None:
            self.message = message

    def clear_selection(self) -> None:
        self.selected_platform_index = None
        self.selected_enemy_index = None
        self.drag_action = None
        self.drag_origin_rect = None

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.clear_selection()
        names = {"platform": "Plateformes", "player": "Joueur", "enemy": "Ennemis"}
        self.message = f"Mode: {names[mode]}"

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_down(event, self.to_editor_pos(event.pos))
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event, self.to_editor_pos(event.pos))
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handle_mouse_up(event)

    def to_editor_pos(self, pos: tuple[int, int]) -> tuple[int, int]:
        return (pos[0] // WINDOW_SCALE, pos[1] // WINDOW_SCALE)

    def handle_keydown(self, event: pygame.event.Event) -> None:
        modifiers = pygame.key.get_mods()
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_1:
            self.set_mode("platform")
        elif event.key == pygame.K_2:
            self.set_mode("player")
        elif event.key == pygame.K_3:
            self.set_mode("enemy")
        elif pygame.K_4 <= event.key <= pygame.K_9:
            self.select_enemy_variant(event.key - pygame.K_4)
        elif event.key in (pygame.K_s, pygame.K_F5) and (event.key == pygame.K_F5 or modifiers & pygame.KMOD_CTRL):
            self.save_level()
        elif event.key == pygame.K_r and modifiers & pygame.KMOD_CTRL:
            self.reload_level()
        elif event.key in (pygame.K_PAGEUP, pygame.K_LEFTBRACKET):
            self.load_level(self.level_index - 1)
        elif event.key in (pygame.K_PAGEDOWN, pygame.K_RIGHTBRACKET):
            self.load_level(self.level_index + 1)
        elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
            self.delete_selection()
        elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
            self.nudge_selection(event.key, fine=bool(modifiers & pygame.KMOD_SHIFT))

    def delete_selection(self) -> None:
        if self.selected_platform_index is not None:
            del self.level.platforms[self.selected_platform_index]
            self.clear_selection()
            self.mark_dirty("Plateforme supprimee")
        elif self.selected_enemy_index is not None:
            del self.level.enemy_spawns[self.selected_enemy_index]
            self.clear_selection()
            self.mark_dirty("Ennemi supprime")

    def nudge_selection(self, key: int, fine: bool) -> None:
        step = 1 if fine else GRID_SIZE
        dx = 0
        dy = 0
        if key == pygame.K_LEFT:
            dx = -step
        elif key == pygame.K_RIGHT:
            dx = step
        elif key == pygame.K_UP:
            dy = -step
        elif key == pygame.K_DOWN:
            dy = step

        if self.selected_platform_index is not None:
            rect = self.level.platforms[self.selected_platform_index]
            rect.x, rect.y = self.clamp_rect_position(rect.move(dx, dy))
            self.mark_dirty()
        elif self.selected_enemy_index is not None:
            x, y, variant = self.level.enemy_spawns[self.selected_enemy_index]
            next_x, next_y = self.clamp_spawn(x + dx, y + dy, ENEMY_WIDTH, ENEMY_HEIGHT)
            self.level.enemy_spawns[self.selected_enemy_index] = (next_x, next_y, variant)
            self.mark_dirty()
        elif self.mode == "player":
            x, y = self.level.player_spawn
            self.level.player_spawn = self.clamp_spawn(x + dx, y + dy, PLAYER_WIDTH, PLAYER_HEIGHT)
            self.mark_dirty()

    def handle_mouse_down(self, event: pygame.event.Event, pos: tuple[int, int]) -> None:
        if pos[1] >= HEIGHT:
            if event.button == 1:
                self.select_enemy_variant_at(pos)
            return

        if event.button == 1:
            if self.mode == "platform":
                self.begin_platform_action(pos)
            elif self.mode == "player":
                self.level.player_spawn = self.snap_spawn(pos, PLAYER_WIDTH, PLAYER_HEIGHT)
                self.clear_selection()
                self.mark_dirty("Spawn joueur deplace")
            elif self.mode == "enemy":
                self.begin_enemy_action(pos)
        elif event.button == 3:
            self.delete_at(pos)

    def handle_mouse_motion(self, event: pygame.event.Event, pos: tuple[int, int]) -> None:
        if self.drag_action is None:
            return

        if self.drag_action == "create_platform":
            self.update_created_platform(pos)
        elif self.drag_action == "move_platform":
            self.update_moved_platform(pos)
        elif self.drag_action == "resize_platform":
            self.update_resized_platform(pos)
        elif self.drag_action == "move_enemy":
            self.update_moved_enemy(pos)

    def handle_mouse_up(self, event: pygame.event.Event) -> None:
        if event.button != 1:
            return

        if self.drag_action == "create_platform" and self.selected_platform_index is not None:
            rect = self.level.platforms[self.selected_platform_index]
            if rect.width < GRID_SIZE or rect.height < GRID_SIZE:
                del self.level.platforms[self.selected_platform_index]
                self.clear_selection()
                self.mark_dirty("Plateforme trop petite annulee")

        self.drag_action = None
        self.drag_origin_rect = None

    def begin_platform_action(self, pos: tuple[int, int]) -> None:
        platform_index = self.platform_at(pos)
        if platform_index is not None:
            self.selected_platform_index = platform_index
            self.selected_enemy_index = None
            rect = self.level.platforms[platform_index]
            self.drag_origin_rect = rect.copy()
            mouse = pygame.Vector2(pos)
            self.drag_offset = mouse - pygame.Vector2(rect.topleft)
            self.drag_action = "resize_platform" if self.is_in_resize_handle(rect, pos) else "move_platform"
            return

        start_x, start_y = self.snap_point(pos)
        rect = pygame.Rect(start_x, start_y, GRID_SIZE, GRID_SIZE)
        self.level.platforms.append(rect)
        self.selected_platform_index = len(self.level.platforms) - 1
        self.selected_enemy_index = None
        self.drag_start = pygame.Vector2(start_x, start_y)
        self.drag_action = "create_platform"
        self.mark_dirty("Plateforme ajoutee")

    def begin_enemy_action(self, pos: tuple[int, int]) -> None:
        enemy_index = self.enemy_at(pos)
        if enemy_index is not None:
            self.selected_enemy_index = enemy_index
            self.selected_platform_index = None
            x, y, variant = self.level.enemy_spawns[enemy_index]
            self.selected_enemy_variant = variant % len(ENEMY_VARIANTS)
            self.drag_offset = pygame.Vector2(pos) - pygame.Vector2(x, y)
            self.drag_action = "move_enemy"
            return

        x, y = self.snap_spawn(pos, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.level.enemy_spawns.append((x, y, self.selected_enemy_variant))
        self.selected_enemy_index = len(self.level.enemy_spawns) - 1
        self.selected_platform_index = None
        self.drag_action = "move_enemy"
        self.drag_offset = pygame.Vector2(ENEMY_WIDTH / 2, ENEMY_HEIGHT / 2)
        self.mark_dirty(f"Ennemi {self.selected_enemy_variant + 1} ajoute")

    def update_created_platform(self, pos: tuple[int, int]) -> None:
        if self.selected_platform_index is None:
            return

        current_x, current_y = self.snap_point(pos)
        left = min(int(self.drag_start.x), current_x)
        top = min(int(self.drag_start.y), current_y)
        right = max(int(self.drag_start.x), current_x + GRID_SIZE)
        bottom = max(int(self.drag_start.y), current_y + GRID_SIZE)
        rect = pygame.Rect(left, top, right - left, bottom - top)
        self.level.platforms[self.selected_platform_index] = self.clamp_rect_size(rect)
        self.mark_dirty()

    def update_moved_platform(self, pos: tuple[int, int]) -> None:
        if self.selected_platform_index is None or self.drag_origin_rect is None:
            return

        mouse = pygame.Vector2(pos) - self.drag_offset
        x, y = self.snap_point((round(mouse.x), round(mouse.y)))
        rect = self.drag_origin_rect.copy()
        rect.topleft = (x, y)
        self.level.platforms[self.selected_platform_index] = self.clamp_rect_size(rect)
        self.mark_dirty()

    def update_resized_platform(self, pos: tuple[int, int]) -> None:
        if self.selected_platform_index is None or self.drag_origin_rect is None:
            return

        x, y = self.snap_point(pos)
        rect = self.drag_origin_rect.copy()
        rect.width = max(GRID_SIZE, x - rect.x + GRID_SIZE)
        rect.height = max(GRID_SIZE, y - rect.y + GRID_SIZE)
        self.level.platforms[self.selected_platform_index] = self.clamp_rect_size(rect)
        self.mark_dirty()

    def update_moved_enemy(self, pos: tuple[int, int]) -> None:
        if self.selected_enemy_index is None:
            return

        mouse = pygame.Vector2(pos) - self.drag_offset
        variant = self.level.enemy_spawns[self.selected_enemy_index][2]
        x, y = self.snap_spawn(
            (round(mouse.x), round(mouse.y)),
            ENEMY_WIDTH,
            ENEMY_HEIGHT,
        )
        self.level.enemy_spawns[self.selected_enemy_index] = (x, y, variant)
        self.mark_dirty()

    def delete_at(self, pos: tuple[int, int]) -> None:
        enemy_index = self.enemy_at(pos)
        if enemy_index is not None:
            del self.level.enemy_spawns[enemy_index]
            self.clear_selection()
            self.mark_dirty("Ennemi supprime")
            return

        platform_index = self.platform_at(pos)
        if platform_index is not None:
            del self.level.platforms[platform_index]
            self.clear_selection()
            self.mark_dirty("Plateforme supprimee")

    def platform_at(self, pos: tuple[int, int]) -> int | None:
        for index in range(len(self.level.platforms) - 1, -1, -1):
            if self.level.platforms[index].collidepoint(pos):
                return index
        return None

    def enemy_at(self, pos: tuple[int, int]) -> int | None:
        for index in range(len(self.level.enemy_spawns) - 1, -1, -1):
            x, y, _variant = self.level.enemy_spawns[index]
            if pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT).collidepoint(pos):
                return index
        return None

    def enemy_palette_rect(self, variant: int) -> pygame.Rect:
        return pygame.Rect(4 + variant * (PALETTE_CELL_SIZE + 2), PALETTE_TOP, PALETTE_CELL_SIZE, PALETTE_CELL_SIZE)

    def select_enemy_variant(self, variant: int) -> None:
        if not 0 <= variant < len(ENEMY_VARIANTS):
            return
        self.selected_enemy_variant = variant
        self.mode = "enemy"
        self.clear_selection()
        self.message = f"Ennemi selectionne: {variant + 1}"

    def select_enemy_variant_at(self, pos: tuple[int, int]) -> bool:
        for variant in range(len(ENEMY_VARIANTS)):
            if self.enemy_palette_rect(variant).collidepoint(pos):
                self.select_enemy_variant(variant)
                return True
        return False

    def is_in_resize_handle(self, rect: pygame.Rect, pos: tuple[int, int]) -> bool:
        handle = pygame.Rect(0, 0, HANDLE_SIZE, HANDLE_SIZE)
        handle.bottomright = rect.bottomright
        return handle.collidepoint(pos)

    def snap_point(self, pos: tuple[int, int]) -> tuple[int, int]:
        x = round(pos[0] / GRID_SIZE) * GRID_SIZE
        y = round(pos[1] / GRID_SIZE) * GRID_SIZE
        return max(0, min(x, WIDTH - GRID_SIZE)), max(0, min(y, HEIGHT - GRID_SIZE))

    def snap_spawn(self, pos: tuple[int, int], width: int, height: int) -> tuple[int, int]:
        x, y = self.snap_point(pos)
        return self.clamp_spawn(x, y, width, height)

    def clamp_spawn(self, x: int, y: int, width: int, height: int) -> tuple[int, int]:
        return max(0, min(x, WIDTH - width)), max(0, min(y, HEIGHT - height))

    def clamp_rect_position(self, rect: pygame.Rect) -> tuple[int, int]:
        x = max(0, min(rect.x, WIDTH - rect.width))
        y = max(0, min(rect.y, HEIGHT - rect.height))
        return x, y

    def clamp_rect_size(self, rect: pygame.Rect) -> pygame.Rect:
        rect.width = max(GRID_SIZE, min(rect.width, WIDTH - rect.x))
        rect.height = max(GRID_SIZE, min(rect.height, HEIGHT - rect.y))
        rect.x, rect.y = self.clamp_rect_position(rect)
        return rect

    def draw(self) -> None:
        self.canvas.fill(BACKGROUND_COLOR)
        self.draw_grid()
        self.draw_platforms()
        self.draw_spawns()
        self.draw_panel()
        pygame.transform.scale(self.canvas, self.screen.get_size(), self.screen)
        pygame.display.flip()

    def draw_grid(self) -> None:
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.canvas, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.canvas, GRID_COLOR, (0, y), (WIDTH, y))

    def draw_platforms(self) -> None:
        for index, platform in enumerate(self.level.platforms):
            pygame.draw.rect(self.canvas, PLATFORM_COLOR, platform, border_radius=2)
            if index == self.selected_platform_index:
                pygame.draw.rect(self.canvas, SELECTED_COLOR, platform, width=1, border_radius=2)
                handle = pygame.Rect(0, 0, HANDLE_SIZE, HANDLE_SIZE)
                handle.bottomright = platform.bottomright
                pygame.draw.rect(self.canvas, SELECTED_COLOR, handle)

    def draw_spawns(self) -> None:
        player = Player(*self.level.player_spawn)
        player.draw(self.canvas, self.camera, self.assets, invulnerable=False)
        pygame.draw.rect(self.canvas, PLAYER_MARKER_COLOR, player.rect, width=1, border_radius=2)
        self.draw_label("P", player.rect.midtop, PLAYER_MARKER_COLOR)

        for index, (x, y, variant) in enumerate(self.level.enemy_spawns):
            enemy = Enemy(x, y, variant)
            enemy.draw(self.canvas, self.camera, self.assets)
            rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
            outline_color = SELECTED_COLOR if index == self.selected_enemy_index else ENEMY_MARKER_COLOR
            pygame.draw.rect(self.canvas, outline_color, rect, width=1, border_radius=2)
            self.draw_label(str(index + 1), rect.midtop, outline_color)

    def draw_label(self, text: str, midbottom: tuple[int, int], color: tuple[int, int, int]) -> None:
        label = self.small_font.render(text, False, color)
        rect = label.get_rect(midbottom=(midbottom[0], midbottom[1] - 2))
        self.canvas.blit(label, rect)

    def draw_panel(self) -> None:
        panel_rect = pygame.Rect(0, HEIGHT, WIDTH, PANEL_HEIGHT)
        pygame.draw.rect(self.canvas, PANEL_COLOR, panel_rect)

        mode_names = {"platform": "Plateformes", "player": "Joueur", "enemy": "Ennemis"}
        dirty_marker = " *" if self.dirty else ""
        title = f"{self.level.path.name}{dirty_marker} | {mode_names[self.mode]}"
        self.draw_text(title, 4, HEIGHT + 4, TEXT_COLOR, self.font)

        controls = [
            "Ctrl+S save  Ctrl+R reload  [ ] lvl",
            "1 plat  2 player  3 enemies  Del rm",
            "Select enemy below, left click place",
        ]
        for row, text in enumerate(controls):
            self.draw_text(text, 4, HEIGHT + 17 + row * 10, MUTED_TEXT_COLOR, self.small_font)

        status_color = SAVE_FLASH_COLOR if self.save_flash_timer > 0 else TEXT_COLOR
        self.draw_text(self.message[:25], WIDTH - 4, HEIGHT + 37, status_color, self.small_font, align_right=True)
        self.draw_enemy_palette()

    def draw_enemy_palette(self) -> None:
        for variant in range(len(ENEMY_VARIANTS)):
            rect = self.enemy_palette_rect(variant)
            is_selected = variant == self.selected_enemy_variant
            border_color = SELECTED_COLOR if is_selected else MUTED_TEXT_COLOR
            pygame.draw.rect(self.canvas, (28, 32, 44), rect, border_radius=2)
            pygame.draw.rect(self.canvas, border_color, rect, width=1, border_radius=2)

            enemy_rect = pygame.Rect(0, 0, ENEMY_WIDTH, ENEMY_HEIGHT)
            enemy_rect.center = rect.center
            enemy = Enemy(enemy_rect.x, enemy_rect.y, variant)
            enemy.draw(self.canvas, self.camera, self.assets)

            label = self.small_font.render(str(variant + 1), False, border_color)
            self.canvas.blit(label, (rect.x + 1, rect.y + 1))

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        font: pygame.font.Font,
        *,
        align_right: bool = False,
    ) -> None:
        rendered = font.render(text, False, color)
        rect = rendered.get_rect(topright=(x, y)) if align_right else rendered.get_rect(topleft=(x, y))
        self.canvas.blit(rendered, rect)
