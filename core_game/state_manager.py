class StateManager:
    def __init__(self):
        self.progress = {
            "current_scene": None,
            "current_step": "1",
            "flags": {},
            "inventory": [],
            "error_count": 0
        }

    def save(self, filepath):
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f)

    def load(self, filepath):
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            self.progress = json.load(f)
        return self.progress.get("current_step", "1")

