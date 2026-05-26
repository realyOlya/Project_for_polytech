import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


class GameEngine:
    def __init__(self, scene_manager):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Тренажёр: Рассольник ленинградский")
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene_manager = scene_manager
        self.dt = 0

    def run(self):
        while self.running:
            current_scene = self.scene_manager.get_current_scene()
            if current_scene:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                    current_scene.handle_event(event)
                current_scene.update(self.dt)
                current_scene.draw(self.screen)
            else:
                self.running = False
            pygame.display.flip()
            self.dt = self.clock.tick(FPS) / 1000.0
        pygame.quit()

