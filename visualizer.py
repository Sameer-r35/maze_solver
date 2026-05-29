import os
import time
import pygame
from config import (
    COLORS, CELL_SIZE, X_OFFSET, Y_OFFSET,
    SIDEBAR_WIDTH, SCREEN_HEIGHT,
    SIDEBAR_BG, SIDEBAR_BORDER, TEXT_COLOR, TEXT_MUTED,
    BG_COLOR, GOLD_COLOR, GOLD_BORDER,
    START, END,
)
from algorithms.bfs    import bfs
from algorithms.dfs    import dfs
from algorithms.ucs    import ucs
from algorithms.greedy import greedy
from algorithms.astar  import astar

COLOR_VISITED  = pygame.Color("#C084FC")
COLOR_FRONTIER = pygame.Color("#FDE047")
COLOR_PATH     = pygame.Color("#4ADE80")
COLOR_CURRENT  = pygame.Color("#F97316")

SPEED_PRESETS = {"1x": 1, "2x": 3, "5x": 8, "Instant": 9999}
ALGO_OPTIONS  = ["BFS", "DFS", "UCS", "Greedy", "A*"]

# ------------------------------------------------------------------ #
# Font paths — relative to this file's location
# ------------------------------------------------------------------ #
_HERE       = os.path.dirname(os.path.abspath(__file__))
_FONTS_DIR  = os.path.join(_HERE, "assets", "fonts")

_JB_BOLD    = os.path.join(_FONTS_DIR, "JetBrainsMono-Bold.ttf")
_JB_REG     = os.path.join(_FONTS_DIR, "JetBrainsMono-Regular.ttf")
_IBM_REG    = os.path.join(_FONTS_DIR, "IBMPlexSans-Regular.ttf")
_IBM_SEMI   = os.path.join(_FONTS_DIR, "IBMPlexSans-SemiBold.ttf")


def _load_font(path, size, fallback="Segoe UI", bold=False):
    """Load a TTF font from path; fall back to a system font if missing."""
    if os.path.exists(path):
        return pygame.font.Font(path, size)
    return pygame.font.SysFont(fallback, size, bold=bold)


class Visualizer:
    def __init__(self, screen, renderer, grid):
        self.screen   = screen
        self.renderer = renderer
        self.grid     = grid

        pygame.font.init()

        # ---- fonts -------------------------------------------------- #
        # Title:          JetBrains Mono Bold  — techy, prominent
        # Section heads:  JetBrains Mono Reg   — code-like small caps feel
        # Shortcut keys:  JetBrains Mono Reg   — [Key] looks natural in mono
        # Button labels:  IBM Plex Sans Semi    — friendly, readable
        # Stats labels:   IBM Plex Sans Reg     — clean body text
        # Stats values:   IBM Plex Sans Semi    — slightly heavier for values
        self.f_title   = _load_font(_JB_BOLD,  20, bold=True)
        self.f_sec     = _load_font(_JB_REG,   11)
        self.f_key     = _load_font(_JB_REG,   11)
        self.f_btn     = _load_font(_IBM_SEMI, 13, bold=True)
        self.f_label   = _load_font(_IBM_REG,  12)
        self.f_value   = _load_font(_IBM_SEMI, 12, bold=True)
        self.f_algo    = _load_font(_IBM_SEMI, 13, bold=True)

        # ---- algorithm state ---------------------------------------- #
        self.generator    = None
        self.solving      = False
        self.paused       = False
        self.done         = False
        self.visited      = set()
        self.frontier     = set()
        self.current_cell = None
        self.path         = None

        # ---- stats -------------------------------------------------- #
        self.nodes_explored  = 0
        self.path_length     = 0
        self.path_cost       = 0.0
        self.coins_collected = 0
        self.final_score     = 0.0
        self.elapsed_ms      = 0.0
        self.start_time      = None

        # ---- UI state ----------------------------------------------- #
        self.selected_algo = "BFS"
        self.speed_label   = "1x"
        self.greed_value   = 0
        self.on_generate   = None

        self._build_ui()

    # ================================================================ #
    # PUBLIC
    # ================================================================ #

    def update(self):
        if not self.solving or self.paused or self.done:
            return
        steps = SPEED_PRESETS[self.speed_label]
        for _ in range(steps):
            if self.generator is None:
                break
            try:
                state = next(self.generator)
                self._apply_state(state)
                if state["path"] is not None:
                    self._finish()
                    break
            except StopIteration:
                self._finish()
                break

    def draw(self):
        self.screen.fill(pygame.Color(BG_COLOR))
        self.renderer.draw_sidebar_background(self.screen)
        self.renderer.draw_grid(self.screen, self.grid)
        self._draw_overlay()
        self._draw_ui_panel()
        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self._handle_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_click(event.pos)
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            self._handle_drag(event.pos)

    def set_grid(self, grid):
        self.grid = grid
        self._reset_state()

    # ================================================================ #
    # OVERLAY — drawn on grid (right side)
    # ================================================================ #

    def _draw_overlay(self):
        cell = CELL_SIZE - 1
        for r, c in self.visited:
            pygame.draw.rect(self.screen, COLOR_VISITED,
                             (X_OFFSET + c * CELL_SIZE, Y_OFFSET + r * CELL_SIZE, cell, cell))
        for r, c in self.frontier:
            pygame.draw.rect(self.screen, COLOR_FRONTIER,
                             (X_OFFSET + c * CELL_SIZE, Y_OFFSET + r * CELL_SIZE, cell, cell))
        if self.current_cell:
            r, c = self.current_cell
            pygame.draw.circle(
                self.screen, COLOR_CURRENT,
                (X_OFFSET + c * CELL_SIZE + CELL_SIZE // 2,
                 Y_OFFSET + r * CELL_SIZE + CELL_SIZE // 2),
                CELL_SIZE // 3)
        if self.path:
            for r, c in self.path:
                pygame.draw.rect(self.screen, COLOR_PATH,
                                 (X_OFFSET + c * CELL_SIZE, Y_OFFSET + r * CELL_SIZE, cell, cell))
        self._redraw_coins()
        self._redraw_start_end()

    def _redraw_coins(self):
        path_set = set(self.path) if self.path else set()
        for r, c in self.grid.coins:
            x  = X_OFFSET + c * CELL_SIZE
            y  = Y_OFFSET + r * CELL_SIZE
            cx = x + CELL_SIZE // 2
            cy = y + CELL_SIZE // 2
            r2 = CELL_SIZE // 4
            if (r, c) in path_set:
                # Dimmed — collected
                pygame.draw.circle(self.screen, pygame.Color("#7C5C1A"), (cx, cy), r2 + 1)
                pygame.draw.circle(self.screen, pygame.Color("#A07830"), (cx, cy), r2)
            else:
                pygame.draw.circle(self.screen, pygame.Color(GOLD_BORDER), (cx, cy), r2 + 1)
                pygame.draw.circle(self.screen, pygame.Color(GOLD_COLOR),  (cx, cy), r2)

    def _redraw_start_end(self):
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                t = self.grid.get_cell(r, c)
                if t in (START, END):
                    pygame.draw.rect(
                        self.screen, pygame.Color(COLORS[t]),
                        (X_OFFSET + c * CELL_SIZE, Y_OFFSET + r * CELL_SIZE,
                         CELL_SIZE - 1, CELL_SIZE - 1))

    # ================================================================ #
    # SIDEBAR UI — left side
    # ================================================================ #

    def _draw_ui_panel(self):
        px = 18
        self._draw_title(px)
        self._draw_algorithm_selector(px)
        self._draw_speed_selector(px)
        self._draw_greed_slider(px)
        self._draw_buttons(px)
        self._draw_stats(px)

    def _draw_title(self, px):
        self.screen.blit(
            self.f_title.render("MAZE SOLVER", True, pygame.Color(TEXT_COLOR)),
            (px, 18))
        pygame.draw.line(self.screen, pygame.Color(SIDEBAR_BORDER),
                         (px, 50), (SIDEBAR_WIDTH - px, 50), 1)

    def _draw_algorithm_selector(self, px):
        y = self.algo_section_y
        self.screen.blit(
            self.f_sec.render("ALGORITHM", True, pygame.Color(TEXT_MUTED)), (px, y))
        y += 18
        for label in ALGO_OPTIONS:
            rect     = self.algo_rects[label]
            selected = (label == self.selected_algo)
            dot      = pygame.Color("#6366F1") if selected else pygame.Color(SIDEBAR_BORDER)
            pygame.draw.circle(self.screen, dot, (rect.x + 7, rect.y + 7), 6)
            if selected:
                pygame.draw.circle(self.screen, pygame.Color("#E2E8F0"),
                                   (rect.x + 7, rect.y + 7), 3)
            self.screen.blit(
                self.f_algo.render(label, True, pygame.Color(TEXT_COLOR)),
                (rect.x + 18, rect.y))

    def _draw_speed_selector(self, px):
        self.screen.blit(
            self.f_sec.render("SPEED", True, pygame.Color(TEXT_MUTED)),
            (px, self.speed_section_y))
        for label, rect in self.speed_rects.items():
            bg = pygame.Color("#6366F1") if label == self.speed_label else pygame.Color(SIDEBAR_BORDER)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            txt = self.f_value.render(label, True, pygame.Color(TEXT_COLOR))
            self.screen.blit(txt, (rect.x + (rect.width - txt.get_width()) // 2, rect.y + 4))

    def _draw_greed_slider(self, px):
        if self.selected_algo != "A*":
            return
        self.screen.blit(
            self.f_sec.render(f"GREED: {self.greed_value}%", True, pygame.Color(TEXT_MUTED)),
            (px, self.greed_section_y))
        t  = self.greed_track
        fw = int(t.width * self.greed_value / 100)
        pygame.draw.rect(self.screen, pygame.Color(SIDEBAR_BORDER), t, border_radius=4)
        if fw > 0:
            pygame.draw.rect(self.screen, pygame.Color("#6366F1"),
                             (t.x, t.y, fw, t.height), border_radius=4)
        pygame.draw.circle(self.screen, pygame.Color("#E2E8F0"),
                           (t.x + fw, t.y + t.height // 2), 6)

    def _draw_buttons(self, px):
        for key, label, color in [
            ("solve",    "Solve",    "#6366F1"),
            ("pause",    "Pause",    "#334155"),
            ("reset",    "Reset",    "#334155"),
            ("generate", "Generate", "#334155"),
        ]:
            rect = self.button_rects[key]
            pygame.draw.rect(self.screen, pygame.Color(color), rect, border_radius=5)
            txt = self.f_btn.render(label, True, pygame.Color("#FFFFFF"))
            self.screen.blit(txt, (rect.x + (rect.width - txt.get_width()) // 2, rect.y + 8))

    def _draw_stats(self, px):
        y = self.stats_y
        pygame.draw.line(self.screen, pygame.Color(SIDEBAR_BORDER),
                         (px, y - 10), (SIDEBAR_WIDTH - px, y - 10), 1)
        self.screen.blit(self.f_sec.render("STATS", True, pygame.Color(TEXT_MUTED)), (px, y))
        y += 18

        coins_val = str(self.coins_collected) if self.done else "—"
        score_val = f"{self.final_score:.0f}" if self.done else "—"
        for label, value in [
            ("Nodes explored",   str(self.nodes_explored)),
            ("Path Length",  str(self.path_length)       if self.path_length  else "—"),
            ("PathCost",    f"{self.path_cost:.0f}"     if self.path_cost    else "—"),
            ("Coins Collected",   coins_val),
            ("Score",   score_val),
            ("Time",    f"{self.elapsed_ms:.1f} ms" if self.elapsed_ms   else "—"),
        ]:
            self.screen.blit(self.f_label.render(label, True, pygame.Color(TEXT_MUTED)), (px, y))
            # Highlight score in gold when positive, red when negative
            if label == "Score" and self.done:
                val_color = pygame.Color(GOLD_COLOR) if self.final_score >= 0 else pygame.Color("#F87171")
            else:
                val_color = pygame.Color(TEXT_COLOR)
            self.screen.blit(self.f_value.render(value, True, val_color), (px + 90, y))
            y += 20

        # Keyboard shortcuts
        y += 8
        pygame.draw.line(self.screen, pygame.Color(SIDEBAR_BORDER),
                         (px, y), (SIDEBAR_WIDTH - px, y), 1)
        y += 10
        for key, desc in [
            ("[Enter]", "Solve"),
            ("[Space]", "Pause"),
            ("[R]",     "Reset"),
            ("[G]",     "Generate"),
            ("[ESC]",   "Exit"),
        ]:
            self.screen.blit(self.f_key.render(key,  True, pygame.Color("#6366F1")), (px, y))
            self.screen.blit(self.f_key.render(desc, True, pygame.Color(TEXT_MUTED)), (px + 62, y))
            y += 17

    # ================================================================ #
    # EVENT HANDLING
    # ================================================================ #

    def _handle_key(self, key):
        if   key in (pygame.K_RETURN, pygame.K_KP_ENTER): self._action_solve()
        elif key == pygame.K_SPACE:                        self._action_pause()
        elif key == pygame.K_r:                            self._action_reset()
        elif key == pygame.K_g:                            self._action_generate()

    def _handle_click(self, pos):
        for label, rect in self.algo_rects.items():
            if rect.collidepoint(pos):
                self.selected_algo = label
                return
        for label, rect in self.speed_rects.items():
            if rect.collidepoint(pos):
                self.speed_label = label
                return
        if self.selected_algo == "A*" and self.greed_track.collidepoint(pos):
            self._update_greed(pos[0])
            return
        for key, rect in self.button_rects.items():
            if rect.collidepoint(pos):
                getattr(self, f"_action_{key}")()
                return

    def _handle_drag(self, pos):
        if self.selected_algo == "A*" and self.greed_track.collidepoint(pos):
            self._update_greed(pos[0])

    def _update_greed(self, mx):
        t = self.greed_track
        self.greed_value = max(0, min(100, int((mx - t.x) / t.width * 100)))

    # ================================================================ #
    # ACTIONS
    # ================================================================ #

    def _action_solve(self):
        self._reset_state()
        start = (1, 1)
        end   = (self.grid.rows - 2, self.grid.cols - 2)
        self.generator  = self._make_generator(start, end)
        self.solving    = True
        self.paused     = False
        self.done       = False
        self.start_time = time.time()

    def _action_pause(self):
        if self.solving:
            self.paused = not self.paused
            if not self.paused and self.start_time:
                self.start_time = time.time() - self.elapsed_ms / 1000

    def _action_reset(self):
        self.grid.reset_search()
        self._reset_state()

    def _action_generate(self):
        if callable(self.on_generate):
            self.on_generate()

    # ================================================================ #
    # INTERNAL
    # ================================================================ #

    def _make_generator(self, start, end):
        a = self.selected_algo
        if   a == "BFS":    return bfs(self.grid, start, end)
        elif a == "DFS":    return dfs(self.grid, start, end)
        elif a == "UCS":    return ucs(self.grid, start, end)
        elif a == "Greedy": return greedy(self.grid, start, end)
        elif a == "A*":     return astar(self.grid, start, end, greed=self.greed_value)

    def _apply_state(self, state):
        self.visited        = state["visited"]
        self.frontier       = state["frontier"]
        self.current_cell   = state["current"]
        self.nodes_explored = len(state["visited"])
        if state["path"] is not None:
            self.path = state["path"]
        if self.start_time:
            self.elapsed_ms = (time.time() - self.start_time) * 1000

    def _finish(self):
        self.solving    = False
        self.done       = True
        self.elapsed_ms = (time.time() - self.start_time) * 1000 if self.start_time else 0
        if self.path:
            self.path_length     = len(self.path)
            self.path_cost       = sum(self.grid.get_cost(*cell) for cell in self.path)
            self.coins_collected = self.grid.get_coins_in_path(self.path)
            self.final_score     = self.coins_collected * 100 - self.path_cost

    def _reset_state(self):
        self.generator       = None
        self.solving         = False
        self.paused          = False
        self.done            = False
        self.visited         = set()
        self.frontier        = set()
        self.current_cell    = None
        self.path            = None
        self.nodes_explored  = 0
        self.path_length     = 0
        self.path_cost       = 0.0
        self.coins_collected = 0
        self.final_score     = 0.0
        self.elapsed_ms      = 0.0
        self.start_time      = None

    # ================================================================ #
    # UI LAYOUT — built once at init
    # ================================================================ #

    def _build_ui(self):
        px = 18
        rw = SIDEBAR_WIDTH - px * 2
        y  = 58

        self.algo_section_y = y
        y += 18
        self.algo_rects = {}
        for label in ALGO_OPTIONS:
            self.algo_rects[label] = pygame.Rect(px, y, rw, 16)
            y += 24
        y += 6

        self.speed_section_y = y
        y += 18
        bw = (rw - 6) // 4
        self.speed_rects = {}
        for i, label in enumerate(SPEED_PRESETS):
            self.speed_rects[label] = pygame.Rect(px + i * (bw + 2), y, bw, 26)
        y += 36

        self.greed_section_y = y
        y += 18
        self.greed_track = pygame.Rect(px, y, rw, 8)
        y += 24

        y += 6
        bh, gap = 34, 7
        self.button_rects = {}
        for key in ("solve", "pause", "reset", "generate"):
            self.button_rects[key] = pygame.Rect(px, y, rw, bh)
            y += bh + gap

        self.stats_y = y + 10