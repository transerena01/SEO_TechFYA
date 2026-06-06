import pygame
from settings import SETTINGS
from classes.loader import (
    load_background,
    load_big_text_glyphs,
    load_coin_frames,
    load_font,
    load_heart_frames,
    load_frames_from_candidates,
    load_scaled_parts,
    load_small_text_glyphs,
    load_ui_small_text_glyphs,
    load_yellow_board_parts,
    load_yellow_paper_parts,
)


class GameHUD:
    def __init__(self, position, heart_count=5, scale=2, coin_scale=1):
        self.position = pygame.Vector2(position)
        self.heart_count = heart_count
        self.scale = scale
        self.coin_scale = coin_scale
        self.frames = load_heart_frames(self.scale)
        self.coin_frames = load_coin_frames(self.coin_scale)
        self.frame_index = 0.0
        self.coin_frame_index = 0.0
        self.animation_speed = 5
        self.spacing = self.frames[0].get_width() + 8
        self.coin_spacing = self.coin_frames[0].get_width() + 8
        coin_icon_value = SETTINGS["COIN_ICON_VALUE"]
        self.coin_slots = max(1, SETTINGS["COINS_PER_HEALTH"] // coin_icon_value) if coin_icon_value else 1
        self.coin_row_y = self.frames[0].get_height() + 12
        self.empty_alpha = 70

    def update(self, dt):
        self.frame_index = (self.frame_index + (self.animation_speed * dt)) % len(self.frames)
        if len(self.coin_frames) > 1:
            self.coin_frame_index = (self.coin_frame_index + (self.animation_speed * dt)) % len(self.coin_frames)

    def draw(self, screen, health, max_health=None, coin_progress=0):
        max_hearts = self.heart_count if max_health is None else max_health
        visible_hearts = max(0, min(int(health), int(max_hearts)))
        frame = self.frames[int(self.frame_index)]
        empty_frame = frame.copy()
        empty_frame.set_alpha(self.empty_alpha)

        for heart_index in range(int(max_hearts)):
            draw_x = round(self.position.x + heart_index * self.spacing)
            draw_y = round(self.position.y)
            heart_surface = frame if heart_index < visible_hearts else empty_frame
            screen.blit(heart_surface, (draw_x, draw_y))

        coin_icon_value = SETTINGS["COIN_ICON_VALUE"]
        visible_coins = max(
            0,
            min(
                self.coin_slots,
                int(coin_progress // coin_icon_value) if coin_icon_value else 0,
            ),
        )
        coin_frame = self.coin_frames[int(self.coin_frame_index)]
        empty_coin_frame = coin_frame.copy()
        empty_coin_frame.set_alpha(self.empty_alpha)
        coin_draw_y = round(self.position.y + self.coin_row_y)

        for coin_index in range(self.coin_slots):
            draw_x = round(self.position.x + coin_index * self.coin_spacing)
            coin_surface = coin_frame if coin_index < visible_coins else empty_coin_frame
            screen.blit(coin_surface, (draw_x, coin_draw_y))


class StartScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width  = SETTINGS["WIDTH"]
        self.height = SETTINGS["HEIGHT"]

        self.bg = load_background("asset/screen_start.png", (self.width, self.height))

        self.font_title  = load_font(SETTINGS["FONT_PATH"], 110)
        self.font_sub    = load_font(SETTINGS["FONT_PATH"], 50)
        self.font_button = load_font(SETTINGS["FONT_PATH"], 48)
        self.font_panel  = load_font(SETTINGS["FONT_PATH"], 26)
        self.title_text = "HA LONG RUN"
        self.subtitle_text = "A Vietnam Adventure"
        self.title_rect = pygame.Rect(0, 0, 0, 0)
        self.big_text_scale = 8
        self.title_letter_spacing = 6
        self.title_word_spacing = 36
        self.title_outline_color = (255, 255, 255, 255)
        self.title_outline_offsets = (
            (-3, 0), (3, 0), (0, -3), (0, 3),
            (-3, -3), (-3, 3), (3, -3), (3, 3),
        )
        self.big_text_glyphs = load_big_text_glyphs(self.big_text_scale)
        self.small_text_scale = 3
        self.small_text_letter_spacing = 3
        self.small_text_word_spacing = 12
        self.small_text_glyphs = load_small_text_glyphs(self.small_text_scale)
        self.subtitle_text_scale = 4
        self.subtitle_text_letter_spacing = 4
        self.subtitle_text_word_spacing = 14
        self.subtitle_text_glyphs = load_small_text_glyphs(self.subtitle_text_scale)
        self.menu_board_scale = 2
        self.yellow_board_parts = load_yellow_board_parts(self.menu_board_scale)
        self.paper_box_scale_x = 1.85
        self.paper_box_scale_y = 4
        self.yellow_paper_parts = load_yellow_paper_parts(
            self.paper_box_scale_x,
            self.paper_box_scale_y,
        )
        self.menu_hover_scale = 1.08
        self.menu_box_padding_x = 18
        self.menu_box_padding_y = 6
        self.menu_text_outline_color = (255, 255, 255, 255)
        self.menu_text_outline_offsets = (
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 2), (1, -1), (1, 1),
        )
        self.subtitle_box_padding_x = 12
        self.start_label = "START GAME"
        self.instructions_label = "INSTRUCTION"
        self.start_board_surface = self.build_menu_board(self.start_label)
        self.instructions_board_surface = self.build_menu_board(self.instructions_label)
        self.subtitle_box_surface = self.build_subtitle_box(self.subtitle_text)

        self.star_scale = 10
        self.star_frames = load_frames_from_candidates(
            [
                "asset/graphics/character/Pink Star",
                "asset/character/Pink Star",
            ],
            "01-Idle",
            pattern="Idle *.png",
            scale=self.star_scale,
            flip_x=True,
        )
        self.star_frame_index = 0.0
        self.star_animation_speed = 0.18
        self.star_base_x = 300
        self.star_base_y = 475

        self.fierce_tooth_scale = 10
        self.fierce_tooth_frames = load_frames_from_candidates(
            [
                "asset/graphics/enemy/Fierce Tooth",
                "asset/enemy/Fierce Tooth",
            ],
            "01-Idle",
            pattern="Idle *.png",
            scale=self.fierce_tooth_scale,
        )
        self.fierce_tooth_frame_index = 0.0
        self.fierce_tooth_animation_speed = 0.18
        self.fierce_tooth_x = 1030
        self.fierce_tooth_y = 372

        self.start_text_rect = pygame.Rect(0, 0, 0, 0)
        self.instructions_text_rect = pygame.Rect(0, 0, 0, 0)

        self.show_instructions = False
        self.panel_rect = pygame.Rect(0, 0, 860, 360)
        self.panel_rect.center = (self.width // 2, self.height // 2 + 30)
        self.close_text_rect = pygame.Rect(0, 0, 0, 0)
        self.instruction_lines = [
            "Use arrow keys (LEFT, RIGHT, UP, DOWN) to move.",
            "Collect all items and reach the finish line to win.",
            "Complete the mission within 2 minutes.",
            "Don't lose all your health.",
        ]

    def create_outline_surface(self, surface, color):
        mask = pygame.mask.from_surface(surface)
        return mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))

    def create_outlined_surface(self, surface, color, offsets):
        outline_surface = self.create_outline_surface(surface, color)
        offset_xs = [ox for ox, _ in offsets]
        offset_ys = [oy for _, oy in offsets]
        min_offset_x = min(0, *offset_xs)
        max_offset_x = max(0, *offset_xs)
        min_offset_y = min(0, *offset_ys)
        max_offset_y = max(0, *offset_ys)

        padded_surface = pygame.Surface(
            (
                surface.get_width() + (max_offset_x - min_offset_x),
                surface.get_height() + (max_offset_y - min_offset_y),
            ),
            pygame.SRCALPHA,
        )
        base_x = -min_offset_x
        base_y = -min_offset_y

        for offset_x, offset_y in offsets:
            padded_surface.blit(outline_surface, (base_x + offset_x, base_y + offset_y))

        padded_surface.blit(surface, (base_x, base_y))
        return padded_surface

    def render_small_text(self, label):
        return self.render_sprite_text(
            label,
            self.small_text_glyphs,
            self.small_text_letter_spacing,
            self.small_text_word_spacing,
        )

    def render_subtitle_text(self, label):
        return self.render_sprite_text(
            label,
            self.subtitle_text_glyphs,
            self.subtitle_text_letter_spacing,
            self.subtitle_text_word_spacing,
        )

    def render_sprite_text(self, label, glyph_map, letter_spacing, word_spacing):
        total_width = 0
        max_height = 0

        for index, char in enumerate(label):
            if char == " ":
                total_width += word_spacing
                continue

            glyph = glyph_map.get(char)
            if glyph is None:
                return None

            total_width += glyph.get_width()
            max_height = max(max_height, glyph.get_height())

            if index < len(label) - 1 and label[index + 1] != " ":
                total_width += letter_spacing

        if total_width <= 0 or max_height <= 0:
            return None

        surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        draw_x = 0

        for index, char in enumerate(label):
            if char == " ":
                draw_x += word_spacing
                continue

            glyph = glyph_map[char]
            surface.blit(glyph, (draw_x, 0))
            draw_x += glyph.get_width()

            if index < len(label) - 1 and label[index + 1] != " ":
                draw_x += letter_spacing

        return surface

    def build_menu_board(self, label):
        text_surface = self.render_small_text(label)
        if text_surface is not None:
            text_surface = self.create_outlined_surface(
                text_surface,
                self.menu_text_outline_color,
                self.menu_text_outline_offsets,
            )
        return self.build_box_surface(text_surface, self.yellow_board_parts, self.menu_box_padding_x)

    def build_subtitle_box(self, label):
        text_surface = self.render_subtitle_text(label.upper())
        return self.build_box_surface(text_surface, self.yellow_paper_parts, self.subtitle_box_padding_x)

    def build_box_surface(self, text_surface, box_parts, padding_x):
        if text_surface is None or len(box_parts) < 3:
            return None

        left_part = box_parts[10]
        middle_part = box_parts[11]
        right_part = box_parts[12]
        inner_width = text_surface.get_width() + padding_x * 2
        middle_count = max(1, (inner_width + middle_part.get_width() - 1) // middle_part.get_width())
        board_width = left_part.get_width() + middle_count * middle_part.get_width() + right_part.get_width()
        board_height = max(left_part.get_height(), middle_part.get_height(), right_part.get_height())
        board_surface = pygame.Surface((board_width, board_height), pygame.SRCALPHA)

        board_surface.blit(left_part, (0, 0))
        draw_x = left_part.get_width()

        for _ in range(middle_count):
            board_surface.blit(middle_part, (draw_x, 0))
            draw_x += middle_part.get_width()

        board_surface.blit(right_part, (draw_x, 0))

        text_rect = text_surface.get_rect(center=(board_surface.get_width() // 2, board_surface.get_height() // 2))
        board_surface.blit(text_surface, text_rect)
        return board_surface

    def update(self):
        if self.star_frames:
            self.star_frame_index = (
                self.star_frame_index + self.star_animation_speed
            ) % len(self.star_frames)
        if self.fierce_tooth_frames:
            self.fierce_tooth_frame_index = (
                self.fierce_tooth_frame_index + self.fierce_tooth_animation_speed
            ) % len(self.fierce_tooth_frames)

    def draw(self):
        self.screen.blit(self.bg, (0, 0))

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))

        self.draw_title((self.width // 2, 127))
        self.draw_subtitle((self.width // 2, 270))

        if self.star_frames:
            self.draw_pink_star()
        if self.fierce_tooth_frames:
            self.draw_fierce_tooth()

        self.draw_menu_text()

        if self.show_instructions:
            self.draw_instruction_panel()

    def draw_pink_star(self):
        frame = self.star_frames[int(self.star_frame_index)]
        star_rect = frame.get_rect(center=(self.star_base_x, self.star_base_y))
        self.screen.blit(frame, star_rect)

    def draw_subtitle(self, center):
        if self.subtitle_box_surface is None:
            sub = self.font_sub.render("A Vietnam Adventure", True, (135, 206, 250))
            self.screen.blit(sub, (self.width // 2 - sub.get_width() // 2, 260))
            return

        subtitle_rect = self.subtitle_box_surface.get_rect(center=center)
        self.screen.blit(self.subtitle_box_surface, subtitle_rect)

    def draw_title(self, topleft_center):
        title_y = topleft_center[1]
        total_width = 0
        max_height = 0

        for index, char in enumerate(self.title_text):
            if char == " ":
                total_width += self.title_word_spacing
                continue

            glyph = self.big_text_glyphs.get(char)
            if glyph is None:
                return self.draw_title_fallback(topleft_center)

            total_width += glyph.get_width()
            max_height = max(max_height, glyph.get_height())

            next_char_exists = index < len(self.title_text) - 1
            if next_char_exists and self.title_text[index + 1] != " ":
                total_width += self.title_letter_spacing

        title_x = (self.width - total_width) // 2
        draw_x = title_x

        for index, char in enumerate(self.title_text):
            if char == " ":
                draw_x += self.title_word_spacing
                continue

            glyph = self.big_text_glyphs[char]
            outline_glyph = self.create_outline_surface(glyph, self.title_outline_color)

            for offset_x, offset_y in self.title_outline_offsets:
                self.screen.blit(outline_glyph, (draw_x + offset_x, title_y + offset_y))

            self.screen.blit(glyph, (draw_x, title_y))
            draw_x += glyph.get_width()

            next_char_exists = index < len(self.title_text) - 1
            if next_char_exists and self.title_text[index + 1] != " ":
                draw_x += self.title_letter_spacing

        self.title_rect = pygame.Rect(title_x, title_y, total_width, max_height)

    def draw_title_fallback(self, topleft_center):
        title_y = topleft_center[1]
        title = self.font_title.render(self.title_text, True, (255, 215, 50))
        title_x = self.width // 2 - title.get_width() // 2

        for offset_x, offset_y in self.title_outline_offsets:
            outline = self.font_title.render(self.title_text, True, (255, 255, 255))
            self.screen.blit(outline, (title_x + offset_x, title_y + offset_y))

        self.screen.blit(title, (title_x, title_y))
        self.title_rect = title.get_rect(topleft=(title_x, title_y))

    def draw_fierce_tooth(self):
        frame = self.fierce_tooth_frames[int(self.fierce_tooth_frame_index)]
        tooth_rect = frame.get_rect(center=(self.fierce_tooth_x, self.fierce_tooth_y))
        self.screen.blit(frame, tooth_rect)

    def draw_menu_text(self):
        mouse_pos = pygame.mouse.get_pos()
        start_center = (self.width // 2, 380)
        instruction_center = (self.width // 2, 450)
        start_hovered = self.get_menu_item_rect(self.start_board_surface, start_center).collidepoint(mouse_pos)
        instruction_hovered = self.get_menu_item_rect(self.instructions_board_surface, instruction_center).collidepoint(mouse_pos)

        self.start_text_rect = self.draw_menu_board_item(
            self.start_board_surface,
            self.start_label,
            start_center,
            start_hovered,
        )
        self.instructions_text_rect = self.draw_menu_board_item(
            self.instructions_board_surface,
            self.instructions_label,
            instruction_center,
            instruction_hovered,
        )

    def get_menu_item_rect(self, board_surface, center):
        if board_surface is None:
            fallback_rect = self.font_button.render("MENU", True, (255, 255, 255)).get_rect(center=center)
            return fallback_rect

        return board_surface.get_rect(center=center)

    def draw_menu_board_item(self, board_surface, fallback_label, center, hovered):
        if board_surface is None:
            return self.draw_menu_item(fallback_label, center, hovered)

        if hovered:
            scaled_width = int(board_surface.get_width() * self.menu_hover_scale)
            scaled_height = int(board_surface.get_height() * self.menu_hover_scale)
            draw_surface = pygame.transform.scale(board_surface, (scaled_width, scaled_height))
        else:
            draw_surface = board_surface

        board_rect = draw_surface.get_rect(center=center)
        self.screen.blit(draw_surface, board_rect)

        return board_rect

    def draw_menu_item(self, label, center, hovered):
        text_color = (255, 215, 50) if hovered else (255, 255, 255)
        border_color = (128, 128, 128)
        label_text = self.font_button.render(label, True, text_color)
        label_rect = label_text.get_rect(center=center)

        for offset_x, offset_y in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (-2, 2), (2, -2), (2, 2)):
            outline_text = self.font_button.render(label, True, border_color)
            self.screen.blit(outline_text, (label_rect.x + offset_x, label_rect.y + offset_y))

        self.screen.blit(label_text, label_rect)
        return label_rect

    def draw_instruction_panel(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, (23, 39, 66), self.panel_rect, border_radius=24)
        pygame.draw.rect(
            self.screen,
            (255, 214, 82),
            self.panel_rect,
            width=4,
            border_radius=24,
        )

        title_text = self.font_sub.render("Instruction", True, (255, 244, 214))
        title_rect = title_text.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 55))
        self.screen.blit(title_text, title_rect)

        for index, line in enumerate(self.instruction_lines):
            line_text = self.font_panel.render(line, True, (232, 240, 255))
            line_rect = line_text.get_rect(
                center=(self.panel_rect.centerx, self.panel_rect.top + 120 + index * 48)
            )
            self.screen.blit(line_text, line_rect)

        mouse_pos = pygame.mouse.get_pos()
        close_center = (self.panel_rect.centerx, self.panel_rect.bottom - 50)
        close_rect = self.font_button.render("Back", True, (255, 255, 255)).get_rect(center=close_center)
        close_hovered = close_rect.collidepoint(mouse_pos)
        self.close_text_rect = self.draw_menu_item("Back", close_center, close_hovered)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self.show_instructions:
            if self.close_text_rect.collidepoint(event.pos):
                self.show_instructions = False
            return None

        if self.start_text_rect.collidepoint(event.pos):
            return "game"

        if self.instructions_text_rect.collidepoint(event.pos):
            self.show_instructions = True

        return None


class LoseScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width = SETTINGS["WIDTH"]
        self.height = SETTINGS["HEIGHT"]
        self.overlay_alpha = 120

        self.text_scale = 5
        self.text_letter_spacing = 4
        self.text_word_spacing = 14
        self.text_glyphs = load_ui_small_text_glyphs(self.text_scale)

        self.board_scale = 4
        self.paper_scale = 4
        self.banner_scale = 5
        self.button_scale = 4

        self.upper_board_parts = load_scaled_parts(
            "asset/graphics/ui/Yellow Board",
            (1, 2, 3, 7, 8, 9),
            scale_x=self.board_scale,
            scale_y=self.board_scale,
        )
        self.lower_board_parts = load_scaled_parts(
            "asset/graphics/ui/Yellow Board",
            (10, 11, 12),
            scale_x=self.board_scale,
            scale_y=self.board_scale,
        )
        self.paper_parts = load_scaled_parts(
            "asset/graphics/ui/Orange Paper",
            (1, 2, 3, 7, 8, 9),
            scale_x=self.paper_scale,
            scale_y=self.paper_scale,
        )
        self.button_parts = load_scaled_parts(
            "asset/graphics/ui/Yellow Button",
            (2, 3, 4),
            scale_x=self.button_scale,
            scale_y=self.button_scale,
        )
        self.banner_parts = load_scaled_parts(
            "asset/graphics/ui/Small Banner",
            (1, 2, 13),
            scale_x=self.banner_scale,
            scale_y=self.banner_scale,
        )

        self.retry_rect = pygame.Rect(0, 0, 0, 0)
        self.menu_rect = pygame.Rect(0, 0, 0, 0)
        self.exit_rect = pygame.Rect(0, 0, 0, 0)

        self._title_surface = self.build_banner("GAME OVER", 1, 2, self.banner_parts[13].get_width(), text_padding=0)
        self._lower_surface = self.build_lower_panel()
        self._retry_surface_normal = self._build_button_surface("RETRY", hovered=False)
        self._retry_surface_hovered = self._build_button_surface("RETRY", hovered=True)
        self._menu_surface_normal = self._build_button_surface("MENU", hovered=False)
        self._menu_surface_hovered = self._build_button_surface("MENU", hovered=True)
        self._exit_surface_normal = self._build_button_surface("EXIT", hovered=False)
        self._exit_surface_hovered = self._build_button_surface("EXIT", hovered=True)

    def render_small_text(self, label):
        total_width = 0
        max_height = 0

        for index, char in enumerate(label):
            if char == " ":
                total_width += self.text_word_spacing
                continue

            glyph = self.text_glyphs.get(char)
            if glyph is None:
                return None

            total_width += glyph.get_width()
            max_height = max(max_height, glyph.get_height())

            if index < len(label) - 1 and label[index + 1] != " ":
                total_width += self.text_letter_spacing

        if total_width <= 0 or max_height <= 0:
            return None

        surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        draw_x = 0

        for index, char in enumerate(label):
            if char == " ":
                draw_x += self.text_word_spacing
                continue

            glyph = self.text_glyphs[char]
            surface.blit(glyph, (draw_x, 0))
            draw_x += glyph.get_width()

            if index < len(label) - 1 and label[index + 1] != " ":
                draw_x += self.text_letter_spacing

        return surface

    def build_three_slice(self, parts, left_idx, middle_idx, right_idx, inner_width):
        left_part = parts[left_idx]
        middle_part = parts[middle_idx]
        right_part = parts[right_idx]
        if inner_width <= 0:
            middle_count = 0
        else:
            middle_count = max(1, (inner_width + middle_part.get_width() - 1) // middle_part.get_width())
        width = left_part.get_width() + middle_count * middle_part.get_width() + right_part.get_width()
        height = max(left_part.get_height(), middle_part.get_height(), right_part.get_height())
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        draw_x = 0
        surface.blit(left_part, (draw_x, 0))
        draw_x += left_part.get_width()

        for _ in range(middle_count):
            surface.blit(middle_part, (draw_x, 0))
            draw_x += middle_part.get_width()

        surface.blit(right_part, (draw_x, 0))
        return surface

    def build_six_slice(self, parts, size):
        width, height = size
        top_left     = parts[1]
        top_mid      = parts[2]
        top_right    = parts[3]
        bot_left     = parts[7]
        bot_mid      = parts[8]
        bot_right    = parts[9]

        min_w = top_left.get_width() + top_right.get_width() + top_mid.get_width()
        width  = max(width, min_w)
        min_h  = top_left.get_height() + bot_left.get_height()
        height = max(height, min_h)

        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        inner_left  = top_left.get_width()
        inner_right = width - top_right.get_width()
        inner_top   = top_left.get_height()
        inner_bot   = height - bot_left.get_height()

        inner_w  = inner_right - inner_left
        inner_h  = inner_bot - inner_top
        if inner_w > 0 and inner_h > 0:
            strip = pygame.transform.scale(top_mid, (inner_w, top_mid.get_height()))
            fill  = pygame.transform.scale(strip, (inner_w, inner_h))
            surface.blit(fill, (inner_left, inner_top))

        if inner_h > 0:
            left_strip = pygame.transform.scale(
                top_left.subsurface(pygame.Rect(0, top_left.get_height() - 1, top_left.get_width(), 1)),
                (top_left.get_width(), inner_h),
            )
            right_strip = pygame.transform.scale(
                top_right.subsurface(pygame.Rect(0, top_right.get_height() - 1, top_right.get_width(), 1)),
                (top_right.get_width(), inner_h),
            )
            surface.blit(left_strip,  (0,                             inner_top))
            surface.blit(right_strip, (width - top_right.get_width(), inner_top))

        draw_x = inner_left
        while draw_x < inner_right:
            seg_w = min(top_mid.get_width(), inner_right - draw_x)
            if seg_w == top_mid.get_width():
                surface.blit(top_mid, (draw_x, 0))
                surface.blit(bot_mid, (draw_x, height - bot_mid.get_height()))
            else:
                surface.blit(
                    pygame.transform.scale(top_mid, (seg_w, top_mid.get_height())),
                    (draw_x, 0),
                )
                surface.blit(
                    pygame.transform.scale(bot_mid, (seg_w, bot_mid.get_height())),
                    (draw_x, height - bot_mid.get_height()),
                )
            draw_x += seg_w

        surface.blit(top_left,  (0,                             0))
        surface.blit(top_right, (width - top_right.get_width(), 0))
        surface.blit(bot_left,  (0,                             height - bot_left.get_height()))
        surface.blit(bot_right, (width - bot_right.get_width(), height - bot_right.get_height()))
        return surface

    def build_banner(self, label, left_idx, right_idx, min_inner_width, text_padding=36):
        text_surface = self.render_small_text(label)
        if text_surface is None:
            return None

        middle_idx = 13
        if text_padding == 0 and min_inner_width == 0:
            inner_width = 0
        else:
            inner_width = max(min_inner_width, text_surface.get_width() + text_padding)
        inner_width = max(0, inner_width - self.banner_parts[middle_idx].get_width())
        banner_surface = self.build_three_slice(self.banner_parts, left_idx, middle_idx, right_idx, inner_width)
        text_rect = text_surface.get_rect(center=(banner_surface.get_width() // 2, banner_surface.get_height() // 2 - 4))
        banner_surface.blit(text_surface, text_rect)
        return banner_surface

    def _build_button_surface(self, label, hovered):
        text_surface = self.render_small_text(label)
        left_part = self.button_parts[2]
        middle_part = self.button_parts[3]
        right_part = self.button_parts[4]
        total_width = left_part.get_width() + middle_part.get_width() + right_part.get_width()
        height = max(left_part.get_height(), middle_part.get_height(), right_part.get_height())
        button_surface = pygame.Surface((total_width, height), pygame.SRCALPHA)
        button_surface.blit(left_part, (0, 0))
        button_surface.blit(middle_part, (left_part.get_width(), 0))
        button_surface.blit(right_part, (left_part.get_width() + middle_part.get_width(), 0))
        text_rect = text_surface.get_rect(center=(button_surface.get_width() // 2, button_surface.get_height() // 2 - 4))
        button_surface.blit(text_surface, text_rect)

        if hovered:
            scaled_width = int(button_surface.get_width() * 1.08)
            scaled_height = int(button_surface.get_height() * 1.08)
            return pygame.transform.scale(button_surface, (scaled_width, scaled_height))
        return button_surface

    def build_upper_panel(self, score):
        middle_w = self.upper_board_parts[2].get_width()   
        board_surface = self.build_six_slice(
            self.upper_board_parts,
            (540 - middle_w, 250),
        )
        paper_surface = self.build_six_slice(self.paper_parts, (390, 150))
        paper_rect = paper_surface.get_rect(
            center=(board_surface.get_width() // 2, board_surface.get_height() // 2)
        )
        board_surface.blit(paper_surface, paper_rect)

        score_line = self.render_small_text("SCORE:" + str(score))
        if score_line is not None:
            score_line_rect = score_line.get_rect(center=(paper_rect.centerx, paper_rect.centery))
            board_surface.blit(score_line, score_line_rect)
        return board_surface

    def build_lower_panel(self):
        return self.build_three_slice(self.lower_board_parts, 10, 11, 12, 430)

    def draw(self, score):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.overlay_alpha))
        self.screen.blit(overlay, (0, 0))

        upper_surface = self.build_upper_panel(score)

        title_rect = self._title_surface.get_rect(center=(self.width // 2, 145))
        upper_rect = upper_surface.get_rect(center=(self.width // 2, 340))
        lower_rect = self._lower_surface.get_rect(center=(self.width // 2, 540))

        self.screen.blit(self._title_surface, title_rect)
        self.screen.blit(upper_surface, upper_rect)
        self.screen.blit(self._lower_surface, lower_rect)

        mouse_pos = pygame.mouse.get_pos()

        menu_w = self._menu_surface_normal.get_width()
        retry_w = self._retry_surface_normal.get_width()
        exit_w = self._exit_surface_normal.get_width()

        btn_spacing = 40
        total_btn_width = menu_w + retry_w + exit_w + btn_spacing * 2
        btn_start_x = lower_rect.centerx - total_btn_width // 2
        btn_y = lower_rect.centery

        menu_cx = btn_start_x + menu_w // 2
        retry_cx = btn_start_x + menu_w + btn_spacing + retry_w // 2
        exit_cx = btn_start_x + menu_w + btn_spacing + retry_w + btn_spacing + exit_w // 2

        menu_surface = self._menu_surface_hovered if self.menu_rect.collidepoint(mouse_pos) else self._menu_surface_normal
        retry_surface = self._retry_surface_hovered if self.retry_rect.collidepoint(mouse_pos) else self._retry_surface_normal
        exit_surface = self._exit_surface_hovered if self.exit_rect.collidepoint(mouse_pos) else self._exit_surface_normal

        self.screen.blit(menu_surface, menu_surface.get_rect(center=(menu_cx, btn_y)))
        self.screen.blit(retry_surface, retry_surface.get_rect(center=(retry_cx, btn_y)))
        self.screen.blit(exit_surface, exit_surface.get_rect(center=(exit_cx, btn_y)))

        self.menu_rect = self._menu_surface_normal.get_rect(center=(menu_cx, btn_y))
        self.retry_rect = self._retry_surface_normal.get_rect(center=(retry_cx, btn_y))
        self.exit_rect = self._exit_surface_normal.get_rect(center=(exit_cx, btn_y))

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self.menu_rect.collidepoint(event.pos):
            return "menu"

        if self.retry_rect.collidepoint(event.pos):
            return "retry"

        if self.exit_rect.collidepoint(event.pos):
            return "exit"

        return None