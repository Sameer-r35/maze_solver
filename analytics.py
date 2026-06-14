"""
analytics.py
============
AnalyticsScreen — tab-based analytics dashboard.

Layout (1280×720):
    HEADER  (y 0–68)    — title, fresh-maze notice, Main Menu button
    TAB BAR (y 68–108)  — 4 tabs
    CONTENT (y 108–648) — full-width content area, changes per tab
    INSIGHT (y 648–720) — fixed insight bar with 2-line explanation

Tabs:
    1. Summary Table    — 7-row algorithm comparison + verdict badges
    2. Descriptive Stats — mean/median/std dev/IQR/skewness per metric
    3. Scatter Plot      — Nodes Explored vs Score, Pearson r
    4. Terrain Profiles  — stacked bars showing path terrain breakdown

Navigation:
    handle_events() returns "MENU" or None each frame.
    ESC key also returns "MENU".
"""

import os
import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BG_COLOR, SIDEBAR_BORDER,
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
PAD          = 28          # outer horizontal padding
HEADER_H     = 68          # height of the header bar
TAB_BAR_H    = 40          # height of the tab bar
INSIGHT_H    = 72          # height of the insight bar at the bottom
CONTENT_Y    = HEADER_H + TAB_BAR_H          # 108
CONTENT_H    = SCREEN_HEIGHT - CONTENT_Y - INSIGHT_H  # ~540
INSIGHT_Y    = SCREEN_HEIGHT - INSIGHT_H

# Colors
ACCENT       = "#6366F1"
ACCENT_HOVER = "#7C7FF5"
WARN         = "#F59E0B"
MUTED_LINE   = "#32323E"
CONTENT_BG   = "#1A1A2A"
INSIGHT_BG   = "#1E1E30"

# Terrain colors for profile bars
TERRAIN_COLORS = {
    PLAIN: "#F5F0E8",
    MUD:   "#8B5E3C",
    WATER: "#4A90D9",
}

# Table columns: (header, data_key, col_width)
TABLE_COLS = [
    ("Algorithm",  "name",             148),
    ("Nodes",      "nodes_explored",    72),
    ("Cost",       "path_cost",         64),
    ("Terrain+",   "terrain_penalty",   74),
    ("Coins",      "coins_collected",   58),
    ("Missed",     "coins_missed",      64),
    ("Score",      "score",             68),
    ("Effic.",     "efficiency_ratio",  64),
    ("Verdict",    "verdicts",         200),
]

# Tab definitions: (key, label)
TABS = [
    ("table",   "Summary Table"),
    ("desc",    "Descriptive Stats"),
    ("scatter", "Scatter Plot"),
    ("terrain", "Terrain Profiles"),
]

# Insight text per tab — edit these freely later
INSIGHTS = {
    "table": (
        "What this shows: Every algorithm variant side-by-side with derived metrics.",
        "Key finding: Compare 'Terrain+' to see which algorithms paid extra for costly terrain — BFS always shows 0 because it ignores costs entirely, which looks efficient but is incorrect.",
    ),
    "desc": (
        "What this shows: Descriptive statistics (mean, median, std dev, IQR, skewness) computed across all 7 algorithm variants.",
        "Key finding: High skewness in 'Nodes Explored' means one algorithm is an outlier — DFS often drags the mean far from the median on open mazes.",
    ),
    "scatter": (
        "What this shows: Does exploring more nodes actually lead to a better score? Each dot is one algorithm variant.",
        "Key finding: A weak or negative Pearson r here means raw exploration effort doesn't buy a better result — search strategy matters more than how hard you search.",
    ),
    "terrain": (
        "What this shows: What percentage of each algorithm's final path walked through Plain, Mud, and Water terrain.",
        "Key finding: UCS and A*(0%) skew heavily toward Plain (cheap terrain). A*(100%) deliberately steps into Mud/Water to collect coins — its terrain bar is the most colorful.",
    ),
}

# Dot colors for scatter plot (one per algorithm variant)
DOT_COLORS = ["#EF4444", "#F97316", "#EAB308", "#22C55E", "#6366F1", "#8B5CF6", "#EC4899"]

# Badge colors
BADGE_COLORS = {
    "Best Score":     "#16A34A",
    "Most Coins":     "#B45309",
    "Cheapest Path":  "#2563EB",
    "Fastest":        "#7C3AED",
    "Most Efficient": "#0E7490",
}


class AnalyticsScreen:
    def __init__(self, screen, grid, fresh_maze=False):
        """
        Parameters
        ----------
        screen      : pygame.Surface
        grid        : Grid object to analyse
        fresh_maze  : True if grid was generated here (user skipped Play)
        """
        self.screen     = screen
        self.grid       = grid
        self.fresh_maze = fresh_maze

        pygame.font.init()
        self.f_title   = _load_font(_JB_BOLD,  17, bold=True)
        self.f_tab     = _load_font(_IBM_SEMI, 13, bold=True)
        self.f_sec     = _load_font(_JB_REG,   11)
        self.f_label   = _load_font(_IBM_REG,  12)
        self.f_value   = _load_font(_IBM_SEMI, 12, bold=True)
        self.f_btn     = _load_font(_IBM_SEMI, 13, bold=True)
        self.f_badge   = _load_font(_IBM_REG,  10)
        self.f_small   = _load_font(_JB_REG,   10)
        self.f_insight = _load_font(_IBM_REG,  12)
        self.f_insight_bold = _load_font(_IBM_SEMI, 12, bold=True)

        # ---- Data --------------------------------------------------- #
        self._rows        = []
        self._desc        = {}
        self._scatter_pts = []
        self._pearson_r   = 0.0
        self._r_label     = ""
        self._profiles    = {}
        self._total_coins = len(grid.coins)
        self._run_analytics()

        # ---- UI state ----------------------------------------------- #
        self.current_tab  = "table"
        self._tab_hovered = None
        self._btn_hovered = False

        # Build rects
        self._build_rects()

    # ================================================================ #
    # PUBLIC API
    # ================================================================ #

    def handle_events(self, events):
        """Returns 'MENU' to navigate back, else None."""
        mouse = pygame.mouse.get_pos()

        # Hover tracking
        self._btn_hovered = self._btn_menu.collidepoint(mouse)
        self._tab_hovered = None
        for key, rect in self._tab_rects.items():
            if rect.collidepoint(mouse):
                self._tab_hovered = key

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Main menu button
                if self._btn_menu.collidepoint(event.pos):
                    return "MENU"
                # Tab clicks
                for key, rect in self._tab_rects.items():
                    if rect.collidepoint(event.pos):
                        self.current_tab = key

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                # Number keys 1-4 switch tabs
                for i, (key, _) in enumerate(TABS):
                    if event.key == getattr(pygame, f"K_{i+1}", None):
                        self.current_tab = key

        return None

    def draw(self):
        self.screen.fill(pygame.Color(BG_COLOR))
        self._draw_header()
        self._draw_tab_bar()
        self._draw_content()
        self._draw_insight_bar()
        self._draw_back_button()
        pygame.display.flip()

    # ================================================================ #
    # SETUP
    # ================================================================ #

    def _build_rects(self):
        """Pre-compute all rects once at init."""
        # Tab bar rects — evenly split across full width minus button space
        tab_area_w = SCREEN_WIDTH - PAD * 2 - 160  # leave room for button
        tab_w      = tab_area_w // len(TABS)
        self._tab_rects = {}
        for i, (key, _) in enumerate(TABS):
            self._tab_rects[key] = pygame.Rect(
                PAD + i * tab_w, HEADER_H,
                tab_w, TAB_BAR_H
            )

        # Main menu button — top right
        self._btn_menu = pygame.Rect(
            SCREEN_WIDTH - PAD - 150, (HEADER_H - 34) // 2,
            150, 34
        )

    def _run_analytics(self):
        """Run all 7 algorithm variants silently and compute all stats."""
        start = (1, 1)
        end   = (self.grid.rows - 2, self.grid.cols - 2)
        raw   = run_analytics_batch(self.grid, start, end)
        self._rows, self._desc        = generate_table_stats(raw, self._total_coins)
        self._scatter_pts, self._pearson_r, self._r_label = calculate_scatter_data(raw)
        self._profiles                = calculate_all_terrain_profiles(raw, self.grid)

    # ================================================================ #
    # HEADER
    # ================================================================ #

    def _draw_header(self):
        # Title
        title = self.f_title.render("ANALYTICS DASHBOARD", True, pygame.Color(ACCENT))
        self.screen.blit(title, (PAD, (HEADER_H - title.get_height()) // 2))

        # Fresh maze warning
        if self.fresh_maze:
            warn = self.f_small.render(
                "⚠  No solver session found — a new maze was generated for this analysis.",
                True, pygame.Color(WARN)
            )
            self.screen.blit(warn, (PAD, (HEADER_H - title.get_height()) // 2 + 26))

        # Bottom border
        pygame.draw.line(
            self.screen, pygame.Color(MUTED_LINE),
            (0, HEADER_H - 1), (SCREEN_WIDTH, HEADER_H - 1), 1
        )

    # ================================================================ #
    # TAB BAR
    # ================================================================ #

    def _draw_tab_bar(self):
        # Background strip
        pygame.draw.rect(
            self.screen, pygame.Color("#16161F"),
            (0, HEADER_H, SCREEN_WIDTH, TAB_BAR_H)
        )

        for key, label in TABS:
            rect       = self._tab_rects[key]
            is_active  = (key == self.current_tab)
            is_hovered = (key == self._tab_hovered)

            # Active tab — slightly lighter background
            if is_active:
                pygame.draw.rect(self.screen, pygame.Color("#2A2A3E"), rect)

            # Tab label
            col  = ACCENT if is_active else (TEXT_COLOR if is_hovered else TEXT_MUTED)
            surf = self.f_tab.render(label, True, pygame.Color(col))
            tx   = rect.x + (rect.width  - surf.get_width())  // 2
            ty   = rect.y + (rect.height - surf.get_height()) // 2
            self.screen.blit(surf, (tx, ty))

            # Active underline
            if is_active:
                pygame.draw.rect(
                    self.screen, pygame.Color(ACCENT),
                    (rect.x, rect.bottom - 3, rect.width, 3)
                )

        # Full bottom border of tab bar
        pygame.draw.line(
            self.screen, pygame.Color(MUTED_LINE),
            (0, HEADER_H + TAB_BAR_H - 1),
            (SCREEN_WIDTH, HEADER_H + TAB_BAR_H - 1), 1
        )

    # ================================================================ #
    # CONTENT AREA — router
    # ================================================================ #

    def _draw_content(self):
        """Route to the correct tab drawing method."""
        # Content area background
        pygame.draw.rect(
            self.screen, pygame.Color(CONTENT_BG),
            (0, CONTENT_Y, SCREEN_WIDTH, CONTENT_H)
        )

        if   self.current_tab == "table":   self._draw_tab_table()
        elif self.current_tab == "desc":    self._draw_tab_desc()
        elif self.current_tab == "scatter": self._draw_tab_scatter()
        elif self.current_tab == "terrain": self._draw_tab_terrain()

    # ================================================================ #
    # TAB 1 — Summary Table
    # ================================================================ #

    def _draw_tab_table(self):
        x = PAD
        y = CONTENT_Y + 18

        # Section header
        sec = self.f_sec.render(
            "ALGORITHM COMPARISON  —  7 variants, all run on the same maze",
            True, pygame.Color(TEXT_MUTED)
        )
        self.screen.blit(sec, (x, y))
        y += 20

        row_h    = 36
        header_h = 26
        total_w  = sum(w for _, _, w in TABLE_COLS)

        # ---- Header row -------------------------------------------- #
        cx = x
        for header, _, col_w in TABLE_COLS:
            surf = self.f_sec.render(header, True, pygame.Color(TEXT_MUTED))
            self.screen.blit(surf, (cx + 4, y + 4))
            cx += col_w

        y += header_h
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (x, y), (x + total_w, y), 1)
        y += 2

        # ---- Data rows --------------------------------------------- #
        for row in self._rows:
            is_best = "Best Score" in row["verdicts"]

            # Highlight best-score row
            if is_best:
                pygame.draw.rect(
                    self.screen, pygame.Color("#1A2E1A"),
                    (x, y, total_w, row_h - 2), border_radius=3
                )

            cx = x
            for _, key, col_w in TABLE_COLS:
                cell_y = y + (row_h - self.f_label.get_height()) // 2

                if key == "name":
                    col  = pygame.Color(ACCENT) if is_best else pygame.Color(TEXT_COLOR)
                    surf = self.f_value.render(str(row[key]), True, col)
                    self.screen.blit(surf, (cx + 4, cell_y))

                elif key == "verdicts":
                    bx = cx + 4
                    for badge in row["verdicts"]:
                        bc     = BADGE_COLORS.get(badge, "#334155")
                        b_surf = self.f_badge.render(badge, True, pygame.Color("#FFFFFF"))
                        b_rect = pygame.Rect(bx, y + 8, b_surf.get_width() + 8, 18)
                        pygame.draw.rect(self.screen, pygame.Color(bc), b_rect, border_radius=3)
                        self.screen.blit(b_surf, (bx + 4, y + 10))
                        bx += b_rect.width + 4

                elif key == "efficiency_ratio":
                    val  = f"{row[key]:.3f}" if row["path_found"] else "—"
                    surf = self.f_label.render(val, True, pygame.Color(TEXT_COLOR))
                    self.screen.blit(surf, (cx + 4, cell_y))

                elif key == "path_cost":
                    val  = f"{row[key]:.0f}" if row["path_found"] else "—"
                    surf = self.f_label.render(val, True, pygame.Color(TEXT_COLOR))
                    self.screen.blit(surf, (cx + 4, cell_y))

                else:
                    val  = str(row[key]) if row["path_found"] else "—"
                    surf = self.f_label.render(val, True, pygame.Color(TEXT_COLOR))
                    self.screen.blit(surf, (cx + 4, cell_y))

                cx += col_w

            y += row_h

        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (x, y), (x + total_w, y), 1)

    # ================================================================ #
    # TAB 2 — Descriptive Stats
    # ================================================================ #

    def _draw_tab_desc(self):
        x = PAD
        y = CONTENT_Y + 18

        sec = self.f_sec.render(
            "DESCRIPTIVE STATISTICS  —  computed across all 7 algorithm variants",
            True, pygame.Color(TEXT_MUTED)
        )
        self.screen.blit(sec, (x, y))
        y += 22

        if not self._desc:
            self.screen.blit(
                self.f_label.render("No data available.", True, pygame.Color(TEXT_MUTED)),
                (x, y)
            )
            return

        # Column headers
        col_w    = 190
        headers  = ["Metric", "Mean", "Median", "Std Dev", "IQR", "Min", "Max", "Skewness"]
        cx = x
        for h in headers:
            surf = self.f_sec.render(h, True, pygame.Color(TEXT_MUTED))
            self.screen.blit(surf, (cx, y))
            cx += col_w
        y += 18
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (x, y), (x + col_w * len(headers), y), 1)
        y += 8

        for metric, stats in self._desc.items():
            skew     = stats["skewness"]
            skew_str = f"{skew:+.3f}"

            # Color-code skewness: red = strong positive, green = strong negative
            if   skew >  0.5: skew_col = "#F87171"
            elif skew < -0.5: skew_col = "#86EFAC"
            else:             skew_col = TEXT_COLOR

            row_vals = [
                (metric,                TEXT_MUTED,  True),
                (str(stats["mean"]),    TEXT_COLOR,  False),
                (str(stats["median"]),  TEXT_COLOR,  False),
                (str(stats["std_dev"]), TEXT_COLOR,  False),
                (str(stats["iqr"]),     TEXT_COLOR,  False),
                (str(stats["min"]),     TEXT_MUTED,  False),
                (str(stats["max"]),     TEXT_MUTED,  False),
                (skew_str,              skew_col,    True),
            ]

            # Row background
            pygame.draw.rect(
                self.screen, pygame.Color("#1E1E2E"),
                (x - 4, y - 2, col_w * len(headers) + 8, 28),
                border_radius=3
            )

            cx = x
            for val, col, bold in row_vals:
                f    = self.f_value if bold else self.f_label
                surf = f.render(val, True, pygame.Color(col))
                self.screen.blit(surf, (cx, y + 4))
                cx += col_w
            y += 34

        # Skewness legend
        y += 16
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (x, y), (x + 500, y), 1)
        y += 10
        legend_items = [
            ("#F87171", "Skewness > +0.5  →  right-skewed (high outlier pulling mean up)"),
            ("#86EFAC", "Skewness < −0.5  →  left-skewed  (low outlier pulling mean down)"),
            (TEXT_COLOR, "Skewness ≈ 0     →  roughly symmetric distribution"),
        ]
        for col, label in legend_items:
            surf = self.f_small.render(label, True, pygame.Color(col))
            self.screen.blit(surf, (x, y))
            y += 18

    # ================================================================ #
    # TAB 3 — Scatter Plot
    # ================================================================ #

    def _draw_tab_scatter(self):
        x = PAD
        y = CONTENT_Y + 18

        # Header + Pearson r value
        sec = self.f_sec.render(
            "NODES EXPLORED  vs  SCORE  —  does more exploration mean a better result?",
            True, pygame.Color(TEXT_MUTED)
        )
        self.screen.blit(sec, (x, y))
        y += 20

        r_str  = f"Pearson r = {self._pearson_r}    {self._r_label}"
        r_surf = self.f_value.render(r_str, True, pygame.Color(WARN))
        self.screen.blit(r_surf, (x, y))
        y += 24

        if not self._scatter_pts:
            self.screen.blit(
                self.f_label.render("No data.", True, pygame.Color(TEXT_MUTED)), (x, y)
            )
            return

        # Chart fills remaining content area
        chart_x = x + 60          # left margin for Y-axis labels
        chart_y = y
        chart_w = SCREEN_WIDTH - PAD * 2 - 60
        chart_h = CONTENT_Y + CONTENT_H - y - 48

        self._render_scatter(chart_x, chart_y, chart_w, chart_h)

    def _render_scatter(self, cx, cy, cw, ch):
        # Chart background
        pygame.draw.rect(self.screen, pygame.Color("#13131E"),
                         (cx, cy, cw, ch), border_radius=6)

        pts   = self._scatter_pts
        xs    = [p["x"] for p in pts]
        ys    = [p["y"] for p in pts]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        xr    = max(x_max - x_min, 1)
        yr    = max(y_max - y_min, 1)

        # Inner padding — extra bottom room for below-dot labels
        ipad_l = 48   # left  (Y-axis labels)
        ipad_r = 20   # right
        ipad_t = 20   # top
        ipad_b = 52   # bottom (X-axis labels + dot labels)

        plot_x = cx + ipad_l
        plot_y = cy + ipad_t
        plot_w = cw - ipad_l - ipad_r
        plot_h = ch - ipad_t - ipad_b

        def to_screen(px, py):
            sx = plot_x + int((px - x_min) / xr * plot_w)
            sy = plot_y + plot_h - int((py - y_min) / yr * plot_h)
            return sx, sy

        # ---- Grid lines -------------------------------------------- #
        for i in range(1, 5):
            gx = plot_x + plot_w * i // 4
            gy = plot_y + plot_h * i // 4
            pygame.draw.line(self.screen, pygame.Color("#222233"),
                             (plot_x, gy), (plot_x + plot_w, gy), 1)
            pygame.draw.line(self.screen, pygame.Color("#222233"),
                             (gx, plot_y), (gx, plot_y + plot_h), 1)

        # ---- Axis lines -------------------------------------------- #
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (plot_x, plot_y + plot_h),
                         (plot_x + plot_w, plot_y + plot_h), 1)
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (plot_x, plot_y),
                         (plot_x, plot_y + plot_h), 1)

        # ---- Y-axis tick labels (5 evenly spaced) ------------------ #
        for i in range(5):
            frac = i / 4
            val  = y_min + frac * yr
            sy   = plot_y + plot_h - int(frac * plot_h)
            lbl  = self.f_small.render(f"{val:.0f}", True, pygame.Color(TEXT_MUTED))
            self.screen.blit(lbl, (cx + ipad_l - lbl.get_width() - 6,
                                   sy - lbl.get_height() // 2))
            # Tick mark
            pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                             (plot_x - 3, sy), (plot_x, sy), 1)

        # ---- X-axis tick labels (5 evenly spaced) ------------------ #
        for i in range(5):
            frac = i / 4
            val  = x_min + frac * xr
            sx   = plot_x + int(frac * plot_w)
            lbl  = self.f_small.render(f"{val:.0f}", True, pygame.Color(TEXT_MUTED))
            self.screen.blit(lbl, (sx - lbl.get_width() // 2,
                                   plot_y + plot_h + 6))
            pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                             (sx, plot_y + plot_h),
                             (sx, plot_y + plot_h + 3), 1)

        # ---- Axis titles ------------------------------------------- #
        x_title = self.f_small.render("Nodes Explored  →", True, pygame.Color(TEXT_MUTED))
        self.screen.blit(x_title, (
            plot_x + plot_w // 2 - x_title.get_width() // 2,
            plot_y + plot_h + 22
        ))

        # Rotated Y-axis title — blit a rotated surface
        y_title_surf = self.f_small.render("← Score", True, pygame.Color(TEXT_MUTED))
        y_title_rot  = pygame.transform.rotate(y_title_surf, 90)
        self.screen.blit(y_title_rot, (
            cx,
            plot_y + plot_h // 2 - y_title_rot.get_height() // 2
        ))

        # ---- Regression line (OLS fit through scatter points) ------ #
        if len(pts) >= 2:
            n     = len(pts)
            mx    = sum(xs) / n
            my    = sum(ys) / n
            num   = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
            den   = sum((xs[i] - mx) ** 2 for i in range(n))
            if den != 0:
                slope     = num / den
                intercept = my - slope * mx
                # Clamp line to plot boundaries using x_min/x_max
                rx1, ry1 = to_screen(x_min, slope * x_min + intercept)
                rx2, ry2 = to_screen(x_max, slope * x_max + intercept)
                # Clip to plot rect before drawing
                ry1 = max(plot_y, min(plot_y + plot_h, ry1))
                ry2 = max(plot_y, min(plot_y + plot_h, ry2))
                pygame.draw.line(self.screen, pygame.Color("#475569"),
                                 (rx1, ry1), (rx2, ry2), 1)
                # Dashed feel — overdraw with bg every 8px
                for seg in range(0, abs(rx2 - rx1), 16):
                    frac  = seg / max(abs(rx2 - rx1), 1)
                    dash_x = rx1 + int((rx2 - rx1) * frac)
                    dash_y = ry1 + int((ry2 - ry1) * frac)
                    dash_ex = rx1 + int((rx2 - rx1) * min(frac + 8 / max(abs(rx2 - rx1), 1), 1))
                    dash_ey = ry1 + int((ry2 - ry1) * min(frac + 8 / max(abs(rx2 - rx1), 1), 1))
                    pygame.draw.line(self.screen, pygame.Color("#13131E"),
                                     (dash_x, dash_y), (dash_ex, dash_ey), 1)

        # ---- Compute screen positions for all dots first ----------- #
        screen_pts = []
        for i, pt in enumerate(pts):
            sx, sy = to_screen(pt["x"], pt["y"])
            screen_pts.append((sx, sy, pt["name"], DOT_COLORS[i % len(DOT_COLORS)]))

        # ---- Draw dots --------------------------------------------- #
        DOT_R = 7
        for sx, sy, name, col in screen_pts:
            pygame.draw.circle(self.screen, pygame.Color(col), (sx, sy), DOT_R + 2)
            pygame.draw.circle(self.screen, pygame.Color("#13131E"), (sx, sy), DOT_R - 1)
            pygame.draw.circle(self.screen, pygame.Color(col), (sx, sy), DOT_R - 3)

        # ---- Labels BELOW each dot, with vertical stacking --------- #
        # Sort by x so collision resolution goes left-to-right.
        # Two dots within 70px horizontally share the below-axis zone,
        # so the right-most one drops an extra line.
        LABEL_GAP   = 4    # px between dot bottom and label top
        LABEL_LINE_H = self.f_small.get_height() + 2
        COLLISION_X  = 70  # px threshold for "same column"

        # Build a list of (sx, sy, name, col, label_row) where label_row
        # is 0 for the first label at that x-zone, 1 for the next, etc.
        sorted_pts   = sorted(screen_pts, key=lambda p: p[0])
        label_slots  = []   # (sx, base_y, row, name, col)
        zone_right   = {}   # last sx in each horizontal zone → next row

        for sx, sy, name, col in sorted_pts:
            base_y = sy + DOT_R + 2 + LABEL_GAP
            # Find which zone this x falls in
            row = 0
            for prev_sx, prev_row in list(zone_right.items()):
                if abs(sx - prev_sx) < COLLISION_X:
                    row = max(row, prev_row + 1)
            zone_right[sx] = row
            label_slots.append((sx, base_y, row, name, col))

        for sx, base_y, row, name, col in label_slots:
            lbl  = self.f_small.render(name, True, pygame.Color(col))
            lx   = sx - lbl.get_width() // 2
            ly   = base_y + row * LABEL_LINE_H
            # Keep label inside chart horizontally
            lx   = max(cx + 2, min(lx, cx + cw - lbl.get_width() - 2))
            # Only draw if within the chart bottom boundary
            if ly + lbl.get_height() <= cy + ch + 2:
                self.screen.blit(lbl, (lx, ly))

    # ================================================================ #
    # TAB 4 — Terrain Profiles
    # ================================================================ #

    def _draw_tab_terrain(self):
        x = PAD
        y = CONTENT_Y + 18

        sec = self.f_sec.render(
            "TERRAIN PROFILES  —  what % of each algorithm's path walked through each terrain type",
            True, pygame.Color(TEXT_MUTED)
        )
        self.screen.blit(sec, (x, y))
        y += 20

        if not self._profiles:
            self.screen.blit(
                self.f_label.render("No data.", True, pygame.Color(TEXT_MUTED)), (x, y)
            )
            return

        # Legend
        terrain_order  = [PLAIN, MUD, WATER]
        terrain_labels = {PLAIN: "Plain (cost 1)", MUD: "Mud (cost 5)", WATER: "Water (cost 10)"}
        lx = x
        for t in terrain_order:
            pygame.draw.rect(self.screen, pygame.Color(TERRAIN_COLORS[t]),
                             (lx, y, 14, 14), border_radius=2)
            lbl = self.f_label.render(terrain_labels[t], True, pygame.Color(TEXT_MUTED))
            self.screen.blit(lbl, (lx + 18, y))
            lx += lbl.get_width() + 42
        y += 28

        # Bar chart — one row per algorithm
        algo_names = list(self._profiles.keys())
        n          = len(algo_names)
        available_h = CONTENT_Y + CONTENT_H - y - 12
        row_h      = max(28, min(52, available_h // n))
        bar_max_w  = SCREEN_WIDTH - PAD * 2 - 180
        label_w    = 120

        for algo in algo_names:
            profile = self._profiles[algo]

            # Row background
            pygame.draw.rect(
                self.screen, pygame.Color("#1E1E2E"),
                (x, y + 2, SCREEN_WIDTH - PAD * 2, row_h - 4),
                border_radius=3
            )

            # Algorithm name
            name_surf = self.f_value.render(algo, True, pygame.Color(TEXT_MUTED))
            self.screen.blit(name_surf, (x + 8, y + (row_h - name_surf.get_height()) // 2))

            # Stacked horizontal bar
            bar_x   = x + label_w
            bar_y   = y + 6
            bar_h   = row_h - 12
            total_w = 0

            for t in terrain_order:
                pct   = profile.get(t, 0.0)
                seg_w = int(pct / 100 * bar_max_w)
                if seg_w < 1:
                    continue
                pygame.draw.rect(
                    self.screen,
                    pygame.Color(TERRAIN_COLORS[t]),
                    (bar_x + total_w, bar_y, seg_w, bar_h),
                    border_radius=2
                )
                # Percentage label inside bar if wide enough
                if seg_w > 36:
                    pct_surf = self.f_small.render(
                        f"{pct:.1f}%", True, pygame.Color("#111111")
                    )
                    self.screen.blit(pct_surf, (
                        bar_x + total_w + seg_w // 2 - pct_surf.get_width() // 2,
                        bar_y + bar_h // 2 - pct_surf.get_height() // 2
                    ))
                total_w += seg_w

            y += row_h

    # ================================================================ #
    # INSIGHT BAR
    # ================================================================ #

    def _draw_insight_bar(self):
        # Background
        pygame.draw.rect(
            self.screen, pygame.Color(INSIGHT_BG),
            (0, INSIGHT_Y, SCREEN_WIDTH, INSIGHT_H)
        )
        pygame.draw.line(
            self.screen, pygame.Color(MUTED_LINE),
            (0, INSIGHT_Y), (SCREEN_WIDTH, INSIGHT_Y), 1
        )

        lines = INSIGHTS.get(self.current_tab, ("", ""))
        y     = INSIGHT_Y + 12

        # Line 1 — bold label "What this shows:"
        if lines[0]:
            surf = self.f_insight_bold.render(lines[0], True, pygame.Color(TEXT_COLOR))
            self.screen.blit(surf, (PAD, y))
            y += surf.get_height() + 6

        # Line 2 — normal text "Key finding:"
        if len(lines) > 1 and lines[1]:
            surf = self.f_insight.render(lines[1], True, pygame.Color(TEXT_MUTED))
            self.screen.blit(surf, (PAD, y))

    # ================================================================ #
    # MAIN MENU BUTTON
    # ================================================================ #

    def _draw_back_button(self):
        col = ACCENT_HOVER if self._btn_hovered else ACCENT
        pygame.draw.rect(self.screen, pygame.Color(col),
                         self._btn_menu, border_radius=6)
        txt = self.f_btn.render("← Main Menu", True, pygame.Color("#FFFFFF"))
        self.screen.blit(txt, (
            self._btn_menu.x + (self._btn_menu.width  - txt.get_width())  // 2,
            self._btn_menu.y + (self._btn_menu.height - txt.get_height()) // 2,
        ))