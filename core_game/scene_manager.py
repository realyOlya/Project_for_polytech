class SceneManager:
    def __init__(self):
        self.current_scene = None
        self.scenes = {}

    def add_scene(self, name, scene):
        self.scenes[name] = scene

    def switch_to(self, name):
        if name in self.scenes:
            self.current_scene = self.scenes[name]

    def get_current_scene(self):
        return self.current_scene

