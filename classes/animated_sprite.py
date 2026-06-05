import math

import pygame
from pygame.sprite import Sprite

from classes.loader import load_frames as load_animation_frames, load_image


class AnimatedSprite(Sprite):
    def __init__(
        self,
        position,
        frames,
        *,
        groups=None,
        animation_speed=8,
        anchor="topleft",
        velocity=(0, 0),
    ):
        if groups is None:
            super().__init__()
        elif isinstance(groups, (list, tuple, set)):
            super().__init__(*groups)
        else:
            super().__init__(groups)

        if not frames:
            raise ValueError("AnimatedSprite requires at least one frame.")

        self.frames = frames
        self.frame_index = 0
        self.animation_speed = animation_speed
        self.anchor = anchor

        self.image = self.frames[0]
        self.rect = self.image.get_rect(**{self.anchor: position})
        self.anchor_position = pygame.Vector2(getattr(self.rect, self.anchor))
        self.position = pygame.Vector2(self.rect.topleft)
        self.velocity = pygame.Vector2(velocity)

    @staticmethod
    def load_frames(folder_path, size=None, flip_x=False):
        return load_animation_frames(folder_path, size=size, flip_x=flip_x)

    @classmethod
    def from_folder(
        cls,
        folder_path,
        position,
        *,
        size=None,
        groups=None,
        animation_speed=8,
        anchor="topleft",
        velocity=(0, 0),
        flip_x=False,
    ):
        frames = cls.load_frames(folder_path, size=size, flip_x=flip_x)
        return cls(
            position,
            frames,
            groups=groups,
            animation_speed=animation_speed,
            anchor=anchor,
            velocity=velocity,
        )

    def set_top_left(self, position):
        self.position.update(position)
        self.rect.topleft = (round(self.position.x), round(self.position.y))
        self.anchor_position.update(getattr(self.rect, self.anchor))

    def set_anchor_position(self, position):
        self.anchor_position.update(position)
        anchor_point = (
            round(self.anchor_position.x),
            round(self.anchor_position.y),
        )
        self.rect = self.image.get_rect(**{self.anchor: anchor_point})
        self.position.update(self.rect.topleft)

    def move(self, dt=1 / 60):
        self.position += self.velocity * dt
        self.set_top_left(self.position)

    def animate(self, dt=1 / 60):
        if len(self.frames) == 1:
            return

        self.frame_index = (self.frame_index + (self.animation_speed * dt)) % len(self.frames)
        self.image = self.frames[int(self.frame_index)]
        self.set_anchor_position(self.anchor_position)

    def update(self, dt=1 / 60):
        self.move(dt)
        self.animate(dt)

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, self.rect.move(offset))


class Collectible(AnimatedSprite):
    def __init__(
        self,
        item_name,
        position,
        frames,
        *,
        coin_value=0,
        health_value=0,
        groups=None,
        animation_speed=8,
        anchor="topleft",
        velocity=(0, 0),
    ):
        super().__init__(
            position,
            frames,
            groups=groups,
            animation_speed=animation_speed,
            anchor=anchor,
            velocity=velocity,
        )
        self.item_name = item_name
        self.coin_value = coin_value
        self.health_value = health_value

    @classmethod
    def from_folder(
        cls,
        folder_path,
        position,
        *,
        item_name,
        coin_value=0,
        health_value=0,
        size=None,
        groups=None,
        animation_speed=8,
        anchor="topleft",
        velocity=(0, 0),
    ):
        frames = cls.load_frames(folder_path, size=size)
        return cls(
            item_name,
            position,
            frames,
            coin_value=coin_value,
            health_value=health_value,
            groups=groups,
            animation_speed=animation_speed,
            anchor=anchor,
            velocity=velocity,
        )

    def collect(self, player):
        if self.coin_value:
            player.add_coins(self.coin_value)
        if self.health_value:
            player.heal(self.health_value)


class PathSprite(AnimatedSprite):
    def __init__(
        self,
        start_position,
        end_position,
        frames,
        *,
        speed=0,
        groups=None,
        animation_speed=8,
        anchor="center",
    ):
        super().__init__(
            start_position,
            frames,
            groups=groups,
            animation_speed=animation_speed,
            anchor=anchor,
        )
        self.path_start = pygame.Vector2(start_position)
        self.path_end = pygame.Vector2(end_position)
        self.path_delta = self.path_end - self.path_start
        self.path_length = self.path_delta.length()
        self.path_direction = (
            self.path_delta.normalize() if self.path_length else pygame.Vector2()
        )
        self.speed = speed
        self.distance = 0
        self.distance_direction = 1
        self.set_anchor_position(self.path_start)

    @classmethod
    def from_folder(
        cls,
        folder_path,
        start_position,
        end_position,
        *,
        speed=0,
        size=None,
        groups=None,
        animation_speed=8,
        anchor="center",
        flip_x=False,
    ):
        frames = cls.load_frames(folder_path, size=size, flip_x=flip_x)
        return cls(
            start_position,
            end_position,
            frames,
            speed=speed,
            groups=groups,
            animation_speed=animation_speed,
            anchor=anchor,
        )

    def move(self, dt=1 / 60):
        if self.path_length <= 0 or self.speed <= 0:
            return

        self.distance += self.distance_direction * self.speed * dt

        while self.distance > self.path_length or self.distance < 0:
            if self.distance > self.path_length:
                self.distance = (2 * self.path_length) - self.distance
                self.distance_direction = -1
            elif self.distance < 0:
                self.distance = -self.distance
                self.distance_direction = 1

        anchor_position = self.path_start + (self.path_direction * self.distance)
        self.set_anchor_position(anchor_position)


class OrbitalSprite(AnimatedSprite):
    def __init__(
        self,
        orbit_center,
        radius,
        start_angle,
        frames,
        *,
        speed=0,
        end_angle=-1,
        groups=None,
        animation_speed=8,
        anchor="center",
    ):
        self.orbit_center = pygame.Vector2(orbit_center)
        self.radius = radius
        self.start_angle = start_angle
        self.angle = start_angle
        self.end_angle = end_angle
        self.speed = speed
        self.angle_direction = 1
        super().__init__(
            self._get_anchor_position(),
            frames,
            groups=groups,
            animation_speed=animation_speed,
            anchor=anchor,
        )

    @staticmethod
    def angle_offset(radius, angle):
        radians = math.radians(angle)
        return pygame.Vector2(
            math.cos(radians) * radius,
            math.sin(radians) * radius,
        )

    def _get_anchor_position(self):
        return self.orbit_center + self.angle_offset(self.radius, self.angle)

    def move(self, dt=1 / 60):
        if self.radius <= 0 or self.speed <= 0:
            return

        angle_delta = math.degrees((self.speed * dt) / self.radius)

        if self.end_angle < 0:
            self.angle = (self.angle + angle_delta) % 360
        else:
            min_angle = min(self.start_angle, self.end_angle)
            max_angle = max(self.start_angle, self.end_angle)
            self.angle += self.angle_direction * angle_delta

            while self.angle > max_angle or self.angle < min_angle:
                if self.angle > max_angle:
                    self.angle = max_angle - (self.angle - max_angle)
                    self.angle_direction = -1
                elif self.angle < min_angle:
                    self.angle = min_angle + (min_angle - self.angle)
                    self.angle_direction = 1

        self.set_anchor_position(self._get_anchor_position())


class WaterArea:
    def __init__(self, rect, top_frames, body_tile, *, animation_speed=8):
        if not top_frames:
            raise ValueError("WaterArea requires at least one top frame.")

        self.rect = pygame.Rect(rect)
        self.top_frames = top_frames
        self.body_tile = body_tile
        self.animation_speed = animation_speed
        self.frame_index = 0
        self.top_height = self.top_frames[0].get_height()
        self.body_surface = self._build_tiled_surface(
            self.body_tile,
            self.rect.width,
            max(0, self.rect.height - self.top_height),
        )
        self.top_surfaces = [
            self._build_tiled_surface(frame, self.rect.width, self.top_height)
            for frame in self.top_frames
        ]

    @staticmethod
    def _build_tiled_surface(tile, width, height):
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        if width <= 0 or height <= 0:
            return surface

        tile_width, tile_height = tile.get_size()
        for y in range(0, height, tile_height):
            for x in range(0, width, tile_width):
                surface.blit(tile, (x, y))
        return surface

    @classmethod
    def from_assets(
        cls,
        rect,
        *,
        top_folder,
        body_path,
        animation_speed=8,
    ):
        top_frames = load_animation_frames(top_folder)
        body_tile = load_image(body_path)
        return cls(
            rect,
            top_frames,
            body_tile,
            animation_speed=animation_speed,
        )

    def update(self, dt=1 / 60):
        if len(self.top_frames) == 1:
            return

        self.frame_index = (
            self.frame_index + (self.animation_speed * dt)
        ) % len(self.top_frames)

    def draw(self, screen, offset=(0, 0)):
        draw_rect = self.rect.move(offset)
        if self.body_surface.get_height() > 0:
            screen.blit(
                self.body_surface,
                (draw_rect.x, draw_rect.y + self.top_height),
            )
        top_surface = self.top_surfaces[int(self.frame_index)]
        screen.blit(top_surface, draw_rect.topleft)
