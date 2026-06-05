import pygame


class MovingPlatformSystem:
    def __init__(self, base_collision_rects):
        self.base_collision_rects = base_collision_rects
        self.solid_objects = []
        self.platform_objects = []

    def register(self, sprite, *, solid=False, platform=False):
        if solid:
            self.solid_objects.append(sprite)
        if platform:
            self.platform_objects.append(sprite)

    def get_collision_rects(self, exclude_moving_object=None):
        moving_rects = [
            moving_object.rect
            for moving_object in self.solid_objects
            if moving_object is not exclude_moving_object
        ]
        return self.base_collision_rects + moving_rects

    def get_supporting_platform(self, player):
        support_rect = player.rect.move(0, 1)
        for moving_platform in self.platform_objects:
            if (
                support_rect.colliderect(moving_platform.rect)
                and player.rect.bottom <= moving_platform.rect.centery
            ):
                return moving_platform
        return None

    def snapshot_rects(self):
        return {
            moving_object: moving_object.rect.copy()
            for moving_object in self.solid_objects
        }

    def carry_player(self, player, standing_platform, previous_rects):
        if standing_platform is None:
            return None

        previous_platform_rect = previous_rects.get(standing_platform)
        if previous_platform_rect is None:
            return None

        platform_delta_x = standing_platform.rect.x - previous_platform_rect.x
        platform_delta_y = standing_platform.rect.y - previous_platform_rect.y
        if not (platform_delta_x or platform_delta_y):
            return None

        player.move_by(
            platform_delta_x,
            platform_delta_y,
            self.get_collision_rects(exclude_moving_object=standing_platform),
        )
        return standing_platform

    def resolve_player_overlap(self, player, previous_rects, carried_platform=None):
        for moving_object in self.solid_objects:
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
