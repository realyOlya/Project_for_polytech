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

        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"

        with open(self.DATA_DIR / "items.json", "r", encoding="utf-8") as f:
            self.items = json.load(f)
        with open(self.DATA_DIR / "image.json", "r", encoding="utf-8") as f:
            self.image_data = json.load(f)

        self.validator = ActionValidator("data/scenarios.json")
        self.error_counter = ErrorCounter()
        self.confirmation = ConfirmationHandler()

        self.correct_count = 0
        self.total_items_to_collect = 0
        self.checkmark_img = None

        self.steps_order = ["1", "2", "3", "4", "5", "6_1", "6_2", "6_3", "7", "8", "9", "10", "11", "12_1", "12_2",
                            "12_3", "12_4", "13", "14", "15", "16", "17", "18"]
        self.step_index = 0
        self.current_step = self.steps_order[0]

        self.bg_image = None
        self.char_image = None
        self.click_zones = []
        self.question_button = None

        self.waiting_for_next = False
        self.is_error = False

        self.font_medium = pygame.font.SysFont("arial", 24)
        self.font_small = pygame.font.SysFont("arial", 18)

        self.load_step(self.current_step)

        try:
            check_path = self.DATA_DIR / "checkmark.png"   # имя файла галочки
            self.checkmark_img = pygame.image.load(str(check_path))
            self.checkmark_img = pygame.transform.scale(self.checkmark_img, (40, 40))
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            self.checkmark_img = None

    def load_step(self, step_id):
        self.current_step = step_id
        self.waiting_for_next = False
        self.is_error = False
        self.click_zones = []
        self.bg_image = None
        self.char_image = None

        step_data = self.validator.get_step(step_id)
        if not step_data:
            self.show_end_screen()
            return

        self.current_question = step_data.get("question", "")

        self.correct_count = 0
        self.total_items_to_collect = 0

        # --- НОВАЯ ЛОГИКА: Создание узкой кнопки вопроса ---
        text_surf = self.font_medium.render(self.current_question, True, (0, 0, 0))
        q_width = text_surf.get_width() + 40  # Захватывает ровно текст + отступы
        q_height = text_surf.get_height() + 20
        self.question_button = Button(400, 250, q_width, q_height, self.current_question, None)

        if step_id in self.image_data:
            visuals = self.image_data[step_id]
            try:
                bg_path = self.DATA_DIR / visuals["background"]
                self.bg_image = pygame.image.load(str(bg_path))
                self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

                char_path = self.DATA_DIR / visuals["character"]
                self.char_image = pygame.image.load(str(char_path))

                for item in visuals.get("items_to_click", []):
                    r = item["rect"]
                    zone = Button(r[0], r[1], r[2], r[3], "", None)
                    zone.action_id = item["id"]
                    zone.is_correct = False          # флаг, отмечена ли зона галочкой
                    self.click_zones.append(zone)
                self.total_items_to_collect = len(self.click_zones)
            except Exception as e:
                print(f"Ошибка загрузки: {e}")

        options = self._get_options_for_step(step_id)
        self._create_option_buttons(options)
        self._create_control_buttons()

        if self.current_step == "4":
            self.next_button = Button((SCREEN_WIDTH - 200) // 2, 620, 200, 50, "ПРОВЕРИТЬ", None)
        else:
            self.next_button = Button((SCREEN_WIDTH - 200) // 2, 620, 200, 50, "ДАЛЕЕ", None)

    def _get_options_for_step(self, step_id):
        if step_id in self.image_data and self.image_data[step_id].get("items_to_click"):
            return []

        options_map = {
            "1": self.items.get("clothes", []), "2": self.items.get("shoes", []),
            "3": self.items.get("hats", []), "4": self.items.get("jewerly", []),
            "5": self.items.get("handwashing", []), "7": ["Перейти в цех"],
            "17": ["Подать суп на бракераж"]
        }
        return options_map.get(step_id, ["Далее"])

    def _create_option_buttons(self, options):
        self.option_buttons = []
        for i, option in enumerate(options[:10]):
            btn = Button((SCREEN_WIDTH - 500) // 2, 250 + i * 45, 500, 35, option, None)
            self.option_buttons.append(btn)

    def _create_control_buttons(self):
        self.next_button = Button((SCREEN_WIDTH - 200) // 2, 620, 200, 50, "ДАЛЕЕ", None)
        self.retry_button = Button((SCREEN_WIDTH - 250) // 2, 620, 250, 50, "ПОПРОБОВАТЬ СНОВА", None)

    def handle_event(self, event):
        if self.confirmation.is_waiting: return
        if self.waiting_for_next:
            if self.next_button.handle_event(event): self.next_step()
            return
        if self.is_error:
            if self.retry_button.handle_event(event): self.load_step(self.current_step)
            return
        if self.total_items_to_collect > 0 and not self.waiting_for_next and not self.is_error:
            if self.next_button.handle_event(event):
                self.check_completion()
                return

        for zone in self.click_zones:
            if zone.handle_event(event):
                self.check_zone_click(zone)
                return

        for i, btn in enumerate(self.option_buttons):
            if btn.handle_event(event):
                self.check_answer(i, btn.text)
                break

    def check_completion(self):
        if self.correct_count == self.total_items_to_collect:
            self.waiting_for_next = True
            self.next_button = Button((SCREEN_WIDTH - 200) // 2, 620, 200, 50, "ДАЛЕЕ", None)
        else:
            self.is_error = True
            self.error_counter.add_error()
    
    def next_step(self):
        self.step_index += 1
        if self.step_index < len(self.steps_order):
            self.load_step(self.steps_order[self.step_index])
        else:
            self.show_end_screen()

    def check_answer(self, idx, text):
        if self.validator.validate(self.current_step, text):
            if idx is not None: self.option_buttons[idx].status = "correct"
            self.waiting_for_next = True
        else:
            self.is_error = True
            self.error_counter.add_error()
            if idx is not None: self.option_buttons[idx].status = "wrong"

    def check_zone_click(self, zone):
        if zone.is_correct:
            return  # уже отмечено
        if self.validator.validate(self.current_step, zone.action_id):
            zone.is_correct = True
            self.correct_count += 1

    def update(self, dt):
        pass

    def draw(self, screen):
        if self.current_step == "4":
            screen.blit(self.bg_image, (0, 0))

            if self.char_image:
                hero_rect_w, hero_rect_h, hero_rect_x, hero_rect_y = 320, 660, 50, 40
                pygame.draw.rect(screen, (255, 255, 255), (hero_rect_x, hero_rect_y, hero_rect_w, hero_rect_h),
                                 border_radius=20)

                target_h = int(hero_rect_h * 0.95)
                aspect_ratio = self.char_image.get_width() / self.char_image.get_height()
                target_w = int(target_h * aspect_ratio)
                scaled_char = pygame.transform.smoothscale(self.char_image, (target_w, target_h))

                screen.blit(scaled_char,
                            (hero_rect_x + (hero_rect_w - target_w) // 2, hero_rect_y + (hero_rect_h - target_h) // 2))

            # Отрисовка вопроса через класс кнопки (узкая плашка)
            if self.question_button:
                self.question_button.draw(screen)
        else:
            screen.fill((240, 240, 255))
            if self.question_button:
                # В обычном режиме центрируем вопрос сверху
                self.question_button.rect.x = (SCREEN_WIDTH - self.question_button.rect.width) // 2
                self.question_button.rect.y = 100
                self.question_button.draw(screen)

        err_text = self.font_small.render(f"Ошибок: {self.error_counter.count}", True, (231, 76, 60))
        screen.blit(err_text, (SCREEN_WIDTH - 120, 20))

        for btn in self.option_buttons: btn.draw(screen)
        if self.waiting_for_next:
            self.next_button.draw(screen)
        elif self.is_error:
            self.retry_button.draw(screen)
        elif self.total_items_to_collect > 0:
            self.next_button.draw(screen)

        # Рисуем галочки на отмеченных зонах
        if self.checkmark_img:
            for zone in self.click_zones:
                if zone.is_correct:
                    x = zone.rect.x + (zone.rect.width - self.checkmark_img.get_width()) // 2
                    y = zone.rect.y + (zone.rect.height - self.checkmark_img.get_height()) // 2
                    screen.blit(self.checkmark_img, (x, y))
