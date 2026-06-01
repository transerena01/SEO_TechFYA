from pathlib import Path
import pygame
from settings import SETTINGS


class StartScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width  = SETTINGS["WIDTH"]
        self.height = SETTINGS["HEIGHT"]
        self.font_path = Path(SETTINGS["FONT_PATH"])

        # Load background
        self.bg = pygame.image.load("asset/screen_start.png").convert()
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))

        # Fonts
        self.font_title  = self.load_font(110)
        self.font_sub    = self.load_font(50)
        self.font_button = self.load_font(48)
        self.font_panel  = self.load_font(26)
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
        self.big_text_glyphs = self.load_big_text_glyphs()
        self.small_text_scale = 3
        self.small_text_letter_spacing = 3
        self.small_text_word_spacing = 12
        self.small_text_glyphs = self.load_small_text_glyphs()
        self.subtitle_text_scale = 4
        self.subtitle_text_letter_spacing = 4
        self.subtitle_text_word_spacing = 14
        self.subtitle_text_glyphs = self.load_small_text_glyphs(scale=self.subtitle_text_scale)
        self.menu_board_scale = 2
        self.yellow_board_parts = self.load_yellow_board_parts()
        self.paper_box_scale_x = 1.85
        self.paper_box_scale_y = 4
        self.yellow_paper_parts = self.load_yellow_paper_parts()
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

        # Pink Star idle animation
        self.star_scale = 10
        self.star_frames = self.load_animation_frames(
            "asset/character/Pink Star/01-Idle",
            self.star_scale,
            flip_x=True,
        )
        self.star_frame_index = 0.0
        self.star_animation_speed = 0.18
        self.star_base_x = 300
        self.star_base_y = 475

        # Fierce Tooth idle animation
        self.fierce_tooth_scale = 10
        self.fierce_tooth_frames = self.load_animation_frames(
            "asset/enemy/Fierce Tooth/01-Idle",
            self.fierce_tooth_scale,
        )
        self.fierce_tooth_frame_index = 0.0
        self.fierce_tooth_animation_speed = 0.18
        self.fierce_tooth_x = 1030
        self.fierce_tooth_y = 372

        # Menu text
        self.start_text_rect = pygame.Rect(0, 0, 0, 0)
        self.instructions_text_rect = pygame.Rect(0, 0, 0, 0)

        # Instruction panel
        self.show_instructions = False
        self.panel_rect = pygame.Rect(0, 0, 860, 320)
        self.panel_rect.center = (self.width // 2, self.height // 2 + 30)
        self.close_text_rect = pygame.Rect(0, 0, 0, 0)
        self.instruction_lines = [
            "Move the mouse to highlight a menu item.",
            "Click Start Game to begin the adventure.",
            "Click Instruction to open this guide again.",
        ]

    def load_font(self, size):
        if self.font_path.exists():
            return pygame.font.Font(self.font_path.as_posix(), size)
        return pygame.font.Font(None, size)

    def load_animation_frames(self, folder_path, scale, flip_x=False):
        idle_dir = Path(folder_path)
        frame_paths = sorted(idle_dir.glob("Idle *.png"))
        frames = []

        for frame_path in frame_paths:
            frame = pygame.image.load(frame_path.as_posix()).convert_alpha()
            frame = pygame.transform.scale_by(frame, scale)
            if flip_x:
                frame = pygame.transform.flip(frame, True, False)
            frames.append(frame)

        return frames

    def load_big_text_glyphs(self):
        glyph_dir = Path("font/Big Text")
        glyphs = {}

        for index, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ", start=1):
            glyph_path = glyph_dir / f"{index}.png"
            if glyph_path.exists():
                glyph = pygame.image.load(glyph_path.as_posix()).convert_alpha()
                glyphs[letter] = pygame.transform.scale_by(glyph, self.big_text_scale)

        return glyphs

    def load_small_text_glyphs(self, scale=None):
        glyph_dir = Path("font/Small Text")
        glyphs = {}
        glyph_scale = self.small_text_scale if scale is None else scale

        for index, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ", start=1):
            glyph_path = glyph_dir / f"{index}.png"
            if glyph_path.exists():
                glyph = pygame.image.load(glyph_path.as_posix()).convert_alpha()
                glyphs[letter] = pygame.transform.scale_by(glyph, glyph_scale)

        return glyphs

    def load_yellow_board_parts(self):
        return self.load_box_parts(
            "asset/Yellow Board",
            self.menu_board_scale,
            self.menu_board_scale,
        )

    def load_yellow_paper_parts(self):
        return self.load_box_parts(
            "asset/Yellow Paper",
            self.paper_box_scale_x,
            self.paper_box_scale_y,
        )

    def load_box_parts(self, folder_path, scale_x, scale_y):
        tile_dir = Path(folder_path)
        parts = {}

        for index in (10, 11, 12):
            tile_path = tile_dir / f"{index}.png"
            if tile_path.exists():
                part = pygame.image.load(tile_path.as_posix()).convert_alpha()
                scaled_width = max(1, round(part.get_width() * scale_x))
                scaled_height = max(1, round(part.get_height() * scale_y))
                parts[index] = pygame.transform.scale(part, (scaled_width, scaled_height))

        return parts

    def create_outline_surface(self, surface, color):
        mask = pygame.mask.from_surface(surface)
        return mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))

    def create_outlined_surface(self, surface, color, offsets):
        outline_surface = self.create_outline_surface(surface, color)
        min_offset_x = min(0, *(offset_x for offset_x, _ in offsets))
        max_offset_x = max(0, *(offset_x for offset_x, _ in offsets))
        min_offset_y = min(0, *(_offset_y for _, _offset_y in offsets))
        max_offset_y = max(0, *(_offset_y for _, _offset_y in offsets))

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
        # Background
        self.screen.blit(self.bg, (0, 0))

        # Dark overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))

        # Title
        self.draw_title((self.width // 2, 127))

        # Subtitle
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
        glyph_items = []
        total_width = 0
        max_height = 0

        for index, char in enumerate(self.title_text):
            if char == " ":
                total_width += self.title_word_spacing
                continue

            glyph = self.big_text_glyphs.get(char)
            if glyph is None:
                return self.draw_title_fallback(topleft_center)

            glyph_items.append((char, glyph))
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
        self.close_text_rect = self.draw_menu_item(
            "Back",
            (self.panel_rect.centerx, self.panel_rect.bottom - 50),
            self.close_text_rect.collidepoint(mouse_pos),
        )

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
