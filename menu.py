"""
menu.py
=======
MenuScreen — the landing page shown when the app first launches,
and when the user clicks "Main Menu" from inside the solver.

Layout:
    - Full-screen scrolling maze-tile background (reuses terrain colors)
    - Centered floating panel with SRCALPHA translucency
    - Three buttons: Play, Analytics, How to Play
    - Title + subtitle rendered in the panel header

Navigation:
    handle_events() returns one of:
        "PLAY"      — user clicked Play
        "ANALYTICS" — user clicked Analytics
        "TUTORIAL"  — user clicked How to Play
        None        — no navigation event this frame
"""

import os
import math
import random
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BG_COLOR, SIDEBAR_BG, SIDEBAR_BORDER,
    TEXT_COLOR, TEXT_MUTED,
    COLORS, PLAIN, MUD, WATER, WALL,
)

# ------------------------------------------------------------------ #
# Font paths — same pattern as visualizer.py
# ------------------------------------------------------------------ #
_HERE      = os.path.dirname(os.path.abspath(__file__))
_FONTS_DIR = os.path.join(_HERE, "assets", "fonts")

_JB_BOLD  = os.path.join(_FONTS_DIR, "JetBrainsMono-Bold.ttf")
_JB_REG   = os.path.join(_FONTS_DIR, "JetBrainsMono-Regular.ttf")
_IBM_REG  = os.path.join(_FONTS_DIR, "IBMPlexSans-Regular.ttf")
_IBM_SEMI = os.path.join(_FONTS_DIR, "IBMPlexSans-SemiBold.ttf")


def _load_font(path, size, fallback="Segoe UI", bold=False):
    if os.path.exists(path):
        return pygame.font.Font(path, size)
    return pygame.font.SysFont(fallback, size, bold=bold)


# ------------------------------------------------------------------ #
# Panel + button sizing
# ------------------------------------------------------------------ #
PANEL_W = 420
PANEL_H = 340

BTN_W   = 320
BTN_H   = 44
BTN_GAP = 12

# Terrain tile size for the scrolling background
TILE    = 22


class MenuScreen:
    def __init__(self):
        pygame.font.init()

        self.f_title    = _load_font(_JB_BOLD,  28, bold=True)
        self.f_subtitle = _load_font(_JB_REG,   12)
        self.f_btn      = _load_font(_IBM_SEMI, 14, bold=True)

        # Panel position — centered
        self.panel_x = (SCREEN_WIDTH  - PANEL_W) // 2
        self.panel_y = (SCREEN_HEIGHT - PANEL_H) // 2

        # Translucent panel surface (drawn once, reused every frame)
        self._panel_surf = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        self._panel_surf.fill((21, 21, 34, 220))   # dark navy, 86% opaque

        # Button rects — positioned relative to screen (not panel)
        # Buttons start 120px below the top of the panel (after title area)
        btn_x    = self.panel_x + (PANEL_W - BTN_W) // 2
        btn_y0   = self.panel_y + 148

        self._buttons = [
            ("PLAY",      "Play",           btn_x, btn_y0),
            ("ANALYTICS", "Analytics",      btn_x, btn_y0 + (BTN_H + BTN_GAP)),
            ("TUTORIAL",  "How to Play",    btn_x, btn_y0 + (BTN_H + BTN_GAP) * 2),
        ]

        self._btn_rects = {
            key: pygame.Rect(bx, by, BTN_W, BTN_H)
            for key, _, bx, by in self._buttons
        }

        # Hover state
        self._hovered = None

        # ---- scrolling background ----------------------------------- #
        # We bake a surface exactly 2× the screen size in both dimensions.
        # Each frame we draw it in a 2×2 grid offset by the scroll value.
        # Because the offset is always < surface size (modulo keeps it bounded),
        # the 2×2 grid always covers the entire screen with no gaps.
        self._scroll_x   = 0.0
        self._scroll_y   = 0.0
        self._scroll_spd = 0.4

        # Surface is 2× screen so the tiled grid has a natural seam point
        self._bg_w = SCREEN_WIDTH  * 2
        self._bg_h = SCREEN_HEIGHT * 2

        cols = self._bg_w // TILE + 1
        rows = self._bg_h // TILE + 1

        _weights = [PLAIN] * 70 + [MUD] * 12 + [WATER] * 8 + [WALL] * 10
        self._bg_tiles = [
            [random.choice(_weights) for _ in range(cols)]
            for _ in range(rows)
        ]
        self._bg_cols = cols
        self._bg_rows = rows

        self._bg_surf = pygame.Surface((self._bg_w, self._bg_h))
        self._bake_background()

    # ================================================================ #
    # PUBLIC
    # ================================================================ #

    def handle_events(self, events):
        """
        Process events. Returns a navigation string or None.
            "PLAY" | "ANALYTICS" | "TUTORIAL" | None
        """
        mouse_pos = pygame.mouse.get_pos()
        self._hovered = None
        for key, rect in self._btn_rects.items():
            if rect.collidepoint(mouse_pos):
                self._hovered = key

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in self._btn_rects.items():
                    if rect.collidepoint(event.pos):
                        return key   # e.g. "PLAY"

        return None

    def update(self):
        """Advance the background scroll animation."""
        self._scroll_x = (self._scroll_x + self._scroll_spd) % self._bg_w
        self._scroll_y = (self._scroll_y + self._scroll_spd * 0.4) % self._bg_h

    def draw(self, screen):
        """Full draw — background, panel, buttons."""
        self._draw_background(screen)
        self._draw_panel(screen)
        self._draw_title(screen)
        self._draw_buttons(screen)
        pygame.display.flip()

    # ================================================================ #
    # BACKGROUND
    # ================================================================ #

    def _bake_background(self):
        """Render the tile grid onto _bg_surf once at startup."""
        for r, row in enumerate(self._bg_tiles):
            for c, terrain in enumerate(row):
                color_hex = COLORS.get(terrain, "#1a1a2e")
                color     = pygame.Color(color_hex)
                # Darken the tiles so they don't compete with the panel
                darkened  = pygame.Color(
                    color.r // 3,
                    color.g // 3,
                    color.b // 3,
                )
                pygame.draw.rect(
                    self._bg_surf, darkened,
                    (c * TILE, r * TILE, TILE - 1, TILE - 1)
                )

    def _draw_background(self, screen):
        """
        Draw the bg_surf in a 2×2 grid offset by scroll values.
        Because scroll_x < bg_w and scroll_y < bg_h (modulo guarantees this),
        the four blits always cover the entire screen with no black gaps.
        """
        ox = int(self._scroll_x)
        oy = int(self._scroll_y)

        for dy in (0, self._bg_h):
            for dx in (0, self._bg_w):
                screen.blit(self._bg_surf, (dx - ox, dy - oy))

    # ================================================================ #
    # PANEL
    # ================================================================ #

    def _draw_panel(self, screen):
        """Blit translucent panel, then draw a border around it."""
        screen.blit(self._panel_surf, (self.panel_x, self.panel_y))

        # Border
        pygame.draw.rect(
            screen,
            pygame.Color(SIDEBAR_BORDER),
            (self.panel_x, self.panel_y, PANEL_W, PANEL_H),
            width=1,
            border_radius=10,
        )

        # Accent line under title area
        line_y = self.panel_y + 128
        pygame.draw.line(
            screen,
            pygame.Color(SIDEBAR_BORDER),
            (self.panel_x + 24, line_y),
            (self.panel_x + PANEL_W - 24, line_y),
            1,
        )

    # ================================================================ #
    # TITLE
    # ================================================================ #

    def _draw_title(self, screen):
        # Main title
        title_surf = self.f_title.render("HEURISTICA", True, pygame.Color("#6366F1"))
        tx = self.panel_x + (PANEL_W - title_surf.get_width()) // 2
        ty = self.panel_y + 38
        screen.blit(title_surf, (tx, ty))

        # Subtitle
        sub_lines = [
            "Weighted terrain  ·  5 algorithms",
            "Coins  ·  Greed heuristic  ·  Analytics",
        ]
        sy = ty + title_surf.get_height() + 10
        for line in sub_lines:
            sub_surf = self.f_subtitle.render(line, True, pygame.Color(TEXT_MUTED))
            sx = self.panel_x + (PANEL_W - sub_surf.get_width()) // 2
            screen.blit(sub_surf, (sx, sy))
            sy += sub_surf.get_height() + 4

    # ================================================================ #
    # BUTTONS
    # ================================================================ #

    def _draw_buttons(self, screen):
        for key, label, bx, by in self._buttons:
            rect      = self._btn_rects[key]
            is_hovered = (self._hovered == key)

            if key == "PLAY":
                # Primary button — accent color, brighter on hover
                bg_color = "#7C7FF5" if is_hovered else "#6366F1"
            else:
                # Secondary buttons — dark, lighter on hover
                bg_color = "#3E4A5E" if is_hovered else "#2D3748"

            pygame.draw.rect(screen, pygame.Color(bg_color), rect, border_radius=7)

            # Subtle border on secondary buttons
            if key != "PLAY":
                pygame.draw.rect(
                    screen, pygame.Color(SIDEBAR_BORDER),
                    rect, width=1, border_radius=7
                )

            txt  = self.f_btn.render(label, True, pygame.Color("#FFFFFF"))
            tx   = rect.x + (rect.width  - txt.get_width())  // 2
            ty   = rect.y + (rect.height - txt.get_height()) // 2
            screen.blit(txt, (tx, ty))