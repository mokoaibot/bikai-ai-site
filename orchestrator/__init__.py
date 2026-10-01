"""
Пакет Главного Агента (Оркестратора) многоагентной системы.
"""

from .core import Orchestrator
from .config import Config

__all__ = ["Orchestrator", "Config"]
