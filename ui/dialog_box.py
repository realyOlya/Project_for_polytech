import pygame
import time
from config import *


class DialogBox:
    def __init__(self, x, y, width, height, text, font_path):
        self.font_path = font_path
        self.font = pygame.font.Font(self.font_path, BUTTON_BASE_FONT_SIZE)
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.lines = self._wrap_text(self.text)
        line_height = self.font.get_linesize()
        new_height = len(self.lines) * line_height + (BUTTON_TEXT_PADDING * 2)
        if new_height > height:
            self.rect.height = new_height
        self.color_normal = BUTTON_COLOR_NORMAL
        self.color_hover = BUTTON_COLOR_HOVER
        self.color_correct = BUTTON_COLOR_CORRECT
        self.color_wrong = BUTTON_COLOR_WRONG
        self.color_selected = BUTTON_COLOR_SELECTED
        self.status = None
        self.is_hovered = False
        self.wrong_timer = 0
        self.WRONG_DURATION = BUTTON_WRONG_DURATION

    def _wrap_text(self, text):
        paragraphs = text.split('\n')
        wrapped_lines = []
        max_width = self.rect.width - (BUTTON_TEXT_PADDING * 2)
        for paragraph in paragraphs:
            words = paragraph.split(' ')
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                w, _ = self.font.size(test_line)
                if w <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        wrapped_lines.append(' '.join(current_line))
                    current_line = [word]
            wrapped_lines.append(' '.join(current_line))
        return wrapped_lines

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
        line_height = self.font.get_linesize()

        for i, line in enumerate(self.lines):
            text_surf = self.font.render(line, True, BUTTON_TEXT_COLOR)
            text_rect = text_surf.get_rect(centerx=self.rect.centerx,
                                           top=self.rect.top + BUTTON_TEXT_PADDING + i * line_height)
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

