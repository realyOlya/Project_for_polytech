import pygame


class InputBox:
    def __init__(self, x, y, w, h, font, text='', validator=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('black')
        self.font = font
        self.text = text
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False
        self.is_error = False
        self.is_correct = False
        self.validator = validator

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            if self.active:
                self.is_error = False

        if event.type == pygame.KEYDOWN:
            if self.active:
                self.is_error = False
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == pygame.K_RETURN:
                    return
                else:
                    if len(self.text) < 15:
                        char = event.unicode
                        if self.validator is None or self.validator(char):
                            self.text += char
                self.txt_surface = self.font.render(self.text, True, self.color)

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect, border_radius=10)
        if self.is_error:
            border_color = (231, 76, 60)
        elif self.active:
            border_color = (100, 100, 100)
        else:
            border_color = (200, 200, 200)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=10)
        screen.blit(self.txt_surface,
                    (self.rect.x + 10, self.rect.y + (self.rect.h - self.txt_surface.get_height()) // 2))
