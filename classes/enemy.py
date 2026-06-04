import pygame

from classes.loader import load_frames, load_frames_from_candidates, load_image

class Tooth:
    def __init__(self, x, y, width=120, height=120, speed=2, patrol_distance=120):
        self.rect = pygame.Rect(x, y, width, height)
        self.start_x = x
        self.speed = speed
        self.direction = 1
        self.patrol_distance = patrol_distance

        self.damage = 1
        self.last_hit_time = 0
        self.hit_cooldown = 1000

        self.width = width
        self.height = height

        self.animations = {
            "idle": self.load_animation("01-Idle"),
            "run": self.load_animation("02-Run"),
        }

        self.state = "run"
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animations[self.state][0]

    def load_animation(self, folder_name):
        candidate_roots = [
            "asset/graphics/enemy/Fierce Tooth",
            "asset/enemy/Fierce Tooth",
        ]
        return load_frames_from_candidates(
            candidate_roots,
            folder_name,
            size=(self.width, self.height),
        )

    def move(self):
        self.rect.x += self.speed * self.direction

        if self.rect.x >= self.start_x + self.patrol_distance:
            self.direction = -1
        elif self.rect.x <= self.start_x:
            self.direction = 1

    def animate(self):
        frames = self.animations[self.state]

        self.frame_index += self.animation_speed

        if self.frame_index >= len(frames):
            self.frame_index = 0

        self.image = frames[int(self.frame_index)]

        if self.direction == 1:
            self.image = pygame.transform.flip(self.image, True, False)

    def attack_player(self, player):
        current_time = pygame.time.get_ticks()

        if self.rect.colliderect(player.rect):
            if current_time - self.last_hit_time >= self.hit_cooldown:
                player.take_damage(self.damage)
                self.last_hit_time = current_time

    def update(self, player):
        self.move()

        if self.speed == 0:
            self.state = "idle"
        else:
            self.state = "run"

        self.animate()
        self.attack_player(player)

    def draw(self, screen, offset=(0, 0)):
        draw_rect = self.rect.move(offset)
        screen.blit(self.image, draw_rect)


class Pearl:
    _base_image = None

    def __init__(self, position, direction, size=(16, 16), speed=280, damage=1):
        if Pearl._base_image is None:
            Pearl._base_image = load_image("asset/graphics/enemies/bullets/pearl.png")

        self.image = pygame.transform.scale(Pearl._base_image, size)
        self.rect = self.image.get_rect(center=position)
        self.position = pygame.Vector2(self.rect.topleft)
        self.velocity = pygame.Vector2(direction * speed, 0)
        self.damage = damage
        self.active = True

    def update(self, dt, player, terrain_rects, world_rect):
        if not self.active:
            return

        self.position += self.velocity * dt
        self.rect.topleft = (round(self.position.x), round(self.position.y))

        if player is not None and self.rect.colliderect(player.rect):
            player.take_damage(self.damage)
            self.active = False
            return

        if not world_rect.colliderect(self.rect):
            self.active = False
            return

        for terrain_rect in terrain_rects:
            if self.rect.colliderect(terrain_rect):
                self.active = False
                return

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, self.rect.move(offset))


class Shell:
    def __init__(self, position, size, *, reverse=False, fire_cooldown_ms=1800):
        self.direction = 1 if reverse else -1
        self.projectile_size = (16, 16)
        self.idle_frames = self.load_frames("idle", size)
        self.fire_frames = self.load_frames("fire", size)
        self.state = "idle"
        self.frame_index = 0.0
        self.fire_animation_speed = 12
        self.fire_cooldown_ms = fire_cooldown_ms
        self.time_since_fire_ms = fire_cooldown_ms
        self.fired_this_cycle = False

        self.image = self.idle_frames[0]
        self.rect = self.image.get_rect(midbottom=position)
        self.projectiles = []

    def load_frames(self, animation_name, size):
        frames = load_frames(
            f"asset/graphics/enemy/shell/{animation_name}",
            size=size,
        )
        if self.direction == -1:
            frames = [pygame.transform.flip(frame, True, False) for frame in frames]
        return frames

    def start_fire_cycle(self):
        self.state = "fire"
        self.frame_index = 0.0
        self.fired_this_cycle = False

    def spawn_pearl(self, terrain_rects):
        spawn_position = (
            self.rect.centerx + self.direction * max(10, self.rect.width // 2 - 10),
            self.rect.centery - 2,
        )
        pearl = Pearl(
            spawn_position,
            self.direction,
            size=self.projectile_size,
        )

        # Nudge new pearls clear of the launch platform before normal
        # terrain collision takes over.
        max_clearance = max(192, self.rect.width * 4)
        clearance_steps = 0
        while clearance_steps < max_clearance and any(
            pearl.rect.colliderect(terrain_rect)
            for terrain_rect in terrain_rects
        ):
            pearl.position.x += self.direction
            pearl.rect.x = round(pearl.position.x)
            clearance_steps += 1

        self.projectiles.append(pearl)

    def update_animation(self, dt, terrain_rects):
        anchor = self.rect.midbottom

        if self.state == "idle":
            self.image = self.idle_frames[0]
            self.rect = self.image.get_rect(midbottom=anchor)
            return

        self.frame_index += self.fire_animation_speed * dt
        frame_number = min(int(self.frame_index), len(self.fire_frames) - 1)
        self.image = self.fire_frames[frame_number]
        self.rect = self.image.get_rect(midbottom=anchor)

        if not self.fired_this_cycle and frame_number >= 2:
            self.spawn_pearl(terrain_rects)
            self.fired_this_cycle = True

        if self.frame_index >= len(self.fire_frames):
            self.state = "idle"
            self.frame_index = 0.0
            self.image = self.idle_frames[0]
            self.rect = self.image.get_rect(midbottom=anchor)

    def update(self, dt, player, terrain_rects, world_rect):
        if self.state == "idle":
            self.time_since_fire_ms += dt * 1000
            if self.time_since_fire_ms >= self.fire_cooldown_ms:
                self.time_since_fire_ms = 0
                self.start_fire_cycle()

        self.update_animation(dt, terrain_rects)

        for projectile in self.projectiles:
            projectile.update(dt, player, terrain_rects, world_rect)

        self.projectiles = [
            projectile for projectile in self.projectiles
            if projectile.active
        ]

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, self.rect.move(offset))
        for projectile in self.projectiles:
            projectile.draw(screen, offset)
