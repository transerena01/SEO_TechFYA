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
from classes.camera import Camera
from classes.ui import GameHUD, StartScreen
from classes.tilemap import GameMap


pygame.init()
pygame.mixer.init()

load_music(
    "asset/SEOmusic/Pokémon Ruby and Sapphire - Oceanic Museum (Remix).mp3",
    volume=0.4,
    loops=-1,
)
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

start_ticks = None
time_limit = 120  # seconds

# Game objects
game_map = GameMap(SETTINGS["MAP_FILE"])
map_objects = game_map.get_objects()

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
moving_solid_objects = []
moving_platform_objects = []
moving_hazard_objects = []
water_areas = []
world_rect = pygame.Rect(0, 0, game_map.pixel_width, game_map.pixel_height)

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
moving_hazard_object_names = {"saw"}
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
        moving_objects.append(
            OrbitalSprite(
                orbit_center,
                radius,
                start_angle,
                [load_image(moving_spike_image_path, size=object_size)],
                speed=object_properties.get("speed", 0),
                end_angle=object_properties.get("end_angle", -1),
                anchor="center",
            )
        )
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
    if object_name in moving_solid_object_names:
        moving_solid_objects.append(moving_sprite)
    if object_properties.get("platform", False):
        moving_platform_objects.append(moving_sprite)
    if object_name in moving_hazard_object_names:
        moving_hazard_objects.append(moving_sprite)


def get_player_collision_rects(exclude_moving_object=None):
    moving_rects = [
        moving_object.rect
        for moving_object in moving_solid_objects
        if moving_object is not exclude_moving_object
    ]
    return terrain_rects + moving_rects


def get_supporting_platform():
    support_rect = player.rect.move(0, 1)
    for moving_platform in moving_platform_objects:
        if support_rect.colliderect(moving_platform.rect) and player.rect.bottom <= moving_platform.rect.centery:
            return moving_platform
    return None


def resolve_player_moving_solid_overlap(previous_rects, carried_platform=None):
    for moving_object in moving_solid_objects:
        if moving_object is carried_platform:
            continue

        if not player.rect.colliderect(moving_object.rect):
            continue

        previous_rect = previous_rects.get(moving_object, moving_object.rect)
        delta_x = moving_object.rect.x - previous_rect.x
        delta_y = moving_object.rect.y - previous_rect.y

        if abs(delta_x) >= abs(delta_y) and delta_x != 0:
            if delta_x > 0:
                player.rect.left = moving_object.rect.right
            else:
                player.rect.right = moving_object.rect.left
            continue

        if delta_y != 0:
            if delta_y > 0:
                player.rect.top = moving_object.rect.bottom
            else:
                player.rect.bottom = moving_object.rect.top
                player.on_ground = True
            continue

        overlap_left = abs(player.rect.right - moving_object.rect.left)
        overlap_right = abs(moving_object.rect.right - player.rect.left)
        overlap_top = abs(player.rect.bottom - moving_object.rect.top)
        overlap_bottom = abs(moving_object.rect.bottom - player.rect.top)
        minimum_overlap = min(
            overlap_left,
            overlap_right,
            overlap_top,
            overlap_bottom,
        )

        if minimum_overlap == overlap_top:
            player.rect.bottom = moving_object.rect.top
            player.on_ground = True
        elif minimum_overlap == overlap_bottom:
            player.rect.top = moving_object.rect.bottom
        elif minimum_overlap == overlap_left:
            player.rect.right = moving_object.rect.left
        else:
            player.rect.left = moving_object.rect.right


def player_touches_hazard(player_rect, hazard_rect, padding=4):
    return player_rect.colliderect(hazard_rect.inflate(padding * 2, padding * 2))


player.check_ground_support(get_player_collision_rects())

hazard_hit_cooldown_ms = 800
hazard_last_hit_time = -hazard_hit_cooldown_ms
hazard_damage = 1

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
                start_ticks = pygame.time.get_ticks()  # Start the timer when the game starts

    # Start Screen
    if state == "start":
        start_screen.update()
        start_screen.draw()

    # GAME

    elif state == "game":
        elapsed_time = (pygame.time.get_ticks() - start_ticks) // 1000
        time_left = max(0, time_limit - elapsed_time)

        if time_left <= 0:
            running = False

        standing_platform = get_supporting_platform()
        previous_moving_rects = {
            moving_object: moving_object.rect.copy()
            for moving_object in moving_solid_objects
        }

        for moving_object in moving_objects:
            moving_object.update(dt)

        carried_platform = None
        if standing_platform is not None:
            previous_platform_rect = previous_moving_rects.get(standing_platform)
            if previous_platform_rect is not None:
                platform_delta_x = standing_platform.rect.x - previous_platform_rect.x
                platform_delta_y = standing_platform.rect.y - previous_platform_rect.y
                if platform_delta_x or platform_delta_y:
                    carried_platform = standing_platform
                    player.move_by(
                        platform_delta_x,
                        platform_delta_y,
                        get_player_collision_rects(exclude_moving_object=standing_platform),
                    )

        resolve_player_moving_solid_overlap(
            previous_moving_rects,
            carried_platform=carried_platform,
        )

        keys = pygame.key.get_pressed()
        player_collision_rects = get_player_collision_rects()
        player.move(keys, player_collision_rects)
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
        timer_text = timer_font.render(f"Time: {time_left}", True, (255, 255, 255))
        screen.blit(timer_text, (SETTINGS["WIDTH"] - 230, 20))
        if not player.alive:
            running = False

    pygame.display.update()

pygame.quit()
sys.exit()
