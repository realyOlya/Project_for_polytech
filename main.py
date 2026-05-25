import pygame
from core_game.game_engine import GameEngine
from core_game.scene_manager import SceneManager
from core_game.state_manager import StateManager
from scene_game.game_scene import GameScene
import os
import sys

def resource_path(relative_path):
    """ Эта функция берет обычный путь и превращает его в путь,
        который понимает .exe файл """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def main():
    pygame.init()
    state_manager = StateManager()
    scene_manager = SceneManager()
    game_scene = GameScene(scene_manager, state_manager)
    scene_manager.add_scene("game", game_scene)
    scene_manager.switch_to("game")
    game = GameEngine(scene_manager)
    game.run()


if __name__ == "__main__":
    main()

