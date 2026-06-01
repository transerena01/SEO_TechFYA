import sys

import pygame

from settings import SETTINGS
from classes.player import Player
from classes.ui import StartScreen
from classes.enemy import Enemy


pygame.init()

screen = pygame.display.set_mode((SETTINGS["WIDTH"], SETTINGS["HEIGHT"]))
pygame.display.set_caption(SETTINGS["TITLE"])
clock = pygame.time.Clock()

# Game states
state = "start"
start_screen = StartScreen(screen)

# Game objects
background = pygame.image.load(SETTINGS["BG_IMAGE"]).convert()
background = pygame.transform.scale(background, (SETTINGS["WIDTH"], SETTINGS["HEIGHT"]))
player = Player(100, 400)
enemy = Enemy(500, 400)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif state == "start":
            action = start_screen.handle_event(event)
            if action == "game":
                state = "game"

    if state == "start":
        start_screen.update()
        start_screen.draw()
    elif state == "game":
        keys = pygame.key.get_pressed()
        player.move(keys)
        player.update()
        enemy.update(player)

        screen.blit(background, (0, 0))
        player.draw(screen)
        enemy.draw(screen)

        if not player.alive:
            print("Game Over!")
            running = False

    pygame.display.update()
    clock.tick(SETTINGS["FPS"])

pygame.quit()
sys.exit()
