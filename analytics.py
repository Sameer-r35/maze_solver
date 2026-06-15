"""
analytics.py
============
AnalyticsScreen — tab-based analytics dashboard.

Layout (1280×720):
    HEADER  (y 0–68)    — title, fresh-maze notice, Main Menu button
    TAB BAR (y 68–108)  — 3 tabs
    CONTENT (y 108–648) — full-width content area, changes per tab
    INSIGHT (y 648–720) — fixed insight bar with 2-line explanation

Tabs:
    1. Summary Table   — 7-row algorithm comparison + verdict badges
    2. Scatter Plot    — Nodes Explored vs Score, Pearson r
    3. Radar Graph     — terrain frequency distribution per algorithm path

Navigation:
    handle_events() returns "MENU" or None each frame.
    ESC key also returns "MENU".
    Keys 1/2/3 switch tabs.
"""

import os
import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BG_COLOR, SIDEBAR_BORDER,
    TEXT_COLOR, TEXT_MUTED,
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
PAD       = 28
HEADER_H  = 68
TAB_BAR_H = 40
INSIGHT_H = 72
CONTENT_Y = HEADER_H + TAB_BAR_H        # 108
CONTENT_H = SCREEN_HEIGHT - CONTENT_Y - INSIGHT_H   # ~540
INSIGHT_Y = SCREEN_HEIGHT - INSIGHT_H

# Colors
ACCENT       = "#6366F1"
ACCENT_HOVER = "#7C7FF5"
WARN         = "#F59E0B"
MUTED_LINE   = "#32323E"
CONTENT_BG   = "#1A1A2A"
INSIGHT_BG   = "#1E1E30"

# Personality axis colors — one per axis
PERSONALITY_COLORS = {
    "avg_step_cost":   "#22C55E",   # green  — cheaper terrain = good
    "coin_ratio":      "#FCD34D",   # gold   — coins
    "path_efficiency": "#6366F1",   # indigo — efficiency
}

PERSONALITY_LABELS = {
    "avg_step_cost":   "Cheap Terrain",
    "coin_ratio":      "Coin Ratio",
    "path_efficiency": "Efficiency",
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

# 3 tabs — descriptive stats removed
TABS = [
    ("table",   "Summary Table"),
    ("scatter", "Scatter Plot"),
    ("terrain", "Radar Graph"),
]

# Insight bar text per tab — edit freely
INSIGHTS = {
    "table": (
        "What this shows: Every algorithm variant side-by-side with derived metrics.",
        "Key finding: Compare 'Terrain+' to see which algorithms paid extra for costly terrain — BFS always shows 0 because it ignores costs entirely, which looks efficient but is wrong.",
    ),
    "scatter": (
        "What this shows: Does exploring more nodes actually lead to a better score? Each dot is one algorithm variant. The dashed line is the OLS regression trend.",
        "Key finding: A weak or negative Pearson r means raw exploration effort doesn't buy a better result — search strategy matters more than how hard you search.",
    ),
    "terrain": (
        "What this shows: Radar graph per algorithm — three axes show Cheap Terrain (%), Coin Ratio (%), and Path Efficiency (%). Wider = better on that axis.",
        "Key finding: UCS and A*(0%) have wide Efficiency + Cheap Terrain axes. A*(100%) has the widest Coin Ratio — it sacrifices efficiency to collect coins. BFS has low efficiency despite a short path because it ignores terrain costs.",
    ),
}

# One color per algorithm variant for scatter dots
DOT_COLORS = ["#EF4444", "#F97316", "#EAB308", "#22C55E", "#6366F1", "#8B5CF6", "#EC4899"]

# Verdict badge colors
BADGE_COLORS = {
    "Best Score":     "#16A34A",
    "Most Coins":     "#B45309",
    "Cheapest Path":  "#2563EB",
    "Fastest":        "#7C3AED",
    "Most Efficient": "#0E7490",
}


class AnalyticsScreen:
    def __init__(self, screen, grid, fresh_maze=False):
        self.screen     = screen
        self.grid       = grid
        self.fresh_maze = fresh_maze

        pygame.font.init()
        self.f_title        = _load_font(_JB_BOLD,  22, bold=True)
        self.f_tab          = _load_font(_IBM_SEMI, 15, bold=True)
        self.f_sec          = _load_font(_JB_REG,   13)
        self.f_label        = _load_font(_IBM_REG,  14)
        self.f_value        = _load_font(_IBM_SEMI, 14, bold=True)
        self.f_btn          = _load_font(_IBM_SEMI, 14, bold=True)
        self.f_badge        = _load_font(_IBM_REG,  12)
        self.f_small        = _load_font(_JB_REG,   12)
        self.f_insight      = _load_font(_IBM_REG,  13)
        self.f_insight_bold = _load_font(_IBM_SEMI, 13, bold=True)

        # ---- Data --------------------------------------------------- #
        self._rows        = []
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
        self._build_rects()

    # ================================================================ #
    # PUBLIC
    # ================================================================ #

    def handle_events(self, events):
        """Returns 'MENU' to navigate back, else None."""
        mouse = pygame.mouse.get_pos()
        self._btn_hovered = self._btn_menu.collidepoint(mouse)
        self._tab_hovered = None
        for key, rect in self._tab_rects.items():
            if rect.collidepoint(mouse):
                self._tab_hovered = key

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._btn_menu.collidepoint(event.pos):
                    return "MENU"
                for key, rect in self._tab_rects.items():
                    if rect.collidepoint(event.pos):
                        self.current_tab = key

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                # Keys 1–3 switch tabs
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
        tab_area_w = SCREEN_WIDTH - PAD * 2 - 160
        tab_w      = tab_area_w // len(TABS)
        self._tab_rects = {}
        for i, (key, _) in enumerate(TABS):
            self._tab_rects[key] = pygame.Rect(
                PAD + i * tab_w, HEADER_H, tab_w, TAB_BAR_H
            )
        self._btn_menu = pygame.Rect(
            SCREEN_WIDTH - PAD - 150, (HEADER_H - 34) // 2, 150, 34
        )

    def _run_analytics(self):
        start = (1, 1)
        end   = (self.grid.rows - 2, self.grid.cols - 2)
        raw   = run_analytics_batch(self.grid, start, end)
        # generate_table_stats returns (rows, desc) — we only need rows now
        self._rows, _ = generate_table_stats(raw, self._total_coins)
        self._scatter_pts, self._pearson_r, self._r_label = calculate_scatter_data(raw)
        self._profiles = calculate_all_terrain_profiles(raw, self.grid)

    # ================================================================ #
    # HEADER
    # ================================================================ #

    def _draw_header(self):
        title = self.f_title.render("ANALYTICS DASHBOARD", True, pygame.Color(ACCENT))
        self.screen.blit(title, (PAD, (HEADER_H - title.get_height()) // 2))

        if self.fresh_maze:
            warn = self.f_small.render(
                "⚠  No solver session found — a new maze was generated for this analysis.",
                True, pygame.Color(WARN)
            )
            self.screen.blit(warn, (PAD, (HEADER_H - title.get_height()) // 2 + 28))

        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (0, HEADER_H - 1), (SCREEN_WIDTH, HEADER_H - 1), 1)

    # ================================================================ #
    # TAB BAR
    # ================================================================ #

    def _draw_tab_bar(self):
        pygame.draw.rect(self.screen, pygame.Color("#16161F"),
                         (0, HEADER_H, SCREEN_WIDTH, TAB_BAR_H))

        for key, label in TABS:
            rect       = self._tab_rects[key]
            is_active  = (key == self.current_tab)
            is_hovered = (key == self._tab_hovered)

            if is_active:
                pygame.draw.rect(self.screen, pygame.Color("#2A2A3E"), rect)

            col  = ACCENT if is_active else (TEXT_COLOR if is_hovered else TEXT_MUTED)
            surf = self.f_tab.render(label, True, pygame.Color(col))
            tx   = rect.x + (rect.width  - surf.get_width())  // 2
            ty   = rect.y + (rect.height - surf.get_height()) // 2
            self.screen.blit(surf, (tx, ty))

            if is_active:
                pygame.draw.rect(self.screen, pygame.Color(ACCENT),
                                 (rect.x, rect.bottom - 3, rect.width, 3))

        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (0, HEADER_H + TAB_BAR_H - 1),
                         (SCREEN_WIDTH, HEADER_H + TAB_BAR_H - 1), 1)

    # ================================================================ #
    # CONTENT ROUTER
    # ================================================================ #

    def _draw_content(self):
        pygame.draw.rect(self.screen, pygame.Color(CONTENT_BG),
                         (0, CONTENT_Y, SCREEN_WIDTH, CONTENT_H))

        if   self.current_tab == "table":   self._draw_tab_table()
        elif self.current_tab == "scatter": self._draw_tab_scatter()
        elif self.current_tab == "terrain": self._draw_tab_terrain()

    # ================================================================ #
    # TAB 1 — Summary Table
    # ================================================================ #

    def _draw_tab_table(self):
        x = PAD
        y = CONTENT_Y + 18

        sec = self.f_sec.render(
            "ALGORITHM COMPARISON  —  7 variants, all run on the same maze",
            True, pygame.Color(TEXT_MUTED)
        )
        self.screen.blit(sec, (x, y))
        y += 20

        row_h    = 36
        header_h = 26
        total_w  = sum(w for _, _, w in TABLE_COLS)

        # Header row
        cx = x
        for header, _, col_w in TABLE_COLS:
            surf = self.f_sec.render(header, True, pygame.Color(TEXT_MUTED))
            self.screen.blit(surf, (cx + 4, y + 4))
            cx += col_w
        y += header_h
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (x, y), (x + total_w, y), 1)
        y += 2

        # Data rows
        for row in self._rows:
            is_best = "Best Score" in row["verdicts"]

            if is_best:
                pygame.draw.rect(self.screen, pygame.Color("#1A2E1A"),
                                 (x, y, total_w, row_h - 2), border_radius=3)

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
    # TAB 2 — Scatter Plot (Nodes Explored vs Score)
    # ================================================================ #

    def _draw_tab_scatter(self):
        x = PAD
        y = CONTENT_Y + 18

        sec = self.f_sec.render(
            "NODES EXPLORED  vs  SCORE  —  does more exploration mean a better result?",
            True, pygame.Color(TEXT_MUTED)
        )
        self.screen.blit(sec, (x, y))
        y += 20

        r_str  = f"Pearson r = {self._pearson_r}    ({self._r_label})"
        r_surf = self.f_value.render(r_str, True, pygame.Color(WARN))
        self.screen.blit(r_surf, (x, y))
        y += 28

        if not self._scatter_pts:
            self.screen.blit(
                self.f_label.render("No data.", True, pygame.Color(TEXT_MUTED)), (x, y)
            )
            return

        chart_x = x + 60
        chart_y = y
        chart_w = SCREEN_WIDTH - PAD * 2 - 60
        chart_h = CONTENT_Y + CONTENT_H - y - 48
        self._render_scatter(chart_x, chart_y, chart_w, chart_h)

    def _render_scatter(self, cx, cy, cw, ch):
        pygame.draw.rect(self.screen, pygame.Color("#13131E"),
                         (cx, cy, cw, ch), border_radius=6)

        pts   = self._scatter_pts
        xs    = [p["x"] for p in pts]
        ys    = [p["y"] for p in pts]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        xr    = max(x_max - x_min, 1)
        yr    = max(y_max - y_min, 1)

        ipad_l, ipad_r, ipad_t, ipad_b = 48, 20, 20, 52
        plot_x = cx + ipad_l
        plot_y = cy + ipad_t
        plot_w = cw - ipad_l - ipad_r
        plot_h = ch - ipad_t - ipad_b

        def to_screen(px, py):
            sx = plot_x + int((px - x_min) / xr * plot_w)
            sy = plot_y + plot_h - int((py - y_min) / yr * plot_h)
            return sx, sy

        # Grid lines
        for i in range(1, 5):
            gx = plot_x + plot_w * i // 4
            gy = plot_y + plot_h * i // 4
            pygame.draw.line(self.screen, pygame.Color("#222233"),
                             (plot_x, gy), (plot_x + plot_w, gy), 1)
            pygame.draw.line(self.screen, pygame.Color("#222233"),
                             (gx, plot_y), (gx, plot_y + plot_h), 1)

        # Axis lines
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (plot_x, plot_y + plot_h), (plot_x + plot_w, plot_y + plot_h), 1)
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (plot_x, plot_y), (plot_x, plot_y + plot_h), 1)

        # Y-axis tick labels
        for i in range(5):
            frac = i / 4
            val  = y_min + frac * yr
            sy   = plot_y + plot_h - int(frac * plot_h)
            lbl  = self.f_small.render(f"{val:.0f}", True, pygame.Color(TEXT_MUTED))
            self.screen.blit(lbl, (cx + ipad_l - lbl.get_width() - 6,
                                   sy - lbl.get_height() // 2))
            pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                             (plot_x - 3, sy), (plot_x, sy), 1)

        # X-axis tick labels
        for i in range(5):
            frac = i / 4
            val  = x_min + frac * xr
            sx   = plot_x + int(frac * plot_w)
            lbl  = self.f_small.render(f"{val:.0f}", True, pygame.Color(TEXT_MUTED))
            self.screen.blit(lbl, (sx - lbl.get_width() // 2, plot_y + plot_h + 6))
            pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                             (sx, plot_y + plot_h), (sx, plot_y + plot_h + 3), 1)

        # Axis titles
        x_title = self.f_small.render("Nodes Explored  →", True, pygame.Color(TEXT_MUTED))
        self.screen.blit(x_title, (
            plot_x + plot_w // 2 - x_title.get_width() // 2,
            plot_y + plot_h + 22
        ))
        y_title_surf = self.f_small.render("← Score", True, pygame.Color(TEXT_MUTED))
        y_title_rot  = pygame.transform.rotate(y_title_surf, 90)
        self.screen.blit(y_title_rot, (
            cx, plot_y + plot_h // 2 - y_title_rot.get_height() // 2
        ))

        # OLS regression line (dashed feel)
        if len(pts) >= 2:
            n   = len(pts)
            mx  = sum(xs) / n
            my  = sum(ys) / n
            num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
            den = sum((xs[i] - mx) ** 2 for i in range(n))
            if den != 0:
                slope     = num / den
                intercept = my - slope * mx
                rx1, ry1  = to_screen(x_min, slope * x_min + intercept)
                rx2, ry2  = to_screen(x_max, slope * x_max + intercept)
                ry1 = max(plot_y, min(plot_y + plot_h, ry1))
                ry2 = max(plot_y, min(plot_y + plot_h, ry2))
                pygame.draw.line(self.screen, pygame.Color("#475569"),
                                 (rx1, ry1), (rx2, ry2), 1)
                # Dashed overdraw
                for seg in range(0, max(abs(rx2 - rx1), 1), 16):
                    frac    = seg / max(abs(rx2 - rx1), 1)
                    dash_x  = rx1 + int((rx2 - rx1) * frac)
                    dash_y  = ry1 + int((ry2 - ry1) * frac)
                    dash_ex = rx1 + int((rx2 - rx1) * min(frac + 8 / max(abs(rx2 - rx1), 1), 1))
                    dash_ey = ry1 + int((ry2 - ry1) * min(frac + 8 / max(abs(rx2 - rx1), 1), 1))
                    pygame.draw.line(self.screen, pygame.Color("#13131E"),
                                     (dash_x, dash_y), (dash_ex, dash_ey), 1)

        # Compute screen positions for all dots
        screen_pts = []
        for i, pt in enumerate(pts):
            sx, sy = to_screen(pt["x"], pt["y"])
            screen_pts.append((sx, sy, pt["name"], DOT_COLORS[i % len(DOT_COLORS)]))

        # Draw dots
        DOT_R = 7
        for sx, sy, name, col in screen_pts:
            pygame.draw.circle(self.screen, pygame.Color(col), (sx, sy), DOT_R + 2)
            pygame.draw.circle(self.screen, pygame.Color("#13131E"), (sx, sy), DOT_R - 1)
            pygame.draw.circle(self.screen, pygame.Color(col), (sx, sy), DOT_R - 3)

        # Labels BELOW each dot — stack vertically when dots overlap horizontally
        LABEL_GAP    = 4
        LABEL_LINE_H = self.f_small.get_height() + 2
        COLLISION_X  = 70

        sorted_pts  = sorted(screen_pts, key=lambda p: p[0])
        label_slots = []
        zone_right  = {}

        for sx, sy, name, col in sorted_pts:
            base_y = sy + DOT_R + 2 + LABEL_GAP
            row    = 0
            for prev_sx, prev_row in list(zone_right.items()):
                if abs(sx - prev_sx) < COLLISION_X:
                    row = max(row, prev_row + 1)
            zone_right[sx] = row
            label_slots.append((sx, base_y, row, name, col))

        for sx, base_y, row, name, col in label_slots:
            lbl = self.f_small.render(name, True, pygame.Color(col))
            lx  = sx - lbl.get_width() // 2
            ly  = base_y + row * LABEL_LINE_H
            lx  = max(cx + 2, min(lx, cx + cw - lbl.get_width() - 2))
            if ly + lbl.get_height() <= cy + ch + 2:
                self.screen.blit(lbl, (lx, ly))

    # ================================================================ #
    # TAB 3 — Radar Graph (Algorithm Personality)
    # ================================================================ #

    def _draw_tab_terrain(self):
        x = PAD
        y = CONTENT_Y + 18

        sec = self.f_sec.render(
            "ALGORITHM PERSONALITY  —  Cheap Terrain · Coin Ratio · Path Efficiency  (0–100%, wider = better)",
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
        axis_order = ["avg_step_cost", "coin_ratio", "path_efficiency"]
        lx = x
        for key in axis_order:
            col = PERSONALITY_COLORS[key]
            lbl = PERSONALITY_LABELS[key]
            pygame.draw.rect(self.screen, pygame.Color(col),
                             (lx, y, 13, 13), border_radius=2)
            surf = self.f_small.render(lbl, True, pygame.Color(TEXT_MUTED))
            self.screen.blit(surf, (lx + 17, y))
            lx += surf.get_width() + 40
        y += 24

        # Grid layout: 4 columns, 2 rows for 7 algorithms
        algo_names = list(self._profiles.keys())
        cols       = 4
        radar_r    = 85
        cell_w     = (SCREEN_WIDTH - PAD * 2) // cols
        available_h = CONTENT_Y + CONTENT_H - y - 12
        cell_h      = available_h // 2

        for idx, algo in enumerate(algo_names):
            col_i = idx % cols
            row_i = idx // cols
            cx    = PAD + col_i * cell_w + cell_w // 2
            cy    = y + row_i * cell_h + cell_h // 2
            self._draw_radar(cx, cy, radar_r, algo, self._profiles[algo])

    def _draw_radar(self, cx, cy, r, title, profile):
        """
        Draws a single radar graph with three axes at 120° angles.

        Axes:
            avg_step_cost   → up (270°)         green  — cheaper = better
            coin_ratio      → bottom-right (30°) gold   — coins collected %
            path_efficiency → bottom-left (150°) indigo — efficiency %

        All values 0–100, mapped to distance from center.
        """
        axis_order = ["avg_step_cost", "coin_ratio", "path_efficiency"]
        angles_deg = [270, 30, 150]
        angles_rad = [math.radians(a) for a in angles_deg]

        # Background circle
        pygame.draw.circle(self.screen, pygame.Color("#1E1E2E"), (cx, cy), r + 10)
        pygame.draw.circle(self.screen, pygame.Color(MUTED_LINE), (cx, cy), r + 10, 1)

        # Concentric reference rings
        for pct in [0.25, 0.5, 0.75, 1.0]:
            pygame.draw.circle(self.screen, pygame.Color("#2A2A3E"), (cx, cy), int(r * pct), 1)

        lbl_50 = self.f_small.render("50%", True, pygame.Color("#444466"))
        self.screen.blit(lbl_50, (cx + int(r * 0.5) + 3, cy - lbl_50.get_height() // 2))

        # Axis spokes
        for angle in angles_rad:
            ex = cx + int(r * math.cos(angle))
            ey = cy + int(r * math.sin(angle))
            pygame.draw.line(self.screen, pygame.Color("#2A2A3E"), (cx, cy), (ex, ey), 1)

        # Build polygon from personality values
        polygon_pts = []
        for i, key in enumerate(axis_order):
            pct   = profile.get(key, 0.0) / 100.0
            dist  = r * pct
            angle = angles_rad[i]
            px    = cx + int(dist * math.cos(angle))
            py    = cy + int(dist * math.sin(angle))
            polygon_pts.append((px, py))

        # Filled polygon
        if len(polygon_pts) >= 3:
            poly_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(poly_surf, (99, 102, 241, 55), polygon_pts)
            self.screen.blit(poly_surf, (0, 0))
            pygame.draw.polygon(self.screen, pygame.Color(ACCENT), polygon_pts, 2)

        # Vertex dots colored per axis
        for i, (px, py) in enumerate(polygon_pts):
            col = PERSONALITY_COLORS[axis_order[i]]
            pygame.draw.circle(self.screen, pygame.Color(col), (px, py), 5)
            pygame.draw.circle(self.screen, pygame.Color("#FFFFFF"), (px, py), 5, 1)

        # Axis endpoint labels
        short_labels = {
            "avg_step_cost":   "Cheap",
            "coin_ratio":      "Coins",
            "path_efficiency": "Effic.",
        }
        label_pad = 16
        for i, key in enumerate(axis_order):
            val   = profile.get(key, 0.0)
            angle = angles_rad[i]
            lx    = cx + int((r + label_pad) * math.cos(angle))
            ly    = cy + int((r + label_pad) * math.sin(angle))
            text  = f"{short_labels[key]} {val:.0f}%"
            surf  = self.f_small.render(text, True, pygame.Color(PERSONALITY_COLORS[key]))
            if math.cos(angle) >= 0:
                self.screen.blit(surf, (lx, ly - surf.get_height() // 2))
            else:
                self.screen.blit(surf, (lx - surf.get_width(), ly - surf.get_height() // 2))

        # Algorithm name below radar
        name_surf = self.f_small.render(title, True, pygame.Color(TEXT_COLOR))
        self.screen.blit(name_surf, (
            cx - name_surf.get_width() // 2,
            cy + r + 14
        ))

    # ================================================================ #
    # INSIGHT BAR
    # ================================================================ #

    def _draw_insight_bar(self):
        pygame.draw.rect(self.screen, pygame.Color(INSIGHT_BG),
                         (0, INSIGHT_Y, SCREEN_WIDTH, INSIGHT_H))
        pygame.draw.line(self.screen, pygame.Color(MUTED_LINE),
                         (0, INSIGHT_Y), (SCREEN_WIDTH, INSIGHT_Y), 1)

        lines = INSIGHTS.get(self.current_tab, ("", ""))
        y     = INSIGHT_Y + 12

        if lines[0]:
            surf = self.f_insight_bold.render(lines[0], True, pygame.Color(TEXT_COLOR))
            self.screen.blit(surf, (PAD, y))
            y += surf.get_height() + 6

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