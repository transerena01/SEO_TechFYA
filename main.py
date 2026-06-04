import pygame
import sys

from settings import SETTINGS
from classes.animated_sprite import AnimatedSprite, Collectible
from classes.enemy import Tooth, Shell
from classes.player import Player
from classes.camera import Camera
from classes.ui import GameHUD, StartScreen
from classes.tilemap import GameMap


pygame.init()
pygame.mixer.init()

pygame.mixer.music.load("asset/SEOmusic/Pokémon Ruby and Sapphire - Oceanic Museum (Remix).mp3")
pygame.mixer.music.set_volume(0.4)
pygame.mixer.music.play(-1)
coin_sound = pygame.mixer.Sound(
        "asset/SEOmusic/ES_User Interface, Alert, Success, Reward, Bright, Happy Twinkle, Short - Epidemic Sound.mp3"
    )
coin_sound.set_volume(0.6)
enemy_hit_sound = pygame.mixer.Sound(
        "asset/SEOmusic/ES_Games, Video, Retro, Enemy Attack 03 - Epidemic Sound.mp3"
    )
enemy_hit_sound.set_volume(0.6)

screen = pygame.display.set_mode((SETTINGS["WIDTH"], SETTINGS["HEIGHT"]))
pygame.display.set_caption(SETTINGS["TITLE"])
clock = pygame.time.Clock()


def scale_size(size, scale):
    return (
        max(1, round(size[0] * scale)),
        max(1, round(size[1] * scale)),
    )


def scale_size_xy(size, scale_x, scale_y):
    return (
        max(1, round(size[0] * scale_x)),
        max(1, round(size[1] * scale_y)),
    )

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

game_hud = GameHUD(
    hud_position,
    heart_count=5,
    coin_scale=SETTINGS["HUD_COIN_SCALE"],
)

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
    tooth_size = scale_size(tooth_size, SETTINGS["TOOTH_SCALE"])
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
collectibles = []
shells = []
world_rect = pygame.Rect(0, 0, game_map.pixel_width, game_map.pixel_height)

animated_object_folders = {
    "flag": "asset/graphics/level/flag",
    "gold": "asset/graphics/items/gold",
    "silver": "asset/graphics/items/silver",
    "diamond": "asset/graphics/items/diamond",
    "potion": "asset/graphics/items/potion",
    "skull": "asset/graphics/items/skull",
}
pickup_object_names = {"gold", "silver", "diamond", "potion", "skull"}
pickup_coin_values = SETTINGS["COLLECTIBLE_COIN_VALUES"]
pickup_health_values = SETTINGS["COLLECTIBLE_HEALTH_VALUES"]

for map_object in game_map.get_objects():
    object_name = (map_object["name"] or "").lower()
    asset_folder = animated_object_folders.get(object_name)
    if asset_folder is None:
        continue

    object_position = (
        round(map_object["x"] + (map_object["width"] / 2)),
        round(map_object["y"] + map_object["height"]),
    )
    object_size = (
        max(1, round(map_object["width"])),
        max(1, round(map_object["height"])),
    )
    if object_name in pickup_object_names:
        if object_name == "skull":
            object_size = scale_size_xy(
                object_size,
                SETTINGS["SKULL_SCALE_X"],
                SETTINGS["SKULL_SCALE_Y"],
            )
        else:
            object_size = scale_size(object_size, SETTINGS["ITEM_SCALE"])
        collectibles.append(
            Collectible.from_folder(
                asset_folder,
                object_position,
                item_name=object_name,
                coin_value=pickup_coin_values.get(object_name, 0),
                health_value=pickup_health_values.get(object_name, 0),
                size=object_size,
                anchor="midbottom",
                animation_speed=8,
            )
        )
        continue

    animated_objects.append(
        AnimatedSprite.from_folder(
            asset_folder,
            object_position,
            size=object_size,
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

        # Tooth enemies
        for tooth in teeth:
            old_points = player.points
            tooth.update(player)
            if player.points < old_points:
                enemy_hit_sound.play()

        game_hud.update(dt)

        # Shell enemies
        for shell in shells:
            old_points = player.points
            shell.update(dt, player, terrain_rects, world_rect)
            if player.points < old_points:
                enemy_hit_sound.play()

        for animated_object in animated_objects:
            animated_object.update(dt)

        # Collectibles
        for collectible in collectibles[:]:
            collectible.update(dt)
            if collectible.rect.colliderect(player.rect):
                coin_sound.play()
                collectible.collect(player)
                collectibles.remove(collectible)

        camera.update(player.rect)
 
        offset = camera.get_offset()
        screen.fill(SETTINGS["SKY_COLOR"]) 
        game_map.draw_background(screen, camera)

        for animated_object in animated_objects:
            animated_object.draw(screen, offset)

        for collectible in collectibles:
            collectible.draw(screen, offset)

        for shell in shells:
            shell.draw(screen, offset)

        player.draw(screen, offset)

        for tooth in teeth:
            tooth.draw(screen, offset)

        game_map.draw_foreground(screen, camera)
        game_hud.draw(screen, player.points, player.max_points, player.coin_progress)
 
        if not player.alive:
            running = False

    pygame.display.update()
    # clock.tick() already called above for dt — don't call again here

pygame.quit()
sys.exit()
