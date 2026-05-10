import json
from typing import Any, Dict, Union, List, Set
from utils import resource_path

class ActionValidator:
    def __init__(self, scenarios_path: str = "data/scenarios.json"):
        full_path = resource_path(scenarios_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.actions = data.get("action", {})

    def get_step(self, step_id: str) -> Dict[str, Any]:
        return self.actions.get(step_id, {})

    def validate(self, step_id: str, user_answer: Union[str, List[str]]) -> bool:
        step = self.get_step(step_id)
        if not step:
            return False
        correct = step.get("correct")

        if isinstance(correct, bool):
            return self._to_bool(user_answer) == correct

        if isinstance(correct, (int, float)):
            return self._compare_number(user_answer, correct)

        if isinstance(correct, str):
            return self._normalize_string(user_answer) == correct.strip().lower()

        if isinstance(correct, list):
            expected_set = {item.strip().lower() for item in correct if isinstance(item, str)}
            user_set = self._normalize_answer_to_set(user_answer)
            return user_set == expected_set
        return False

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in ("true", "yes", "да", "1")
        return bool(value)

    @staticmethod
    def _compare_number(user_answer: Any, expected: float) -> bool:
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
        if isinstance(value, str):
            return value.strip().lower()
        return str(value).strip().lower()

    @staticmethod
    def _normalize_answer_to_set(answer: Union[str, List[str]]) -> Set[str]:
        if isinstance(answer, str):
            return {answer.strip().lower()}

        if isinstance(answer, list):
            return {str(item).strip().lower() for item in answer}
        return set()

    @staticmethod
    def validate_cooking_sequence(actions: Dict[str, List[str]], expected: Dict[str, List[str]]) -> bool:
        if set(actions.keys()) != set(expected.keys()):
            return False

        for i, steps in expected.items():
            if actions.get(i) != steps:
                return False
        return True
