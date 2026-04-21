import pygame
import json
from pathlib import Path
from core_game.scene import Scene
from ui.button import Button
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from game_logic.validator import ActionValidator
from game_logic.scoring import ErrorCounter
from game_logic.confirmation_handler import ConfirmationHandler


class GameScene(Scene):
    def __init__(self, scene_manager, state_manager):
        super().__init__(scene_manager, state_manager)

        # Загрузка items.json с использованием pathlib
        BASE_DIR = Path(__file__).resolve().parent.parent
        with open(BASE_DIR / "data" / "items.json", "r", encoding="utf-8") as f:
            self.items = json.load(f)

        # Использование новых классов
        self.validator = ActionValidator("data/scenarios.json")
        self.error_counter = ErrorCounter()
        self.confirmation = ConfirmationHandler()

        # Порядок шагов
        self.steps_order = [
            "1", "2", "3", "4", "5",
            "6_1", "6_2", "6_3",
            "7", "8", "9", "10", "11",
            "12_1", "12_2", "12_3", "12_4",
            "13", "14", "15", "16", "17", "18"
        ]
        self.step_index = 0
        self.current_step = self.steps_order[0]

        # Состояния
        self.waiting_for_next = False
        self.is_error = False
        self.sequence_selected = []
        self.multi_selected = []
        self.products_stage = 0
        self.selected_vegetables = []
        self.cut_index = 0

        # Кнопки
        self.option_buttons = []
        self.next_button = None
        self.retry_button = None

        # Шрифты
        self.font_large = pygame.font.SysFont("arial", 32)
        self.font_medium = pygame.font.SysFont("arial", 24)
        self.font_small = pygame.font.SysFont("arial", 18)

        self.load_step(self.current_step)

    def load_step(self, step_id):
        """Загружает шаг по ID"""
        self.current_step = step_id
        self.waiting_for_next = False
        self.is_error = False
        self.sequence_selected = []
        self.multi_selected = []

        step_data = self.validator.get_step(step_id)
        if not step_data:
            self.show_end_screen()
            return

        self.current_question = step_data.get("question", "")
        self.current_correct = step_data.get("correct", "")

        options = self._get_options_for_step(step_id)
        self._create_option_buttons(options)
        self._create_control_buttons()

    def _get_options_for_step(self, step_id):
        """Возвращает варианты для шага из items.json"""
        options_map = {
            "1": self.items["clothes"],
            "2": self.items["shoes"],
            "3": self.items["hats"],
            "4": self.items["jewerly"],
            "5": self.items["handwashing"],
            "6_1": self.items["meat"],
            "6_2": self.items["vegetables"],
            "6_3": self.items["cereal"],
            "7": ["Перейти в цех"],
            "8": self.items["workshop"],
            "9": self.items["meat_workshop"],
            "10": self.items["workshop"],
            "11": self.items["vegetables_workshop"],
            "12_1": self.items["cuts"],
            "12_2": self.items["cuts"],
            "12_3": self.items["cuts"],
            "12_4": self.items["cuts"],
            "13": self.items["workshop"],
            "14": self.items["dishes"],
            "15": self.items["cooking"],
            "16": self.items["temperature"],
            "17": ["Подать суп на бракераж"],
            "18": self.items["cleaning"],
        }
        return options_map.get(step_id, ["Далее"])

    def _create_option_buttons(self, options):
        """Создаёт кнопки с вариантами ответов"""
        self.option_buttons = []
        button_width = 500
        button_height = 35  # было 50
        start_x = (SCREEN_WIDTH - button_width) // 2
        start_y = 250 # было 350

        for i, option in enumerate(options[:10]):
            btn = Button(
                start_x,
                start_y + i * (button_height + 10),
                button_width,
                button_height,
                option,
                None
            )
            self.option_buttons.append(btn)

    def _create_control_buttons(self):
        """Создаёт кнопки Далее и Попробовать снова"""
        self.next_button = Button(
            (SCREEN_WIDTH - 200) // 2, 620, 200, 50, "ДАЛЕЕ", None
        )
        self.retry_button = Button(
            (SCREEN_WIDTH - 250) // 2, 620, 250, 50, "ПОПРОБОВАТЬ СНОВА", None
        )

    def handle_event(self, event):
        # Ожидание подтверждения
        if self.confirmation.is_waiting:
            return

        if self.waiting_for_next:
            if self.next_button and self.next_button.handle_event(event):
                self.next_step()
            return

        if self.is_error:
            if self.retry_button and self.retry_button.handle_event(event):
                self.load_step(self.current_step)
            return

        for i, btn in enumerate(self.option_buttons):
            if btn.handle_event(event):
                self.check_answer(i, btn.text)
                break

    def next_step(self):
        """Переход к следующему шагу"""
        self.step_index += 1
        if self.step_index < len(self.steps_order):
            self.load_step(self.steps_order[self.step_index])
        else:
            self.show_end_screen()

    def check_answer(self, idx, text):

        """Проверка ответа с использованием ActionValidator"""

        # Обычный шаг (один правильный ответ) — используем валидатор
        if self.validator.validate(self.current_step, text):
            self.option_buttons[idx].status = "correct"
            self.waiting_for_next = True
        else:
            self._show_error()
            self.option_buttons[idx].status = "wrong"
            # Показываем правильный ответ (если это строка)

    def _show_error(self):
        self.is_error = True
        self.error_counter.add_error()
        print(f"[Ошибка] Шаг {self.current_step}! Всего ошибок: {self.error_counter.count}")

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((240, 240, 255))

        # Заголовок
        title = self.font_small.render(f"Шаг {self.current_step} из {len(self.steps_order)}", True, (100, 100, 100))
        screen.blit(title, (20, 20))

        # Счётчик ошибок
        error_text = self.font_small.render(f"Ошибок: {self.error_counter.count}", True, (231, 76, 60))
        screen.blit(error_text, (SCREEN_WIDTH - 120, 20))

        # Вопрос
        if hasattr(self, 'current_question'):
            question_text = self.font_medium.render(self.current_question, True, (0, 0, 0))
            screen.blit(question_text, (SCREEN_WIDTH // 2 - question_text.get_width() // 2, 100))

        # Кнопки
        for btn in self.option_buttons:
            btn.draw(screen)

        # Кнопки управления
        if self.waiting_for_next and self.next_button:
            self.next_button.draw(screen)
        elif self.is_error and self.retry_button:
            self.retry_button.draw(screen)