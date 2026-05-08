import time
from config import *


class Feedback:
    def __init__(self, screen_width, screen_height, font):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.message = ""
        self.color = (0, 0, 0)
        self.x = screen_width // 2
        self.start_y = screen_height - 60
        self.y = self.start_y
        self.is_active = False
        self.start_time = 0
        self.DURATION = FEEDBACK_DURATION
        self.SPEED = FEEDBACK_SPEED

    def show(self, message, is_success=True):
        self.message = message
        self.is_active = True
        self.start_time = time.time()
        self.y = self.start_y
        self.color = FEEDBACK_COLOR_SUCCESS if is_success else FEEDBACK_COLOR_ERROR

    def draw(self, surface):
        if not self.is_active:
            return
        elapsed = time.time() - self.start_time

        if elapsed > self.DURATION:
            self.is_active = False
            return
        self.y = self.start_y - (elapsed * self.SPEED)
        text_surf = self.font.render(self.message, True, self.color)

        if elapsed > self.DURATION * 0.6:
            alpha = int(255 * (1 - (elapsed / self.DURATION)))
            text_surf.set_alpha(max(0, alpha))
        text_rect = text_surf.get_rect(center=(self.x, self.y))
        surface.blit(text_surf, text_rect)
