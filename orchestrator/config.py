"""
config.py — конфигурация Оркестратора.

Все чувствительные данные (API-ключи и т.п.) читаются ИСКЛЮЧИТЕЛЬНО из
переменных окружения облачного окружения Arena AI. Ничего секретного
в этом файле не хранится и не хардкодится.
"""

import os
from pathlib import Path


class Config:
    """
    Конфигурация Оркестратора.

    Читает ключи API и прочие настройки из переменных окружения.
    Если какой-то ключ не задан — система не падает, а просто помечает
    его как недоступный (это нормально для первой итерации ядра).
    """

    # Список переменных окружения с ключами API, которые потенциально
    # могут использовать Оркестратор и его субагенты.
    ENV_KEYS = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "ARENA_API_KEY",
        "GOOGLE_API_KEY",
        "GROQ_API_KEY",
        "XAI_API_KEY",
    ]

    def __init__(self, base_dir: Path | None = None):
        # Корень репозитория (monorepo). По умолчанию — на уровень выше orchestrator/.
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent

        # Чтение ключей API из окружения Arena AI.
        self.api_keys = {key: os.environ.get(key) for key in self.ENV_KEYS}

        # Прочие настройки окружения.
        self.model_name = os.environ.get("ORCHESTRATOR_MODEL", "gpt-4o-mini")
        self.environment = os.environ.get("ARENA_ENV", "arena-cloud")

        # Ключевые пути репозитория (единая точка правды для всей системы).
        self.agents_dir = self.base_dir / "agents"
        self.global_knowledge_dir = self.base_dir / "global_knowledge"
        self.global_logs_dir = self.base_dir / "global_logs"
        self.orchestrator_log_file = self.global_logs_dir / "orchestrator.log"
        self.system_state_file = self.base_dir / "system_state.json"

    def get_key(self, name: str) -> str | None:
        """Возвращает значение ключа API по имени переменной окружения."""
        return self.api_keys.get(name)

    def has_key(self, name: str) -> bool:
        """Проверяет, задан ли ключ API."""
        return bool(self.api_keys.get(name))

    def summary(self) -> dict:
        """Безопасная сводка конфигурации (без значений самих ключей)."""
        return {
            "environment": self.environment,
            "model_name": self.model_name,
            "base_dir": str(self.base_dir),
            "available_keys": [k for k, v in self.api_keys.items() if v],
            "missing_keys": [k for k, v in self.api_keys.items() if not v],
        }
