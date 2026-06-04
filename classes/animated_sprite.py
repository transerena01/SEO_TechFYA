import pygame
from pygame.sprite import Sprite

from classes.loader import load_frames as load_animation_frames


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
        self.position = pygame.Vector2(self.rect.topleft)
        self.velocity = pygame.Vector2(velocity)

    @staticmethod
    def load_frames(folder_path, size=None):
        return load_animation_frames(folder_path, size=size)

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
    ):
        frames = cls.load_frames(folder_path, size=size)
        return cls(
            position,
            frames,
            groups=groups,
            animation_speed=animation_speed,
            anchor=anchor,
            velocity=velocity,
        )

    def move(self, dt=1 / 60):
        self.position += self.velocity * dt
        self.rect.topleft = (round(self.position.x), round(self.position.y))

    def animate(self, dt=1 / 60):
        if len(self.frames) == 1:
            return

        anchor_position = getattr(self.rect, self.anchor)
        self.frame_index = (self.frame_index + (self.animation_speed * dt)) % len(self.frames)
        self.image = self.frames[int(self.frame_index)]
        self.rect = self.image.get_rect(**{self.anchor: anchor_position})
        self.position.update(self.rect.topleft)

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
