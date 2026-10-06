"""
config.py — конфигурация Оркестратора.

Все чувствительные данные (API-ключи и т.п.) читаются ИСКЛЮЧИТЕЛЬНО из
переменных окружения облачного окружения Arena AI. Ничего секретного
в этом файле не хранится и не хардкодится.
"""

import os
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    """Ищет вверх от `start` ближайшую папку с `.git` (корень репозитория).

    Если не найдена (например, .git отсутствует в песочнице) — падаем
    обратно на фиксированное число уровней вверх, соответствующее
    текущей вложенности engine/dashboard/config.py -> корень.
    """
    current = start if start.is_dir() else start.parent
    for _ in range(8):
        if (current / ".git").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return start.resolve().parent.parent.parent


class Config:
    """
    Конфигурация Оркестратора.

    Читает ключи API и прочие настройки из переменных окружения.
    Если какой-то ключ не задан — система не падает, а просто помечает
    его как недоступный (это нормально для первой итерации ядра).
    """

    # Список переменных окружения с ключами API, которые потенциально
    # может использовать единственный исполнитель при работе над проектами.
    ENV_KEYS = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "ARENA_API_KEY",
        "GOOGLE_API_KEY",
        "GROQ_API_KEY",
        "XAI_API_KEY",
    ]

    def __init__(self, base_dir: Path | None = None):
        # Корень репозитория (monorepo). По умолчанию ищем вверх от этого
        # файла первую папку с ".git" — надёжно независимо от того, на
        # сколько уровней вложен dashboard/ (сейчас: engine/dashboard/).
        self.base_dir = Path(base_dir) if base_dir else _find_repo_root(Path(__file__).resolve())

        # Чтение ключей API из окружения Arena AI.
        self.api_keys = {key: os.environ.get(key) for key in self.ENV_KEYS}

        # Прочие настройки окружения.
        self.model_name = os.environ.get("ORCHESTRATOR_MODEL", "gpt-4o-mini")
        self.environment = os.environ.get("ARENA_ENV", "arena-cloud")

        # Ключевые пути репозитория (единая точка правды для всей системы).
        # projects_dir хранит контекстные профили направлений (НЕ отдельных
        # ботов) для единственного исполнителя. Папка на диске называется
        # directions/ (понятнее пользователю, чем "projects").
        self.projects_dir = self.base_dir / "directions"
        self.global_knowledge_dir = self.base_dir / "shared" / "knowledge"
        self.global_logs_dir = self.base_dir / "shared" / "logs"
        self.orchestrator_log_file = self.global_logs_dir / "orchestrator.log"
        self.system_state_file = self.base_dir / "engine" / "state" / "system_state.json"

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
