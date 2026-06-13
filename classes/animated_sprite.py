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
        invincibility_duration_ms=0,
        groups=None,
        animation_speed=8,
        anchor="topleft",
        velocity=(0, 0),
        hover_amplitude=0,
        hover_speed=0,
        hover_phase=0,
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
        self.invincibility_duration_ms = max(0, int(invincibility_duration_ms))
        self.base_anchor_position = pygame.Vector2(self.anchor_position)
        self.hover_amplitude = max(0.0, float(hover_amplitude))
        self.hover_speed = max(0.0, float(hover_speed))
        self.hover_phase = float(hover_phase)
        self.hover_elapsed = 0.0

    @classmethod
    def from_folder(
        cls,
        folder_path,
        position,
        *,
        item_name,
        coin_value=0,
        health_value=0,
        invincibility_duration_ms=0,
        size=None,
        groups=None,
        animation_speed=8,
        anchor="topleft",
        velocity=(0, 0),
        hover_amplitude=0,
        hover_speed=0,
        hover_phase=0,
    ):
        frames = cls.load_frames(folder_path, size=size)
        return cls(
            item_name,
            position,
            frames,
            coin_value=coin_value,
            health_value=health_value,
            invincibility_duration_ms=invincibility_duration_ms,
            groups=groups,
            animation_speed=animation_speed,
            anchor=anchor,
            velocity=velocity,
            hover_amplitude=hover_amplitude,
            hover_speed=hover_speed,
            hover_phase=hover_phase,
        )

    @classmethod
    def from_image(
        cls,
        image_path,
        position,
        *,
        item_name,
        coin_value=0,
        health_value=0,
        invincibility_duration_ms=0,
        size=None,
        groups=None,
        anchor="topleft",
        velocity=(0, 0),
        hover_amplitude=0,
        hover_speed=0,
        hover_phase=0,
    ):
        return cls(
            item_name,
            position,
            [load_image(image_path, size=size)],
            coin_value=coin_value,
            health_value=health_value,
            invincibility_duration_ms=invincibility_duration_ms,
            groups=groups,
            animation_speed=0,
            anchor=anchor,
            velocity=velocity,
            hover_amplitude=hover_amplitude,
            hover_speed=hover_speed,
            hover_phase=hover_phase,
        )

    def move(self, dt=1 / 60):
        self.base_anchor_position += self.velocity * dt
        float_offset_y = 0.0
        if self.hover_amplitude > 0 and self.hover_speed > 0:
            self.hover_elapsed += dt
            float_offset_y = -math.sin(
                (self.hover_elapsed * self.hover_speed) + self.hover_phase
            ) * self.hover_amplitude
        self.set_anchor_position(
            self.base_anchor_position + pygame.Vector2(0, float_offset_y)
        )

    def collect(self, player):
        if self.coin_value:
            player.add_coins(self.coin_value)
        if self.health_value:
            player.heal(self.health_value)
        if self.invincibility_duration_ms:
            player.grant_invincibility(self.invincibility_duration_ms)


class LeverSwitch(AnimatedSprite):
    def __init__(
        self,
        position,
        inactive_image,
        active_image,
        *,
        groups=None,
        anchor="midbottom",
    ):
        super().__init__(
            position,
            [inactive_image],
            groups=groups,
            animation_speed=0,
            anchor=anchor,
        )
        self.inactive_image = inactive_image
        self.active_image = active_image
        self.is_activated = False

    @classmethod
    def from_images(
        cls,
        position,
        *,
        inactive_path,
        active_path,
        size=None,
        groups=None,
        anchor="midbottom",
    ):
        inactive_image = load_image(inactive_path, size=size)
        active_image = load_image(active_path, size=size)
        return cls(
            position,
            inactive_image,
            active_image,
            groups=groups,
            anchor=anchor,
        )

    def activate(self):
        if self.is_activated:
            return False

        self.is_activated = True
        self.image = self.active_image
        self.set_anchor_position(self.anchor_position)
        return True


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

    def get_path_anchor_position(self):
        return self.path_start + (self.path_direction * self.distance)

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

        self.set_anchor_position(self.get_path_anchor_position())


class FloatingPathSprite(PathSprite):
    def __init__(
        self,
        start_position,
        end_position,
        frames,
        *,
        water_area=None,
        groups=None,
        speed=0,
        animation_speed=8,
        anchor="center",
    ):
        self.water_area = water_area
        super().__init__(
            start_position,
            end_position,
            frames,
            speed=speed,
            groups=groups,
            animation_speed=animation_speed,
            anchor=anchor,
        )

    def get_float_offset_y(self):
        if self.water_area is None:
            return 0
        return self.water_area.rect.top - self.water_area.initial_top

    def move(self, dt=1 / 60):
        super().move(dt)
        base_anchor_position = self.get_path_anchor_position()
        float_offset_y = self.get_float_offset_y()
        if float_offset_y:
            self.set_anchor_position(
                base_anchor_position + pygame.Vector2(0, float_offset_y)
            )
        elif self.anchor_position != base_anchor_position:
            self.set_anchor_position(base_anchor_position)


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
    def __init__(
        self,
        rect,
        top_frames,
        body_tile,
        *,
        animation_speed=8,
        rise_speed=0,
        rise_delay=0,
        rise_target_y=0,
    ):
        if not top_frames:
            raise ValueError("WaterArea requires at least one top frame.")

        self.rect = pygame.Rect(rect)
        self.initial_top = self.rect.top
        self.bottom = self.rect.bottom
        self.top_frames = top_frames
        self.body_tile = body_tile
        self.animation_speed = animation_speed
        self.rise_speed = max(0.0, float(rise_speed))
        self.rise_delay = max(0.0, float(rise_delay))
        self.rise_target_y = min(self.rect.top, round(float(rise_target_y)))
        self.top_position = float(self.rect.top)
        self.elapsed = 0.0
        self.frame_index = 0
        self.top_height = self.top_frames[0].get_height()
        self.body_surface = self._build_tiled_surface(
            self.body_tile,
            self.rect.width,
            max(0, self.bottom - self.top_height - self.rise_target_y),
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
        rise_speed=0,
        rise_delay=0,
        rise_target_y=0,
    ):
        top_frames = load_animation_frames(top_folder)
        body_tile = load_image(body_path)
        return cls(
            rect,
            top_frames,
            body_tile,
            animation_speed=animation_speed,
            rise_speed=rise_speed,
            rise_delay=rise_delay,
            rise_target_y=rise_target_y,
        )

    def rise(self, pixels):
        """Move the water surface up by `pixels` (sub-pixel safe).

        pygame.Rect only stores integers, so tiny per-frame amounts
        (e.g. 8px/s x 0.016s = 0.13px) would truncate to 0 every frame.
        A float accumulator banks fractional pixels and only commits
        whole pixels, so the rise is smooth and nothing is lost.
        """
        self._rise_accum = getattr(self, "_rise_accum", 0.0) + pixels
        whole = int(self._rise_accum)
        if whole == 0:
            return
        self._rise_accum -= whole
        self.rect.y      -= whole
        self.rect.height += whole
        new_body_height = max(0, self.rect.height - self.top_height)
        self.body_surface = self._build_tiled_surface(
            self.body_tile,
            self.rect.width,
            new_body_height,
        )

    def update(self, dt=1 / 60):
        if len(self.top_frames) > 1:
            self.frame_index = (
                self.frame_index + (self.animation_speed * dt)
            ) % len(self.top_frames)

        if self.rise_speed <= 0:
            return

        self.elapsed += dt
        if self.elapsed < self.rise_delay or self.top_position <= self.rise_target_y:
            return

        # Keep the bottom edge fixed and raise only the waterline.
        self.top_position = max(
            self.rise_target_y,
            self.top_position - (self.rise_speed * dt),
        )
        new_top = round(self.top_position)
        if new_top != self.rect.top:
            self.rect.top = new_top
            self.rect.height = max(self.top_height, self.bottom - self.rect.top)

    def draw(self, screen, offset=(0, 0)):
        draw_rect = self.rect.move(offset)
        body_height = max(0, self.rect.height - self.top_height)
        if body_height > 0:
            screen.blit(
                self.body_surface,
                (draw_rect.x, draw_rect.y + self.top_height),
                area=pygame.Rect(0, 0, self.rect.width, body_height),
            )
        top_surface = self.top_surfaces[int(self.frame_index)]
        screen.blit(top_surface, draw_rect.topleft)
