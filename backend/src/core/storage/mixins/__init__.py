"""
Миксины для работы с различными таблицами базы данных
"""

from .contracts_mixin import ContractsMixin
from .sessions_mixin import SessionsMixin

__all__ = ['ContractsMixin', 'SessionsMixin']
