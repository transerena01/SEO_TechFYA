from pathlib import Path

import pygame


def load_font(font_path, size):
    font_file = Path(font_path)
    if font_file.exists():
        return pygame.font.Font(font_file.as_posix(), size)
    return pygame.font.Font(None, size)


def load_image(path, *, alpha=True, size=None, scale=None, flip_x=False):
    image_path = Path(path)
    image = pygame.image.load(image_path.as_posix())
    image = image.convert_alpha() if alpha else image.convert()

    if size is not None:
        image = pygame.transform.scale(image, size)
    elif scale is not None:
        image = pygame.transform.scale_by(image, scale)

    if flip_x:
        image = pygame.transform.flip(image, True, False)

    return image


def load_background(path, size):
    return load_image(path, alpha=False, size=size)


def load_music(path, *, volume=1.0, loops=-1):
    music_path = Path(path)
    pygame.mixer.music.load(music_path.as_posix())
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(loops)


def load_sound(path, *, volume=1.0):
    sound_path = Path(path)
    sound = pygame.mixer.Sound(sound_path.as_posix())
    sound.set_volume(volume)
    return sound


def load_frames(
    folder_path,
    *,
    pattern="*.png",
    size=None,
    scale=None,
    flip_x=False,
    sort_key=None,
):
    folder = Path(folder_path)
    if not folder.is_dir():
        raise FileNotFoundError(f"Could not find animation folder: {folder}")

    frame_paths = [path for path in folder.glob(pattern) if path.is_file()]
    if sort_key is None:
        frame_paths.sort(key=lambda path: path.name.lower())
    else:
        frame_paths.sort(key=sort_key)

    if not frame_paths:
        raise ValueError(f"No PNG frames found in animation folder: {folder}")

    return [
        load_image(
            frame_path,
            size=size,
            scale=scale,
            flip_x=flip_x,
        )
        for frame_path in frame_paths
    ]


def load_frames_from_candidates(
    candidate_roots,
    folder_name,
    *,
    size=None,
    scale=None,
    flip_x=False,
    pattern="*.png",
    sort_key=None,
):
    candidate_paths = [Path(root) / folder_name for root in candidate_roots]
    folder_path = next((path for path in candidate_paths if path.is_dir()), None)

    if folder_path is None:
        raise FileNotFoundError(
            f"Could not find animation folder '{folder_name}' in: {candidate_roots}"
        )

    return load_frames(
        folder_path,
        pattern=pattern,
        size=size,
        scale=scale,
        flip_x=flip_x,
        sort_key=sort_key,
    )


def load_glyph_map(folder_path, characters, *, scale, start_index=1):
    glyph_dir = Path(folder_path)
    glyphs = {}

    for index, char in enumerate(characters, start=start_index):
        glyph_path = glyph_dir / f"{index}.png"
        if glyph_path.exists():
            glyphs[char] = load_image(glyph_path, scale=scale)

    return glyphs


def load_big_text_glyphs(scale):
    return load_glyph_map(
        "font/Big Text",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        scale=scale,
    )


def load_small_text_glyphs(scale):
    return load_glyph_map(
        "font/Small Text",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        scale=scale,
    )


def load_ui_small_text_glyphs(scale):
    folder = "asset/graphics/ui/Small Text/Small Text"
    glyphs = load_glyph_map(
        folder,
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        scale=scale,
        start_index=1,
    )
    glyphs.update(
        load_glyph_map(
            folder,
            "1234567890",
            scale=scale,
            start_index=27,
        )
    )
    glyphs.update(load_glyph_map(folder, ":", scale=scale, start_index=50))
    return glyphs


def load_scaled_parts(folder_path, indices, *, scale_x, scale_y):
    tile_dir = Path(folder_path)
    parts = {}

    for index in indices:
        tile_path = tile_dir / f"{index}.png"
        if not tile_path.exists():
            continue

        part = load_image(tile_path)
        scaled_width = max(1, round(part.get_width() * scale_x))
        scaled_height = max(1, round(part.get_height() * scale_y))
        parts[index] = pygame.transform.scale(part, (scaled_width, scaled_height))

    return parts


def load_box_parts(folder_path, scale_x, scale_y):
    return load_scaled_parts(
        folder_path,
        (10, 11, 12),
        scale_x=scale_x,
        scale_y=scale_y,
    )


def load_yellow_board_parts(scale):
    return load_box_parts(
        "asset/graphics/ui/Yellow Board",
        scale,
        scale,
    )


def load_yellow_paper_parts(scale_x, scale_y):
    return load_box_parts(
        "asset/graphics/ui/Yellow Paper",
        scale_x,
        scale_y,
    )


def load_heart_frames(scale):
    return load_frames(
        "asset/graphics/ui/heart",
        scale=scale,
        sort_key=lambda path: int(path.stem),
    )


def load_coin_frames(scale):
    return [
        load_image(
            "asset/graphics/ui/coin.png",
            scale=scale,
        )
    ]
