import os

import pygame


class Player:
    def __init__(self, x, y, width=100, height=90):
        self.rect = pygame.Rect(x, y, width, height)

        self.speed = 5
        self.velocity_y = 0
        self.gravity = 0.5
        self.jump_force = -12
        self.on_ground = False
        self.horizontal_input = 0
        self.facing_right = True
        self.previous_y = self.rect.y

        self.points = 3
        self.alive = True

        self.animations = {
            "run": self.load_animation("02-Run"),
            "jump": self.load_animation("03-Jump"),
            "fall": self.load_animation("04-Fall"),
            "ground": self.load_animation("05-Ground"),
        }
        self.state = "ground"
        self.frame_index = 0
        self.animation_speed = 0.06
        self.image = self.animations[self.state][0]

    def load_animation(self, folder_name):
        frames = []
        candidate_roots = [
            os.path.join("asset", "graphics", "character", "Pink Star"),
            os.path.join("asset", "character", "Pink Star"),
        ]
        folder_path = next(
            (
                os.path.join(root, folder_name)
                for root in candidate_roots
                if os.path.isdir(os.path.join(root, folder_name))
            ),
            None,
        )
        if folder_path is None:
            raise FileNotFoundError(
                f"Could not find animation folder '{folder_name}' in: {candidate_roots}"
            )

        for file_name in sorted(os.listdir(folder_path)):
            if not file_name.endswith(".png"):
                continue

            image_path = os.path.join(folder_path, file_name)
            image = pygame.image.load(image_path).convert_alpha()
            image = pygame.transform.scale(image, (self.rect.width, self.rect.height))
            frames.append(image)

        return frames

    def move(self, keys, terrain_rects):
        was_on_ground = self.on_ground
        self.previous_y = self.rect.y
        self.horizontal_input = 0

        if keys[pygame.K_LEFT]:
            self.horizontal_input = -1
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.horizontal_input = 1
            self.facing_right = True

        self.rect.x += self.horizontal_input * self.speed
        self.collide_horizontal(terrain_rects)

        if keys[pygame.K_UP] and self.on_ground:
            self.velocity_y = self.jump_force
            self.on_ground = False

        self.velocity_y += self.gravity
        self.rect.y += int(self.velocity_y)
        self.on_ground = False
        self.collide_vertical(terrain_rects)

        if not self.on_ground and was_on_ground and self.velocity_y >= 0:
            self.check_ground_support(terrain_rects)

    def collide_horizontal(self, terrain_rects):
        for rect in terrain_rects:
            if self.rect.colliderect(rect):
                if self.rect.centerx < rect.centerx:
                    self.rect.right = rect.left
                else:
                    self.rect.left = rect.right

    def collide_vertical(self, terrain_rects):
        for rect in terrain_rects:
            if self.rect.colliderect(rect):
                if self.velocity_y > 0:
                    self.rect.bottom = rect.top
                    self.on_ground = True
                elif self.velocity_y < 0:
                    self.rect.top = rect.bottom
                self.velocity_y = 0

    def check_ground_support(self, terrain_rects):
        support_rect = self.rect.move(0, 1)
        for rect in terrain_rects:
            if support_rect.colliderect(rect):
                self.on_ground = True
                self.velocity_y = 0
                return

    def update_state(self):
        if not self.on_ground:
            if self.rect.y > self.previous_y:
                self.state = "fall"
            else:
                self.state = "jump"
        elif self.horizontal_input != 0:
            self.state = "run"
        else:
            self.state = "ground"

    def animate(self):
        frames = self.animations[self.state]
        self.frame_index += self.animation_speed

        if self.frame_index >= len(frames):
            self.frame_index = 0

        frame = frames[int(self.frame_index)]
        if self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        self.image = frame

    def check_status(self):
        if self.points <= 0:
            self.alive = False

    def update(self):
        self.check_status()
        previous_state = self.state
        self.update_state()
        if previous_state != self.state:
            self.frame_index = 0
        self.animate()

    def draw(self, screen, offset=(0, 0)):
        draw_rect = self.rect.move(offset)
        screen.blit(self.image, draw_rect)
