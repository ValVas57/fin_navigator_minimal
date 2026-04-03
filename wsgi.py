import sys
import os

# Добавляем путь к проекту
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from app.main import app as application