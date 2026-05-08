class ConfirmationHandler:
    def __init__(self):
        self.is_waiting = False
        self.pending_choice = None
        self.on_confirm_callback = None

    def request_confirmation(self, choice_text: str, on_confirm):
        self.is_waiting = True
        self.pending_choice = choice_text
        self.on_confirm_callback = on_confirm

    def confirm(self):
        if self.is_waiting and self.on_confirm_callback:
            self.on_confirm_callback(self.pending_choice)
        self.reset()

    def cancel(self):
        self.reset()

    def reset(self):
        self.is_waiting = False
        self.pending_choice = None
        self.on_confirm_callback = None
