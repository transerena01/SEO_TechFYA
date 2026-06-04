import pygame
import sys

from settings import SETTINGS
from classes.animated_sprite import AnimatedSprite
from classes.enemy import Tooth, Shell
from classes.player import Player
from classes.camera import Camera
from classes.ui import GameHUD, StartScreen
from classes.tilemap import GameMap


pygame.init()

screen = pygame.display.set_mode((SETTINGS["WIDTH"], SETTINGS["HEIGHT"]))
pygame.display.set_caption(SETTINGS["TITLE"])
clock = pygame.time.Clock()

# Game states
state = "start"
start_screen = StartScreen(screen)

# Game objects
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
camera.update(player.rect)

hud_anchor = game_map.get_object_by_name("Data")
if hud_anchor:
    hud_position = (
        round(hud_anchor["x"]) + 16,
        round(hud_anchor["y"]) + 16,
    )
else:
    hud_position = (16, 16)

game_hud = GameHUD(hud_position, heart_count=5)

teeth = []
tooth_objects = [
    obj for obj in game_map.get_objects()
    if (obj["name"] or "").lower() == "tooth"
]

for tooth_object in tooth_objects:
    tooth_size = (
        max(1, round(tooth_object["width"])),
        max(1, round(tooth_object["height"])),
    )
    tooth_spawn = (
        round(tooth_object["x"] + (tooth_object["width"] / 2)),
        round(tooth_object["y"] + tooth_object["height"]),
    )
    tooth = Tooth(0, 0, width=tooth_size[0], height=tooth_size[1])
    tooth.rect.midbottom = tooth_spawn
    tooth.start_x = tooth.rect.x
    teeth.append(tooth)

if not teeth:
    fallback_tooth = Tooth(500, 400)
    fallback_tooth.start_x = fallback_tooth.rect.x
    teeth.append(fallback_tooth)

animated_objects = []
shells = []
world_rect = pygame.Rect(0, 0, game_map.pixel_width, game_map.pixel_height)

flag_object = game_map.get_object_by_name("flag")
if flag_object:
    flag_position = (
        round(flag_object["x"] + (flag_object["width"] / 2)),
        round(flag_object["y"] + flag_object["height"]),
    )
    flag_size = (
        max(1, round(flag_object["width"])),
        max(1, round(flag_object["height"])),
    )
    animated_objects.append(
        AnimatedSprite.from_folder(
            "asset/graphics/level/flag",
            flag_position,
            size=flag_size,
            anchor="midbottom",
            animation_speed=8,
        )
    )

shell_objects = [
    obj for obj in game_map.get_objects()
    if (obj["name"] or "").lower() == "shell"
]

for shell_object in shell_objects:
    shell_spawn = (
        round(shell_object["x"] + (shell_object["width"] / 2)),
        round(shell_object["y"] + shell_object["height"]),
    )
    shell_size = (
        max(1, round(shell_object["width"])),
        max(1, round(shell_object["height"])),
    )
    shell_properties = shell_object.get("properties", {})
    shell_facing_right = bool(shell_properties.get("reverse", False)) ^ bool(shell_object.get("flip_x", False))
    shells.append(
        Shell(
            shell_spawn,
            shell_size,
            reverse=shell_facing_right,
        )
    )

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
        for tooth in teeth:
            tooth.update(player)
        game_hud.update(dt)
        for shell in shells:
            shell.update(dt, player, terrain_rects, world_rect)
        for animated_object in animated_objects:
            animated_object.update(dt)
        camera.update(player.rect)
 
        offset = camera.get_offset()
        screen.fill(SETTINGS["SKY_COLOR"]) 
        game_map.draw_background(screen, camera)
        for animated_object in animated_objects:
            animated_object.draw(screen, offset)
        for shell in shells:
            shell.draw(screen, offset)
        player.draw(screen, offset)
        for tooth in teeth:
            tooth.draw(screen, offset)
        game_map.draw_foreground(screen, camera)
        game_hud.draw(screen, player.points, player.max_points)
 
        if not player.alive:
            running = False

    pygame.display.update()
    # clock.tick() already called above for dt — don't call again here

pygame.quit()
sys.exit()
