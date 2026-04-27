import pygame

class InputBox:
    def __init__(self, x, y, w, h, font, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('black')
        self.font = font
        self.text = text
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False
        self.is_error = False  # Новое свойство для проверки на пустоту

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            if self.active:
                self.is_error = False  # Сбрасываем ошибку, когда пользователь начал печатать

        if event.type == pygame.KEYDOWN:
            if self.active:
                self.is_error = False  # Сбрасываем ошибку при вводе
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if len(self.text) < 15:
                        self.text += event.unicode
                self.txt_surface = self.font.render(self.text, True, self.color)

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect, border_radius=10)

        # Выбираем цвет рамки
        if self.is_error:
            border_color = (231, 76, 60)  # Красный, если нажали "Далее" при пустом поле
        elif self.active:
            border_color = (100, 100, 100)
        else:
            border_color = (200, 200, 200)

        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=10)
        screen.blit(self.txt_surface,
                    (self.rect.x + 10, self.rect.y + (self.rect.h - self.txt_surface.get_height()) // 2))