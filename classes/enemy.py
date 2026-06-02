import pygame
import os


class Enemy:
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
        frames = []

        folder_path = os.path.join(
            "asset",
            "enemy",
            "Fierce Tooth",
            folder_name
        )

        for file_name in sorted(os.listdir(folder_path)):
            if file_name.endswith(".png"):
                image_path = os.path.join(folder_path, file_name)
                image = pygame.image.load(image_path).convert_alpha()
                image = pygame.transform.scale(image, (self.width, self.height))
                frames.append(image)

        return frames

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
                player.points -= self.damage
                self.last_hit_time = current_time
                print("Player got hit! Points:", player.points)

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
