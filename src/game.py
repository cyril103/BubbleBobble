import pygame

from src.assets import AssetManager
from src.camera import Camera
from src.entities.bubble import Bubble
from src.entities.collectable import Collectable
from src.entities.enemy import Enemy
from src.entities.particle import Particle
from src.entities.player import Player
from src.level import Level, discover_level_paths
from src.settings import (
    BACKGROUND_COLOR,
    BUBBLE_CHAIN_POP_MARGIN,
    BUBBLE_REPEL_STRENGTH,
    COLLECTABLE_SIZE,
    FPS,
    HEIGHT,
    LEVELS_DIR,
    LEVEL_END_DELAY,
    LEVEL_TRANSITION_DURATION,
    PLATFORM_COLOR,
    PLAYER_BUBBLE_POP_MIN_UPWARD_SPEED,
    PLAYER_DEATH_DURATION,
    READY_DURATION,
    SPAWN_INVULNERABILITY_DURATION,
    STARTING_LIVES,
    TITLE,
    WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from src.states import GameState
from src.systems.collisions import bubble_hits_enemy, player_hits_enemy, player_stomps_trapped_enemy
from src.ui.hud import draw_hud
from src.ui.screens import draw_overlay, draw_ready_overlay, draw_title_screen


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.scene_surface = pygame.Surface((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.assets = AssetManager()
        self.camera = Camera()
        self.running = True

        self.level_paths = discover_level_paths(LEVELS_DIR)
        if not self.level_paths:
            raise RuntimeError("Aucun fichier de niveau trouve dans levels/.")

        self.level_index = 0
        self.level = Level.from_file(self.level_paths[self.level_index])
        self.player = Player(*self.level.player_spawn)
        self.bubbles: list[Bubble] = []
        self.collectables: list[Collectable] = []
        self.enemies: list[Enemy] = []
        self.particles: list[Particle] = []
        self.state = GameState.TITLE
        self.score = 0
        self.lives = STARTING_LIVES
        self.spawn_invulnerability_timer = 0.0
        self.ready_timer = 0.0
        self.level_end_timer = 0.0
        self.pending_end_state: GameState | None = None
        self.death_timer = 0.0
        self.pending_post_death_state: GameState | None = None
        self.transition_timer = 0.0
        self.transition_target_level_index: int | None = None
        self.transition_from_surface: pygame.Surface | None = None
        self.transition_to_surface: pygame.Surface | None = None
        self.message = "Fleches/A-D pour bouger, Espace pour sauter, F pour tirer"
        self.reset_level()
        self.state = GameState.TITLE

    def present_scene(self) -> None:
        if self.screen.get_size() == self.scene_surface.get_size():
            self.screen.blit(self.scene_surface, (0, 0))
        else:
            scaled_scene = pygame.transform.scale(self.scene_surface, self.screen.get_size())
            self.screen.blit(scaled_scene, (0, 0))
        pygame.display.flip()

    def start_game(self) -> None:
        self.load_level(0, keep_score=False, keep_lives=False)

    def reset_level(self) -> None:
        self.player = Player(*self.level.player_spawn)
        self.bubbles = []
        self.collectables = []
        self.enemies = [Enemy(x, y, variant) for x, y, variant in self.level.enemy_spawns]
        self.particles = []
        self._resolve_spawn_collisions()
        self.spawn_invulnerability_timer = SPAWN_INVULNERABILITY_DURATION
        self.ready_timer = READY_DURATION
        self.level_end_timer = 0.0
        self.pending_end_state = None
        self.death_timer = 0.0
        self.pending_post_death_state = None
        self.transition_timer = 0.0
        self.transition_target_level_index = None
        self.transition_from_surface = None
        self.transition_to_surface = None

    def _resolve_spawn_collisions(self) -> None:
        occupied_rects = [self.player.rect]

        for enemy in self.enemies:
            if not any(enemy.rect.colliderect(rect) for rect in occupied_rects):
                occupied_rects.append(enemy.rect)
                continue

            for candidate_x in range(24, WIDTH - enemy.rect.width, 56):
                candidate_rect = enemy.rect.copy()
                candidate_rect.x = candidate_x
                if any(candidate_rect.colliderect(rect) for rect in occupied_rects):
                    continue

                enemy.rect.x = candidate_rect.x
                enemy.x = float(enemy.rect.x)
                break

            occupied_rects.append(enemy.rect)

    def load_level(self, level_index: int, keep_score: bool = True, keep_lives: bool = True) -> None:
        self.level_index = level_index
        self.level = Level.from_file(self.level_paths[self.level_index])
        self.state = GameState.READY
        if not keep_score:
            self.score = 0
        if not keep_lives:
            self.lives = STARTING_LIVES
        self.message = f"{self.level.name} - elimine tous les ennemis."
        self.reset_level()

    def has_next_level(self) -> bool:
        return self.level_index < len(self.level_paths) - 1

    def advance_to_next_level(self) -> None:
        if self.has_next_level():
            self.load_level(self.level_index + 1)
        else:
            self.state = GameState.CAMPAIGN_COMPLETE
            self.message = "Campagne terminee."
            self.bubbles = []

    def restart_game(self) -> None:
        self.load_level(0, keep_score=False, keep_lives=False)

    def spawn_bubble(self) -> None:
        bubble_x = self.player.rect.centerx + self.player.facing * 10
        bubble_y = self.player.rect.centery - 3
        self.bubbles.append(Bubble(bubble_x, bubble_y, self.player.facing))

    def spawn_pop(self, center: tuple[int, int]) -> None:
        self.particles.append(Particle(pygame.Vector2(center)))

    def spawn_player_death_effect(self, center: tuple[int, int]) -> None:
        offsets = ((0, 0), (-7, -4), (7, -4), (-5, 7), (5, 7))
        for offset_x, offset_y in offsets:
            self.spawn_pop((center[0] + offset_x, center[1] + offset_y))

    def respawn_player(self) -> None:
        self.player = Player(*self.level.player_spawn)
        self.player.velocity_x = 0.0
        self.player.velocity_y = 0.0
        self.bubbles = []
        self.spawn_invulnerability_timer = SPAWN_INVULNERABILITY_DURATION

    def spawn_collectable(self, center: tuple[int, int], variant: int, launch_direction: int) -> None:
        size = COLLECTABLE_SIZE
        score = 400 + (variant % 6) * 100
        self.collectables.append(
            Collectable(center[0] - size / 2, center[1] - size / 2, variant, score, launch_direction=launch_direction)
        )

    def defeat_enemy(self, enemy: Enemy, launch_origin_x: float | None = None) -> None:
        enemy.alive = False
        self.score += 250
        self.spawn_pop(enemy.rect.center)
        origin_x = self.player.rect.centerx if launch_origin_x is None else launch_origin_x
        launch_direction = 1 if origin_x <= enemy.rect.centerx else -1
        self.spawn_collectable(enemy.rect.center, enemy.variant, launch_direction)
        self.message = "Ennemi elimine."

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.state == GameState.TITLE and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.start_game()
                elif self.state == GameState.PLAYING and event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.player.jump()
                elif self.state == GameState.PLAYING and event.key in (pygame.K_f, pygame.K_LCTRL, pygame.K_RCTRL):
                    self.spawn_bubble()
                elif self.state == GameState.LEVEL_CLEAR and event.key in (pygame.K_RETURN, pygame.K_r):
                    self.advance_to_next_level()
                elif self.state in (GameState.CAMPAIGN_COMPLETE, GameState.GAME_OVER) and event.key in (
                    pygame.K_RETURN,
                    pygame.K_r,
                ):
                    self.restart_game()

    def update_bubbles(self, dt: float) -> None:
        active_bubbles: list[Bubble] = []
        pop_origins: list[tuple[pygame.Vector2, float]] = []

        for bubble in self.bubbles:
            was_active = bubble.update(dt, self.level.platforms)
            if not was_active:
                self.spawn_pop(bubble.rect.center)
                pop_origins.append((bubble.center.copy(), bubble.current_radius))
                continue

            captured_enemy = False
            for enemy in self.enemies:
                if enemy.alive and not enemy.trapped and bubble_hits_enemy(bubble, enemy):
                    enemy.trap()
                    self.score += 100
                    self.spawn_pop(bubble.rect.center)
                    self.message = "Ennemi capture. Touche-le avant qu'il se libere."
                    captured_enemy = True
                    break

            if not captured_enemy:
                active_bubbles.append(bubble)

        active_bubbles = self.resolve_player_bubble_pops(active_bubbles, pop_origins)
        self.resolve_player_trapped_bubble_pops(pop_origins)
        active_bubbles = self.resolve_bubble_chain_pops(active_bubbles, pop_origins)
        self.resolve_bubble_collisions(active_bubbles, self.trapped_enemies())
        self.bubbles = active_bubbles

    def trapped_enemies(self) -> list[Enemy]:
        return [enemy for enemy in self.enemies if enemy.alive and enemy.trapped]

    def player_can_pop_bubbles(self) -> bool:
        return not self.player.on_ground and self.player.velocity_y <= -PLAYER_BUBBLE_POP_MIN_UPWARD_SPEED

    def resolve_player_bubble_pops(
        self, bubbles: list[Bubble], pop_origins: list[tuple[pygame.Vector2, float]]
    ) -> list[Bubble]:
        if not self.player_can_pop_bubbles():
            return bubbles

        active_bubbles: list[Bubble] = []
        for bubble in bubbles:
            if self.player.rect.colliderect(bubble.rect):
                self.spawn_pop(bubble.rect.center)
                pop_origins.append((bubble.center.copy(), bubble.current_radius))
                self.message = "Bulle eclatee."
            else:
                active_bubbles.append(bubble)

        return active_bubbles

    def resolve_player_trapped_bubble_pops(self, pop_origins: list[tuple[pygame.Vector2, float]]) -> None:
        if not self.player_can_pop_bubbles():
            return

        for enemy in self.trapped_enemies():
            if not self.player.rect.colliderect(enemy.rect):
                continue

            pop_origins.append((enemy.center.copy(), enemy.current_radius))
            self.defeat_enemy(enemy)

    def resolve_bubble_chain_pops(
        self, bubbles: list[Bubble], pop_origins: list[tuple[pygame.Vector2, float]]
    ) -> list[Bubble]:
        if not pop_origins:
            return bubbles

        active_bubbles = bubbles[:]
        source_index = 0
        while source_index < len(pop_origins):
            source_center, source_radius = pop_origins[source_index]
            source_index += 1

            remaining_bubbles: list[Bubble] = []
            for bubble in active_bubbles:
                pop_distance = source_radius + bubble.current_radius + BUBBLE_CHAIN_POP_MARGIN
                if source_center.distance_to(bubble.center) <= pop_distance:
                    self.spawn_pop(bubble.rect.center)
                    pop_origins.append((bubble.center.copy(), bubble.current_radius))
                    continue

                remaining_bubbles.append(bubble)

            active_bubbles = remaining_bubbles

            for enemy in self.trapped_enemies():
                pop_distance = source_radius + enemy.current_radius + BUBBLE_CHAIN_POP_MARGIN
                if source_center.distance_to(enemy.center) > pop_distance:
                    continue

                pop_origins.append((enemy.center.copy(), enemy.current_radius))
                self.defeat_enemy(enemy, source_center.x)

        return active_bubbles

    def resolve_bubble_collisions(self, bubbles: list[Bubble], trapped_enemies: list[Enemy] | None = None) -> None:
        bubble_bodies = [*bubbles, *(trapped_enemies or [])]

        for index, bubble in enumerate(bubble_bodies):
            for other in bubble_bodies[index + 1 :]:
                delta = other.center - bubble.center
                distance = delta.length()
                min_distance = bubble.current_radius + other.current_radius
                if distance >= min_distance:
                    continue

                if distance <= 0.001:
                    direction = pygame.Vector2(1, 0)
                else:
                    direction = delta / distance

                overlap = min_distance - distance
                offset = direction * (overlap * BUBBLE_REPEL_STRENGTH * 0.5)
                bubble.nudge(-offset)
                other.nudge(offset)

    def update_enemies(self, dt: float) -> None:
        for enemy in self.enemies:
            enemy.update(dt, self.level.platforms)

            if enemy.alive and player_stomps_trapped_enemy(self.player, enemy):
                self.defeat_enemy(enemy)
            elif (
                self.spawn_invulnerability_timer <= 0
                and enemy.alive
                and not enemy.trapped
                and player_hits_enemy(self.player, enemy)
            ):
                self.handle_player_hit()
                return

        if self.enemies and all(not enemy.alive for enemy in self.enemies) and self.pending_end_state is None:
            self.start_level_end_sequence()

    def start_level_end_sequence(self) -> None:
        self.level_end_timer = LEVEL_END_DELAY
        self.pending_end_state = GameState.TRANSITION if self.has_next_level() else GameState.CAMPAIGN_COMPLETE
        self.message = "Niveau nettoye. Ramasse les bonus avant la transition."

    def create_transition_snapshot(self, next_level_index: int) -> tuple[pygame.Surface, pygame.Surface]:
        current_surface = pygame.Surface((WIDTH, HEIGHT))
        self.render_scene_to(
            current_surface,
            self.level,
            self.player,
            self.bubbles,
            self.collectables,
            self.enemies,
            self.particles,
            self.score,
            self.lives,
            self.level.name,
            "STAGE CLEAR",
            player_invulnerable=self.spawn_invulnerability_timer > 0,
        )

        next_level = Level.from_file(self.level_paths[next_level_index])
        next_player = Player(*next_level.player_spawn)
        next_enemies = [Enemy(x, y, variant) for x, y, variant in next_level.enemy_spawns]
        next_surface = pygame.Surface((WIDTH, HEIGHT))
        self.render_scene_to(
            next_surface,
            next_level,
            next_player,
            [],
            [],
            next_enemies,
            [],
            self.score,
            self.lives,
            next_level.name,
            "NEXT STAGE",
            player_invulnerable=False,
        )
        return current_surface, next_surface

    def begin_level_transition(self) -> None:
        next_level_index = self.level_index + 1
        self.transition_from_surface, self.transition_to_surface = self.create_transition_snapshot(next_level_index)
        self.transition_target_level_index = next_level_index
        self.transition_timer = LEVEL_TRANSITION_DURATION
        self.state = GameState.TRANSITION

    def update_transition(self, dt: float) -> None:
        self.transition_timer = max(0.0, self.transition_timer - dt)
        if self.transition_timer > 0:
            return

        target_level = self.transition_target_level_index
        self.transition_target_level_index = None
        self.transition_from_surface = None
        self.transition_to_surface = None
        if target_level is None:
            self.state = GameState.CAMPAIGN_COMPLETE
            self.message = "Campagne terminee."
            return
        self.load_level(target_level)

    def handle_player_hit(self) -> None:
        self.lives -= 1
        self.bubbles = []
        self.death_timer = PLAYER_DEATH_DURATION
        if self.lives <= 0:
            self.lives = 0
            self.state = GameState.DYING
            self.pending_post_death_state = GameState.GAME_OVER
            self.message = "Plus de vies."
            return

        self.state = GameState.DYING
        self.pending_post_death_state = GameState.PLAYING
        self.message = "Vie perdue. Respawn..."

    def update_collectables(self, dt: float) -> None:
        active_collectables: list[Collectable] = []

        for collectable in self.collectables:
            if not collectable.update(dt, self.level.platforms):
                continue
            if collectable.pickup_delay <= 0 and collectable.rect.colliderect(self.player.rect):
                self.score += collectable.score
                self.message = f"Bonus ramasse: +{collectable.score}"
                continue
            active_collectables.append(collectable)

        self.collectables = active_collectables

    def update_particles(self, dt: float) -> None:
        self.particles = [particle for particle in self.particles if particle.update(dt)]

    def update_dying(self, dt: float) -> None:
        self.death_timer = max(0.0, self.death_timer - dt)
        self.update_particles(dt)
        if self.death_timer > 0:
            return

        next_state = self.pending_post_death_state
        self.pending_post_death_state = None
        if next_state == GameState.GAME_OVER:
            self.state = GameState.GAME_OVER
            return

        self.respawn_player()
        self.state = GameState.PLAYING
        self.message = f"{self.level.name} - elimine tous les ennemis."

    def update_level_end_timer(self, dt: float) -> None:
        if self.pending_end_state is None:
            return

        self.level_end_timer = max(0.0, self.level_end_timer - dt)
        if self.level_end_timer > 0:
            return

        next_state = self.pending_end_state
        self.pending_end_state = None

        if next_state == GameState.TRANSITION:
            self.begin_level_transition()
            return

        self.state = next_state
        if next_state == GameState.CAMPAIGN_COMPLETE:
            self.message = "Campagne terminee."
            self.bubbles = []

    def update_ready_scene(self, dt: float) -> None:
        self.player.settle(dt, self.level.platforms)
        for enemy in self.enemies:
            enemy.settle(dt, self.level.platforms)
        self.update_collectables(dt)
        self.update_particles(dt)

    def update(self, dt: float) -> None:
        if self.state == GameState.TITLE:
            return

        if self.state == GameState.READY:
            self.ready_timer = max(0.0, self.ready_timer - dt)
            self.update_ready_scene(dt)
            if self.ready_timer <= 0:
                self.state = GameState.PLAYING
                self.message = f"{self.level.name} - elimine tous les ennemis."
            return

        if self.state == GameState.TRANSITION:
            self.update_transition(dt)
            return

        if self.state == GameState.DYING:
            self.update_dying(dt)
            return

        if self.state != GameState.PLAYING:
            return

        self.spawn_invulnerability_timer = max(0.0, self.spawn_invulnerability_timer - dt)

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(dt, self.level.platforms)
        self.update_bubbles(dt)
        self.update_enemies(dt)
        self.update_collectables(dt)
        self.update_particles(dt)
        self.update_level_end_timer(dt)

    def render_scene_to(
        self,
        surface: pygame.Surface,
        level: Level,
        player: Player,
        bubbles: list[Bubble],
        collectables: list[Collectable],
        enemies: list[Enemy],
        particles: list[Particle],
        score: int,
        lives: int,
        level_name: str,
        message: str,
        *,
        player_invulnerable: bool,
        draw_player: bool = True,
    ) -> None:
        surface.fill(BACKGROUND_COLOR)

        for platform in level.platforms:
            pygame.draw.rect(surface, PLATFORM_COLOR, self.camera.apply_rect(platform), border_radius=8)

        for bubble in bubbles:
            bubble.draw(surface, self.camera, self.assets)

        for collectable in collectables:
            collectable.draw(surface, self.camera, self.assets)

        for enemy in enemies:
            if enemy.alive:
                enemy.draw(surface, self.camera, self.assets)

        for particle in particles:
            particle.draw(surface, self.camera, self.assets)

        if draw_player:
            player.draw(surface, self.camera, self.assets, invulnerable=player_invulnerable)
        draw_hud(surface, self.assets.hud_font, score, lives, level_name, message)

    def draw_transition(self) -> None:
        if self.transition_from_surface is None or self.transition_to_surface is None:
            self.scene_surface.fill(BACKGROUND_COLOR)
            return

        progress = 1.0 - (self.transition_timer / LEVEL_TRANSITION_DURATION)
        offset = round(progress * HEIGHT)
        self.scene_surface.fill(BACKGROUND_COLOR)
        self.scene_surface.blit(self.transition_from_surface, (0, -offset))
        self.scene_surface.blit(self.transition_to_surface, (0, HEIGHT - offset))

    def draw(self) -> None:
        if self.state == GameState.TITLE:
            self.scene_surface.fill(BACKGROUND_COLOR)
            draw_title_screen(
                self.scene_surface,
                self.assets.title_font,
                self.assets.overlay_font,
                blink_on=(pygame.time.get_ticks() // 450) % 2 == 0,
            )
            self.present_scene()
            return

        if self.state == GameState.TRANSITION:
            self.draw_transition()
            self.present_scene()
            return

        self.render_scene_to(
            self.scene_surface,
            self.level,
            self.player,
            self.bubbles,
            self.collectables,
            self.enemies,
            self.particles,
            self.score,
            self.lives,
            self.level.name,
            self.message,
            player_invulnerable=self.spawn_invulnerability_timer > 0,
            draw_player=self.state != GameState.DYING,
        )

        if self.state == GameState.READY:
            draw_ready_overlay(self.scene_surface, self.assets.title_font, self.assets.overlay_font, self.level.name)
        elif self.state == GameState.DYING:
            death_progress = 1.0 - (self.death_timer / PLAYER_DEATH_DURATION)
            self.player.draw_death(self.scene_surface, self.camera, self.assets, death_progress)
            draw_overlay(
                self.scene_surface,
                self.assets.title_font,
                self.assets.overlay_font,
                "OOPS!",
                [f"Vies restantes: {self.lives}"],
            )
        elif self.state == GameState.CAMPAIGN_COMPLETE:
            draw_overlay(
                self.scene_surface,
                self.assets.title_font,
                self.assets.overlay_font,
                "Campagne Complete",
                [f"Score final: {self.score}", "Appuie sur Entree ou R pour recommencer"],
            )
        elif self.state == GameState.GAME_OVER:
            draw_overlay(
                self.scene_surface,
                self.assets.title_font,
                self.assets.overlay_font,
                "Game Over",
                [f"Score final: {self.score}", "Appuie sur Entree ou R pour recommencer"],
            )

        self.present_scene()

    def run_frame(self) -> None:
        dt = self.clock.tick(FPS) / 1000.0
        self.handle_events()
        self.update(dt)
        self.draw()

    def run(self, max_frames: int | None = None) -> None:
        frames = 0

        while self.running:
            self.run_frame()

            frames += 1
            if max_frames is not None and frames >= max_frames:
                self.running = False

        pygame.quit()

    async def run_async(self) -> None:
        while self.running:
            self.run_frame()
            import asyncio

            await asyncio.sleep(0)

        pygame.quit()
