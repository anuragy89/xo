"""
wordsearch.py — Word Search grid engine + Pillow image renderer.

Grid generation:
  1. Place each word in a random direction (H, V, diagonal, + reverse).
  2. Fill remaining cells with random uppercase letters.

Image renderer:
  Creates a dark-themed grid image showing:
  - Theme header
  - Letter grid with highlighted found words
  - Word count / progress info
"""

import io
import random
import string

from PIL import Image, ImageDraw, ImageFont

# ── Directions: (row_delta, col_delta) ────────────────────
DIRECTIONS = [
    (0, 1),   # right
    (0, -1),  # left
    (1, 0),   # down
    (-1, 0),  # up
    (1, 1),   # diagonal down-right
    (1, -1),  # diagonal down-left
    (-1, 1),  # diagonal up-right
    (-1, -1), # diagonal up-left
]


def generate_grid(words: list[str], size: int = 10) -> dict:
    """
    Generate a word search grid.

    Returns: {
        "grid": list[list[str]],  -- size×size letter grid
        "size": int,
        "placements": {word: [(r, c), ...]}  -- cell coords for each word
    }
    """
    grid = [["" for _ in range(size)] for _ in range(size)]
    placements: dict[str, list[tuple[int, int]]] = {}

    # Sort by longest first — easier to place long words first
    sorted_words = sorted(words, key=len, reverse=True)

    for word in sorted_words:
        placed = _place_word(grid, word, size)
        if placed:
            placements[word] = placed

    # Fill empty cells
    for r in range(size):
        for c in range(size):
            if grid[r][c] == "":
                grid[r][c] = random.choice(string.ascii_uppercase)

    return {"grid": grid, "size": size, "placements": placements}


def _place_word(grid: list[list[str]], word: str, size: int, max_attempts: int = 100) -> list[tuple[int, int]] | None:
    """Try to place a word in the grid. Returns cell positions or None."""
    dirs = DIRECTIONS[:]
    random.shuffle(dirs)

    for _ in range(max_attempts):
        dr, dc = random.choice(dirs)
        # Calculate valid start positions
        r = random.randint(0, size - 1)
        c = random.randint(0, size - 1)

        # Check if word fits from (r, c) in direction (dr, dc)
        end_r = r + dr * (len(word) - 1)
        end_c = c + dc * (len(word) - 1)
        if end_r < 0 or end_r >= size or end_c < 0 or end_c >= size:
            continue

        # Check for conflicts
        positions = []
        ok = True
        for i, ch in enumerate(word):
            nr, nc = r + dr * i, c + dc * i
            existing = grid[nr][nc]
            if existing != "" and existing != ch:
                ok = False
                break
            positions.append((nr, nc))

        if not ok:
            continue

        # Place it
        for i, ch in enumerate(word):
            nr, nc = positions[i]
            grid[nr][nc] = ch

        return positions

    return None  # Could not place


def find_word_in_grid(grid: list[list[str]], word: str, size: int) -> list[tuple[int, int]] | None:
    """
    Verify that a word exists in the grid along a valid direction.
    Returns cell positions if found, else None.
    """
    word = word.upper()
    for r in range(size):
        for c in range(size):
            if grid[r][c] != word[0]:
                continue
            for dr, dc in DIRECTIONS:
                end_r = r + dr * (len(word) - 1)
                end_c = c + dc * (len(word) - 1)
                if end_r < 0 or end_r >= size or end_c < 0 or end_c >= size:
                    continue
                positions = []
                match = True
                for i, ch in enumerate(word):
                    nr, nc = r + dr * i, c + dc * i
                    if grid[nr][nc] != ch:
                        match = False
                        break
                    positions.append((nr, nc))
                if match:
                    return positions
    return None


# ── Image Renderer ────────────────────────────────────────

# Colors
BG_COLOR       = (30, 30, 46)       # dark navy
GRID_BG        = (45, 45, 65)       # cell background
CELL_BORDER    = (60, 60, 85)       # grid lines
TEXT_COLOR      = (200, 210, 230)    # letter color
FOUND_BG       = (50, 140, 80)      # green highlight for found
FOUND_TEXT     = (255, 255, 255)     # white on found
HEADER_COLOR   = (130, 170, 255)    # theme title
PROGRESS_COLOR = (255, 200, 80)     # word count

CELL_SIZE = 42
PADDING   = 20
HEADER_H  = 60
FOOTER_H  = 50


def render_grid_image(
    grid: list[list[str]],
    size: int,
    theme: str,
    total_words: int,
    found_words: list[str],
    placements: dict[str, list[list[int]]],
) -> bytes:
    """Render grid as a PNG image. Returns bytes."""
    grid_px = size * CELL_SIZE
    width   = grid_px + PADDING * 2
    height  = HEADER_H + grid_px + FOOTER_H + PADDING

    img  = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Build set of highlighted cells
    found_cells: set[tuple[int, int]] = set()
    for word in found_words:
        coords = placements.get(word, [])
        for pos in coords:
            if isinstance(pos, (list, tuple)):
                found_cells.add((pos[0], pos[1]))

    x_off = PADDING
    y_off = HEADER_H

    # Try to use a nice built-in font, fall back to default
    try:
        font_letter = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_footer = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except (OSError, IOError):
        font_letter = ImageFont.load_default()
        font_header = font_letter
        font_footer = font_letter

    # ── Header ────────────────────────────
    draw.text(
        (PADDING, 15),
        f"🔍 THEME: {theme}",
        fill=HEADER_COLOR,
        font=font_header,
    )

    # ── Grid cells ────────────────────────
    for r in range(size):
        for c in range(size):
            cx = x_off + c * CELL_SIZE
            cy = y_off + r * CELL_SIZE

            is_found = (r, c) in found_cells

            # Cell background
            bg = FOUND_BG if is_found else GRID_BG
            draw.rounded_rectangle(
                [cx + 1, cy + 1, cx + CELL_SIZE - 1, cy + CELL_SIZE - 1],
                radius=4, fill=bg, outline=CELL_BORDER,
            )

            # Letter
            letter = grid[r][c]
            fg = FOUND_TEXT if is_found else TEXT_COLOR
            bbox = draw.textbbox((0, 0), letter, font=font_letter)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = cx + (CELL_SIZE - tw) // 2
            ty = cy + (CELL_SIZE - th) // 2 - 2
            draw.text((tx, ty), letter, fill=fg, font=font_letter)

    # ── Footer ────────────────────────────
    found_count = len(found_words)
    footer_y = y_off + grid_px + 10
    draw.text(
        (PADDING, footer_y),
        f"🔎 Find {total_words} words!    ✅ Found: {found_count}/{total_words}",
        fill=PROGRESS_COLOR,
        font=font_footer,
    )

    # ── Export ─────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
