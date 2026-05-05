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

        # Загрузка данных
        with open(self.DATA_DIR / "items.json", "r", encoding="utf-8") as f:
            self.items = json.load(f)
        with open(self.DATA_DIR / "image.json", "r", encoding="utf-8") as f:
            self.image_data = json.load(f)
        with open(self.DATA_DIR / "start_info.json", "r", encoding="utf-8") as f:
            self.info_data = json.load(f)
        with open(self.DATA_DIR / "scene_text.json", "r", encoding="utf-8") as f:
            self.text = json.load(f)

        self.validator = ActionValidator("data/scenarios.json")
        self.error_counter = ErrorCounter()
        self.confirmation = ConfirmationHandler()

        # Новые поля для механики множественного клика
        self.correct_count = 0
        self.total_items_to_collect = 0
        self.checkmark_img = None

        self.multi_select_mode = False
        self.selected_options = set()  # индексы выбранных опций
        self.waiting_for_next = False

        # Порядок сцен (включая вступление)
        # self.steps_order = [
        #     '0', '0.1', '1', '2', '3', '4', '5', '6_1', '6_2', '6_3',
        #     '7', '8', '9', '10', '11', '12_1', '12_2', '12_3', '12_4',
        #     '13', '14', '15', '16', '17', '18'
        # ]
        self.steps_order = [
            '0', '0.1', '1', '2', '3', '4', '5_1', '5', '6', '6.1', '6.2', '6.3',
            '7', '8', '8.1', '9', '9.1', '10', '10.1', '11', '12.1', '12.2', '12.3', '12.4',
            '13', '13.1', '14', '15', '16', '17', '18'
        ]
        self.step_index = 0
        self.current_step = self.steps_order[0]

        self.hero_rect = (50, 40, 320, 660)

        self.bg_image = None
        self.char_image = None
        self.extra_image = None
        self.extra_image_pos = (0, 0)
        self.click_zones = []
        self.option_buttons = []
        self.question_button = None

        self.waiting_for_next = False
        self.is_error = False

        self.font_medium = pygame.font.SysFont("arial", 24)
        self.font_small = pygame.font.SysFont("arial", 24)

        # Получаем данные для сцены 0.1
        scene_cfg = self.image_data.get("0.1", {})
        # Берем координаты из JSON. Если их там нет, используем 450 как страховку
        coords = scene_cfg.get("input_pos", [390, 450, 500, 50])

        # Валидатор char.isalpha() разрешает только буквы (русские и английские)
        # Дополнительно разрешаем пробел, если он нужен в имени
        self.name_input = InputBox(
            coords[0], coords[1], coords[2], coords[3],
            self.font_medium,
            validator=lambda char: char.isalpha() or char == " "
        )
        # В методе __init__ класса GameScene
        self.sequence_input = None  # Инициализируем пустой переменной
        self.sequence_label = "Введите правильную последовательность:"

        self.sequence_next_button = None  # Добавьте эту строку
        self.sequence_input = None

        self.current_question = ""
        self.next_button = None

        self.final_button = None
        self.showing_results = False

        # Загрузка изображения галочки
        try:
            check_path = self.DATA_DIR / "images" / "scene_4" / "галочка.png"
            self.checkmark_img = pygame.image.load(str(check_path))
            self.checkmark_img = pygame.transform.scale(self.checkmark_img, (40, 40))
        except Exception as e:
            print(f"Ошибка загрузки галочка.png: {e}")
            self.checkmark_img = None

        self.multi_select_mode = False
        self.selected_options = set()
        self.final_button = None
        self.showing_results = False

        self.option_buttons = []
        self.current_question = None
        self.next_button = None

        self.load_step(self.current_step)

    def load_step(self, step_id):
        self.current_step = step_id
        self.waiting_for_next = False
        self.is_error = False
        self.click_zones = []
        self.option_buttons = []
        self.bg_image = None
        self.char_image = None
        self.extra_image = None
        self.question_button = None
        self.correct_count = 0
        self.total_items_to_collect = 0
        self.multi_select_mode = False
        self.selected_options.clear()

        self.multi_select_mode = False
        self.selected_options = set()
        self.final_button = None
        self.showing_results = False

        self.option_buttons = []
        self.current_question = None
        self.next_button = None

        step_data = self.validator.get_step(step_id)
        if not step_data:
            self.show_end_screen()
            return

        visuals = self.image_data.get(step_id, {})

        self.final_button = None
        self.showing_results = False

        try:
            # Фон
            if "background" in visuals:
                bg_path = self.DATA_DIR / visuals["background"]
                if bg_path.exists():
                    self.bg_image = pygame.image.load(str(bg_path))
                    self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

            # Персонаж
            if "character" in visuals:
                char_path = self.DATA_DIR / visuals["character"]
                if char_path.exists():
                    self.char_image = pygame.image.load(str(char_path))

            # Дополнительное изображение
            if "extra_image" in visuals:
                ext_data = visuals["extra_image"]
                ext_path = self.DATA_DIR / ext_data["path"]
                if ext_path.exists():
                    self.extra_image = pygame.image.load(str(ext_path))
                    self.extra_image_pos = ext_data["pos"]

            # Зоны клика (координаты относительно области персонажа)
            hx, hy, hw, hh = self.hero_rect      # (50, 40, 320, 660)
            for item in visuals.get("items_to_click", []):
                r = item["rect"]
                zone = Button(hx + r[0], hy + r[1], r[2], r[3], "", None)
                zone.action_id = item["id"]
                zone.is_correct = False
                self.click_zones.append(zone)

        except Exception as e:
            print(f"Ошибка загрузки ресурсов: {e}")

        # Определяем, является ли сцена множественным выбором предметов
        if self.click_zones:
            self.total_items_to_collect = len(self.click_zones)
            self.option_buttons = []   # опции не нужны
        else:
            # Обычные текстовые варианты
            options = self._get_options_for_step(step_id)

            correct = step_data.get("correct")
            self.multi_select_mode = isinstance(correct, list)
            if self.multi_select_mode:
                self.total_items_to_collect = len(options)

            custom_buttons_pos = visuals.get("buttons_pos", None)
            default_pos = visuals.get("options_pos", [(SCREEN_WIDTH - 500) // 2, 250])
            start_x, start_y = default_pos[0], default_pos[1]
            self._create_option_buttons(options, start_x, start_y, custom_buttons_pos)

        # Кнопка вопроса (если есть текст вопроса)
        self.current_question = step_data.get("question", "").strip()
        if self.current_question:
            text_surf = self.font_medium.render(self.current_question, True, (0, 0, 0))
            q_width = text_surf.get_width() + 40
            q_height = text_surf.get_height() + 20

            # Позиция вопроса: из конфига или по умолчанию
            if "question_pos" in visuals:
                q_x, q_y = visuals["question_pos"]
            else:
                q_x = (SCREEN_WIDTH - q_width) // 2
                q_y = 50 if self.bg_image else 100

            self.question_button = Button(q_x, q_y, q_width, q_height, self.current_question, None)

        # Кнопки управления
        self._create_control_buttons()

    def _get_options_for_step(self, step_id):
        # Если сцена содержит кликабельные зоны – опции не нужны
        if step_id in self.image_data and self.image_data[step_id].get("items_to_click"):
            return []

        options_map = {
            "0": self.items.get("introduction", []),
            "0.1": self.items.get("introduction_2", []),
            "1": self.items.get("clothes", []),
            "2": self.items.get("shoes", []),
            "3": self.items.get("hats", []),
            "4": self.items.get("jewerly", []),  # сюда не попадём из-за проверки выше
            "5_1":  ["Нажмите, чтобы продолжить"],
            "5": self.items.get("handwashing", []),
            "6": ["Нажмите, чтобы продолжить"],
            "6.1": self.items.get("meat", []),
            "6.2": self.items.get("vegetables", []),
            "6.3": self.items.get("cereal", []),
            "7": ["Нажмите, чтобы продолжить"],
            "8": self.items.get("workshop", []),
            "8.1": ["Нажмите, чтобы продолжить"],
            "9": self.items.get("meat_workshop", []),
            "9.1": ["Нажмите, чтобы продолжить"],
            "10": self.items.get("workshop", []),
            "10.1": ["Нажмите, чтобы продолжить"],
            "11": self.items.get("vegetables_workshop", []),
            "12.1": self.items.get("cuts", []),
            "12.2": self.items.get("cuts", []),
            "12.3": self.items.get("cuts", []),
            "12.4": ["Нажмите, чтобы продолжить"],
            "13": self.items.get("workshop", []),
            "13.1": ["Нажмите, чтобы продолжить"],
            "14": self.items.get("dishes", []),
            "16": self.items.get("temperature", []),
            "17": ["Подать суп на бракераж"],
            "18": self.items.get("cleaning", []),
        }
        return options_map.get(step_id, ["Далее"])

    def _get_description_for_step(self, step_id):
        # Словарь сопоставления ID шага и ключей из scene_text.json
        descriptions_map = {

            "1": self.text.get("scene_1", ""),
            "2": self.text.get("scene_2", ""),
            "3": self.text.get("scene_3", ""),
            "4": self.text.get("scene_4", ""),
            "5_1": [],
            "5": self.text.get("scene_5", ""),
            "6": [],
            "6.1": self.text.get("scene_6.1", ""),
            "6.2": self.text.get("scene_6.2", ""),
            "6.3": self.text.get("scene_6.3", ""),
            "7": [],
            "8": self.text.get("scene_8", ""),
            "8.1": [],
            "9": self.text.get("scene_9", ""),
            "9.1": [],
            "10": self.text.get("scene_10", ""),
            "10.1": [],
            "11": self.text.get("scene_11", ""),
            "12.1": self.text.get("scene_12.1", ""),
            "12.2": self.text.get("scene_12.2", ""),
            "12.3": self.text.get("scene_12.3", ""),
            "12.4": [],
            "13": self.text.get("scene_13", ""),
            "13.1": [],
            "14": self.text.get("scene_14", ""),
            "15": self.text.get("scene_15", ""),
            "16": self.text.get("scene_16", ""),
            "17": self.text.get("scene_17", ""),
            "18": self.text.get("scene_18", ""),
        }
        return descriptions_map.get(step_id, "")

    def _create_option_buttons(self, options, start_x, start_y, custom_positions=None):
        self.option_buttons = []
        current_y = start_y

        for i, option in enumerate(options[:10]):
            if custom_positions and i < len(custom_positions):
                x, y = custom_positions[i]
            else:
                x, y = start_x, current_y

            btn = DialogBox(x, y, 500, 35, option, None)
            self.option_buttons.append(btn)
            current_y += btn.rect.height + 10

    def _create_control_buttons(self):
        # Для сцен с предметами используем кнопку "ПРОВЕРИТЬ", иначе "ДАЛЕЕ"
        if self.total_items_to_collect > 0 or self.multi_select_mode:
            btn_text = "ПРОВЕРИТЬ"
            btn_width = 250
        else:
            btn_text = "ДАЛЕЕ"
            btn_width = 200

        self.next_button = Button((SCREEN_WIDTH - btn_width) // 2, 620, btn_width, 50, btn_text, None)
        self.retry_button = Button((SCREEN_WIDTH - 250) // 2, 620, 250, 50, "ПОПРОБОВАТЬ СНОВА", None)

    def handle_event(self, event):

        # Если мы на 5-й сцене
        if self.current_step == "5":
            if self.sequence_input:
                self.sequence_input.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.sequence_next_button and self.sequence_next_button.rect.collidepoint(event.pos):
                    self.check_sequence_answer()
        # ОБЯЗАТЕЛЬНО ПОТОМ УДАЛИТЬ УБРАТЬ
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:
                self.next_step()
                return
        #

        if self.confirmation.is_waiting:
            return

        # Ввод имени на шаге 0.1
        if self.current_step == "0.1":
            self.name_input.handle_event(event)

        # Обработка кнопки "Далее", когда ожидаем перехода
        if self.waiting_for_next:
            if self.next_button.handle_event(event):
                self.next_step()
            return

        # Режим ошибки: только кнопка "Попробовать снова"
        if self.is_error:
            if self.retry_button.handle_event(event):
                self.load_step(self.current_step)
            return

        if self.multi_select_mode:
            if self.next_button and self.next_button.handle_event(event):
                self.check_multi_select()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.option_buttons):
                    if btn.rect.collidepoint(event.pos):
                        if i in self.selected_options:
                            self.selected_options.remove(i)
                            btn.status = "normal"  # "не выбрано"
                        else:
                            self.selected_options.add(i)
                            btn.status = "correct"  # подсвечиваем как выбранное
                        return

        # Множественный выбор предметов (зоны клика)

        if self.multi_select_mode:
            if self.next_button and self.next_button.handle_event(event):
                self.check_multi_select()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.option_buttons):
                    if btn.rect.collidepoint(event.pos):
                        if i in self.selected_options:
                            self.selected_options.remove(i)
                            btn.status = "normal"
                        else:
                            self.selected_options.add(i)
                            btn.status = "correct"
                        return

        if self.total_items_to_collect > 0:
            # Прямая проверка попадания мыши в зону (без callback)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for zone in self.click_zones:
                    if zone.rect.collidepoint(mouse_pos):
                        self.check_zone_click(zone)
                        return
            # Клик по кнопке "ПРОВЕРИТЬ" (или "ДАЛЕЕ" после завершения)
            if self.next_button.handle_event(event):
                self.check_completion()
                return
            # Все остальные события в этом режиме игнорируем
            return

        # Обычные кнопки ответов
        for i, btn in enumerate(self.option_buttons):
            if btn.handle_event(event):
                self.check_answer(i, btn.text)
                break

        if self.final_button and self.final_button.handle_event(event):
            self.showing_results = True
            return

        if self.showing_results:
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                self.show_end_screen()
            return

    def check_answer(self, idx, text):
        if self.validator.validate(self.current_step, text):
            # Мгновенный переход для вступления
            if self.current_step in ["0", "0.1", "5_1", "6", "7", "8.1", "9.1", "10.1", "12.4", "13.1"]:
                if self.current_step == "0.1":
                    player_name = self.name_input.text.strip()
                    if not player_name:
                        self.name_input.is_error = True
                        return
                    self.name_input.is_error = False
                    self.state_manager.progress["player_name"] = player_name

                self.next_step()
                return

            # Обычный правильный ответ
            if idx is not None:
                self.option_buttons[idx].status = "correct"
            self.waiting_for_next = True
        else:
            self.is_error = True
            self.error_counter.add_error()
            if idx is not None:
                self.option_buttons[idx].status = "wrong"

    def check_zone_click(self, zone):
        """Обработка клика по предмету на персонаже."""
        if zone.is_correct:
            return

        # Получаем эталонный ответ из сценария
        step_data = self.validator.get_step(self.current_step)
        correct = step_data.get("correct", [])

        # Если correct — список, проверяем вхождение action_id в этот список
        if isinstance(correct, list):
            normalized_action = zone.action_id.strip().lower()
            allowed_ids = [item.strip().lower() for item in correct]
            if normalized_action in allowed_ids:
                zone.is_correct = True
                self.correct_count += 1
        else:
            # Для строк, чисел, булевых — используем стандартную валидацию
            if self.validator.validate(self.current_step, zone.action_id):
                zone.is_correct = True
                self.correct_count += 1

    def check_completion(self):
        """Проверка, все ли правильные предметы выбраны."""
        if self.correct_count == self.total_items_to_collect:
            self.waiting_for_next = True
            # Меняем кнопку на "ДАЛЕЕ" для продолжения
            btn_width = 200
            self.next_button = Button((SCREEN_WIDTH - btn_width) // 2, 620, btn_width, 50, "ДАЛЕЕ", None)
        else:
            self.is_error = True
            self.error_counter.add_error()

    def next_step(self):
        self.step_index += 1
        if self.step_index < len(self.steps_order):
            self.load_step(self.steps_order[self.step_index])
        else:
            self.show_end_screen()
            # Сразу после изменения шага проверяем:
        if self.current_step == "5":
            self.setup_step_5()

    def setup_step_5(self):
        # Берем координаты из JSON
        pos = self.image_data["5"].get("input_pos", [390, 450, 400, 50])

        # Создаем InputBox с валидатором только для цифр
        self.sequence_input = InputBox(
            pos[0], pos[1], pos[2], pos[3],
            self.font_medium,
            validator=lambda char: char.isdigit()
        )

        # Создаем кнопку "Далее" рядом (координаты можно взять из JSON или рассчитать)
        btn_pos = self.image_data["5"].get("next_button_pos", [765, 550]) # ЗАЧЕМ ЭТО????
        self.sequence_next_button = Button(130, 610, 250, 50, "Далее", None)

    def check_sequence_answer(self):
        # 1. Получаем правильный ответ. В вашем классе это self.validator.actions
        # Используем .get("5", {}), чтобы избежать ошибки, если шага "5" нет в JSON
        step_data = self.validator.actions.get("5", {})
        correct_answer = step_data.get("correct", "")

        # 2. Получаем ввод пользователя
        user_answer = self.sequence_input.text.strip()

        # 3. Проверка
        # Сравниваем как строки. Если нужно игнорировать пробелы, можно добавить .replace(" ", "")
        if user_answer == str(correct_answer) and user_answer != "":
            self.sequence_input = None
            self.sequence_next_button = None
            self.next_step()
        else:
            # Если неверно или пусто — подсвечиваем красным
            self.sequence_input.is_error = True

            # Увеличиваем счетчик ошибок, если он у вас инициализирован
            if hasattr(self, 'error_counter'):
                self.error_counter.add_error()

    def update(self, dt):
        pass

    def draw_description_block(self, screen, text, rect_coords, font):
        """
        rect_coords: (x, y, ширина, высота)
        """
        # Отрисовка подложки (как в инструкции шага 0.1)
        pygame.draw.rect(screen, (255, 255, 255), rect_coords, border_radius=15)
        pygame.draw.rect(screen, (0, 0, 0), rect_coords, 2, border_radius=15)

        x, y, w, h = rect_coords
        padding = 20
        current_y = y + padding
        max_w = w - (padding * 2)

        # Обработка \n и автоматический перенос
        paragraphs = text.split('\n')
        for paragraph in paragraphs:
            words = paragraph.split(' ')
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                if font.size(test_line)[0] < max_w:
                    current_line = test_line
                else:
                    surf = font.render(current_line.strip(), True, (0, 0, 0))
                    screen.blit(surf, (x + padding, current_y))
                    current_y += font.get_linesize()
                    current_line = word + " "

            if current_line:
                surf = font.render(current_line.strip(), True, (0, 0, 0))
                screen.blit(surf, (x + padding, current_y))
                current_y += font.get_linesize()

    def draw(self, screen):
        # Фон
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
            if self.extra_image:
                screen.blit(self.extra_image, self.extra_image_pos)

            # Персонаж
            if self.char_image:
                hero_rect_w, hero_rect_h, hero_rect_x, hero_rect_y = 320, 660, 50, 40
                pygame.draw.rect(screen, (255, 255, 255),
                                 (hero_rect_x, hero_rect_y, hero_rect_w, hero_rect_h),
                                 border_radius=20)
                target_h = int(hero_rect_h * 0.95)
                aspect_ratio = self.char_image.get_width() / self.char_image.get_height()
                target_w = int(target_h * aspect_ratio)
                scaled_char = pygame.transform.smoothscale(self.char_image, (target_w, target_h))
                screen.blit(scaled_char,
                            (hero_rect_x + (hero_rect_w - target_w) // 2,
                             hero_rect_y + (hero_rect_h - target_h) // 2))

            # ВЫДЕЛЕНИЕ ЗОН УБРАТЬ УДАЛИТЬ
            for zone in self.click_zones:
                pygame.draw.rect(screen, (0, 0, 0), zone.rect, 2)

            description_text = self._get_description_for_step(self.current_step)
            if description_text and self.current_step != "0.1":
                visuals = self.image_data.get(self.current_step, {})
                coords = visuals.get("text_rect", [400, 50, 500, 150])
                text_rect = pygame.Rect(coords)
                self.draw_description_block(screen, description_text, text_rect, self.font_small)

            # Окно инструкции для шага 0.1
            if self.current_step == "0.1":
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))

                box_w, box_h = 920, 520
                box_x, box_y = (SCREEN_WIDTH - box_w) // 2, (SCREEN_HEIGHT - box_h) // 2
                pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_w, box_h), border_radius=20)

                title = self.info_data["tutorial"]["title"]
                title_surf = self.font_medium.render(title, True, (0, 0, 0))
                screen.blit(title_surf, ((SCREEN_WIDTH - title_surf.get_width()) // 2, box_y + 30))

                y_text = box_y + 100
                for line in self.info_data["tutorial"]["text"]:
                    line_surf = self.font_small.render(line, True, (40, 40, 40))
                    screen.blit(line_surf, (box_x + 40, y_text))
                    y_text += 40

                controls_text = self.info_data.get("tutorial", {}).get("controls", "")
                if controls_text:
                    ctrl_surf = self.font_small.render(controls_text, True, (100, 100, 100))
                    screen.blit(ctrl_surf, (box_x + 40, y_text + 10))

                # Текст подсказки перед вводом
                prompt_surf = self.font_small.render("Введите ваше имя:", True, (0, 0, 0))
                # Центрируем подсказку над полем ввода (по Y берем позицию поля - 30)
                screen.blit(prompt_surf, ((SCREEN_WIDTH - prompt_surf.get_width()) // 2, self.name_input.rect.y - 30))

                # УДАЛЕНО: принудительное переопределение self.name_input.rect.y
                # Теперь отрисовка просто использует те координаты, что заданы в __init__
                self.name_input.draw(screen)

        else:
            screen.fill((240, 240, 255))
            if self.question_button:
                self.question_button.rect.x = (SCREEN_WIDTH - self.question_button.rect.width) // 2
                self.question_button.rect.y = 100
                self.question_button.draw(screen)

        if self.bg_image and self.question_button and self.current_step != "0.1":
            self.question_button.draw(screen)

        if self.current_step == "5" and self.sequence_input:
            # Рисуем подпись
            label_surf = self.font_small.render(self.sequence_label, True, (0, 0, 0))
            # Рисуем чуть выше поля ввода
            screen.blit(label_surf, (self.sequence_input.rect.x, self.sequence_input.rect.y - 30))

            # Рисуем само поле и кнопку
            self.sequence_input.draw(screen)
            self.sequence_next_button.draw(screen)

        err_text = self.font_small.render(f"Ошибок: {self.error_counter.count}", True, (231, 76, 60))
        screen.blit(err_text, (SCREEN_WIDTH - 120, 20))

        if self.option_buttons and not self.final_button:
            for btn in self.option_buttons:
                btn.draw(screen)

        if self.waiting_for_next:
            self.next_button.draw(screen)
        elif self.is_error:
            self.retry_button.draw(screen)
        elif self.total_items_to_collect > 0:
            self.next_button.draw(screen)

        if self.final_button:
            self.final_button.draw(screen)

        if self.checkmark_img:
            for zone in self.click_zones:
                if zone.is_correct:
                    x = zone.rect.x + (zone.rect.width - self.checkmark_img.get_width()) // 2
                    y = zone.rect.y + (zone.rect.height - self.checkmark_img.get_height()) // 2
                    screen.blit(self.checkmark_img, (x, y))

        if self.showing_results:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            box_w, box_h = 600, 400
            box_x, box_y = (SCREEN_WIDTH - box_w) // 2, (SCREEN_HEIGHT - box_h) // 2
            pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_w, box_h), border_radius=20)

            name = self.state_manager.progress.get("player_name", "Игрок")
            name_surf = self.font_medium.render(f"Повар: {name}", True, (0, 0, 0))
            screen.blit(name_surf, (box_x + 50, box_y + 80))

            err_count = self.error_counter.count
            err_surf = self.font_medium.render(f"Допущено ошибок: {err_count}", True, (231, 76, 60))
            screen.blit(err_surf, (box_x + 50, box_y + 160))
            hint_surf = self.font_small.render("Нажмите любую кнопку мыши, чтобы завершить", True, (100, 100, 100))
            screen.blit(hint_surf, (box_x + 50, box_y + 280))

    def check_multi_select(self):
        selected_texts = [self.option_buttons[i].text for i in self.selected_options]
        if self.validator.validate(self.current_step, selected_texts):
            if self.current_step == "18":
                self.multi_select_mode = False
                self.total_items_to_collect = 0
                self.option_buttons = []
                self.final_button = Button(
                    (SCREEN_WIDTH - 250) // 2, 620, 250, 50,
                    "ПОДВЕСТИ ИТОГИ", None
                )
            else:
                self.waiting_for_next = True
                self.multi_select_mode = False
                self.total_items_to_collect = 0
                self.option_buttons = []
                self._create_control_buttons()
        else:
            self.is_error = True
            self.error_counter.add_error()

    def show_end_screen(self):
        pygame.quit()
        exit()
