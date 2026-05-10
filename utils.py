from pathlib import Path
import sys
import os


def resource_path(relative_path):
    """Возвращает путь к ресурсу в виде объекта Path"""
    if hasattr(sys, '_MEIPASS'):
        # Путь внутри .exe
        base_path = Path(sys._MEIPASS)
    else:
        # Путь при обычной разработке
        base_path = Path(os.path.abspath("."))

    return base_path / relative_path