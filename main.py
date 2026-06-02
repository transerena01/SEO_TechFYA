import pygame
import sys

from settings import SETTINGS
from classes.player import Player
from classes.camera import Camera
from classes.ui import StartScreen
from classes.enemy import Enemy
from classes.tilemap import GameMap


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
game_map = GameMap(SETTINGS["MAP_FILE"])
camera = Camera(
    SETTINGS["WIDTH"],
    SETTINGS["HEIGHT"],
    game_map.pixel_width,
    game_map.pixel_height,
    follow_y=True,
)

terrain_rects = game_map.get_terrain_rects()
terrain_rects += game_map.get_boundary_rects()

player = Player(0, 0)
player_spawn = game_map.get_object_anchor("Player")
if player_spawn:
    player.rect.midbottom = player_spawn
else:
    player.rect.topleft = (100, 400)

player.rect.left = max(0, player.rect.left)
player.rect.top = max(0, player.rect.top)
player.check_ground_support(terrain_rects)
camera.snap_to(player.rect)

enemy = Enemy(500, 400)

running = True
while running:
    dt = clock.tick(SETTINGS["FPS"]) / 1000 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif state == "start":
            action = start_screen.handle_event(event)
            if action == "game":
                state = "game"

    # Start Screen
    if state == "start":
        start_screen.update()
        start_screen.draw()

    # GAME
    elif state == "game":
        keys = pygame.key.get_pressed()
        player.move(keys, terrain_rects)  
        player.update()
        enemy.update(player)
        camera.update(player.rect)

        world_offset = game_map.get_draw_offset(camera)
        screen.fill(SETTINGS["SKY_COLOR"]) 
        game_map.draw_background(screen, camera)
        player.draw(screen, world_offset)
        enemy.draw(screen, world_offset)
        game_map.draw_foreground(screen, camera)

        if not player.alive:
            print("Game Over!")
            running = False

    pygame.display.update()
    # clock.tick() already called above for dt — don't call again here

pygame.quit()
sys.exit()
