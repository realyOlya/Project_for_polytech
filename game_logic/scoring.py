class ErrorCounter:
    def __init__(self):
        self._count = 0

    def add_error(self) -> None:
        self._count += 1

    def reset(self) -> None:
        self._count = 0

    @property
    def count(self) -> int:
        return self._count

