import json
from typing import Any, Dict, Union, List, Set

class ActionValidator:
    def __init__(self, scenarios_path: str = "data/scenarios.json"):
        with open(scenarios_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.actions = data.get("action", {})

    def get_step(self, step_id: str) -> Dict[str, Any]:
        return self.actions.get(step_id, {})

    def validate(self, step_id: str, user_answer: Union[str, List[str]]) -> bool:
        """
        Поддерживаемые типы поля 'correct':
          - строка (точное совпадение)
          - число (приведение к float)
          - булево значение
          - список строк (множество выбранных элементов, порядок не важен)
        """
        step = self.get_step(step_id)
        if not step:
            return False
        correct = step.get("correct")

        # 1. Булево значение
        if isinstance(correct, bool):
            return self._to_bool(user_answer) == correct

        # 2. Число (int или float)
        if isinstance(correct, (int, float)):
            return self._compare_number(user_answer, correct)

        # 3. Строка – прямое сравнение
        if isinstance(correct, str):
            return self._normalize_string(user_answer) == correct.strip().lower()

        # 4. Список строк (множество)
        if isinstance(correct, list):
            expected_set = {item.strip().lower() for item in correct if isinstance(item, str)}
            user_set = self._normalize_answer_to_set(user_answer)
            return user_set == expected_set

        # Неизвестный тип
        return False

    @staticmethod
    def _to_bool(value: Any) -> bool:
        """Преобразует ответ пользователя в булево значение."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("true", "yes", "да", "1")
        return bool(value)

    @staticmethod
    def _compare_number(user_answer: Any, expected: float) -> bool:
        """Сравнивает ответ пользователя с ожидаемым числом."""
        try:
            if isinstance(user_answer, str):
                return float(user_answer.strip()) == expected
            if isinstance(user_answer, (int, float)):
                return float(user_answer) == expected
            return False
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _normalize_string(value: Any) -> str:
        """Приводит ответ к единой строке в нижнем регистре без лишних пробелов."""
        if isinstance(value, str):
            return value.strip().lower()
        return str(value).strip().lower()

    @staticmethod
    def _normalize_answer_to_set(answer: Union[str, List[str]]) -> Set[str]:
        """Преобразует ответ пользователя в множество нормализованных строк."""
        if isinstance(answer, str):
            return {answer.strip().lower()}
        if isinstance(answer, list):
            return {str(item).strip().lower() for item in answer}
        return set()

    @staticmethod
    def validate_cooking_sequence(actions: Dict[str, List[str]], expected: Dict[str, List[str]]) -> bool:
        """Проверяет, что для каждого ингредиента записанные действия совпадают с ожидаемыми."""
        if set(actions.keys()) != set(expected.keys()):
            return False
        for ingr, steps in expected.items():
            if actions.get(ingr) != steps:
                return False
        return True
