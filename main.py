import pygame
import sys
import random
from settings import SETTINGS
from classes.player import Player
from classes.platform import Platform
from classes.camera import Camera
from classes.ui import StartScreen
from classes.enemy import Enemy

pygame.init()

screen = pygame.display.set_mode((SETTINGS["WIDTH"], SETTINGS["HEIGHT"]))
pygame.display.set_caption(SETTINGS["TITLE"])
clock  = pygame.time.Clock()

# Game states
state        = "start"
start_screen = StartScreen(screen)

# Game objects (init sau khi bắt đầu game)
background = pygame.image.load(SETTINGS["BG_IMAGE"]).convert()
background = pygame.transform.scale(background, (SETTINGS["WIDTH"], SETTINGS["HEIGHT"]))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif state == "start":
            action = start_screen.handle_event(event)
            if action == "game":
                state = "game"

    # ── START SCREEN ──
    if state == "start":
        start_screen.update()
        start_screen.draw()

    # ── GAME ──
    elif state == "game":
        screen.blit(background, (0, 0))
        # TODO: update & draw player, enemies, platforms

    pygame.display.update()
    clock.tick(SETTINGS["FPS"])

pygame.quit()
sys.exit()
