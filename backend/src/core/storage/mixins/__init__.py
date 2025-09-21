"""
Миксины для работы с различными таблицами базы данных
"""

from .contracts_mixin import ContractsMixin
from .sessions_mixin import SessionsMixin
from .history_mixin import HistoryMixin

__all__ = ['ContractsMixin', 'SessionsMixin', 'HistoryMixin']
