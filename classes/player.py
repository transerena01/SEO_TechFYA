import pygame

class Player:
    def __init__(self, x, y, width=40, height=60):
        self.rect = pygame.Rect(x, y, width, height)

        self.color = (0, 150, 255)

        # movement
        self.speed = 5

        # game stats
        self.points = 3
        self.alive = True
    # MOVEMENT FUNCTION
    def move(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed
    def check_status(self):
        if self.points < 0:
            self.alive = False
    def update(self):
        self.check_status()
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)