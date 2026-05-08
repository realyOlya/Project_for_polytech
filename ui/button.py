import pygame
import time
from config import *


class Button:
    def __init__(self, x, y, width, height, text, font_path):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font_path = font_path
        self.base_size = BUTTON_BASE_FONT_SIZE
        self.font = self.fit_text()
        self.color_normal = BUTTON_COLOR_NORMAL
        self.color_hover = BUTTON_COLOR_HOVER
        self.color_correct = BUTTON_COLOR_CORRECT
        self.color_wrong = BUTTON_COLOR_WRONG
        self.color_selected = BUTTON_COLOR_SELECTED
        self.status = None
        self.is_hovered = False
        self.wrong_timer = 0
        self.WRONG_DURATION = BUTTON_WRONG_DURATION

    def fit_text(self):
        current_size = self.base_size
        test_font = pygame.font.Font(self.font_path, current_size)
        while (test_font.size(self.text)[0] > self.rect.width - BUTTON_TEXT_PADDING
               and current_size > BUTTON_MIN_FONT_SIZE):
            current_size -= 1
            test_font = pygame.font.Font(self.font_path, current_size)
        return test_font

    def draw(self, surface):
        color = self.color_normal
        if self.status == 'correct':
            color = self.color_correct
        elif self.status == 'wrong':
            color = self.color_wrong
        elif self.status == 'selected':
            color = self.color_selected
        elif self.is_hovered:
            color = self.color_hover
        pygame.draw.rect(surface, color, self.rect, border_radius=BUTTON_BORDER_RADIUS)
        pygame.draw.rect(surface, BUTTON_BORDER_COLOR, self.rect, width=2, border_radius=BUTTON_BORDER_RADIUS)
        text_surf = self.font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if self.status is not None:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False

    def set_wrong(self):
        self.status = 'wrong'
        self.wrong_timer = time.time()

    def reset(self):
        self.status = None
        self.is_hovered = False
        self.wrong_timer = 0
