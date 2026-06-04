import pygame
import pytmx
from pytmx.util_pygame import load_pygame
from pathlib import Path
import xml.etree.ElementTree as ET


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
        for layer in self.tmx_data.visible_layers:
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
