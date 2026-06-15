"""
tutorial.py
===========
TutorialScreen — A step-by-step interactive instructions page.
Displays a small pop-up modal panel with "Next" and "Skip" controls.
"""

import os
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BG_COLOR, TEXT_COLOR, TEXT_MUTED
)

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

# UI Theme Config matches main design
PANEL_W, PANEL_H = 500, 320
ACCENT       = "#6366F1"
ACCENT_HOVER = "#7C7FF5"
PANEL_BG     = "#1E1E30"
BORDER_COLOR = "#32323E"

TUTORIAL_STEPS = [
    {
        "title": "Welcome to Heuristica!",
        "lines": [
            "This application simulates and evaluates how different",
            "pathfinding algorithms navigate weighted environments.",
            "Let's learn the basics!"
        ]
    },
    {
        "title": "1. Terrain & Movement Costs",
        "lines": [
            "Not all open spaces are equal! Moving through cells costs:",
            "  • PLAIN Terrain  →  1 point",
            "  • MUD Terrain     →  5 points",
            "  • WATER Terrain →  10 points",
            "Grey Walls block algorithms completely."
        ]
    },
    {
        "title": "2. Coin Collection",
        "lines": [
            "Gold circles represent optional high-value coins.",
            "Algorithms that pick up coins earn major score bonuses!",
            "Some algorithms prioritize paths with heavy coin clusters."
        ]
    },
    {
        "title": "3. Controlling the AI",
        "lines": [
            "Use the sidebar panel on the main interface to:",
            "  • Pick an algorithm (BFS, DFS, UCS, A*, Greedy)",
            "  • Adjust solution speed or trigger a clean layout",
            "  • Run step-by-step or instantly execute solutions"
        ]
    },
    {
        "title": "4. Performance Analytics",
        "lines": [
            "Click 'Main Menu' to hop into the Analytics board.",
            "There you can evaluate execution speeds, nodes explored,",
            "and algorithm 'personalities' side-by-side via graphs."
        ]
    }
]

class TutorialScreen:
    def __init__(self):
        pygame.font.init()
        self.f_title = _load_font(_JB_BOLD,  20, bold=True)
        self.f_body  = _load_font(_IBM_REG,  15)
        self.f_btn   = _load_font(_IBM_SEMI, 14, bold=True)
        self.f_step  = _load_font(_JB_REG,   12)

        self.current_step = 0
        
        # Center the pop-up modal card on screen
        self.panel_x = (SCREEN_WIDTH - PANEL_W) // 2
        self.panel_y = (SCREEN_HEIGHT - PANEL_H) // 2
        self.panel_rect = pygame.Rect(self.panel_x, self.panel_y, PANEL_W, PANEL_H)
        
        # Button geometric boundaries
        self._build_buttons()
        self._hovered_btn = None

    def _build_buttons(self):
        btn_w, btn_h = 110, 36
        gap = 16
        
        # Next / Finish Button (Bottom Right)
        self.btn_next_rect = pygame.Rect(
            self.panel_x + PANEL_W - btn_w - 24,
            self.panel_y + PANEL_H - btn_h - 24,
            btn_w, btn_h
        )
        
        # Skip / Close Button (Bottom Left)
        self.btn_skip_rect = pygame.Rect(
            self.panel_x + 24,
            self.panel_y + PANEL_H - btn_h - 24,
            btn_w, btn_h
        )

    def handle_events(self, events):
        """Returns 'MENU' when finished or exited, otherwise None."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Track active hover highlights
        if self.btn_next_rect.collidepoint(mouse_pos):
            self._hovered_btn = "NEXT"
        elif self.btn_skip_rect.collidepoint(mouse_pos):
            self._hovered_btn = "SKIP"
        else:
            self._hovered_btn = None

        for event in events:
            if event.type == pygame.QUIT:
                return "MENU"
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_RIGHT):
                    if self.current_step < len(TUTORIAL_STEPS) - 1:
                        self.current_step += 1
                    else:
                        return "MENU"
                elif event.key == pygame.K_LEFT and self.current_step > 0:
                    self.current_step -= 1

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_next_rect.collidepoint(event.pos):
                    if self.current_step < len(TUTORIAL_STEPS) - 1:
                        self.current_step += 1
                    else:
                        return "MENU"
                elif self.btn_skip_rect.collidepoint(event.pos):
                    return "MENU"
                    
        return None

    def draw(self, screen):
        # Background fallback base paint
        screen.fill(pygame.Color(BG_COLOR))
        
        # Optional subtle decoration: dim layout behind pop-up card
        dim_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surface.fill((10, 10, 16, 120))
        screen.blit(dim_surface, (0, 0))

        # 1. Main Modal Pop-up Card Box
        pygame.draw.rect(screen, pygame.Color(PANEL_BG), self.panel_rect, border_radius=12)
        pygame.draw.rect(screen, pygame.Color(BORDER_COLOR), self.panel_rect, width=2, border_radius=12)

        step_data = TUTORIAL_STEPS[self.current_step]

        # 2. Render Step Tracker (e.g., "STEP 1 OF 5")
        step_str = f"STEP {self.current_step + 1} OF {len(TUTORIAL_STEPS)}"
        step_surf = self.f_step.render(step_str, True, pygame.Color(TEXT_MUTED))
        screen.blit(step_surf, (self.panel_x + 24, self.panel_y + 24))

        # 3. Render Header Title Text
        title_surf = self.f_title.render(step_data["title"], True, pygame.Color(ACCENT))
        screen.blit(title_surf, (self.panel_x + 24, self.panel_y + 46))

        # Horizontal separator accent rule line
        pygame.draw.line(
            screen, pygame.Color(BORDER_COLOR),
            (self.panel_x + 24, self.panel_y + 80),
            (self.panel_x + PANEL_W - 24, self.panel_y + 80), 1
        )

        # 4. Render Instructions Body text lines
        text_y = self.panel_y + 98
        for line in step_data["lines"]:
            color = TEXT_COLOR if not line.strip().startswith("•") else "#FCD34D"
            txt_surf = self.f_body.render(line, True, pygame.Color(color))
            screen.blit(txt_surf, (self.panel_x + 24, text_y))
            text_y += txt_surf.get_height() + 8

        # 5. Draw Action Controls Buttons
        # Skip / Exit Button
        skip_bg = "#2D3748" if self._hovered_btn != "SKIP" else "#3E4A5E"
        pygame.draw.rect(screen, pygame.Color(skip_bg), self.btn_skip_rect, border_radius=6)
        pygame.draw.rect(screen, pygame.Color(BORDER_COLOR), self.btn_skip_rect, width=1, border_radius=6)
        skip_txt = "Skip Tutorial" if self.current_step < len(TUTORIAL_STEPS) - 1 else "Close"
        skip_surf = self.f_btn.render(skip_txt, True, pygame.Color(TEXT_COLOR))
        screen.blit(skip_surf, (
            self.btn_skip_rect.x + (self.btn_skip_rect.width - skip_surf.get_width()) // 2,
            self.btn_skip_rect.y + (self.btn_skip_rect.height - skip_surf.get_height()) // 2
        ))

        # Next / Finish Button
        next_bg = ACCENT if self._hovered_btn != "NEXT" else ACCENT_HOVER
        pygame.draw.rect(screen, pygame.Color(next_bg), self.btn_next_rect, border_radius=6)
        next_txt = "Next →" if self.current_step < len(TUTORIAL_STEPS) - 1 else "Finish!"
        next_surf = self.f_btn.render(next_txt, True, pygame.Color("#FFFFFF"))
        screen.blit(next_surf, (
            self.btn_next_rect.x + (self.btn_next_rect.width - next_surf.get_width()) // 2,
            self.btn_next_rect.y + (self.btn_next_rect.height - next_surf.get_height()) // 2
        ))