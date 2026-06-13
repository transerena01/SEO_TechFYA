import pygame
import pytmx
from pytmx.util_pygame import load_pygame
from pathlib import Path
import random
import xml.etree.ElementTree as ET

from classes.loader import load_frames, load_image


class ParallaxBackground:
    def __init__(
        self,
        screen_size,
        world_size,
        *,
        background_path,
        sky_color,
        large_cloud_path=None,
        small_cloud_folder=None,
    ):
        self.screen_width, self.screen_height = screen_size
        self.world_width, self.world_height = world_size
        self.sky_color = sky_color
        self.elapsed = 0.0
        self.cloud_loop_width = max(
            self.screen_width * 2,
            self.world_width + self.screen_width,
        )

        self.backdrop_surface = None
        self.backdrop_shift_x = 0
        self.backdrop_shift_y = 0
        self.backdrop_vertical_factor = 0.18
        self.large_clouds = []
        self.small_clouds = []

        self._load_backdrop(background_path)
        self.large_clouds = self._build_large_clouds(large_cloud_path)
        self.small_clouds = self._build_small_clouds(small_cloud_folder)

    def _load_backdrop(self, background_path):
        if not background_path:
            return

        try:
            backdrop_surface = load_image(background_path, alpha=False)
        except (FileNotFoundError, pygame.error):
            return

        target_width = self.screen_width + min(
            max(0, self.world_width - self.screen_width),
            round(self.screen_width * 0.55),
        )
        scale = max(
            self.screen_height / max(1, backdrop_surface.get_height()),
            target_width / max(1, backdrop_surface.get_width()),
        )
        scaled_width = max(1, round(backdrop_surface.get_width() * scale))
        scaled_height = max(1, round(backdrop_surface.get_height() * scale))
        self.backdrop_surface = pygame.transform.scale(
            backdrop_surface,
            (scaled_width, scaled_height),
        )
        self.backdrop_shift_x = max(
            0,
            self.backdrop_surface.get_width() - self.screen_width,
        )
        self.backdrop_shift_y = max(
            0,
            self.backdrop_surface.get_height() - self.screen_height,
        )

    def _build_large_clouds(self, large_cloud_path):
        if not large_cloud_path:
            return []

        try:
            large_cloud = load_image(large_cloud_path)
        except (FileNotFoundError, pygame.error):
            return []

        target_width = max(
            self.screen_width - 120,
            round(self.screen_width * 0.92),
        )
        scale = target_width / max(1, large_cloud.get_width())
        target_height = max(1, round(large_cloud.get_height() * scale))
        large_cloud = pygame.transform.scale(
            large_cloud,
            (target_width, target_height),
        )
        large_cloud.set_alpha(170)

        return [
            {
                "surface": large_cloud,
                "base_x": -120.0,
                "y": 42,
                "speed": 9.0,
                "depth": 0.06,
                "vertical_depth": 0.02,
            },
            {
                "surface": large_cloud,
                "base_x": self.screen_width * 0.78,
                "y": 118,
                "speed": 13.0,
                "depth": 0.1,
                "vertical_depth": 0.03,
            },
        ]

    def _build_small_clouds(self, small_cloud_folder):
        if not small_cloud_folder:
            return []

        try:
            small_cloud_frames = load_frames(small_cloud_folder)
        except (FileNotFoundError, ValueError, pygame.error):
            return []

        rng = random.Random(11)
        small_clouds = []
        cloud_count = 14

        for cloud_index in range(cloud_count):
            frame = small_cloud_frames[cloud_index % len(small_cloud_frames)]
            scale = rng.uniform(0.9, 1.45)
            scaled_size = (
                max(1, round(frame.get_width() * scale)),
                max(1, round(frame.get_height() * scale)),
            )
            cloud_surface = pygame.transform.scale(frame, scaled_size)
            cloud_surface.set_alpha(rng.randint(170, 235))
            small_clouds.append(
                {
                    "surface": cloud_surface,
                    "base_x": rng.uniform(
                        -self.screen_width * 0.25,
                        self.cloud_loop_width,
                    ),
                    "y": rng.randint(64, round(self.screen_height * 0.48)),
                    "speed": rng.uniform(18.0, 36.0),
                    "depth": rng.uniform(0.14, 0.3),
                    "vertical_depth": rng.uniform(0.03, 0.06),
                }
            )

        return small_clouds

    def update(self, dt=1 / 60):
        self.elapsed += dt

    def _get_camera_ratio(self, camera_value, range_value):
        if range_value <= 0:
            return 0.0
        return max(0.0, min(1.0, camera_value / range_value))

    def _draw_cloud(self, screen, camera, cloud):
        cloud_surface = cloud["surface"]
        cloud_width = cloud_surface.get_width()
        loop_width = self.cloud_loop_width + cloud_width
        draw_x = (
            cloud["base_x"]
            - (self.elapsed * cloud["speed"])
            - (camera.x * cloud["depth"])
        )
        draw_x = ((draw_x + cloud_width) % loop_width) - cloud_width
        draw_y = round(cloud["y"] - (camera.y * cloud["vertical_depth"]))

        for wrapped_x in (draw_x - loop_width, draw_x, draw_x + loop_width):
            if wrapped_x < self.screen_width and wrapped_x + cloud_width > 0:
                screen.blit(cloud_surface, (round(wrapped_x), draw_y))

    def draw(self, screen, camera):
        screen.fill(self.sky_color)

        if self.backdrop_surface is not None:
            x_ratio = self._get_camera_ratio(
                camera.x,
                self.world_width - self.screen_width,
            )
            y_ratio = self._get_camera_ratio(
                camera.y,
                self.world_height - self.screen_height,
            )
            backdrop_x = -round(self.backdrop_shift_x * x_ratio)
            backdrop_y = -round(
                self.backdrop_shift_y
                * y_ratio
                * self.backdrop_vertical_factor
            )
            screen.blit(self.backdrop_surface, (backdrop_x, backdrop_y))

        for cloud in self.large_clouds:
            self._draw_cloud(screen, camera, cloud)

        for cloud in self.small_clouds:
            self._draw_cloud(screen, camera, cloud)


class GameMap:
    def __init__(self, tmx_path):
        self.tmx_path = Path(tmx_path)
        self.object_flag_map = self._load_object_flag_map()
        self.tmx_data = load_pygame(tmx_path) 

        self.tile_width = self.tmx_data.tilewidth
        self.tile_height = self.tmx_data.tileheight
        self.pixel_width = self.tmx_data.width * self.tile_width
        self.pixel_height = self.tmx_data.height * self.tile_height

        self.background_surface = pygame.Surface(
            (self.pixel_width, self.pixel_height), pygame.SRCALPHA
        )
        self.foreground_surface = pygame.Surface(
            (self.pixel_width, self.pixel_height), pygame.SRCALPHA
        )
        self.render_visual_layers()

    def render_visual_layers(self):
        for layer in self.tmx_data.visible_layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue

            layer_name = (layer.name or "").lower()
            target = (
                self.foreground_surface
                if layer_name in {"fg", "foreground"}
                else self.background_surface
            )

            for x, y, surf in layer.tiles():
                if surf:
                    target.blit(surf, (x * self.tile_width, y * self.tile_height))

    def get_terrain_rects(self):
        rects = []
        for layer in self.tmx_data.visible_layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue
            layer_name = (layer.name or "").lower()
            if layer_name not in {"terrain", "platforms"}:
                continue
            for x, y, surf in layer.tiles():
                rects.append(pygame.Rect(
                    x * self.tile_width,
                    y * self.tile_height,
                    self.tile_width,
                    self.tile_height,
                ))
        return rects

    def get_boundary_rects(self):
        t = 20
        return [
            pygame.Rect(0, -t, self.pixel_width, t),                
            pygame.Rect(0, self.pixel_height, self.pixel_width, t), 
            pygame.Rect(-t, 0, t, self.pixel_height),               
            pygame.Rect(self.pixel_width, 0, t, self.pixel_height), 
        ]

    def get_objects(self):
        objects = []
        for layer in self.tmx_data.layers:
            if not isinstance(layer, pytmx.TiledObjectGroup):
                continue
            for obj in layer:
                properties = dict(getattr(obj, "properties", {}))
                object_id = getattr(obj, "id", None)
                flag_data = self.object_flag_map.get(object_id, {})
                objects.append({
                    "id":     object_id,
                    "name":   obj.name,    
                    "layer":  layer.name,  
                    "x":      obj.x,
                    "y":      obj.y,
                    "width":  obj.width,
                    "height": obj.height,
                    "gid":    getattr(obj, "gid", None),
                    "raw_gid": flag_data.get("raw_gid"),
                    "flip_x": flag_data.get("flip_x", False),
                    "properties": properties,
                })
        return objects

    def _load_object_flag_map(self):
        horizontal_flip_flag = 0x80000000
        object_flags = {}
        root = ET.parse(self.tmx_path).getroot()

        for object_element in root.findall(".//object[@gid]"):
            object_id = int(object_element.get("id"))
            raw_gid = int(object_element.get("gid"))
            object_flags[object_id] = {
                "raw_gid": raw_gid,
                "flip_x": bool(raw_gid & horizontal_flip_flag),
            }

        return object_flags

    def get_object_by_name(self, name):
        target_name = name.lower()
        for obj in self.get_objects():
            object_name = obj["name"] or ""
            if object_name.lower() == target_name:
                return obj
        return None

    def get_object_anchor(self, name):
        obj = self.get_object_by_name(name)
        if not obj:
            return None

        return (
            round(obj["x"] + (obj["width"] / 2)),
            round(obj["y"] + obj["height"]),
        )

    def get_draw_offset(self, camera):
        return (-camera.x, -camera.y)

    def draw_background(self, screen, camera):
        screen.blit(self.background_surface, self.get_draw_offset(camera))

    def draw_foreground(self, screen, camera):
        screen.blit(self.foreground_surface, self.get_draw_offset(camera))
