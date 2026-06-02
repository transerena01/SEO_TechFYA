class Camera:
    def __init__(self, screen_width, screen_height, world_width, world_height, follow_y=False):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = world_width
        self.world_height = world_height
        self.follow_y = follow_y
        self.x = 0
        self.y = 0
        self.focus_x = screen_width // 2
        self.focus_y = screen_height // 2
        self.deadzone_width = 0
        self.deadzone_height = 0

    def get_x_bounds(self):
        return 0, max(0, self.world_width - self.screen_width)

    def clamp(self):
        min_x, max_x = self.get_x_bounds()
        self.x = max(min_x, min(int(self.x), max_x))

        if self.world_height > self.screen_height:
            max_y = self.world_height - self.screen_height
            self.y = max(0, min(int(self.y), max_y))
        else:
            self.y = 0

    def snap_to(self, target_rect):
        self.x = target_rect.centerx - self.focus_x
        if self.follow_y:
            self.y = target_rect.centery - self.focus_y
        self.clamp()

    def update(self, target_rect):
        self.x = target_rect.centerx - self.focus_x
        if self.follow_y:
            self.y = target_rect.centery - self.focus_y
        self.clamp()
