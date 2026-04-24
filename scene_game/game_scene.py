import pygame
import json
from pathlib import Path
from core_game.scene import Scene
from ui.button import Button
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from game_logic.validator import ActionValidator
from game_logic.scoring import ErrorCounter
from game_logic.confirmation_handler import ConfirmationHandler
from ui.dialog_box import DialogBox
from ui.input_box import InputBox


class GameScene(Scene):
    def __init__(self, scene_manager, state_manager):
        super().__init__(scene_manager, state_manager)

        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"

        with open(self.DATA_DIR / "items.json", "r", encoding="utf-8") as f:
            self.items = json.load(f)
        with open(self.DATA_DIR / "image.json", "r", encoding="utf-8") as f:
            self.image_data = json.load(f)

            # Загружаем инструкцию
        with open(self.DATA_DIR / "start_info.json", "r", encoding="utf-8") as f:
            self.info_data = json.load(f)

        self.validator = ActionValidator("data/scenarios.json")
        self.error_counter = ErrorCounter()
        self.confirmation = ConfirmationHandler()

        self.steps_order = ['0', "0.1","1", "2", "3", "4", "5", "6_1", "6_2", "6_3", "7", "8", "9", "10", "11", "12_1", "12_2",
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

        # Создаем поле ввода (центрируем по экрану)
        self.name_input = InputBox((SCREEN_WIDTH - 300) // 2, 450, 300, 50, self.font_medium)

        self.load_step(self.current_step)



    def load_step(self, step_id):
        self.current_step = step_id
        self.waiting_for_next = False
        self.is_error = False
        self.click_zones = []
        self.bg_image = None
        self.char_image = None
        self.extra_image = None
        self.extra_image_pos = (0, 0)
        # Важно: обнуляем кнопку вопроса, чтобы она не тянулась из прошлого шага
        self.question_button = None

        step_data = self.validator.get_step(step_id)
        if not step_data:
            self.show_end_screen()
            return

        visuals = self.image_data.get(step_id, {})

        try:
            # 1. Загрузка фона
            if "background" in visuals:
                bg_path = self.DATA_DIR / visuals["background"]
                if bg_path.exists():
                    self.bg_image = pygame.image.load(str(bg_path))
                    self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

            # 2. Загрузка персонажа
            if "character" in visuals:
                char_path = self.DATA_DIR / visuals["character"]
                if char_path.exists():
                    self.char_image = pygame.image.load(str(char_path))

            # 3. Загрузка дополнительной картинки
            if "extra_image" in visuals:
                ext_data = visuals["extra_image"]
                ext_path = self.DATA_DIR / ext_data["path"]
                if ext_path.exists():
                    self.extra_image = pygame.image.load(str(ext_path))
                    self.extra_image_pos = ext_data["pos"]

            # 4. Зоны клика
            for item in visuals.get("items_to_click", []):
                r = item["rect"]
                zone = Button(r[0], r[1], r[2], r[3], "", None)
                zone.action_id = item["id"]
                self.click_zones.append(zone)

        except Exception as e:
            print(f"Ошибка загрузки ресурсов: {e}")

        # --- ПРОВЕРКА СУЩЕСТВОВАНИЯ ВОПРОСА ---
        self.current_question = step_data.get("question", "").strip()

        # Если строка вопроса не пустая, создаем кнопку
        if self.current_question:
            text_surf = self.font_medium.render(self.current_question, True, (0, 0, 0))
            q_width = text_surf.get_width() + 40
            q_height = text_surf.get_height() + 20
            # Центрируем по горизонтали, Y ставим 50 (или любой другой из конфига)
            self.question_button = Button((SCREEN_WIDTH - q_width) // 2, 50, q_width, q_height, self.current_question,
                                          None)

        # Логика кнопок ответов
        options = self._get_options_for_step(step_id)
        custom_buttons_pos = visuals.get("buttons_pos", None)
        default_pos = visuals.get("options_pos", [(SCREEN_WIDTH - 500) // 2, 250])
        start_x, start_y = default_pos[0], default_pos[1]

        self._create_option_buttons(options, start_x, start_y, custom_buttons_pos)
        self._create_control_buttons()

    def _get_options_for_step(self, step_id):
        if step_id in self.image_data and self.image_data[step_id].get("items_to_click"):
            return []

        options_map = {
            "0": self.items.get("introduction",[]), "0.1": self.items.get("introduction_2",[]),
            "1": self.items.get("clothes", []), "2": self.items.get("shoes", []),
            "3": self.items.get("hats", []), "4": self.items.get("jewerly", []),
            "5": self.items.get("handwashing", []), "7": ["Перейти в цех"],
            "17": ["Подать суп на бракераж"]
        }
        return options_map.get(step_id, ["Далее"])

    def _create_option_buttons(self, options, start_x, start_y, custom_positions=None):
        self.option_buttons = []
        current_y = start_y

        for i, option in enumerate(options[:10]):
            # Если в JSON прописаны координаты для ЭТОЙ конкретной кнопки (по индексу)
            if custom_positions and i < len(custom_positions):
                x, y = custom_positions[i]
            else:
                x, y = start_x, current_y

            btn = DialogBox(x, y, 500, 35, option, None)
            self.option_buttons.append(btn)

            # Обновляем Y для следующей кнопки (если нет кастомной позиции)
            current_y += btn.rect.height + 10

    def _create_control_buttons(self):
        self.next_button = Button((SCREEN_WIDTH - 200) // 2, 620, 200, 50, "ДАЛЕЕ", None)
        self.retry_button = Button((SCREEN_WIDTH - 250) // 2, 620, 250, 50, "ПОПРОБОВАТЬ СНОВА", None)

    def handle_event(self, event):
        if self.confirmation.is_waiting: return

        # Обработка ввода текста на нужном шаге
        if self.current_step == "0.1":
            self.name_input.handle_event(event)

        if self.waiting_for_next:
            if self.next_button.handle_event(event):
                self.next_step()
            return

        if self.is_error:
            if self.retry_button.handle_event(event):
                self.load_step(self.current_step)
            return

        # Зоны клика и кнопки
        for zone in self.click_zones:
            if zone.handle_event(event):
                self.check_answer(None, zone.action_id)
                return

        for i, btn in enumerate(self.option_buttons):
            if btn.handle_event(event):
                self.check_answer(i, btn.text)
                break

    def next_step(self):
        self.step_index += 1
        if self.step_index < len(self.steps_order):
            self.load_step(self.steps_order[self.step_index])
        else:
            self.show_end_screen()

    def check_answer(self, idx, text):
        if self.validator.validate(self.current_step, text):
            # Мгновенный переход для вступления (0) и ввода имени (0.1)
            if self.current_step in ["0", "0.1"]:
                if self.current_step == "0.1":
                    player_name = self.name_input.text.strip()
                    if not player_name:
                        self.name_input.is_error = True
                        return  # Не даем нажать, если имя пустое

                    # Сохраняем имя и сразу идем к игре
                    self.name_input.is_error = False
                    self.state_manager.progress["player_name"] = player_name

                self.next_step()
                return

            # Для всех остальных шагов оставляем старую логику с кнопкой "Далее"
            if idx is not None:
                self.option_buttons[idx].status = "correct"
            self.waiting_for_next = True
        else:
            self.is_error = True
            self.error_counter.add_error()
            if idx is not None:
                self.option_buttons[idx].status = "wrong"



    def update(self, dt):
        pass

    def draw(self, screen):
        # 1. Отрисовка фона и персонажа
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
            if self.extra_image:
                screen.blit(self.extra_image, self.extra_image_pos)

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

            # --- БЛОК ИНСТРУКЦИИ (ШАГ 0.1) ---
            if self.current_step == "0.1":
                # Затемнение заднего плана
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))

                # Окно инструкции
                box_w, box_h = 750, 520
                box_x, box_y = (SCREEN_WIDTH - box_w) // 2, (SCREEN_HEIGHT - box_h) // 2
                pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_w, box_h), border_radius=20)

                # 1. Заголовок
                title = self.info_data["tutorial"]["title"]
                title_surf = self.font_medium.render(title, True, (0, 0, 0))
                screen.blit(title_surf, ((SCREEN_WIDTH - title_surf.get_width()) // 2, box_y + 30))

                # 2. ЦИКЛ ОТРИСОВКИ ТЕКСТА (пункты 1-4)
                y_text = box_y + 100
                for line in self.info_data["tutorial"]["text"]:
                    line_surf = self.font_small.render(line, True, (40, 40, 40))
                    screen.blit(line_surf, (box_x + 40, y_text))
                    y_text += 40  # Расстояние между строками

                # 3. Управление (controls)
                controls_text = self.info_data.get("tutorial", {}).get("controls", "")
                if controls_text:
                    ctrl_surf = self.font_small.render(controls_text, True, (100, 100, 100))
                    screen.blit(ctrl_surf, (box_x + 40, y_text + 10))

                # 4. Поле ввода имени
                prompt_surf = self.font_small.render("Введите ваше имя:", True, (0, 0, 0))
                screen.blit(prompt_surf, ((SCREEN_WIDTH - prompt_surf.get_width()) // 2, box_y + 360))

                # Привязываем координаты InputBox к нашему окну
                self.name_input.rect.x = (SCREEN_WIDTH - self.name_input.rect.width) // 2
                self.name_input.rect.y = box_y + 390
                self.name_input.draw(screen)
            # --- КОНЕЦ БЛОКА ИНСТРУКЦИИ ---

            if self.question_button:
                self.question_button.draw(screen)
        else:
            # Если нет фона
            screen.fill((240, 240, 255))
            if self.question_button:
                self.question_button.rect.x = (SCREEN_WIDTH - self.question_button.rect.width) // 2
                self.question_button.rect.y = 100
                self.question_button.draw(screen)

        # Отрисовка счетчика ошибок
        err_text = self.font_small.render(f"Ошибок: {self.error_counter.count}", True, (231, 76, 60))
        screen.blit(err_text, (SCREEN_WIDTH - 120, 20))

        # Отрисовка кнопок ответов и управления
        for btn in self.option_buttons:
            btn.draw(screen)

        if self.waiting_for_next:
            self.next_button.draw(screen)
        elif self.is_error:
            self.retry_button.draw(screen)