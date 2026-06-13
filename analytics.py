"""
analytics.py
============
AnalyticsScreen — full-screen analytics dashboard.

Receives a grid from the caller (either the solver's current grid,
or a freshly generated one if the user came straight from the menu).
Shows a "NEW MAZE GENERATED" notice in the latter case.

Layout (1280×720):
    LEFT PANEL  (px 0–620)   — Summary table + verdict badges
    RIGHT PANEL (px 640–1280) — top: Descriptive stats block
                                mid: Scatter plot (Nodes vs Score)
                                bot: Terrain profile bars

Navigation:
    [Main Menu] button  → returns "MENU"
    ESC key             → returns "MENU"
    handle_events() returns "MENU" or None each frame.
"""

import os
import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BG_COLOR, SIDEBAR_BG, SIDEBAR_BORDER,
    TEXT_COLOR, TEXT_MUTED,
    PLAIN, MUD, WATER,
)
from statistics_engine import (
    run_analytics_batch,
    generate_table_stats,
    calculate_scatter_data,
    calculate_all_terrain_profiles,
)

# ------------------------------------------------------------------ #
# Fonts
# ------------------------------------------------------------------ #
_HERE      = os.path.dirname(os.path.abspath(__file__))
_FONTS_DIR = os.path.join(_HERE, "assets", "fonts")
_JB_BOLD   = os.path.join(_FONTS_DIR, "JetBrainsMono-Bold.ttf")
_JB_REG    = os.path.join(_FONTS_DIR, "JetBrainsMono-Regular.ttf")
_IBM_REG   = os.path.join(_FONTS_DIR, "IBMPlexSans-Regular.ttf")
_IBM_SEMI  = os.path.join(_FONTS_DIR, "IBMPlexSans-SemiBold.ttf")


def _load_font(path, size, fallback="Segoe UI", bold=False):
    if os.path.exists(path):
        return pygame.font.Font(path, size)
    return pygame.font.SysFont(fallback, size, bold=bold)


# ------------------------------------------------------------------ #
# Layout constants
# ------------------------------------------------------------------ #
PAD        = 24          # outer padding
DIVIDER    = 630         # x position of the vertical divider
COL_R      = DIVIDER + PAD   # right panel content start x

# Accent colors
ACCENT     = "#6366F1"
ACCENT2    = "#22C55E"
WARN       = "#F59E0B"
MUTED_LINE = "#32323E"

# Terrain display colors (for profile bars)
TERRAIN_COLORS = {
    PLAIN: "#F5F0E8",
    MUD:   "#8B5E3C",
    WATER: "#4A90D9",
}

# Table column definitions: (header, key, width)
TABLE_COLS = [
    ("Algorithm",  "name",             130),
    ("Nodes",      "nodes_explored",    58),
    ("Cost",       "path_cost",         52),
    ("Terrain+",   "terrain_penalty",   62),
    ("Coins",      "coins_collected",   46),
    ("Missed",     "coins_missed",      50),
    ("Score",      "score",             56),
    ("Effic.",     "efficiency_ratio",  50),
    ("Verdict",    "verdicts",         110),
]


class AnalyticsScreen:
    def __init__(self, screen, grid, fresh_maze=False):
        """
        Parameters
        ----------
        screen      : pygame.Surface
        grid        : Grid object to analyse
        fresh_maze  : True if we generated this grid here (user skipped Play)
        """
        self.screen      = screen
        self.grid        = grid
        self.fresh_maze  = fresh_maze

        pygame.font.init()
        self.f_title   = _load_font(_JB_BOLD,  18, bold=True)
        self.f_sec     = _load_font(_JB_REG,   11)
        self.f_label   = _load_font(_IBM_REG,  11)
        self.f_value   = _load_font(_IBM_SEMI, 11, bold=True)
        self.f_btn     = _load_font(_IBM_SEMI, 13, bold=True)
        self.f_badge   = _load_font(_IBM_REG,  10)
        self.f_notice  = _load_font(_JB_REG,   10)

        # ---- Run analytics (may take ~1 second) --------------------- #
        self._loading    = True
        self._rows       = []
        self._desc       = {}
        self._scatter_pts= []
        self._pearson_r  = 0.0
        self._r_label    = ""
        self._profiles   = {}
        self._total_coins= len(grid.coins)

        # Back button
        btn_w, btn_h = 140, 34
        self._btn_menu = pygame.Rect(
            SCREEN_WIDTH - PAD - btn_w,
            PAD,
            btn_w, btn_h
        )
        self._btn_hovered = False

        # Run immediately (blocking — fast enough for this data size)
        self._run_analytics()

    # ================================================================ #
    # PUBLIC
    # ================================================================ #

    def handle_events(self, events):
        """Returns 'MENU' to navigate back, else None."""
        mouse = pygame.mouse.get_pos()
        self._btn_hovered = self._btn_menu.collidepoint(mouse)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._btn_menu.collidepoint(event.pos):
                    return "MENU"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "MENU"
        return None

    def draw(self):
        self.screen.fill(pygame.Color(BG_COLOR))
        self._draw_header()
        self._draw_divider()
        self._draw_left_panel()
        self._draw_right_panel()
        self._draw_back_button()
        pygame.display.flip()

    # ================================================================ #
    # DATA
    # ================================================================ #

    def _run_analytics(self):
        start_pos = (1, 1)
        end_pos   = (self.grid.rows - 2, self.grid.cols - 2)

        raw = run_analytics_batch(self.grid, start_pos, end_pos)
        self._rows, self._desc = generate_table_stats(raw, self._total_coins)
        self._scatter_pts, self._pearson_r, self._r_label = calculate_scatter_data(raw)
        self._profiles = calculate_all_terrain_profiles(raw, self.grid)
        self._loading  = False

    # ================================================================ #
    # HEADER
    # ================================================================ #

    def _draw_header(self):
        # Title
        title = self.f_title.render("ANALYTICS DASHBOARD", True, pygame.Color(ACCENT))
        self.screen.blit(title, (PAD, PAD + 6))

        # Fresh maze notice
        if self.fresh_maze:
            notice = self.f_notice.render(
                "⚠  No solver session detected — a new maze was generated for this analysis.",
                True, pygame.Color(WARN)
            )
            self.screen.blit(notice, (PAD, PAD + 34))

        # Separator line under header
        y = 64
        pygame.draw.line(
            self.screen, pygame.Color(MUTED_LINE),
            (PAD, y), (SCREEN_WIDTH - PAD, y), 1
        )

    # ================================================================ #
    # DIVIDER
    # ================================================================ #

    def _draw_divider(self):
        pygame.draw.line(
            self.screen, pygame.Color(MUTED_LINE),
            (DIVIDER, 72), (DIVIDER, SCREEN_HEIGHT - PAD), 1
        )

    # ================================================================ #
    # LEFT PANEL — Summary table
    # ================================================================ #

    def _draw_left_panel(self):
        y = 78
        sec = self.f_sec.render("ALGORITHM COMPARISON TABLE", True, pygame.Color(TEXT_MUTED))
        self.screen.blit(sec, (PAD, y))
        y += 18

        self._draw_table(PAD, y)

    def _draw_table(self, x, y):
        row_h    = 28
        header_h = 24

        # --- header row -------------------------------------------- #
        cx = x
        for header, _, col_w in TABLE_COLS:
            surf = self.f_sec.render(header.upper(), True, pygame.Color(TEXT_MUTED))
            self.screen.blit(surf, (cx, y))
            cx += col_w
        y += header_h

        # Thin line under header
        pygame.draw.line(
            self.screen, pygame.Color(MUTED_LINE),
            (x, y), (x + sum(w for _, _, w in TABLE_COLS), y), 1
        )
        y += 4

        # --- data rows --------------------------------------------- #
        for row in self._rows:
            is_best = "Best Score" in row["verdicts"]
            row_color = pygame.Color("#1E2A1E") if is_best else None

            if row_color:
                total_w = sum(w for _, _, w in TABLE_COLS)
                pygame.draw.rect(self.screen, row_color,
                                 (x - 2, y - 2, total_w + 4, row_h - 2),
                                 border_radius=3)

            cx = x
            for _, key, col_w in TABLE_COLS:
                if key == "verdicts":
                    # Badge pills
                    bx = cx
                    for badge in row["verdicts"]:
                        badge_color = self._badge_color(badge)
                        b_surf = self.f_badge.render(badge, True, pygame.Color("#FFFFFF"))
                        b_rect = pygame.Rect(bx, y + 2, b_surf.get_width() + 8, 16)
                        pygame.draw.rect(self.screen, pygame.Color(badge_color),
                                         b_rect, border_radius=3)
                        self.screen.blit(b_surf, (bx + 4, y + 4))
                        bx += b_rect.width + 4
                elif key == "name":
                    color = pygame.Color(ACCENT) if is_best else pygame.Color(TEXT_COLOR)
                    surf  = self.f_value.render(str(row[key]), True, color)
                    self.screen.blit(surf, (cx, y + 6))
                elif key == "efficiency_ratio":
                    val  = f"{row[key]:.3f}"
                    surf = self.f_label.render(val, True, pygame.Color(TEXT_COLOR))
                    self.screen.blit(surf, (cx, y + 6))
                elif key == "path_cost":
                    val  = f"{row[key]:.0f}"
                    surf = self.f_label.render(val, True, pygame.Color(TEXT_COLOR))
                    self.screen.blit(surf, (cx, y + 6))
                else:
                    if not row["path_found"] and key != "name":
                        val  = "—"
                        surf = self.f_label.render(val, True, pygame.Color(TEXT_MUTED))
                    else:
                        surf = self.f_label.render(str(row[key]), True, pygame.Color(TEXT_COLOR))
                    self.screen.blit(surf, (cx, y + 6))
                cx += col_w

            y += row_h

        # Bottom border
        pygame.draw.line(
            self.screen, pygame.Color(MUTED_LINE),
            (x, y), (x + sum(w for _, _, w in TABLE_COLS), y), 1
        )
        y += 16

        # --- Descriptive stats block below table ------------------- #
        self._draw_desc_stats_inline(x, y)

    def _draw_desc_stats_inline(self, x, y):
        """4-column mini stats block: mean / median / std dev / skewness."""
        sec = self.f_sec.render("DESCRIPTIVE STATISTICS  (across 7 algorithm variants)", True, pygame.Color(TEXT_MUTED))
        self.screen.blit(sec, (x, y))
        y += 16

        col_w = 140
        headers = ["Metric", "Mean", "Std Dev", "Skewness"]
        for i, h in enumerate(headers):
            surf = self.f_sec.render(h, True, pygame.Color(TEXT_MUTED))
            self.screen.blit(surf, (x + i * col_w, y))
        y += 14

        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (x, y), (x + col_w * 4, y), 1)
        y += 6

        for metric, stats in self._desc.items():
            skew     = stats["skewness"]
            skew_str = f"{skew:+.3f}"
            skew_col = "#F87171" if skew > 0.5 else "#86EFAC" if skew < -0.5 else TEXT_COLOR

            vals = [
                (metric,            TEXT_MUTED),
                (str(stats["mean"]), TEXT_COLOR),
                (str(stats["std_dev"]), TEXT_COLOR),
                (skew_str,           skew_col),
            ]
            for i, (val, col) in enumerate(vals):
                surf = self.f_label.render(val, True, pygame.Color(col))
                self.screen.blit(surf, (x + i * col_w, y))
            y += 18

    def _badge_color(self, badge):
        return {
            "Best Score":    "#16A34A",
            "Most Coins":    "#B45309",
            "Cheapest Path": "#2563EB",
            "Fastest":       "#7C3AED",
            "Most Efficient":"#0E7490",
        }.get(badge, "#334155")

    # ================================================================ #
    # RIGHT PANEL — Scatter + Terrain Profiles
    # ================================================================ #

    def _draw_right_panel(self):
        y = 78

        # Section 1: Scatter plot
        sec = self.f_sec.render("NODES EXPLORED  vs  SCORE  (Pearson r)", True, pygame.Color(TEXT_MUTED))
        self.screen.blit(sec, (COL_R, y))
        y += 16

        r_str  = f"r = {self._pearson_r}  →  {self._r_label}"
        r_surf = self.f_label.render(r_str, True, pygame.Color(WARN))
        self.screen.blit(r_surf, (COL_R, y))
        y += 18

        scatter_h = 200
        self._draw_scatter(COL_R, y, SCREEN_WIDTH - PAD - COL_R, scatter_h)
        y += scatter_h + 28

        # Divider between sections
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (COL_R, y - 12), (SCREEN_WIDTH - PAD, y - 12), 1)

        # Section 2: Terrain profiles
        sec2 = self.f_sec.render("TERRAIN PROFILE  (% of path through each terrain)", True, pygame.Color(TEXT_MUTED))
        self.screen.blit(sec2, (COL_R, y))
        y += 18

        self._draw_terrain_profiles(COL_R, y, SCREEN_WIDTH - PAD - COL_R,
                                    SCREEN_HEIGHT - PAD - y)

    # ------------------------------------------------------------------ #
    # Scatter plot
    # ------------------------------------------------------------------ #

    def _draw_scatter(self, x, y, w, h):
        """Scatter plot: X = nodes explored, Y = score. One dot per algorithm."""
        if not self._scatter_pts:
            return

        # Chart area (inset for axis labels)
        margin_l, margin_b = 52, 32
        cx = x + margin_l
        cy = y
        cw = w - margin_l - 8
        ch = h - margin_b

        # Background rect
        pygame.draw.rect(self.screen, pygame.Color("#1C1C2E"),
                         (cx, cy, cw, ch), border_radius=4)

        # Data ranges
        xs      = [p["x"] for p in self._scatter_pts]
        ys      = [p["y"] for p in self._scatter_pts]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        x_range = max(x_max - x_min, 1)
        y_range = max(y_max - y_min, 1)

        def to_px(px, py):
            sx = cx + int((px - x_min) / x_range * (cw - 20)) + 10
            sy = cy + ch - int((py - y_min) / y_range * (ch - 20)) - 10
            return sx, sy

        # Grid lines (3 horizontal, 3 vertical — subtle)
        for i in range(1, 4):
            gx = cx + cw * i // 4
            gy = cy + ch * i // 4
            pygame.draw.line(self.screen, pygame.Color("#2A2A3E"),
                             (cx, gy), (cx + cw, gy), 1)
            pygame.draw.line(self.screen, pygame.Color("#2A2A3E"),
                             (gx, cy), (gx, cy + ch), 1)

        # Axis labels
        x_lbl = self.f_notice.render(str(x_min), True, pygame.Color(TEXT_MUTED))
        self.screen.blit(x_lbl, (cx, cy + ch + 4))
        x_lbl2 = self.f_notice.render(str(x_max), True, pygame.Color(TEXT_MUTED))
        self.screen.blit(x_lbl2, (cx + cw - x_lbl2.get_width(), cy + ch + 4))

        y_lbl = self.f_notice.render(str(y_max), True, pygame.Color(TEXT_MUTED))
        self.screen.blit(y_lbl, (x, cy))
        y_lbl2 = self.f_notice.render(str(y_min), True, pygame.Color(TEXT_MUTED))
        self.screen.blit(y_lbl2, (x, cy + ch - 12))

        # Dots + labels
        dot_colors = [
            "#EF4444", "#F97316", "#EAB308",
            "#22C55E", "#6366F1", "#8B5CF6", "#EC4899"
        ]
        for i, pt in enumerate(self._scatter_pts):
            sx, sy   = to_px(pt["x"], pt["y"])
            dot_col  = dot_colors[i % len(dot_colors)]
            pygame.draw.circle(self.screen, pygame.Color(dot_col), (sx, sy), 6)
            pygame.draw.circle(self.screen, pygame.Color("#FFFFFF"), (sx, sy), 6, 1)

            # Algorithm name label — offset to avoid overlap
            lbl  = self.f_notice.render(pt["name"], True, pygame.Color(dot_col))
            lx   = sx + 8
            ly   = sy - 6
            # Keep label inside chart bounds
            if lx + lbl.get_width() > cx + cw:
                lx = sx - lbl.get_width() - 8
            self.screen.blit(lbl, (lx, ly))

        # Axis lines
        pygame.draw.line(self.screen, pygame.Color(TEXT_MUTED),
                         (cx, cy + ch), (cx + cw, cy + ch), 1)   # X axis
        pygame.draw.line(self.screen, pygame.Color(TEXT_MUTED),
                         (cx, cy), (cx, cy + ch), 1)              # Y axis

        # Axis titles
        x_title = self.f_notice.render("Nodes Explored →", True, pygame.Color(TEXT_MUTED))
        self.screen.blit(x_title, (cx + cw // 2 - x_title.get_width() // 2, cy + ch + 18))

    # ------------------------------------------------------------------ #
    # Terrain profiles
    # ------------------------------------------------------------------ #

    def _draw_terrain_profiles(self, x, y, w, h):
        """Grouped horizontal bar chart: one row per algorithm, 3 bars per row."""
        if not self._profiles:
            return

        algo_names = list(self._profiles.keys())
        n          = len(algo_names)
        row_h      = max(16, min(24, (h - 30) // n))
        bar_max_w  = w - 120    # space for algorithm name label

        terrain_order = [PLAIN, MUD, WATER]
        t_labels      = {PLAIN: "Plain", MUD: "Mud", WATER: "Water"}

        # Legend
        lx = x
        for t in terrain_order:
            col  = TERRAIN_COLORS[t]
            pygame.draw.rect(self.screen, pygame.Color(col), (lx, y, 10, 10))
            lbl  = self.f_notice.render(t_labels[t], True, pygame.Color(TEXT_MUTED))
            self.screen.blit(lbl, (lx + 13, y))
            lx  += lbl.get_width() + 28
        y += 18

        for algo in algo_names:
            profile = self._profiles[algo]

            # Algorithm name
            name_surf = self.f_notice.render(algo, True, pygame.Color(TEXT_MUTED))
            self.screen.blit(name_surf, (x, y + 2))

            # Stacked bar — Plain | Mud | Water
            bar_x   = x + 100
            bar_y   = y + 2
            bar_h   = row_h - 6
            total_w = 0

            for t in terrain_order:
                pct   = profile.get(t, 0.0)
                seg_w = int(pct / 100 * bar_max_w)
                if seg_w > 0:
                    pygame.draw.rect(
                        self.screen,
                        pygame.Color(TERRAIN_COLORS[t]),
                        (bar_x + total_w, bar_y, seg_w, bar_h),
                        border_radius=2
                    )
                    # Show % if wide enough
                    if seg_w > 28:
                        pct_surf = self.f_notice.render(
                            f"{pct:.0f}%", True, pygame.Color("#00000088")
                        )
                        self.screen.blit(
                            pct_surf,
                            (bar_x + total_w + seg_w // 2 - pct_surf.get_width() // 2,
                             bar_y + bar_h // 2 - pct_surf.get_height() // 2)
                        )
                    total_w += seg_w

            y += row_h

    # ================================================================ #
    # BACK BUTTON
    # ================================================================ #

    def _draw_back_button(self):
        color = "#7C7FF5" if self._btn_hovered else "#6366F1"
        pygame.draw.rect(self.screen, pygame.Color(color),
                         self._btn_menu, border_radius=6)
        txt = self.f_btn.render("← Main Menu", True, pygame.Color("#FFFFFF"))
        self.screen.blit(txt, (
            self._btn_menu.x + (self._btn_menu.width  - txt.get_width())  // 2,
            self._btn_menu.y + (self._btn_menu.height - txt.get_height()) // 2,
        ))