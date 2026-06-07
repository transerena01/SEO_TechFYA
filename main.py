import pygame
import sys

from settings import SETTINGS
from classes.animated_sprite import (
    AnimatedSprite,
    Collectible,
    OrbitalSprite,
    PathSprite,
    WaterArea,
)
from classes.enemy import Tooth, Shell
from classes.loader import load_font, load_image, load_music, load_sound
from classes.player import Player
from classes.platform import MovingPlatformSystem
from classes.camera import Camera
from classes.ui import GameHUD, LoseScreen, StartScreen, WinScreen
from classes.tilemap import GameMap


pygame.init()
pygame.mixer.init()

START_SCREEN_MUSIC_PATH = "asset/SEOmusic/Intro_hello_Vietnam.mp3"
MAIN_GAME_MUSIC_PATH = "asset/SEOmusic/Pokémon Ruby and Sapphire - Oceanic Museum (Remix).mp3"


def play_background_music(path, volume):
    load_music(path, volume=volume, loops=-1)


play_background_music(START_SCREEN_MUSIC_PATH, volume=0.6)

coin_sound = load_sound(
    "asset/SEOmusic/ES_User Interface, Alert, Success, Reward, Bright, Happy Twinkle, Short - Epidemic Sound.mp3",
    volume=0.6,
)
enemy_hit_sound = load_sound(
    "asset/SEOmusic/ES_Games, Video, Retro, Enemy Attack 03 - Epidemic Sound.mp3",
    volume=0.6,
)

screen = pygame.display.set_mode((SETTINGS["WIDTH"], SETTINGS["HEIGHT"]))
pygame.display.set_caption(SETTINGS["TITLE"])
clock = pygame.time.Clock()
timer_font = load_font(SETTINGS["FONT_PATH"], 36)

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


def get_path_endpoints(map_object, sprite_size):
    x = map_object["x"]
    y = map_object["y"]
    width = max(0, map_object["width"])
    height = max(0, map_object["height"])
    sprite_width, sprite_height = sprite_size

    if width >= height:
        center_y = y + (height / 2)
        start_x = x + min(width / 2, sprite_width / 2)
        end_x = x + max(width / 2, width - (sprite_width / 2))
        start = (round(start_x), round(center_y))
        end = (round(end_x), round(center_y))
    else:
        center_x = x + (width / 2)
        start_y = y + min(height / 2, sprite_height / 2)
        end_y = y + max(height / 2, height - (sprite_height / 2))
        start = (round(center_x), round(start_y))
        end = (round(center_x), round(end_y))

    if map_object.get("properties", {}).get("flip", False):
        start, end = end, start

    return start, end


# Game states
state = "start"
start_screen = StartScreen(screen)
lose_screen = LoseScreen(screen)
win_screen = WinScreen(screen)
lose_background = None
win_background = None

start_ticks = None
time_limit = 120  # seconds

# Game objects
game_map = GameMap(SETTINGS["MAP_FILE"])
map_objects = game_map.get_objects()

# Win condition: player touches the flag
_flag_obj = game_map.get_object_by_name("flag")
if _flag_obj:
    flag_rect = pygame.Rect(
        round(_flag_obj["x"]),
        round(_flag_obj["y"]),
        max(1, round(_flag_obj["width"])),
        max(1, round(_flag_obj["height"])),
    )
else:
    flag_rect = None

camera = Camera(
    SETTINGS["WIDTH"],
    SETTINGS["HEIGHT"],
    game_map.pixel_width,
    game_map.pixel_height,
    follow_y=True,
)

terrain_rects = game_map.get_terrain_rects()
terrain_rects += game_map.get_boundary_rects()

solid_object_names = {
    "barrel",
    "crate",
    "palm_small",
    "palm_large",
    "saw",
}
hazard_object_names = {"floor_spike", "saw"}
solid_object_rects = []
hazard_rects = []

for map_object in map_objects:
    object_name = (map_object["name"] or "").lower()
    object_layer = (map_object["layer"] or "").lower()
    object_rect = pygame.Rect(
        round(map_object["x"]),
        round(map_object["y"]),
        max(1, round(map_object["width"])),
        max(1, round(map_object["height"])),
    )

    if object_name in {"palm_large", "palm_small"}:
        collision_scale = (
            SETTINGS["PALM_LARGE_COLLISION_SCALE"]
            if object_name == "palm_large"
            else SETTINGS["PALM_SMALL_COLLISION_SCALE"]
        )
        scaled_rect = pygame.Rect(
            0,
            0,
            max(1, round(object_rect.width * collision_scale)),
            max(1, round(object_rect.height * collision_scale)),
        )
        scaled_rect.midbottom = object_rect.midbottom
        object_rect = scaled_rect

    if object_layer == "objects" and object_name in solid_object_names:
        solid_object_rects.append(object_rect)

    if object_layer == "objects" and object_name in hazard_object_names:
        hazard_rects.append(object_rect)

terrain_rects += solid_object_rects

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
    obj for obj in map_objects
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
moving_objects = []
moving_hazard_objects = []
water_areas = []
water_rects = []
world_rect = pygame.Rect(0, 0, game_map.pixel_width, game_map.pixel_height)
moving_platform_system = MovingPlatformSystem(terrain_rects)

animated_object_folders = {
    "flag": "asset/graphics/level/flag",
    "saw": "asset/graphics/enemies/saw/animation",
    "floor_spike": "asset/graphics/enemies/floor_spikes",
    "palm_bg": "asset/graphics/level/palms/palm_bg",
    "palm_bg_left": "asset/graphics/level/palms/palm_bg_left",
    "palm_bg_right": "asset/graphics/level/palms/palm_bg_right",
    "palm_small": "asset/graphics/level/palms/palm_small",
    "palm_large": "asset/graphics/level/palms/palm_large",
    "gold": "asset/graphics/items/gold",
    "silver": "asset/graphics/items/silver",
    "diamond": "asset/graphics/items/diamond",
    "potion": "asset/graphics/items/potion",
    "skull": "asset/graphics/items/skull",
}
static_object_images = {
    "barrel": "asset/graphics/objects/barrel.png",
    "crate": "asset/graphics/objects/crate.png",
}
pickup_object_names = {"gold", "silver", "diamond", "potion", "skull"}
pickup_coin_values = SETTINGS["COLLECTIBLE_COIN_VALUES"]
pickup_health_values = SETTINGS["COLLECTIBLE_HEALTH_VALUES"]
object_layer_animated_names = {
    "flag",
    "saw",
    "floor_spike",
    "palm_bg",
    "palm_bg_left",
    "palm_bg_right",
    "palm_small",
    "palm_large",
}

for map_object in map_objects:
    object_name = (map_object["name"] or "").lower()
    object_layer = (map_object["layer"] or "").lower()
    asset_folder = animated_object_folders.get(object_name)
    static_image_path = static_object_images.get(object_name)
    if asset_folder is None and static_image_path is None:
        continue

    if object_name in pickup_object_names and object_layer != "items":
        continue

    if (
        object_name in object_layer_animated_names
        or object_name in static_object_images
    ) and object_layer != "objects":
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

    if static_image_path is not None:
        animated_objects.append(
            AnimatedSprite(
                object_position,
                [load_image(static_image_path, size=object_size)],
                anchor="midbottom",
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
    obj for obj in map_objects
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
    shell_facing_right = bool(shell_properties.get("reverse", False)) ^ bool(
        shell_object.get("flip_x", False)
    )
    shells.append(
        Shell(
            shell_spawn,
            shell_size,
            reverse=shell_facing_right,
        )
    )

water_objects = [
    obj
    for obj in map_objects
    if (obj["layer"] or "").lower() == "water"
    and (obj["name"] or "").lower() == "water"
]

for water_object in water_objects:
    water_rect = pygame.Rect(
        round(water_object["x"]),
        round(water_object["y"]),
        max(1, round(water_object["width"])),
        max(1, round(water_object["height"])),
    )
    water_rects.append(water_rect)
    water_areas.append(
        WaterArea.from_assets(
            water_rect,
            top_folder="asset/graphics/level/water/top",
            body_path="asset/graphics/level/water/body.png",
            animation_speed=6,
        )
    )

moving_object_definitions = {
    "boat": {
        "image_path": "asset/graphics/objects/boat/0.png",
        "size": None,
        "animation_speed": 0,
    },
    "helicopter": {
        "folder_path": "asset/graphics/level/helicopter",
        "size": None,
        "animation_speed": 8,
    },
    "saw": {
        "folder_path": "asset/graphics/enemies/saw/animation",
        "size": (64, 64),
        "animation_speed": 12,
    },
}
moving_solid_object_names = {"boat", "saw", "helicopter"}
moving_hazard_object_names = {"saw", "spike"}
moving_spike_image_path = "asset/graphics/enemies/spike_ball/Spiked Ball.png"

for map_object in map_objects:
    object_name = (map_object["name"] or "").lower()
    object_layer = (map_object["layer"] or "").lower()
    object_properties = map_object.get("properties", {})

    if object_layer != "moving objects":
        continue

    if object_name == "spike":
        object_size = (
            max(1, round(map_object["width"])),
            max(1, round(map_object["height"])),
        )
        spike_center = (
            round(map_object["x"] + (map_object["width"] / 2)),
            round(map_object["y"] + (map_object["height"] / 2)),
        )
        start_angle = object_properties.get("start_angle", 0)
        radius = object_properties.get("radius", 0)
        orbit_center = (
            pygame.Vector2(spike_center)
            - OrbitalSprite.angle_offset(radius, start_angle)
        )
        moving_spike = OrbitalSprite(
            orbit_center,
            radius,
            start_angle,
            [load_image(moving_spike_image_path, size=object_size)],
            speed=object_properties.get("speed", 0),
            end_angle=object_properties.get("end_angle", -1),
            anchor="center",
        )
        moving_objects.append(moving_spike)
        moving_hazard_objects.append(moving_spike)
        continue

    moving_object_definition = moving_object_definitions.get(object_name)
    if moving_object_definition is None:
        continue

    flip_x = object_properties.get("flip", False)
    size = moving_object_definition["size"]
    animation_speed = moving_object_definition["animation_speed"]

    if "folder_path" in moving_object_definition:
        frames = AnimatedSprite.load_frames(
            moving_object_definition["folder_path"],
            size=size,
            flip_x=flip_x,
        )
    else:
        frames = [load_image(
            moving_object_definition["image_path"],
            size=size,
            flip_x=flip_x,
        )]

    sprite_size = frames[0].get_size()
    start_position, end_position = get_path_endpoints(map_object, sprite_size)
    moving_sprite = PathSprite(
        start_position,
        end_position,
        frames,
        speed=object_properties.get("speed", 0),
        animation_speed=animation_speed,
        anchor="center",
    )
    moving_objects.append(moving_sprite)
    moving_platform_system.register(
        moving_sprite,
        solid=object_name in moving_solid_object_names,
        platform=object_properties.get("platform", False),
    )
    if object_name in moving_hazard_object_names:
        moving_hazard_objects.append(moving_sprite)


def player_touches_hazard(player_rect, hazard_rect, padding=4):
    return player_rect.colliderect(hazard_rect.inflate(padding * 2, padding * 2))


def player_submerged_in_water(player_rect, water_rect):
    if not player_rect.colliderect(water_rect):
        return False

    submerged_height = player_rect.bottom - water_rect.top
    return submerged_height >= player_rect.height * 2.5


player.check_ground_support(moving_platform_system.get_collision_rects())

hazard_hit_cooldown_ms = 800
hazard_last_hit_time = -hazard_hit_cooldown_ms
hazard_damage = 1


def enter_lose_state():
    global lose_background, state
    lose_background = screen.copy()
    state = "lose"


def enter_win_state():
    global win_background, state, win_time_left
    win_background = screen.copy()
    win_time_left = time_left
    state = "win"


def reset_game():
    global player, start_ticks, hazard_last_hit_time, state, lose_background, win_background

    # reset player position
    player_spawn = game_map.get_object_anchor("Player")
    if player_spawn:
        player.rect.midbottom = player_spawn
    else:
        player.rect.topleft = (100, 400)

    # reset player stats
    player.points = player.max_points
    player.alive = True
    player.coins = 0
    player.coin_progress = 0
    player.rect.left = max(0, player.rect.left)
    player.rect.top = max(0, player.rect.top)
    player.check_ground_support(terrain_rects)

    # reset camera and timer
    camera.update(player.rect)
    start_ticks = pygame.time.get_ticks()
    hazard_last_hit_time = -hazard_hit_cooldown_ms
    lose_background = None
    win_background = None
    state = "game"


running = True
win_time_left = 0
while running:
    dt = clock.tick(SETTINGS["FPS"]) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif state == "start":
            action = start_screen.handle_event(event)
            if action == "game":
                reset_game()
                play_background_music(MAIN_GAME_MUSIC_PATH, volume=0.4)
        elif state == "lose":
            action = lose_screen.handle_event(event)
            if action == "retry":
                reset_game()
                continue
            if action == "menu":
                state = "start"
                lose_background = None
                continue
            if action == "exit":
                running = False
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                elif event.key in (pygame.K_m, pygame.K_ESCAPE):
                    running = False
        elif state == "win":
            action = win_screen.handle_event(event)
            if action == "retry":
                reset_game()
                play_background_music(MAIN_GAME_MUSIC_PATH, volume=0.4)
                continue
            if action == "menu":
                state = "start"
                win_background = None
                play_background_music(START_SCREEN_MUSIC_PATH, volume=0.6)
                continue
            if action == "exit":
                running = False
                continue

    # Start Screen
    if state == "start":
        start_screen.update()
        start_screen.draw()

    # GAME

    elif state == "game":
        elapsed_time = (pygame.time.get_ticks() - start_ticks) // 1000
        time_left = max(0, time_limit - elapsed_time)

        if time_left <= 0:
            enter_lose_state()
            continue

        standing_platform = moving_platform_system.get_supporting_platform(player)
        previous_moving_rects = moving_platform_system.snapshot_rects()

        for moving_object in moving_objects:
            moving_object.update(dt)

        carried_platform = moving_platform_system.carry_player(
            player,
            standing_platform,
            previous_moving_rects,
        )

        moving_platform_system.resolve_player_overlap(
            player,
            previous_moving_rects,
            carried_platform=carried_platform,
        )

        keys = pygame.key.get_pressed()
        player_collision_rects = moving_platform_system.get_collision_rects()
        player.move(keys, player_collision_rects)
        player.update()

        if any(player_submerged_in_water(player.rect, water_rect) for water_rect in water_rects):
            enter_lose_state()
            continue

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

        for water_area in water_areas:
            water_area.update(dt)

        for animated_object in animated_objects:
            animated_object.update(dt)

        # Collectibles
        for collectible in collectibles[:]:
            collectible.update(dt)
            if collectible.rect.colliderect(player.rect):
                coin_sound.play()
                collectible.collect(player)
                collectibles.remove(collectible)

        current_time = pygame.time.get_ticks()
        if current_time - hazard_last_hit_time >= hazard_hit_cooldown_ms:
            touching_static_hazard = any(
                player_touches_hazard(player.rect, hazard_rect)
                for hazard_rect in hazard_rects
            )
            touching_moving_hazard = any(
                player_touches_hazard(player.rect, moving_hazard.rect)
                for moving_hazard in moving_hazard_objects
            )
            if touching_static_hazard or touching_moving_hazard:
                enemy_hit_sound.play()
                player.take_damage(hazard_damage)
                hazard_last_hit_time = current_time
        camera.update(player.rect)

        # Win condition — player reaches the Vietnam flag
        if flag_rect and player.rect.colliderect(flag_rect):
            enter_win_state()
            continue

        offset = camera.get_offset()
        screen.fill(SETTINGS["SKY_COLOR"])
        game_map.draw_background(screen, camera)

        for water_area in water_areas:
            water_area.draw(screen, offset)

        for animated_object in animated_objects:
            animated_object.draw(screen, offset)

        for moving_object in moving_objects:
            moving_object.draw(screen, offset)

        for collectible in collectibles:
            collectible.draw(screen, offset)

        for shell in shells:
            shell.draw(screen, offset)

        player.draw(screen, offset)

        for tooth in teeth:
            tooth.draw(screen, offset)

        game_map.draw_foreground(screen, camera)
        game_hud.draw(screen, player.points, player.max_points, player.coin_progress)
        timer_text = timer_font.render(f"TIME: {time_left}", True, (255, 244, 214))
        screen.blit(timer_text, (SETTINGS["WIDTH"] - timer_text.get_width() - 30, 25))
        if not player.alive:
            enter_lose_state()
    elif state == "lose":
        if lose_background is not None:
            screen.blit(lose_background, (0, 0))
        else:
            screen.fill((23, 39, 66))
        lose_screen.draw(player.coins)
    elif state == "win":
        if win_background is not None:
            screen.blit(win_background, (0, 0))
        else:
            screen.fill((23, 39, 66))
        win_screen.update(dt)
        win_screen.draw(player.coins, win_time_left)
    pygame.display.update()

pygame.quit()
sys.exit()