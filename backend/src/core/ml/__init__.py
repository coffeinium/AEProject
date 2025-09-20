"""
Модуль машинного обучения и обработки текста для AEProject

Содержит алгоритмы и утилиты для:
- Нечеткого поиска и сравнения строк
- Исправления опечаток
- Анализа схожести текстов
- Асинхронной работы с ML моделями
- Классификации намерений
"""

from .submodules.levenshtein import LevenshteinCalculator
from .submodules.model import AsyncMLModel

__all__ = [
    'LevenshteinCalculator',
    'AsyncMLModel'
]
