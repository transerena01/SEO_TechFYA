import pygame
from settings import SETTINGS
from classes.loader import (
    load_background,
    load_big_text_glyphs,
    load_coin_frames,
    load_frames,
    load_font,
    load_image,
    load_heart_frames,
    load_frames_from_candidates,
    load_scaled_parts,
    load_small_text_glyphs,
    load_ui_small_text_glyphs,
    load_yellow_board_parts,
    load_yellow_paper_parts,
)


class SpriteTextRenderer:
    NORMALIZATION_REPLACEMENTS = {
        "&": " AND ",
        "+": " PLUS ",
        "=": " EQUALS ",
        ".": " ",
        ",": " ",
        "(": " ",
        ")": " ",
        "-": " ",
        "/": " ",
        "!": " ",
        "?": " ",
        "'": "",
    }

    def __init__(self, glyphs, letter_spacing, word_spacing):
        self.glyphs = glyphs
        self.letter_spacing = letter_spacing
        self.word_spacing = word_spacing

    @classmethod
    def normalize_for_glyphs(cls, label, glyph_map):
        normalized = label.upper()
        for old, new in cls.NORMALIZATION_REPLACEMENTS.items():
            normalized = normalized.replace(old, new)

        cleaned = "".join(char if char == " " or char in glyph_map else " " for char in normalized)
        return " ".join(cleaned.split())

    def render(self, label):
        total_width = 0
        max_height = 0

        for index, char in enumerate(label):
            if char == " ":
                total_width += self.word_spacing
                continue

            glyph = self.glyphs.get(char)
            if glyph is None:
                return None

            total_width += glyph.get_width()
            max_height = max(max_height, glyph.get_height())

            if index < len(label) - 1 and label[index + 1] != " ":
                total_width += self.letter_spacing

        if total_width <= 0 or max_height <= 0:
            return None

        surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        draw_x = 0

        for index, char in enumerate(label):
            if char == " ":
                draw_x += self.word_spacing
                continue

            glyph = self.glyphs[char]
            surface.blit(glyph, (draw_x, 0))
            draw_x += glyph.get_width()

            if index < len(label) - 1 and label[index + 1] != " ":
                draw_x += self.letter_spacing

        return surface

    def render_normalized(self, label):
        return self.render(self.normalize_for_glyphs(label, self.glyphs))


def build_three_slice_surface(parts, left_idx, middle_idx, right_idx, inner_width):
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


def build_six_slice_surface(parts, size):
    width, height = size
    top_left = parts[1]
    top_mid = parts[2]
    top_right = parts[3]
    bot_left = parts[7]
    bot_mid = parts[8]
    bot_right = parts[9]

    min_w = top_left.get_width() + top_right.get_width() + top_mid.get_width()
    width = max(width, min_w)
    min_h = top_left.get_height() + bot_left.get_height()
    height = max(height, min_h)

    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    inner_left = top_left.get_width()
    inner_right = width - top_right.get_width()
    inner_top = top_left.get_height()
    inner_bot = height - bot_left.get_height()

    inner_w = inner_right - inner_left
    inner_h = inner_bot - inner_top
    if inner_w > 0 and inner_h > 0:
        strip = pygame.transform.scale(top_mid, (inner_w, top_mid.get_height()))
        fill = pygame.transform.scale(strip, (inner_w, inner_h))
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
        surface.blit(left_strip, (0, inner_top))
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

    surface.blit(top_left, (0, 0))
    surface.blit(top_right, (width - top_right.get_width(), 0))
    surface.blit(bot_left, (0, height - bot_left.get_height()))
    surface.blit(bot_right, (width - bot_right.get_width(), height - bot_right.get_height()))
    return surface


class ResultScreenBase:
    def __init__(self, screen, title_label, *, title_padding):
        self.screen = screen
        self.width = SETTINGS["WIDTH"]
        self.height = SETTINGS["HEIGHT"]
        self.overlay_alpha = 120

        self.text_scale = 5
        self.text_letter_spacing = 4
        self.text_word_spacing = 14
        self.text_renderer = SpriteTextRenderer(
            load_ui_small_text_glyphs(self.text_scale),
            self.text_letter_spacing,
            self.text_word_spacing,
        )

        self.board_scale = 4
        self.paper_scale = 4
        self.banner_scale = 5
        self.button_scale = 4
        self.button_hover_scale = 1.08

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

        self._title_surface = self.build_banner(
            title_label,
            1,
            2,
            self.banner_parts[13].get_width(),
            text_padding=title_padding,
        )
        self._lower_surface = self.build_lower_panel()
        self._retry_surface_normal = self.build_button_surface("RETRY", hovered=False)
        self._retry_surface_hovered = self.build_button_surface("RETRY", hovered=True)
        self._menu_surface_normal = self.build_button_surface("MENU", hovered=False)
        self._menu_surface_hovered = self.build_button_surface("MENU", hovered=True)
        self._exit_surface_normal = self.build_button_surface("EXIT", hovered=False)
        self._exit_surface_hovered = self.build_button_surface("EXIT", hovered=True)

    def render_small_text(self, label):
        return self.text_renderer.render(label)

    def build_three_slice(self, parts, left_idx, middle_idx, right_idx, inner_width):
        return build_three_slice_surface(parts, left_idx, middle_idx, right_idx, inner_width)

    def build_six_slice(self, parts, size):
        return build_six_slice_surface(parts, size)

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

    def build_button_surface(self, label, hovered):
        text_surface = self.render_small_text(label)
        button_surface = self.build_three_slice(self.button_parts, 2, 3, 4, self.button_parts[3].get_width())
        text_rect = text_surface.get_rect(center=(button_surface.get_width() // 2, button_surface.get_height() // 2 - 4))
        button_surface.blit(text_surface, text_rect)

        if hovered:
            scaled_width = int(button_surface.get_width() * self.button_hover_scale)
            scaled_height = int(button_surface.get_height() * self.button_hover_scale)
            return pygame.transform.scale(button_surface, (scaled_width, scaled_height))
        return button_surface

    def build_lower_panel(self):
        return self.build_three_slice(self.lower_board_parts, 10, 11, 12, 430)

    def draw_overlay(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.overlay_alpha))
        self.screen.blit(overlay, (0, 0))

    def draw_title(self, center):
        if self._title_surface is None:
            return pygame.Rect(0, 0, 0, 0)

        title_rect = self._title_surface.get_rect(center=center)
        self.screen.blit(self._title_surface, title_rect)
        return title_rect

    def draw_lower_panel(self, center):
        lower_rect = self._lower_surface.get_rect(center=center)
        self.screen.blit(self._lower_surface, lower_rect)
        self.draw_footer_buttons(lower_rect)
        return lower_rect

    def draw_footer_buttons(self, lower_rect):
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
        self.small_text_renderer = SpriteTextRenderer(
            self.small_text_glyphs,
            self.small_text_letter_spacing,
            self.small_text_word_spacing,
        )
        self.subtitle_text_scale = 4
        self.subtitle_text_letter_spacing = 4
        self.subtitle_text_word_spacing = 14
        self.subtitle_text_glyphs = load_small_text_glyphs(self.subtitle_text_scale)
        self.subtitle_text_renderer = SpriteTextRenderer(
            self.subtitle_text_glyphs,
            self.subtitle_text_letter_spacing,
            self.subtitle_text_word_spacing,
        )
        self.instruction_title_text_scale = 6
        self.instruction_title_letter_spacing = 4
        self.instruction_title_word_spacing = 14
        self.instruction_title_glyphs = load_ui_small_text_glyphs(self.instruction_title_text_scale)
        self.instruction_title_renderer = SpriteTextRenderer(
            self.instruction_title_glyphs,
            self.instruction_title_letter_spacing,
            self.instruction_title_word_spacing,
        )
        self.instruction_body_text_scale = 3
        self.instruction_body_letter_spacing = 3
        self.instruction_body_word_spacing = 12
        self.instruction_body_glyphs = load_ui_small_text_glyphs(self.instruction_body_text_scale)
        self.instruction_body_renderer = SpriteTextRenderer(
            self.instruction_body_glyphs,
            self.instruction_body_letter_spacing,
            self.instruction_body_word_spacing,
        )
        self.instruction_button_text_scale = 4
        self.instruction_button_letter_spacing = 4
        self.instruction_button_word_spacing = 14
        self.instruction_button_glyphs = load_ui_small_text_glyphs(self.instruction_button_text_scale)
        self.instruction_button_renderer = SpriteTextRenderer(
            self.instruction_button_glyphs,
            self.instruction_button_letter_spacing,
            self.instruction_button_word_spacing,
        )
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

        # --- Instruction panel: Green Board nine-slice ---
        self.instruction_panel_board_scale = 4
        self.instruction_panel_parts = load_scaled_parts(
            "asset/graphics/ui/Green Board",
            tuple(range(1, 10)),
            scale_x=self.instruction_panel_board_scale,
            scale_y=self.instruction_panel_board_scale,
        )
        self.instruction_paper_scale = 2
        self.instruction_paper_parts = load_scaled_parts(
            "asset/graphics/ui/Yellow Paper",
            tuple(range(1, 10)),
            scale_x=self.instruction_paper_scale,
            scale_y=self.instruction_paper_scale,
        )
        self.instruction_title_paper_scale = 1.25
        self.instruction_title_paper_parts = load_scaled_parts(
            "asset/graphics/ui/Yellow Paper",
            tuple(range(1, 10)),
            scale_x=self.instruction_title_paper_scale,
            scale_y=self.instruction_title_paper_scale,
        )

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
        self.instruction_page = 0
        # Instruction popup layout: edit these values directly to move or resize the pieces.
        self.instruction_panel_size = (960, 600)
        self.instruction_panel_center_offset = (0, 0)
        self.instruction_title_paper_size = (820, 100)
        self.instruction_title_paper_offset = (0, -60)
        self.instruction_body_paper_size = (820, 360)
        self.instruction_body_paper_offset = (0, 20)

        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.instruction_panel_surface = None
        self.instruction_panel_paper_surface = None
        self.instruction_panel_title_paper_surface = None
        self.instruction_panel_board_inner_rect = pygame.Rect(0, 0, 0, 0)
        self.instruction_panel_title_paper_rect = pygame.Rect(0, 0, 0, 0)
        self.instruction_panel_title_inner_rect = pygame.Rect(0, 0, 0, 0)
        self.instruction_panel_paper_rect = pygame.Rect(0, 0, 0, 0)
        self.instruction_panel_inner_rect = pygame.Rect(0, 0, 0, 0)
        self.rebuild_instruction_panel_layout()
        self.instruction_close_button_surface = None
        self.instruction_close_button_rect = pygame.Rect(0, 0, 0, 0)
        self.instruction_close_button_size = (55, 55)
        self.instruction_close_icon_scale = 3.5
        self.instruction_close_button_offset = (10, 10)
        self.instruction_nav_button_size = (55, 55)
        self.instruction_nav_icon_scale = 3.5
        self.instruction_button_hover_scale = 1.12
        self.instruction_prev_button_surface = None
        self.instruction_next_button_surface = None
        try:
            close_button = load_image(
                "asset/graphics/ui/Green Button/1.png",
                size=self.instruction_close_button_size,
            )
            close_icon = load_image(
                "asset/graphics/ui/Small Text/Small Icons/5.png",
                scale=self.instruction_close_icon_scale,
            )
            self.instruction_close_button_surface = close_button.copy()
            close_icon_rect = close_icon.get_rect(center=self.instruction_close_button_surface.get_rect().center)
            self.instruction_close_button_surface.blit(close_icon, close_icon_rect)
        except Exception as e:
            print(f"Instruction close button load failed: {e}")
            self.instruction_close_button_surface = self._build_fallback_close_button_surface()
        self.instruction_prev_button_surface = self._build_instruction_icon_button_surface(
            "asset/graphics/ui/Small Text/Small Icons/1.png",
            self.instruction_nav_button_size,
            self.instruction_nav_icon_scale,
        )
        self.instruction_next_button_surface = self._build_instruction_icon_button_surface(
            "asset/graphics/ui/Small Text/Small Icons/2.png",
            self.instruction_nav_button_size,
            self.instruction_nav_icon_scale,
        )
        self.close_text_rect = pygame.Rect(0, 0, 0, 0)
        self.prev_rect = pygame.Rect(0, 0, 0, 0)
        self.next_rect = pygame.Rect(0, 0, 0, 0)
        try:
            _potion_frames = load_frames("asset/graphics/items/potion")
            _pw = _potion_frames[0].get_width()
            _ph = _potion_frames[0].get_height()
            _target = 48
            _scale = _target / max(_pw, _ph)
            self.potion_frames = [
                pygame.transform.scale(f, (max(1, round(_pw * _scale)), max(1, round(_ph * _scale))))
                for f in _potion_frames
            ]
        except Exception:
            self.potion_frames = []
        self.potion_frame_index = 0.0
        self.potion_anim_speed = 0.12

        def _load_scaled(folder, target_h):
            try:
                frames = load_frames(folder)
                w0, h0 = frames[0].get_size()
                scale = target_h / max(h0, 1)
                return [
                    pygame.transform.scale(f, (max(1, round(w0 * scale)), max(1, round(h0 * scale))))
                    for f in frames
                ]
            except Exception:
                return []

        TARGET_H = 48
        self.tooth_frames   = _load_scaled("asset/graphics/enemy/Fierce Tooth/02-Run", TARGET_H)
        self.shell_frames   = _load_scaled("asset/graphics/enemy/shell/idle",          TARGET_H)
        self.saw_frames     = _load_scaled("asset/graphics/enemies/saw/animation",     TARGET_H)
        self.spike_frames   = _load_scaled("asset/graphics/enemies/floor_spikes",      TARGET_H)
        self.tooth_fi   = 0.0
        self.shell_fi   = 0.0
        self.saw_fi     = 0.0
        self.spike_fi   = 0.0
        self.enemy_anim_speed = 0.12

        try:
            _body = load_image("asset/graphics/level/water/body.png")
            _top_frames = load_frames("asset/graphics/level/water/top")
            self.water_body   = _body
            self.water_top_frames = _top_frames
        except Exception:
            self.water_body = None
            self.water_top_frames = []
        self.water_top_fi    = 0.0
        self.water_top_speed = 0.08
        self.water_alpha     = 110

        self.instruction_pages = [
            {
                "title": "Movement",
                "lines": [
                    "Use the arrow keys to move your character.",
                    "LEFT RIGHT    walk left or right",
                    "UP            jump",
                    "You can jump over enemies and hazards.",
                ],
            },
            {
                "title": "Coins & Score",
                "lines": [
                    "Silver gem      =  10 coins",
                    "Gold gem        =  20 coins",
                    "Red Lantern     =  30 coins",
                    "Gold Lantern    =  50 coins",
                    "Every 20 points = + 1 gold coin",
                    "5 gold coins    = + 1 heart ",
                ],
            },
            {
                "title": "Health & Potions",
                "lines": [
                    "You start with 10 hearts of health.",
                    "Every 100 coins earned = +1 heart (auto).",
                    "Potion         restores 1 heart instantly.",
                ],
            },
            {
                "title": "Enemies & Hazards",
                "lines": [
                    "Fierce Tooth    patrols left and right.",
                    "Shell           fires pearls at you.",
                    "Saw             deal damage on contact.",
                ],
            },
            {
                "title": "Water",
                "lines": [
                    "Falling into water is instant death.",
                    "You lose if your body sinks too deep.",
                    "Stay on platforms above the waterline.",
                ],
            },
            {
                "title": "Win & Lose",
                "lines": [
                    "You have 2 minutes to complete the level.",
                    "Reach the flag at the end to win.",
                    "You lose if:",
                    "   Time runs out",
                    "   Health reaches zero",
                    "   You fall into water",
                ],
            },
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
        return self.small_text_renderer.render(label)

    def render_subtitle_text(self, label):
        return self.subtitle_text_renderer.render(label)

    def render_instruction_title_text(self, label):
        return self.instruction_title_renderer.render_normalized(label)

    def render_instruction_body_text(self, label):
        return self.instruction_body_renderer.render_normalized(label)

    def render_instruction_button_text(self, label):
        return self.instruction_button_renderer.render_normalized(label)

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

        inner_width = text_surface.get_width() + padding_x * 2
        board_surface = build_three_slice_surface(box_parts, 10, 11, 12, inner_width)
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
        if self.potion_frames:
            self.potion_frame_index = (
                self.potion_frame_index + self.potion_anim_speed
            ) % len(self.potion_frames)
        if self.water_top_frames:
            self.water_top_fi = (
                self.water_top_fi + self.water_top_speed
            ) % len(self.water_top_frames)
        for frames, attr in [
            (self.tooth_frames, "tooth_fi"),
            (self.shell_frames, "shell_fi"),
            (self.saw_frames,   "saw_fi"),
            (self.spike_frames, "spike_fi"),
        ]:
            if frames:
                setattr(self, attr, (getattr(self, attr) + self.enemy_anim_speed) % len(frames))

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
 
        tip_text = self.font_panel.render(
            "TIP: Hold UP longer for a higher jump!",
            True,
            (255, 244, 180),
        )
        tip_x = self.width // 2 - tip_text.get_width() // 2
        tip_y = self.height - tip_text.get_height() - 18
        tip_shadow = self.font_panel.render(
            "TIP: Hold UP longer for a higher jump!",
            True,
            (0, 0, 0),
        )
        self.screen.blit(tip_shadow, (tip_x + 1, tip_y + 1))
        self.screen.blit(tip_text, (tip_x, tip_y))

        if self.show_instructions:
            mouse_pos = pygame.mouse.get_pos()
            self.draw_instruction_panel()
            bir = self.instruction_panel_board_inner_rect
            btn_y = self.panel_rect.bottom - 40
            prev_center = (bir.left - 90,  btn_y)
            next_center = (bir.right + 90, btn_y)
            has_prev_page = self.instruction_page > 0
            has_next_page = self.instruction_page < len(self.instruction_pages) - 1
            close_hovered = False
            if self.instruction_close_button_surface is not None:
                close_hovered = self._get_instruction_close_button_base_rect().collidepoint(mouse_pos)
            prev_hovered = (
                has_prev_page
                and self.instruction_prev_button_surface is not None
                and self.instruction_prev_button_surface.get_rect(center=prev_center).collidepoint(mouse_pos)
            )
            next_hovered = (
                has_next_page
                and self.instruction_next_button_surface is not None
                and self.instruction_next_button_surface.get_rect(center=next_center).collidepoint(mouse_pos)
            )
            self.draw_instruction_close_button(hovered=close_hovered)
            self.prev_rect = pygame.Rect(0, 0, 0, 0)
            self.next_rect = pygame.Rect(0, 0, 0, 0)
            if has_prev_page:
                self.prev_rect = self.draw_instruction_icon_button(
                    self.instruction_prev_button_surface,
                    prev_center,
                    hovered=prev_hovered,
                )
            if has_next_page:
                self.next_rect = self.draw_instruction_icon_button(
                    self.instruction_next_button_surface,
                    next_center,
                    hovered=next_hovered,
                )

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

    def draw_instruction_panel_button(self, label, center):
        text_surface = self.render_instruction_button_text(label)
        if text_surface is None:
            return self.draw_menu_item(label, center, False)

        outlined_surface = self.create_outlined_surface(
            text_surface,
            (128, 128, 128, 255),
            ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (-2, 2), (2, -2), (2, 2)),
        )
        button_rect = outlined_surface.get_rect(center=center)
        self.screen.blit(outlined_surface, button_rect)
        return button_rect

    def draw_instruction_icon_button(self, button_surface, center, hovered=False):
        if button_surface is None:
            return pygame.Rect(0, 0, 0, 0)

        draw_surface = self._get_instruction_hover_surface(button_surface, hovered)
        button_rect = draw_surface.get_rect(center=center)
        self.screen.blit(draw_surface, button_rect)
        return button_rect

    def _get_instruction_close_button_base_rect(self):
        if self.instruction_close_button_surface is None:
            return pygame.Rect(0, 0, 0, 0)

        offset_x, offset_y = self.instruction_close_button_offset
        return self.instruction_close_button_surface.get_rect(
            top=self.panel_rect.top + offset_y,
            right=self.panel_rect.right - offset_x,
        )

    def draw_instruction_close_button(self, hovered=False):
        if self.instruction_close_button_surface is None:
            self.instruction_close_button_rect = pygame.Rect(0, 0, 0, 0)
            return self.instruction_close_button_rect

        base_rect = self._get_instruction_close_button_base_rect()
        draw_surface = self._get_instruction_hover_surface(
            self.instruction_close_button_surface,
            hovered,
        )
        button_rect = draw_surface.get_rect(
            center=base_rect.center,
        )
        self.screen.blit(draw_surface, button_rect)
        self.instruction_close_button_rect = button_rect
        return button_rect

    def rebuild_instruction_panel_layout(self):
        panel_width, panel_height = self.instruction_panel_size
        offset_x, offset_y = self.instruction_panel_center_offset
        self.panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        self.panel_rect.center = (self.width // 2 + offset_x, self.height // 2 + offset_y)

        self.instruction_panel_surface = None
        self.instruction_panel_paper_surface = None
        self.instruction_panel_title_paper_surface = None
        self.instruction_panel_board_inner_rect = self.panel_rect.inflate(-48, -48)

        if all(idx in self.instruction_panel_parts for idx in range(1, 10)):
            self.instruction_panel_surface = self._build_instruction_panel_surface(
                self.instruction_panel_parts,
                self.panel_rect.size,
            )
            self.instruction_panel_board_inner_rect = self._get_panel_inner_rect(
                self.instruction_panel_parts,
                self.panel_rect,
            )

        title_width, title_height = self.instruction_title_paper_size
        title_offset_x, title_top = self.instruction_title_paper_offset
        self.instruction_panel_title_paper_rect = pygame.Rect(0, 0, title_width, title_height)
        self.instruction_panel_title_paper_rect.centerx = self.instruction_panel_board_inner_rect.centerx + title_offset_x
        self.instruction_panel_title_paper_rect.top = self.instruction_panel_board_inner_rect.top + title_top
        self.instruction_panel_title_inner_rect = self.instruction_panel_title_paper_rect.inflate(-24, -24)

        if all(idx in self.instruction_title_paper_parts for idx in range(1, 10)):
            self.instruction_panel_title_paper_surface = self._build_instruction_panel_surface(
                self.instruction_title_paper_parts,
                self.instruction_panel_title_paper_rect.size,
            )
            self.instruction_panel_title_inner_rect = self._get_panel_inner_rect(
                self.instruction_title_paper_parts,
                self.instruction_panel_title_paper_rect,
            )

        body_width, body_height = self.instruction_body_paper_size
        body_offset_x, body_top = self.instruction_body_paper_offset
        self.instruction_panel_paper_rect = pygame.Rect(0, 0, body_width, body_height)
        self.instruction_panel_paper_rect.centerx = self.instruction_panel_board_inner_rect.centerx + body_offset_x
        self.instruction_panel_paper_rect.top = self.instruction_panel_board_inner_rect.top + body_top
        self.instruction_panel_inner_rect = self.instruction_panel_paper_rect.inflate(-24, -24)

        if all(idx in self.instruction_paper_parts for idx in range(1, 10)):
            self.instruction_panel_paper_surface = self._build_instruction_panel_surface(
                self.instruction_paper_parts,
                self.instruction_panel_paper_rect.size,
            )
            self.instruction_panel_inner_rect = self._get_panel_inner_rect(
                self.instruction_paper_parts,
                self.instruction_panel_paper_rect,
            )

    # ------------------------------------------------------------------
    # Green Board nine-slice helpers
    # ------------------------------------------------------------------
    def _blit_tiled_region(self, surface, tile, target_rect):
        if target_rect.width <= 0 or target_rect.height <= 0:
            return

        tile_w, tile_h = tile.get_size()
        for draw_y in range(target_rect.top, target_rect.bottom, tile_h):
            seg_h = min(tile_h, target_rect.bottom - draw_y)
            for draw_x in range(target_rect.left, target_rect.right, tile_w):
                seg_w = min(tile_w, target_rect.right - draw_x)
                surface.blit(
                    tile,
                    (draw_x, draw_y),
                    pygame.Rect(0, 0, seg_w, seg_h),
                )

    def _build_instruction_panel_surface(self, parts, size):
        """Build a tiled nine-slice surface for the instruction popup layers."""
        p = parts
        width, height = size
        tl, tm, tr = p[1], p[2], p[3]
        ml, mm, mr = p[4], p[5], p[6]
        bl, bm, br = p[7], p[8], p[9]

        lw = ml.get_width()
        rw = mr.get_width()
        th = tm.get_height()
        bh = bm.get_height()

        width  = max(width,  lw + rw + mm.get_width())
        height = max(height, th + bh + mm.get_height())

        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        iw = width  - lw - rw
        ih = height - th - bh

        self._blit_tiled_region(surf, tm, pygame.Rect(lw, 0, iw, th))
        self._blit_tiled_region(surf, bm, pygame.Rect(lw, height - bh, iw, bh))
        self._blit_tiled_region(surf, ml, pygame.Rect(0, th, lw, ih))
        self._blit_tiled_region(surf, mr, pygame.Rect(width - rw, th, rw, ih))
        self._blit_tiled_region(surf, mm, pygame.Rect(lw, th, iw, ih))

        surf.blit(tl, (0,          0))
        surf.blit(tr, (width - rw, 0))
        surf.blit(bl, (0,          height - bh))
        surf.blit(br, (width - rw, height - bh))
        return surf

    def _get_panel_inner_rect(self, parts, outer_rect):
        """Return the usable inner rect inside a nine-slice border."""
        p = parts
        lw = p[4].get_width()
        rw = p[6].get_width()
        th = p[2].get_height()
        bh = p[8].get_height()
        return pygame.Rect(
            outer_rect.left + lw,
            outer_rect.top  + th,
            max(0, outer_rect.width  - lw - rw),
            max(0, outer_rect.height - th - bh),
        )

    def _build_fallback_close_button_surface(self):
        width, height = self.instruction_close_button_size
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(surface, (113, 178, 132), surface.get_rect(), border_radius=6)
        pygame.draw.rect(surface, (47, 73, 62), surface.get_rect(), width=3, border_radius=6)
        pygame.draw.line(surface, (47, 73, 62), (10, 10), (width - 10, height - 10), 3)
        pygame.draw.line(surface, (47, 73, 62), (width - 10, 10), (10, height - 10), 3)
        return surface

    def _get_instruction_hover_surface(self, surface, hovered):
        if not hovered:
            return surface

        scaled_width = max(1, round(surface.get_width() * self.instruction_button_hover_scale))
        scaled_height = max(1, round(surface.get_height() * self.instruction_button_hover_scale))
        return pygame.transform.scale(surface, (scaled_width, scaled_height))

    def _build_instruction_icon_button_surface(self, icon_path, size, icon_scale):
        try:
            button_surface = load_image(
                "asset/graphics/ui/Green Button/1.png",
                size=size,
            )
            icon_surface = load_image(icon_path, scale=icon_scale)
            icon_rect = icon_surface.get_rect(center=button_surface.get_rect().center)
            button_surface.blit(icon_surface, icon_rect)
            return button_surface
        except Exception as e:
            print(f"Instruction icon button load failed for {icon_path}: {e}")
            return self._build_fallback_close_button_surface()

    # ------------------------------------------------------------------

    def draw_instruction_panel(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        self.screen.blit(overlay, (0, 0))

        # Draw the Green Board nine-slice frame
        if self.instruction_panel_surface is not None:
            self.screen.blit(self.instruction_panel_surface, self.panel_rect.topleft)
        else:
            # Fallback plain rectangle if asset not found
            pygame.draw.rect(self.screen, (23, 39, 66), self.panel_rect, border_radius=24)
            pygame.draw.rect(self.screen, (255, 214, 82), self.panel_rect, width=4, border_radius=24)

        if self.instruction_panel_paper_surface is not None:
            self.screen.blit(self.instruction_panel_paper_surface, self.instruction_panel_paper_rect.topleft)
        if self.instruction_panel_title_paper_surface is not None:
            self.screen.blit(self.instruction_panel_title_paper_surface, self.instruction_panel_title_paper_rect.topleft)

        # Use the inner rect (inside the border) for all content placement
        ir = self.instruction_panel_inner_rect
        # --- Water background (page 4) ---
                # --- Water background (page 4) ---
        WATER_PAGE_INDEX = 4

        if (
            self.instruction_page == WATER_PAGE_INDEX
            and self.water_body
        ):
            water_height = 180
            water_y = ir.bottom - water_height

            water_surf = pygame.Surface(
                (ir.width, water_height),
                pygame.SRCALPHA,
            )

            ww, wh = water_surf.get_size()

            body_tile = self.water_body.copy()
            body_tile.set_alpha(self.water_alpha)

            tile_w = body_tile.get_width()
            tile_h = body_tile.get_height()

            # Fill water body
            for ty in range(0, wh, tile_h):
                for tx in range(0, ww, tile_w):
                    water_surf.blit(body_tile, (tx, ty))

            # Animated water top
            if self.water_top_frames:
                top_frame = self.water_top_frames[
                    int(self.water_top_fi)
                ].copy()

                top_frame.set_alpha(self.water_alpha)

                top_w = top_frame.get_width()

                for tx in range(0, ww, top_w):
                    water_surf.blit(top_frame, (tx, 0))

            self.screen.blit(
                water_surf,
                (ir.left, water_y),
            )


        page = self.instruction_pages[self.instruction_page]

        # --- Title ---
        title_text = self.render_instruction_title_text(page["title"])
        if title_text is None:
            title_text = self.font_sub.render(page["title"], True, (255, 244, 214))
        if self.instruction_panel_title_paper_surface is not None:
            tir = self.instruction_panel_title_inner_rect
            title_rect = title_text.get_rect(center=(tir.centerx, tir.centery + 8))
            self.screen.blit(title_text, title_rect)
        else:
            title_rect = title_text.get_rect(center=(ir.centerx, ir.top + 32))
            self.screen.blit(title_text, title_rect)

        # --- Content lines ---
        line_start_y = ir.top + (28 if self.instruction_panel_title_paper_surface is not None else 82)
        if len(page["lines"]) > 1:
            line_spacing = min(
                40,
                max(26, (ir.bottom - 22 - line_start_y) // (len(page["lines"]) - 1)),
            )
        else:
            line_spacing = 0
        for index, line in enumerate(page["lines"]):
            line_text = self.render_instruction_body_text(line)
            if line_text is None:
                line_text = self.font_panel.render(line, True, (232, 240, 255))
            line_rect = line_text.get_rect(
                center=(ir.centerx, line_start_y + index * line_spacing)
            )
            self.screen.blit(line_text, line_rect)

        # --- Sprite decorations ---
        HEALTH_PAGE_INDEX = 2
        if self.instruction_page == HEALTH_PAGE_INDEX and self.potion_frames:
            potion_frame = self.potion_frames[int(self.potion_frame_index)]
            sprite_x = ir.right - 60
            sprite_y = line_start_y + 2 * line_spacing
            potion_rect = potion_frame.get_rect(center=(sprite_x, sprite_y))
            self.screen.blit(potion_frame, potion_rect)

        ENEMIES_PAGE_INDEX = 3
        if self.instruction_page == ENEMIES_PAGE_INDEX:
            sprite_x = ir.right - 60
            enemy_sprites = [
                (self.tooth_frames, self.tooth_fi),
                (self.shell_frames, self.shell_fi),
                (self.saw_frames,   self.saw_fi),
            ]
            for row, (frames, fi) in enumerate(enemy_sprites):
                if not frames:
                    continue
                frame = frames[int(fi)]
                sprite_y = line_start_y + row * line_spacing
                sprite_rect = frame.get_rect(center=(sprite_x, sprite_y))
                self.screen.blit(frame, sprite_rect)

        # --- Page dots ---
        total_pages = len(self.instruction_pages)
        dot_radius = 5
        dot_spacing = 18
        dots_total_w = total_pages * dot_spacing - (dot_spacing - dot_radius * 2)
        dot_start_x = ir.centerx - dots_total_w // 2
        dot_y = self.panel_rect.bottom - 90
        for i in range(total_pages):
            dot_x = dot_start_x + i * dot_spacing
            color = (255, 214, 82) if i == self.instruction_page else (100, 100, 130)
            pygame.draw.circle(self.screen, color, (dot_x, dot_y), dot_radius)

    def handle_event(self, event):
        if self.show_instructions:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.instruction_page = max(0, self.instruction_page - 1)
                    return None
                elif event.key == pygame.K_RIGHT:
                    if self.instruction_page < len(self.instruction_pages) - 1:
                        self.instruction_page += 1
                    else:
                        self.show_instructions = False
                    return None
                elif event.key in (pygame.K_ESCAPE,):
                    self.show_instructions = False
                    return None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.instruction_close_button_rect.collidepoint(event.pos):
                    self.show_instructions = False
                elif self.prev_rect.collidepoint(event.pos):
                    self.instruction_page = max(0, self.instruction_page - 1)
                elif self.next_rect.collidepoint(event.pos):
                    if self.instruction_page < len(self.instruction_pages) - 1:
                        self.instruction_page += 1
                    else:
                        self.show_instructions = False
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self.start_text_rect.collidepoint(event.pos):
            return "game"

        if self.instructions_text_rect.collidepoint(event.pos):
            self.show_instructions = True
            self.instruction_page = 0

        return None


class LoseScreen(ResultScreenBase):
    def __init__(self, screen):
        super().__init__(screen, "GAME OVER", title_padding=0)

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

    def draw(self, score):
        self.draw_overlay()
        upper_surface = self.build_upper_panel(score)

        self.draw_title((self.width // 2, 145))
        upper_rect = upper_surface.get_rect(center=(self.width // 2, 340))
        self.screen.blit(upper_surface, upper_rect)
        self.draw_lower_panel((self.width // 2, 540))


class WinScreen(ResultScreenBase):
    def __init__(self, screen):
        super().__init__(screen, "YOU WIN!", title_padding=36)

        try:
            _flag = load_image("asset/graphics/objects/flag.png")
            _fw, _fh = _flag.get_size()
            _target_h = 120
            _scale = _target_h / max(_fh, 1)
            self.flag_image = pygame.transform.scale(
                _flag,
                (max(1, round(_fw * _scale)), max(1, round(_fh * _scale))),
            )
        except Exception:
            self.flag_image = None

        try:
            _fframes = load_frames("asset/graphics/level/flag")
            _fw0, _fh0 = _fframes[0].get_size()
            _target_h = 120
            _sc = _target_h / max(_fh0, 1)
            self.flag_frames = [
                pygame.transform.scale(f, (max(1, round(_fw0 * _sc)), max(1, round(_fh0 * _sc))))
                for f in _fframes
            ]
        except Exception:
            self.flag_frames = []
        self.flag_fi = 0.0
        self.flag_speed = 0.12

    def build_upper_panel(self, score, _time_left):
        board = self.build_six_slice(self.upper_board_parts, (540, 250))
        paper = self.build_six_slice(self.paper_parts, (390, 150))
        paper_rect = paper.get_rect(center=(board.get_width() // 2, board.get_height() // 2))
        board.blit(paper, paper_rect)

        score_surf = self.render_small_text("SCORE:" + str(score))
        if score_surf:
            board.blit(score_surf, score_surf.get_rect(center=paper_rect.center))
        return board

    def update(self, dt):
        if self.flag_frames:
            self.flag_fi = (self.flag_fi + self.flag_speed) % len(self.flag_frames)

    def draw(self, score, time_left):
        # Golden celebratory overlay (different from lose screen's dark overlay)
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((255, 200, 0, 60))
        self.screen.blit(overlay, (0, 0))

        # Animated flag — top centre
        flag_draw = None
        if self.flag_frames:
            flag_draw = self.flag_frames[int(self.flag_fi)]
        elif self.flag_image:
            flag_draw = self.flag_image
        if flag_draw is not None:
            self.screen.blit(flag_draw, flag_draw.get_rect(center=(self.width // 2, 110)))

        title_y = 200 if flag_draw is None else 195
        self.draw_title((self.width // 2, title_y))

        upper_surface = self.build_upper_panel(score, time_left)
        upper_rect = upper_surface.get_rect(center=(self.width // 2, 360))
        self.screen.blit(upper_surface, upper_rect)

        self.draw_lower_panel((self.width // 2, 530))
