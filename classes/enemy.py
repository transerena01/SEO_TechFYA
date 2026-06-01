import pygame

class Enemy:
    def __init__(self, x, y, width=40, height=40, speed=2, patrol_distance=120):
        self.rect = pygame.Rect(x, y, width, height)
        self.start_x = x
        self.speed = speed
        self.direction = 1
        self.patrol_distance = patrol_distance

        self.damage = 1
        self.last_hit_time = 0
        self.hit_cooldown = 1000  # 1000 ms = 1 second

    def move(self):
        self.rect.x += self.speed * self.direction

        if self.rect.x > self.start_x + self.patrol_distance:
            self.direction = -1
        elif self.rect.x < self.start_x:
            self.direction = 1

    def attack_player(self, player):
        current_time = pygame.time.get_ticks()

        if self.rect.colliderect(player.rect):
            if current_time - self.last_hit_time >= self.hit_cooldown:
                player.points -= self.damage
                self.last_hit_time = current_time
                print("Player got hit! Points:", player.points)

    def update(self, player):
        self.move()
        self.attack_player(player)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)