import pygame
import random # Import random module 
from setting import SETTING # Import game setting 
from classes.player import Player # Import player from the player class
from classes.platform import Platform # Import platform from the platform class
from classes.camera import Camera # Import Camera
from classes.ui import UI # Import UI
from classes.enemy import Enemy # Import enemy from the enemy class


# Initialize game
pygame.init()

screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
player = Player(100, 400)
enemy = Enemy(500, 400)
running = True
while running:         
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()
    player.move(keys)
    player.update()
    enemy.update(player)
    enemy.draw(screen)
    screen.fill((255, 255, 255))
    pygame.display.flip()
    ## GAME OVER CONDITIONS: 
    if not player.alive:
        print("Game Over!")
        running = False

    clock.tick(120)


# Create game window
screen = pygame.display.set_mode((SETTING["WIDTH"], SETTING["HEIGHT"]))
pygame.display.set_caption(SETTING["TITLE"])


pygame.quit()