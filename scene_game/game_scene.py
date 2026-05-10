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
from utils import resource_path


class GameScene(Scene):
    def __init__(self, scene_manager, state_manager):
        super().__init__(scene_manager, state_manager)
        self.BASE_DIR = resource_path("")
        self.DATA_DIR = self.BASE_DIR / "data"
        self.ASSETS_DIR = self.BASE_DIR / "assets"


        with open(self.DATA_DIR / "items.json", "r", encoding="utf-8") as f:
            self.items = json.load(f)
        with open(self.DATA_DIR / "image.json", "r", encoding="utf-8") as f:
            self.image_data = json.load(f)
        with open(self.DATA_DIR / "start_info.json", "r", encoding="utf-8") as f:
            self.info_data = json.load(f)
        with open(self.DATA_DIR / "scene_text.json", "r", encoding="utf-8") as f:
            self.text = json.load(f)
        with open(self.DATA_DIR / "instruction.json", "r", encoding="utf-8") as f:
            self.instructions = json.load(f)

        self.show_help_window = False
        self.help_button = Button(20, 20, 40, 40, "?", None)
        self.validator = ActionValidator(str(resource_path("data/scenarios.json")))
        self.error_counter = ErrorCounter()
        self.error_button = Button(SCREEN_WIDTH - 250, 10, 240, 36,
                                   f"Ошибок: {self.error_counter.count}", font_path=None)
        self.confirmation = ConfirmationHandler()
        self.correct_count = 0
        self.total_items_to_collect = 0
        self.checkmark_img = None
        self.multi_select_mode = False
        self.selected_options = set()
        self.waiting_for_next = False
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
        scene_cfg = self.image_data.get("0.1", {})
        coords = scene_cfg.get("input_pos", [390, 450, 500, 50])
        self.name_input = InputBox(coords[0], coords[1], coords[2], coords[3], self.font_medium,
                                   validator=lambda char: char.isalpha() or char == " " or char == "-")
        self.sequence_input = None
        self.sequence_label = "Введите правильную последовательность:"
        self.sequence_next_button = None
        self.sequence_locked = False
        self.sequence_input = None
        self.current_question = ""
        self.next_button = None
        self.final_button = None
        self.showing_results = False
        self.cooking_ingredients = ["Кура", "Картофель", "Морковь и Репчатый лук", "Огурцы солёные", "Перловая крупа"]
        self.cooking_flags = {ing: False for ing in self.cooking_ingredients}
        self.cooking_actions = {ing: [] for ing in self.cooking_ingredients}
        self.overlay_active = False
        self.overlay_ingredient = None
        self.overlay_step = 1
        self.overlay_buttons = []
        self.overlay_texts = []
        self.overlay_reset_btn = None

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
        self.sequence_label_text = None
        self.label_rect = None
        self.show_help_window = False
        self.help_button = Button(20, 20, 40, 40, "?", None)
        self.scene15_reset_button = None
        self.cooking_validation_passed = False
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
        self.overlay_active = False
        self.overlay_ingredient = None
        self.overlay_step = 1
        self.overlay_buttons = []
        self.overlay_texts = []
        self.overlay_reset_btn = None

        if step_id == "15":
            ingredients_left = [ing for ing in self.cooking_ingredients if not self.cooking_flags[ing]]
            self._create_ingredient_buttons(ingredients_left)
            visuals = self.image_data.get("15", {})
            if "background" in visuals:
                bg_path = self.DATA_DIR / visuals["background"]
                if bg_path.exists():
                    self.bg_image = pygame.image.load(str(bg_path))
                    self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            check_btn_pos = visuals.get("check_button_pos", [(SCREEN_WIDTH - 500) // 2, 620])
            self.next_button = Button(
                check_btn_pos[0], check_btn_pos[1], 500, 50,
                "ПРОВЕРИТЬ" if not self.cooking_validation_passed else "ДАЛЕЕ",
                None
            )

            if self.current_question:
                text_surf = self.font_medium.render(self.current_question, True, (0, 0, 0))
                qx = (SCREEN_WIDTH - text_surf.get_width() - 40) // 2
                qy = 50
                self.question_button = Button(qx, qy, text_surf.get_width()+40, text_surf.get_height()+20,
                                              self.current_question, None)
            return
        step_data = self.validator.get_step(step_id)

        if not step_data:
            self.show_end_screen()
            return
        visuals = self.image_data.get(step_id, {})
        self.final_button = None
        self.showing_results = False

        try:
            if "background" in visuals:
                bg_path = self.DATA_DIR / visuals["background"]
                if bg_path.exists():
                    self.bg_image = pygame.image.load(str(bg_path))
                    self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

            if "character" in visuals:
                char_path = self.DATA_DIR / visuals["character"]
                if char_path.exists():
                    self.char_image = pygame.image.load(str(char_path))

            if "extra_image" in visuals:
                ext_data = visuals["extra_image"]
                ext_path = self.DATA_DIR / ext_data["path"]
                if ext_path.exists():
                    self.extra_image = pygame.image.load(str(ext_path))
                    self.extra_image_pos = ext_data["pos"]
            hx, hy, hw, hh = self.hero_rect

            for item in visuals.get("items_to_click", []):
                r = item["rect"]
                zone = Button(hx + r[0], hy + r[1], r[2], r[3], "", None)
                zone.action_id = item["id"]
                zone.is_correct = False
                self.click_zones.append(zone)

        except Exception as e:
            print(f"Ошибка загрузки ресурсов: {e}")

        if self.click_zones:
            self.total_items_to_collect = len(self.click_zones)
            self.option_buttons = []

        else:
            options = self._get_options_for_step(step_id)
            correct = step_data.get("correct")
            self.multi_select_mode = isinstance(correct, list)
            if self.multi_select_mode:
                self.total_items_to_collect = len(options)
            custom_buttons_pos = visuals.get("buttons_pos", None)
            default_pos = visuals.get("options_pos", [(SCREEN_WIDTH - 500) // 2, 250])
            start_x, start_y = default_pos[0], default_pos[1]
            self._create_option_buttons(options, start_x, start_y, custom_buttons_pos)
        self.current_question = step_data.get("question", "").strip()

        if self.current_question:
            text_surf = self.font_medium.render(self.current_question, True, (0, 0, 0))
            q_width = text_surf.get_width() + 40
            q_height = text_surf.get_height() + 20
            if "question_pos" in visuals:
                q_x, q_y = visuals["question_pos"]
            else:
                q_x = (SCREEN_WIDTH - q_width) // 2
                q_y = 50 if self.bg_image else 100
            self.question_button = Button(q_x, q_y, q_width, q_height, self.current_question, None)
        self._create_control_buttons()

    def _get_options_for_step(self, step_id):
        if step_id in self.image_data and self.image_data[step_id].get("items_to_click"):
            return []
        options_map = {
            "0": self.items.get("introduction", []),
            "0.1": self.items.get("introduction_2", []),
            "1": self.items.get("clothes", []),
            "2": self.items.get("shoes", []),
            "3": self.items.get("hats", []),
            "4": self.items.get("jewerly", []),
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
            "15": self.items.get("ingredients", []),
            "16": self.items.get("temperature", []),
            "17": ["Нажмите, чтобы продолжить"],
            "18": self.items.get("cleaning", []),
        }
        return options_map.get(step_id, ["Далее"])

    def _get_description_for_step(self, step_id):
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

    def _create_ingredient_buttons(self, ingredients):
        self.option_buttons = []
        visuals = self.image_data.get("15", {})
        positions = visuals.get("buttons_pos", [])
        for i, ing in enumerate(ingredients):
            if i < len(positions):
                x, y = positions[i]
            else:
                x, y = 130, 310 + i * 70
            btn = DialogBox(x, y, 500, 35, ing, None)
            self.option_buttons.append(btn)

    def _create_control_buttons(self):
        if self.total_items_to_collect > 0 or self.multi_select_mode:
            btn_text = "ПРОВЕРИТЬ"
            btn_width = 250
        else:
            btn_text = "ДАЛЕЕ"
            btn_width = 200
        self.next_button = Button((SCREEN_WIDTH - btn_width) // 2, 620, btn_width, 50, btn_text, None)
        self.retry_button = Button((SCREEN_WIDTH - 250) // 2, 620, 250, 50, "ПОПРОБОВАТЬ СНОВА", None)

    # УДАЛИТЬ УБРАТЬ
    # def previous_step(self):
    #     if self.step_index > 0:
    #         self.step_index -= 1
    #         self.load_step(self.steps_order[self.step_index])

    def handle_event(self, event):
        # УДАЛИТЬ УБРАТЬ
        # if event.type == pygame.KEYDOWN:
        #     if event.key == pygame.K_n:
        #         self.next_step()
        #         return
        #     if event.key == pygame.K_b:
        #         self.previous_step()
        #         return
        #
        if self.show_help_window:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.show_help_window = False
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.help_button.rect.collidepoint(event.pos):
                self.show_help_window = True
                return

        if self.current_step == "5":
            if self.sequence_input and not self.sequence_locked:
                self.sequence_input.handle_event(event)

            if event.type == pygame.MOUSEMOTION:
                if self.sequence_next_button:
                    self.sequence_next_button.handle_event(event)
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.sequence_next_button and self.sequence_next_button.rect.collidepoint(event.pos):
                    if self.sequence_next_button.text == "Далее":
                        self.sequence_input = None
                        self.sequence_next_button = None
                        self.next_step()
                    elif self.sequence_next_button.text == "ПОПРОБОВАТЬ СНОВА":
                        self.reset_step_5()
                    else:
                        self.check_sequence_answer()

                for btn in self.option_buttons:
                    if btn.rect.collidepoint(event.pos):
                        return
            return

        if self.overlay_active:
            self._handle_overlay_event(event)
            return

        if self.confirmation.is_waiting:
            return

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

        if self.multi_select_mode:
            if event.type == pygame.MOUSEMOTION:
                for btn in self.option_buttons:
                    btn.handle_event(event)

            if self.next_button and self.next_button.handle_event(event):
                self.check_multi_select()
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.option_buttons):
                    if btn.rect.collidepoint(event.pos):
                        if i in self.selected_options:
                            self.selected_options.remove(i)
                            btn.status = None
                        else:
                            self.selected_options.add(i)
                            btn.status = "selected"
                        return

        if self.total_items_to_collect > 0:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for zone in self.click_zones:
                    if zone.rect.collidepoint(mouse_pos):
                        self.check_zone_click(zone)
                        return

            if self.next_button.handle_event(event):
                self.check_completion()
                return
            return

        if self.current_step == "15" and not self.waiting_for_next and not self.is_error:
            if self.next_button and self.next_button.handle_event(event):
                if self.next_button.text == "ДАЛЕЕ":
                    self.next_step()
                elif self.next_button.text == "Неверно. Попробуйте еще раз":
                    self._reset_scene_15()
                else:
                    self.check_cooking_sequence()
                return

            for i, btn in enumerate(self.option_buttons):
                if btn.handle_event(event):
                    self._start_cooking_overlay(btn.text)
                    return

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
            if self.current_step in ["0", "0.1", "5_1", "6", "7", "8.1", "9.1", "10.1", "12.4", "13.1", "17"]:
                if self.current_step == "0.1":
                    player_name = self.name_input.text.strip()
                    if not player_name:
                        self.name_input.is_error = True
                        return
                    self.name_input.is_error = False
                    self.state_manager.progress["player_name"] = player_name
                self.next_step()
                return

            if idx is not None:
                self.option_buttons[idx].status = "correct"
            self.waiting_for_next = True
        else:
            self.is_error = True
            self.error_counter.add_error()
            if idx is not None:
                self.option_buttons[idx].status = "wrong"

    def check_zone_click(self, zone):
        if zone.is_correct:
            return
        step_data = self.validator.get_step(self.current_step)
        correct = step_data.get("correct", [])

        if isinstance(correct, list):
            normalized_action = zone.action_id.strip().lower()
            allowed_ids = [item.strip().lower() for item in correct]
            if normalized_action in allowed_ids:
                zone.is_correct = True
                self.correct_count += 1
        else:
            if self.validator.validate(self.current_step, zone.action_id):
                zone.is_correct = True
                self.correct_count += 1

    def check_completion(self):
        if self.correct_count == self.total_items_to_collect:
            self.waiting_for_next = True
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

        if self.current_step == "5":
            self.setup_step_5()

    def reset_step_5(self):
        self.sequence_input.text = ""
        self.sequence_input.txt_surface = self.sequence_input.font.render(
            "", True, self.sequence_input.color
        )
        self.sequence_input.is_error = False
        self.sequence_input.is_correct = False
        self.sequence_locked = False
        self.sequence_input.active = True
        self.sequence_next_button.text = "Проверить"

    def setup_step_5(self):
        pos = self.image_data["5"].get("input_pos", [390, 450, 400, 50])
        self.sequence_input = InputBox(
            pos[0], pos[1], pos[2], pos[3],
            self.font_medium,
            validator=lambda char: char.isdigit()
        )
        self.sequence_input.text = ""
        self.sequence_label_text = "Введите правильную последовательность:"
        self.label_rect = pygame.Rect(130, 540, 500, 50)
        self.sequence_next_button = Button(900, 540, 250, 50, "Проверить", None)
        self.sequence_locked = False

    def check_sequence_answer(self):
        step_data = self.validator.actions.get("5", {})
        correct_answer = str(step_data.get("correct", ""))
        user_answer = self.sequence_input.text.strip()
        if user_answer == correct_answer:
            self.sequence_input.is_error = False
            self.sequence_input.is_correct = True
            self.sequence_next_button.text = "Далее"
            self.sequence_locked = True
        else:
            self.sequence_input.is_error = True
            self.sequence_locked = True
            self.sequence_next_button.text = "ПОПРОБОВАТЬ СНОВА"
            if hasattr(self, 'error_counter'):
                self.error_counter.add_error()

    def update(self, dt):
        pass

    @staticmethod
    def draw_description_block(screen, text, rect_coords, font):
        pygame.draw.rect(screen, (255, 255, 255), rect_coords, border_radius=15)
        pygame.draw.rect(screen, (0, 0, 0), rect_coords, 2, border_radius=15)
        x, y, w, h = rect_coords
        padding = 20
        current_y = y + padding
        max_w = w - (padding * 2)
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
        if self.showing_results:
            self._draw_results(screen)
            return

        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
            if self.extra_image:
                screen.blit(self.extra_image, self.extra_image_pos)

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

            for zone in self.click_zones:
                if zone.is_correct and self.checkmark_img:
                    x = zone.rect.x + (zone.rect.width - self.checkmark_img.get_width()) // 2
                    y = zone.rect.y + (zone.rect.height - self.checkmark_img.get_height()) // 2
                    screen.blit(self.checkmark_img, (x, y))

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
            prompt_surf = self.font_small.render("Введите ваше имя:", True, (0, 0, 0))
            screen.blit(prompt_surf, ((SCREEN_WIDTH - prompt_surf.get_width()) // 2, self.name_input.rect.y - 35))
            self.name_input.draw(screen)

        if self.current_step not in ["0", "0.1"]:
            description_text = self._get_description_for_step(self.current_step)

            if description_text:
                visuals = self.image_data.get(self.current_step, {})
                coords = visuals.get("text_rect", [400, 50, 500, 150])
                self.draw_description_block(screen, description_text, pygame.Rect(coords), self.font_small)

            if self.question_button:
                self.question_button.draw(screen)

        if self.current_step == "5" and self.sequence_input:
            pygame.draw.rect(screen, (255, 255, 255), self.label_rect, border_radius=10)
            pygame.draw.rect(screen, (0, 0, 0), self.label_rect, 2, border_radius=10)
            label_surf = self.font_small.render(self.sequence_label_text, True, (0, 0, 0))
            text_x = self.label_rect.x + (self.label_rect.width - label_surf.get_width()) // 2
            text_y = self.label_rect.y + (self.label_rect.height - label_surf.get_height()) // 2
            screen.blit(label_surf, (text_x, text_y))
            self.sequence_input.draw(screen)
            if hasattr(self.sequence_input, 'is_correct') and self.sequence_input.is_correct:
                pygame.draw.rect(screen, (0, 200, 0), self.sequence_input.rect, 3, border_radius=5)
            self.sequence_next_button.draw(screen)

        if self.current_step not in ["0", "0.1"]:
            self.error_button.text = f"Ошибок: {self.error_counter.count}"
            self.error_button.font = self.error_button.fit_text()
            self.error_button.draw(screen)

        if self.option_buttons and not self.overlay_active:
            for btn in self.option_buttons:
                btn.draw(screen)

        if self.final_button:
            self.final_button.draw(screen)

        if self.waiting_for_next:
            self.next_button.draw(screen)
        elif self.is_error:
            self.retry_button.draw(screen)
        elif self.total_items_to_collect > 0:
            self.next_button.draw(screen)
        elif self.current_step == "15" and self.next_button and not self.overlay_active:
            self.next_button.draw(screen)

        if self.current_step not in ["0", "0.1"]:
            center = self.help_button.rect.center
            radius = self.help_button.rect.width // 2
            pygame.draw.circle(screen, (255, 255, 255), center, radius)
            pygame.draw.circle(screen, (0, 0, 0), center, radius, 2)
            help_sym = self.font_small.render("?", True, (0, 0, 0))
            screen.blit(help_sym, help_sym.get_rect(center=center))
            if self.show_help_window:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                screen.blit(overlay, (0, 0))
                box_w, box_h = 800, 350
                box_rect = pygame.Rect((SCREEN_WIDTH - box_w) // 2, (SCREEN_HEIGHT - box_h) // 2, box_w, box_h)
                scene_id = self.current_step.split('.')[0]
                instruction_text = self.instructions.get(
                    self.current_step,
                    self.instructions.get(f"scene_{scene_id}", "Инструкция для этого этапа еще не добавлена.")
                )
                self.draw_description_block(screen, instruction_text, box_rect, self.font_small)
                close_hint = self.font_small.render("Нажмите в любое место, чтобы закрыть", True, (200, 200, 200))
                screen.blit(close_hint, (SCREEN_WIDTH // 2 - close_hint.get_width() // 2, box_rect.bottom + 15))

        if self.overlay_active:
            self._draw_overlay(screen)

    def _draw_results(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        box_w, box_h = 600, 400
        box_rect = pygame.Rect(
            (SCREEN_WIDTH - box_w) // 2,
            (SCREEN_HEIGHT - box_h) // 2,
            box_w, box_h
        )
        pygame.draw.rect(screen, (255, 255, 255), box_rect, border_radius=20)
        pygame.draw.rect(screen, (0, 0, 0), box_rect, 2, border_radius=20)
        player_name = self.state_manager.progress.get("player_name", "Игрок")
        name_surf = self.font_medium.render(f"Имя: {player_name}", True, (0, 0, 0))
        screen.blit(name_surf, (box_rect.x + 50, box_rect.y + 50))
        errors_surf = self.font_medium.render(
            f"Количество ошибок: {self.error_counter.count}", True, (0, 0, 0)
        )
        screen.blit(errors_surf, (box_rect.x + 50, box_rect.y + 120))
        hint_surf = self.font_small.render(
            "Нажмите в любом месте, чтобы закрыть программу", True, (120, 120, 120)
        )
        screen.blit(hint_surf, (box_rect.x + 50, box_rect.y + box_h - 60))

    def check_multi_select(self):
        selected_texts = [self.option_buttons[i].text for i in self.selected_options]
        if self.validator.validate(self.current_step, selected_texts):
            for i in self.selected_options:
                self.option_buttons[i].status = "correct"
            if self.current_step == "18":
                self.final_button = Button((SCREEN_WIDTH - 250) // 2, 620, 250, 50, "ПОДВЕСТИ ИТОГИ", None)
                self.multi_select_mode = False
                self.total_items_to_collect = 0
            else:
                self.waiting_for_next = True
                self.multi_select_mode = False
                self.total_items_to_collect = 0
                self._create_control_buttons()
        else:
            for i in self.selected_options:
                self.option_buttons[i].status = "wrong"
            self.is_error = True
            self.error_counter.add_error()

    @staticmethod
    def show_end_screen():
        pygame.quit()
        exit()

    def _start_cooking_overlay(self, ingredient):
        self.overlay_active = True
        self.overlay_ingredient = ingredient
        self.overlay_step = 1
        self._build_overlay_ui()

    def _build_overlay_ui(self):
        cfg = self.image_data.get("15_1", {})
        self.overlay_buttons = []
        self.overlay_texts = []
        x, y, w, h = cfg.get("reset_button_pos", [390, 30, 500, 50])
        self.overlay_reset_btn = Button(x, y, w, h, "Нажмите, чтобы начать заново", None)
        txt_rect = cfg.get("text_rect", [400, 110, 480, 60])
        self.overlay_texts.append({"rect": txt_rect, "text": self.text.get("scene_15_1", "")})
        prod_rect = cfg.get("product_label_pos", [390, 190, 500, 50])
        self.overlay_texts.append({"rect": prod_rect, "text": self.overlay_ingredient, "is_button": True})
        row1 = cfg.get("buttons_row1", [[130, 270, 400, 50], [650, 270, 400, 50]])
        btn1 = Button(row1[0][0], row1[0][1], row1[0][2], row1[0][3], "Положить в кастрюлю", None)
        btn2 = Button(row1[1][0], row1[1][1], row1[1][2], row1[1][3], "Припустить в сковороде", None)
        if self.overlay_step == 2:
            btn1.status = "disabled"
            btn2.status = "selected"
        self.overlay_buttons = [btn1, btn2]

        if self.overlay_step == 2:
            lbl_rect = cfg.get("next_label_pos", [390, 350, 500, 40])
            self.overlay_texts.append({"rect": lbl_rect, "text": "Что делать далее?", "is_label": True})
            row2 = cfg.get("buttons_row2", [[130, 410, 400, 50], [650, 410, 400, 50]])
            btn3 = Button(row2[0][0], row2[0][1], row2[0][2], row2[0][3], "Положить в кастрюлю", None)
            btn4 = Button(row2[1][0], row2[1][1], row2[1][2], row2[1][3], "Оставить в сковороде", None)
            self.overlay_buttons.extend([btn3, btn4])

    def _handle_overlay_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for btn in self.overlay_buttons:
                if btn.status is None:
                    btn.handle_event(event)
            if self.overlay_reset_btn:
                self.overlay_reset_btn.handle_event(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.overlay_reset_btn and self.overlay_reset_btn.rect.collidepoint(pos):
                self._reset_overlay_to_initial()
                return

            for btn in self.overlay_buttons:
                if btn.status == "disabled":
                    continue

                if btn.rect.collidepoint(pos):
                    self._on_overlay_button_click(btn.text)
                    return

    def _on_overlay_button_click(self, action):
        if action == "Положить в кастрюлю":
            if self.overlay_step == 1:
                self._finish_cooking([action])
            else:
                self._finish_cooking(["Припустить в сковороде", action])
        elif action == "Припустить в сковороде":
            self.overlay_step = 2
            self._build_overlay_ui()
        elif action == "Оставить в сковороде":
            self._finish_cooking(["Припустить в сковороде", action])

    def _finish_cooking(self, actions_list):
        self.cooking_actions[self.overlay_ingredient] = actions_list
        self.cooking_flags[self.overlay_ingredient] = True
        self._close_overlay()
        if self.current_step == "15":
            still_left = [ing for ing in self.cooking_ingredients if not self.cooking_flags[ing]]
            self._create_ingredient_buttons(still_left)

    def _close_overlay(self):
        self.overlay_active = False
        self.overlay_ingredient = None
        self.overlay_step = 1
        self.overlay_buttons = []
        self.overlay_texts = []
        self.overlay_reset_btn = None

    def _reset_scene_15(self):
        self.cooking_flags = {ing: False for ing in self.cooking_ingredients}
        self.cooking_actions = {ing: [] for ing in self.cooking_ingredients}
        self.cooking_validation_passed = False
        self._close_overlay()
        self.load_step("15")

    def _reset_overlay_to_initial(self):
        self.overlay_step = 1
        self.cooking_actions[self.overlay_ingredient] = []
        self._build_overlay_ui()

    def _draw_overlay(self, screen):
        overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay_surf.fill((0, 0, 0, 180))
        screen.blit(overlay_surf, (0, 0))
        bg_rect = pygame.Rect(100, 80, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 160)
        pygame.draw.rect(screen, (255, 255, 255), bg_rect, border_radius=20)
        if self.overlay_reset_btn:
            self.overlay_reset_btn.draw(screen)

        for item in self.overlay_texts:
            rect = item["rect"]
            if item.get("is_button"):
                pygame.draw.rect(screen, (220, 220, 220), rect, border_radius=5)
                pygame.draw.rect(screen, (180, 180, 180), rect, 2, border_radius=5)
                surf = self.font_medium.render(item["text"], True, (0, 0, 0))
                screen.blit(surf, (rect[0] + 10, rect[1] + 10))
            else:
                surf = self.font_medium.render(item["text"], True, (0, 0, 0))
                screen.blit(surf, (rect[0] + 10, rect[1] + 10))

        for btn in self.overlay_buttons:
            btn.draw(screen)

    def check_cooking_sequence(self):
        if not all(self.cooking_flags.values()):
            self.error_counter.add_error()
            self.next_button.text = "Неверно. Попробуйте еще раз"
            return
        expected = self.validator.get_step("15").get("correct", {})

        if self.validator.validate_cooking_sequence(self.cooking_actions, expected):
            self.cooking_validation_passed = True
            self.next_button.text = "ДАЛЕЕ"
            self.next_button.status = None
            self.waiting_for_next = False
        else:
            self.error_counter.add_error()
            self.next_button.text = "Неверно. Попробуйте еще раз"
