"""
core.py — ядро Главного Агента (Оркестратора).

Context-Driven архитектура: Оркестратор принимает произвольные текстовые
команды (через handle_chat_message), с помощью "ИИ-мозга" (orchestrator.brain)
понимает намерение пользователя и материализует его в реальной файловой
структуре monorepo (agents/, global_knowledge/, tasks.json, логи и т.д.).

Дашборд — лишь "зеркало": он не создаёт сущности напрямую, а только
отображает то, что здесь, в ядре, уже произошло и записано на диск.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import Config
from .brain import Brain


_TRANSLIT_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c",
    "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
    "я": "ya",
}


def _translit(text: str) -> str:
    """Простая транслитерация кириллицы в латиницу для читаемых слагов."""
    result = []
    for ch in text:
        lower = ch.lower()
        if lower in _TRANSLIT_MAP:
            mapped = _TRANSLIT_MAP[lower]
            result.append(mapped.upper() if ch.isupper() and mapped else mapped)
        else:
            result.append(ch)
    return "".join(result)


class Orchestrator:
    """Главный Агент (Оркестратор) Context-Driven многоагентной системы."""

    VALID_STATUSES = ("todo", "in_progress", "done")

    def __init__(self, base_dir: Optional[Path] = None):
        self.config = Config(base_dir=base_dir)
        self.brain = Brain(self.config)

        self.base_dir = self.config.base_dir
        self.agents_dir = self.config.agents_dir
        self.global_knowledge_dir = self.config.global_knowledge_dir
        self.global_logs_dir = self.config.global_logs_dir
        self.log_file = self.config.orchestrator_log_file
        self.state_file = self.config.system_state_file

        self.tasks_file = self.base_dir / "tasks.json"
        self.chat_history_file = self.global_logs_dir / "chat_history.json"
        self.activity_file = self.global_logs_dir / "activity.jsonl"
        self.global_knowledge_manifest = self.global_knowledge_dir / "entries.json"
        self.export_dir = self.base_dir / "exports"
        self.settings_file = self.base_dir / "orchestrator_settings.json"

        for d in (self.agents_dir, self.global_knowledge_dir, self.global_logs_dir, self.export_dir):
            d.mkdir(parents=True, exist_ok=True)
        (self.export_dir / "history").mkdir(parents=True, exist_ok=True)

        for f, default in (
            (self.tasks_file, "[]"),
            (self.chat_history_file, "[]"),
            (self.global_knowledge_manifest, "[]"),
        ):
            if not f.exists():
                f.write_text(default, encoding="utf-8")

        if not self.settings_file.exists():
            self._write_settings(self._default_settings())

        self._log("Оркестратор инициализирован.", action="system_init")

    # ------------------------------------------------------------------ #
    # Настройки системы (например, уровень автономии)
    # ------------------------------------------------------------------ #

    AUTONOMY_LEVELS = {
        "full_auto": "Полная автономия — создаю агентов/скилы/задачи сразу по ходу работы.",
        "confirm_agents_only": "Создаю скилы и задачи сразу, но для НОВОГО агента сначала спрашиваю подтверждение.",
        "confirm_all": "Перед любым изменением системы сначала предлагаю план и жду подтверждения.",
    }

    @staticmethod
    def _default_settings() -> dict:
        return {
            "autonomy_level": "confirm_all",
            "auto_push": False,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }

    def _write_settings(self, settings: dict) -> None:
        self.settings_file.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_settings(self) -> dict:
        try:
            settings = json.loads(self.settings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            settings = {}
        merged = {**self._default_settings(), **settings}
        if merged != settings:
            self._write_settings(merged)
        return merged

    def set_autonomy_level(self, level: str) -> dict:
        if level not in self.AUTONOMY_LEVELS:
            raise ValueError(f"Неизвестный уровень автономии: {level}. Доступны: {list(self.AUTONOMY_LEVELS)}")
        settings = self.get_settings()
        settings["autonomy_level"] = level
        settings["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self._write_settings(settings)
        self._log(
            f"Уровень автономии Оркестратора изменён на '{level}': {self.AUTONOMY_LEVELS[level]}",
            action="settings_change",
        )
        return settings

    def set_auto_push(self, enabled: bool) -> dict:
        settings = self.get_settings()
        settings["auto_push"] = bool(enabled)
        settings["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self._write_settings(settings)
        state_label = "включён" if enabled else "выключен"
        self._log(f"Автоматический Git-push {state_label}.", action="settings_change")
        return settings

    # ------------------------------------------------------------------ #
    # Git-синхронизация (автономный push без явной команды пользователя)
    # ------------------------------------------------------------------ #

    def _load_sync_git_module(self):
        """Динамически импортирует sync_git.py из корня monorepo (не пакет, а скрипт)."""
        module_name = "sync_git"
        if module_name in sys.modules:
            return sys.modules[module_name]
        spec = importlib.util.spec_from_file_location(module_name, self.base_dir / "sync_git.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def auto_push(self, reason: str = "автоматическая синхронизация") -> dict:
        """
        Выполняет push в GitHub прямо сейчас (используется и автоматикой, и
        Оркестратором вручную, когда он сам решает, что пора сохранить прогресс).
        Никогда не бросает исключение наружу — любая ошибка просто логируется.
        """
        try:
            sync_git = self._load_sync_git_module()
            git_sync = sync_git.GitSync(base_dir=self.base_dir)
            result = git_sync.push(message=f"Авто-синхронизация: {reason}")
        except Exception as exc:  # noqa: BLE001
            self._log(f"Авто-push не удался ({reason}): {exc}", level="ERROR", action="auto_push_failed")
            return {"status": "error", "error": str(exc)}

        if result["status"] == "ok":
            self._log(f"Авто-push выполнен ({reason}).", action="auto_push")
        else:
            self._log(
                f"Авто-push не завершён ({reason}): статус {result['status']}.",
                level="WARNING", action="auto_push_failed",
            )
        return result

    def maybe_auto_push(self, reason: str) -> Optional[dict]:
        """Вызывает auto_push(), только если включена настройка auto_push."""
        if self.get_settings().get("auto_push"):
            return self.auto_push(reason)
        return None

    # ------------------------------------------------------------------ #
    # Логирование (текстовый лог + структурированная лента активности)
    # ------------------------------------------------------------------ #

    def _log(self, message: str, level: str = "INFO", action: str = "info", **extra) -> None:
        timestamp = datetime.now()
        ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{ts_str}] [{level}] {message}\n")

        record = {
            "timestamp": timestamp.isoformat(timespec="seconds"),
            "level": level,
            "action": action,
            "message": message,
        }
        record.update(extra)
        with open(self.activity_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_recent_activity(self, limit: int = 50) -> list[dict]:
        if not self.activity_file.exists():
            return []
        lines = self.activity_file.read_text(encoding="utf-8").splitlines()
        records = []
        for line in lines[-limit:]:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        records.reverse()
        return records

    # ------------------------------------------------------------------ #
    # Чат: единая точка входа для управления системой
    # ------------------------------------------------------------------ #

    def _load_chat_history(self) -> list[dict]:
        try:
            return json.loads(self.chat_history_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_chat_message(self, role: str, text: str, meta: Optional[dict] = None) -> None:
        history = self._load_chat_history()
        history.append(
            {
                "role": role,
                "text": text,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "meta": meta or {},
            }
        )
        self.chat_history_file.write_text(
            json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_chat_history(self) -> list[dict]:
        return self._load_chat_history()

    def _brain_context(self) -> dict:
        agents = [self._read_agent_metadata(p) for p in self._agent_dirs()]
        tasks = self._load_tasks()
        return {"agents": agents, "tasks": tasks}

    def handle_chat_message(self, text: str) -> dict:
        """
        Главная точка входа Context-Driven управления.
        Понимает намерение и применяет изменения к файловой системе.
        Возвращает {"reply": str, "intent": dict}.
        """
        self._save_chat_message("user", text)
        self._log(f"Получена команда в чате: \"{text}\"", action="chat_in")

        intent = self.brain.interpret(text, self._brain_context())
        action = intent.get("action", "unknown")
        reply = "Не понял команду 🤔"

        try:
            if action == "create_agent":
                reply = self._apply_create_agent(intent)
            elif action == "add_skill":
                reply = self._apply_add_skill(intent)
            elif action == "create_task":
                reply = self._apply_create_task(intent)
            elif action == "update_task_status":
                reply = self._apply_update_task_status(intent)
            elif action == "add_knowledge":
                reply = self._apply_add_knowledge(intent)
            elif action == "delete_agent":
                reply = self._apply_delete_agent(intent)
            elif action == "query_status":
                reply = self._apply_query_status()
            elif action == "empty":
                reply = "Напишите команду, например: «Создай SEO-агента для анализа ключевых слов»."
            else:
                reply = (
                    "Не удалось распознать команду. Попробуйте, например:\n"
                    "• «Создай агента-переводчика для перевода документов»\n"
                    "• «Добавь переводчику скилл работы со словарями»\n"
                    "• «Создай задачу для переводчика: перевести отчёт»\n"
                    "• «Запомни паттерн: всегда проверяй источники»"
                )
        except Exception as exc:  # noqa: BLE001
            self._log(f"Ошибка выполнения намерения '{action}': {exc}", level="ERROR", action="error")
            reply = f"⚠️ Произошла ошибка при выполнении команды: {exc}"

        self._save_chat_message("assistant", reply, meta={"intent": intent})
        self._log(f"Ответ ассистента: \"{reply[:200]}\"", action="chat_out")

        self.run_audit()
        return {"reply": reply, "intent": intent}

    # ------------------------------------------------------------------ #
    # Применение намерений
    # ------------------------------------------------------------------ #

    def _apply_create_agent(self, intent: dict) -> str:
        name_hint = intent.get("name") or "agent"
        role = intent.get("role") or f"{name_hint.capitalize()}-агент"
        task_description = intent.get("task_description") or "Задача не уточнена."
        result = self.create_agent(name_hint, role=role, task_description=task_description)
        if result["status"] == "exists":
            return f"Агент «{result['name']}» уже существует в системе (папка `{result['path']}`)."
        self.maybe_auto_push(f"создан агент {result['name']}")
        return (
            f"✅ Создан новый субагент **{result['name']}**\n"
            f"- Роль: {role}\n"
            f"- Задача: {task_description}\n"
            f"- Папка: `{result['path']}`"
        )

    def _apply_add_skill(self, intent: dict) -> str:
        agent_name = intent.get("agent")
        if not agent_name:
            hint = intent.get("agent_hint")
            return self._agent_not_found_reply(hint)
        skill_name = intent.get("skill_name") or "новый_скил"
        result = self.add_skill(agent_name, skill_name)
        return (
            f"🛠 Агенту **{agent_name}** добавлен новый скил: «{result['skill_title']}»\n"
            f"Файл: `{result['path']}`"
        )

    def _apply_create_task(self, intent: dict) -> str:
        agent_name = intent.get("agent")
        title = intent.get("title") or "Новая задача"
        task = self.create_task(agent_name, title)
        who = agent_name or "без привязки к агенту"
        return f"📋 Создана задача #{task['id']} ({who}): {task['title']}"

    def _apply_update_task_status(self, intent: dict) -> str:
        task_id = intent.get("task_id")
        status = intent.get("status", "done")
        if task_id is None:
            tasks = self._load_tasks()
            if not tasks:
                return "В системе пока нет задач."
            task_id = tasks[-1]["id"]
        task = self.update_task_status(task_id, status)
        if task is None:
            return f"Задача #{task_id} не найдена."
        status_ru = {"todo": "к выполнению", "in_progress": "в процессе", "done": "готово"}[status]
        return f"✅ Задача #{task['id']} «{task['title']}» теперь имеет статус: {status_ru}."

    def _apply_add_knowledge(self, intent: dict) -> str:
        scope = intent.get("scope", "global")
        agent_name = intent.get("agent")
        if scope == "local" and not agent_name:
            return self._agent_not_found_reply(None)
        kind = intent.get("kind", "approved")
        content = intent.get("content") or "Без описания."
        entry = self.add_knowledge(scope=scope, kind=kind, content=content, agent_name=agent_name)
        kind_ru = "✅ успешный паттерн" if kind == "approved" else "⚠️ ошибка, которой нужно избегать"
        where = f"глобальную базу" if scope == "global" else f"локальную базу агента «{agent_name}»"
        return f"📚 В {where} добавлена запись ({kind_ru}): {entry['title']}"

    def _apply_delete_agent(self, intent: dict) -> str:
        agent_name = intent.get("agent")
        if not agent_name:
            return self._agent_not_found_reply(intent.get("raw_mention"))
        ok = self.delete_agent(agent_name)
        if ok:
            self.maybe_auto_push(f"удалён агент {agent_name}")
            return f"🗑 Агент «{agent_name}» и все его файлы удалены из системы."
        return f"Агент «{agent_name}» не найден."

    def _apply_query_status(self) -> str:
        state = self.run_audit()
        counts = {"todo": 0, "in_progress": 0, "done": 0}
        for t in state["tasks"]:
            counts[t["status"]] = counts.get(t["status"], 0) + 1
        return (
            f"📊 Текущее состояние системы:\n"
            f"- Агентов: {state['agents_count']}\n"
            f"- Скилов всего: {sum(a['skills_count'] for a in state['agents'])}\n"
            f"- Задач: {len(state['tasks'])} (todo: {counts['todo']}, "
            f"в процессе: {counts['in_progress']}, готово: {counts['done']})\n"
            f"- Записей в глобальной базе знаний: {len(state['global_knowledge_entries'])}"
        )

    def _agent_not_found_reply(self, hint: Optional[str]) -> str:
        agents = [self._read_agent_metadata(p) for p in self._agent_dirs()]
        names = ", ".join(a["name"] for a in agents) if agents else "пока нет ни одного агента"
        hint_part = f" (искал похожее на «{hint}»)" if hint else ""
        return (
            f"Не нашёл подходящего агента{hint_part}. Существующие агенты: {names}. "
            f"Сначала создайте агента, например: «Создай агента {hint or 'Имя'} для ...»."
        )

    # ------------------------------------------------------------------ #
    # Работа с агентами
    # ------------------------------------------------------------------ #

    @staticmethod
    def _slugify(name: str, fallback_prefix: str = "item") -> str:
        """Превращает произвольное (в т.ч. кириллическое) имя в безопасный слаг."""
        name = _translit(name)
        name = unicodedata.normalize("NFKD", name)
        name = name.encode("ascii", "ignore").decode("ascii")
        name = name.strip().lower()
        name = re.sub(r"[^a-z0-9_-]+", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")
        return name or f"{fallback_prefix}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    @classmethod
    def _sanitize_name(cls, name: str) -> str:
        return cls._slugify(name, fallback_prefix="agent")

    def _agent_dirs(self) -> list[Path]:
        if not self.agents_dir.exists():
            return []
        return sorted(p for p in self.agents_dir.iterdir() if p.is_dir() and not p.name.startswith("."))

    def create_agent(self, name: str, role: Optional[str] = None, task_description: str = "") -> dict:
        safe_name = self._sanitize_name(name)
        agent_path = self.agents_dir / safe_name

        if agent_path.exists():
            self._log(f"Попытка создать агента '{safe_name}' отклонена: уже существует.",
                       level="WARNING", action="create_agent_skipped", agent=safe_name)
            return {"status": "exists", "name": safe_name, "path": str(agent_path.relative_to(self.base_dir))}

        role = role or f"{name.capitalize()}-агент"

        agent_path.mkdir(parents=True)
        (agent_path / "skills").mkdir()
        (agent_path / "knowledge").mkdir()
        (agent_path / "logs").mkdir()
        (agent_path / "__init__.py").write_text("", encoding="utf-8")

        (agent_path / "agent.py").write_text(self._render_agent_code(safe_name, role, task_description),
                                              encoding="utf-8")

        (agent_path / "skills" / "__init__.py").write_text("# Локальные скилы агента.\n", encoding="utf-8")
        (agent_path / "skills" / "manifest.json").write_text("[]", encoding="utf-8")

        (agent_path / "knowledge" / "notes.md").write_text(
            f"# База знаний агента `{safe_name}`\n\n## Роль\n{role}\n\n## Задача\n{task_description}\n",
            encoding="utf-8",
        )
        (agent_path / "knowledge" / "entries.json").write_text("[]", encoding="utf-8")

        created_at = datetime.now().isoformat(timespec="seconds")
        agent_log_path = agent_path / "logs" / f"{safe_name}.log"
        agent_log_path.write_text(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] "
            f"Агент '{safe_name}' создан Оркестратором. Роль: {role}. Задача: {task_description}\n",
            encoding="utf-8",
        )

        metadata = {
            "name": safe_name,
            "display_name": name,
            "role": role,
            "task_description": task_description,
            "created_at": created_at,
            "path": str(agent_path.relative_to(self.base_dir)),
        }
        (agent_path / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        self._log(
            f"Создан новый субагент '{safe_name}' (роль: {role}).",
            action="create_agent", agent=safe_name,
        )
        return {"status": "created", "name": safe_name, "path": str(agent_path.relative_to(self.base_dir))}

    def delete_agent(self, agent_name: str) -> bool:
        import shutil

        safe_name = self._sanitize_name(agent_name)
        agent_path = self.agents_dir / safe_name
        if not agent_path.exists():
            return False
        shutil.rmtree(agent_path)
        self._log(f"Агент '{safe_name}' удалён из системы.", level="WARNING",
                   action="delete_agent", agent=safe_name)
        return True

    @staticmethod
    def _render_agent_code(agent_name: str, role: str, task_description: str) -> str:
        class_name = "".join(part.capitalize() for part in agent_name.split("_")) + "Agent"
        return f'''"""
agent.py — автоматически сгенерированный субагент "{agent_name}".

Роль: {role}
Задача: {task_description}

Сгенерировано Оркестратором (orchestrator/core.py) по текстовой команде
пользователя из чата (Context-Driven создание).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

AGENT_NAME = "{agent_name}"
ROLE = "{role}"
TASK_DESCRIPTION = "{task_description}"
AGENT_DIR = Path(__file__).resolve().parent
LOG_FILE = AGENT_DIR / "logs" / f"{{AGENT_NAME}}.log"


class {class_name}:
    """Автосгенерированный субагент."""

    def __init__(self):
        self.name = AGENT_NAME
        self.role = ROLE
        self.task_description = TASK_DESCRIPTION

    def log(self, message: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{{timestamp}}] [{{level}}] {{message}}\\n")

    def run(self, *args, **kwargs):
        """Точка входа агента. Реализуйте логику под конкретную задачу."""
        self.log(f"Агент '{{self.name}}' ({{self.role}}) запущен: {{self.task_description}}")
        # TODO: реализовать конкретную логику субагента.
        self.log(f"Агент '{{self.name}}' завершил выполнение.")


if __name__ == "__main__":
    {class_name}().run()
'''

    def _read_agent_metadata(self, agent_dir: Path) -> dict:
        metadata_path = agent_dir / "metadata.json"
        if metadata_path.exists():
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                data.setdefault("name", agent_dir.name)
                return data
            except json.JSONDecodeError:
                pass
        return {"name": agent_dir.name, "display_name": agent_dir.name, "role": "", "task_description": "",
                "created_at": "", "path": str(agent_dir.relative_to(self.base_dir))}

    def find_agent(self, name_or_mention: str) -> Optional[dict]:
        agents = [self._read_agent_metadata(p) for p in self._agent_dirs()]
        safe = self._sanitize_name(name_or_mention)
        for a in agents:
            if a["name"] == safe:
                return a
        return self.brain.find_agent_mention(name_or_mention, agents)

    # ------------------------------------------------------------------ #
    # Скилы
    # ------------------------------------------------------------------ #

    def add_skill(self, agent_name: str, skill_title: str, description: str = "") -> dict:
        agent = self.find_agent(agent_name)
        if agent is None:
            raise ValueError(f"Агент '{agent_name}' не найден.")

        agent_dir = self.base_dir / agent["path"]
        skills_dir = agent_dir / "skills"
        skills_dir.mkdir(exist_ok=True)
        manifest_path = skills_dir / "manifest.json"

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            manifest = []

        slug = self._slugify(skill_title, fallback_prefix="skill")[:40]
        file_name = f"{slug}.py"
        func_name = slug if not slug[0].isdigit() else f"s_{slug}"

        (skills_dir / file_name).write_text(
            f'"""\n'
            f'Скил "{skill_title}" агента "{agent["name"]}".\n'
            f'{description}\n'
            f'"""\n\n\n'
            f"def {func_name}(*args, **kwargs):\n"
            f'    """Реализация скила "{skill_title}". Заполните логику."""\n'
            f'    return "{skill_title} ещё не реализован"\n',
            encoding="utf-8",
        )

        entry = {
            "name": skill_title,
            "file": file_name,
            "description": description,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        manifest.append(entry)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        self._log(
            f"Агенту '{agent['name']}' добавлен скил: «{skill_title}».",
            action="add_skill", agent=agent["name"],
        )
        return {"skill_title": skill_title, "path": str((skills_dir / file_name).relative_to(self.base_dir))}

    # ------------------------------------------------------------------ #
    # Задачи
    # ------------------------------------------------------------------ #

    def _load_tasks(self) -> list[dict]:
        try:
            return json.loads(self.tasks_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_tasks(self, tasks: list[dict]) -> None:
        self.tasks_file.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_task(self, agent_name: Optional[str], title: str) -> dict:
        tasks = self._load_tasks()
        next_id = (max((t["id"] for t in tasks), default=0)) + 1

        resolved_agent = None
        if agent_name:
            agent = self.find_agent(agent_name)
            resolved_agent = agent["name"] if agent else agent_name

        task = {
            "id": next_id,
            "agent": resolved_agent,
            "title": title,
            "status": "todo",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        tasks.append(task)
        self._save_tasks(tasks)

        self._log(
            f"Создана задача #{task['id']} для '{resolved_agent or 'системы'}': {title}",
            action="create_task", agent=resolved_agent, task_id=task["id"],
        )
        return task

    def update_task_status(self, task_id: int, status: str) -> Optional[dict]:
        if status not in self.VALID_STATUSES:
            status = "todo"
        tasks = self._load_tasks()
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = status
                t["updated_at"] = datetime.now().isoformat(timespec="seconds")
                self._save_tasks(tasks)
                self._log(
                    f"Статус задачи #{task_id} изменён на '{status}'.",
                    action="update_task", task_id=task_id, status=status,
                )
                return t
        return None

    # ------------------------------------------------------------------ #
    # База знаний
    # ------------------------------------------------------------------ #

    def _append_global_knowledge_md(self, kind: str, title: str, content: str) -> None:
        file_name = "approved_patterns.md" if kind == "approved" else "avoid_mistakes.md"
        path = self.global_knowledge_dir / file_name
        date = datetime.now().strftime("%Y-%m-%d")
        block = f"\n### [{date}] {title}\n{content}\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(block)

    def add_knowledge(self, scope: str, kind: str, content: str, agent_name: Optional[str] = None) -> dict:
        title = content.strip().split(". ")[0][:80] or "Новая запись"
        entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "scope": scope,
            "kind": kind,
            "title": title,
            "content": content,
            "agent": None,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

        if scope == "global":
            try:
                manifest = json.loads(self.global_knowledge_manifest.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                manifest = []
            manifest.append(entry)
            self.global_knowledge_manifest.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            self._append_global_knowledge_md(kind, title, content)
            self._log(f"Добавлена запись в глобальную базу знаний: «{title}».",
                       action="add_knowledge", scope="global")
        else:
            agent = self.find_agent(agent_name) if agent_name else None
            if agent is None:
                raise ValueError(f"Агент '{agent_name}' не найден для локальной записи знаний.")
            entry["agent"] = agent["name"]
            agent_dir = self.base_dir / agent["path"]
            entries_path = agent_dir / "knowledge" / "entries.json"
            try:
                local_manifest = json.loads(entries_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                local_manifest = []
            local_manifest.append(entry)
            entries_path.write_text(json.dumps(local_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            notes_path = agent_dir / "knowledge" / "notes.md"
            kind_label = "✅ Сработало хорошо" if kind == "approved" else "⚠️ Следует избегать"
            with open(notes_path, "a", encoding="utf-8") as f:
                f.write(f"\n### {kind_label}: {title}\n{content}\n")

            self._log(f"Добавлена локальная запись знаний агенту '{agent['name']}': «{title}».",
                       action="add_knowledge", scope="local", agent=agent["name"])

        return entry

    def _load_global_knowledge_entries(self) -> list[dict]:
        try:
            return json.loads(self.global_knowledge_manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    # ------------------------------------------------------------------ #
    # Полный аудит репозитория -> system_state.json
    # ------------------------------------------------------------------ #

    @staticmethod
    def _count_lines(file_path: Path) -> int:
        if not file_path.exists():
            return 0
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())

    def _audit_global_knowledge_files(self) -> list[dict]:
        entries = []
        if self.global_knowledge_dir.exists():
            for md_file in sorted(self.global_knowledge_dir.glob("*.md")):
                entries.append({
                    "file": md_file.name,
                    "size_bytes": md_file.stat().st_size,
                    "lines": self._count_lines(md_file),
                })
        return entries

    def _audit_agent(self, agent_dir: Path) -> dict:
        metadata = self._read_agent_metadata(agent_dir)

        manifest_path = agent_dir / "skills" / "manifest.json"
        try:
            skills = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            skills = []

        knowledge_entries_path = agent_dir / "knowledge" / "entries.json"
        try:
            knowledge_entries = json.loads(knowledge_entries_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            knowledge_entries = []

        total_log_lines = 0
        log_files = []
        logs_dir = agent_dir / "logs"
        if logs_dir.exists():
            for log_file in sorted(logs_dir.glob("*.log")):
                lines = self._count_lines(log_file)
                total_log_lines += lines
                log_files.append({"file": log_file.name, "lines": lines})

        return {
            "name": metadata["name"],
            "display_name": metadata.get("display_name", metadata["name"]),
            "role": metadata.get("role", ""),
            "task_description": metadata.get("task_description", ""),
            "created_at": metadata.get("created_at", ""),
            "path": metadata.get("path", str(agent_dir.relative_to(self.base_dir))),
            "skills": skills,
            "skills_count": len(skills),
            "knowledge_entries": knowledge_entries,
            "log_files": log_files,
            "log_lines": total_log_lines,
        }

    def run_audit(self) -> dict:
        """
        Полностью пересканирует репозиторий и формирует актуальный JSON-снимок
        архитектуры системы (system_state.json): агенты, скилы, задачи,
        глобальная/локальная база знаний, логи.
        """
        agents = [self._audit_agent(p) for p in self._agent_dirs()]
        tasks = self._load_tasks()

        state = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "config": self.config.summary(),
            "settings": self.get_settings(),
            "orchestrator": {
                "log_file": str(self.log_file.relative_to(self.base_dir)),
                "log_lines": self._count_lines(self.log_file),
            },
            "global_knowledge_files": self._audit_global_knowledge_files(),
            "global_knowledge_entries": self._load_global_knowledge_entries(),
            "agents_count": len(agents),
            "agents": agents,
            "tasks": tasks,
            "chat_messages_count": len(self._load_chat_history()),
        }

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        return state

    # ------------------------------------------------------------------ #
    # Экспорт: сборка цельного Markdown мета-промта системы
    # ------------------------------------------------------------------ #

    def export_meta_prompt(self) -> dict:
        state = self.run_audit()
        lines = []
        lines.append("# МЕТА-ПРОМТ АРХИТЕКТУРЫ МУЛЬТИАГЕНТНОЙ СИСТЕМЫ")
        lines.append("")
        lines.append(f"_Сформировано автоматически: {state['generated_at']}_")
        lines.append("")
        lines.append(
            "Этот файл — полный, самодостаточный снимок текущей архитектуры системы. "
            "Передайте его новому Оркестратору в чистом окружении, чтобы он восстановил "
            "структуру агентов, их скилы, задачи и базу знаний."
        )
        lines.append("")
        lines.append("## 1. Обзор системы")
        lines.append(f"- Всего субагентов: {state['agents_count']}")
        lines.append(f"- Всего задач: {len(state['tasks'])}")
        lines.append(f"- Записей в глобальной базе знаний: {len(state['global_knowledge_entries'])}")
        lines.append("")

        lines.append("## 2. Субагенты")
        if not state["agents"]:
            lines.append("_Субагенты пока не созданы._")
        for agent in state["agents"]:
            lines.append(f"### 🤖 {agent['display_name']} (`{agent['name']}`)")
            lines.append(f"- Роль: {agent['role']}")
            lines.append(f"- Задача: {agent['task_description']}")
            lines.append(f"- Путь в репозитории: `{agent['path']}`")
            if agent["skills"]:
                lines.append("- Скилы:")
                for s in agent["skills"]:
                    lines.append(f"  - **{s['name']}** — {s.get('description') or 'без описания'}")
            if agent["knowledge_entries"]:
                lines.append("- Локальная база знаний:")
                for k in agent["knowledge_entries"]:
                    label = "✅" if k["kind"] == "approved" else "⚠️"
                    lines.append(f"  - {label} {k['title']}")
            lines.append("")

        lines.append("## 3. Задачи")
        if not state["tasks"]:
            lines.append("_Задач пока нет._")
        for t in state["tasks"]:
            lines.append(f"- [{t['status']}] #{t['id']} ({t['agent'] or 'без агента'}): {t['title']}")
        lines.append("")

        lines.append("## 4. Глобальная база знаний")
        for entry in state["global_knowledge_entries"]:
            label = "✅ Паттерн" if entry["kind"] == "approved" else "⚠️ Избегать"
            lines.append(f"### {label}: {entry['title']}")
            lines.append(entry["content"])
            lines.append("")

        lines.append("## 5. Инструкция по развёртыванию в новом окружении")
        lines.append(
            "Разверните чистый Оркестратор (`orchestrator/`, `dashboard/`, `run_orchestrator.py`), "
            "затем последовательно отправьте в чат следующие команды, чтобы воссоздать систему:"
        )
        lines.append("")
        step = 1
        for agent in state["agents"]:
            lines.append(f"{step}. Создай агента {agent['display_name']} с ролью {agent['role']} "
                          f"для {agent['task_description']}")
            step += 1
            for s in agent["skills"]:
                lines.append(f"{step}. Добавь агенту {agent['display_name']} скилл {s['name']}")
                step += 1
        lines.append("")

        content = "\n".join(lines)

        main_path = self.export_dir / "META_PROMPT.md"
        main_path.write_text(content, encoding="utf-8")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_path = self.export_dir / "history" / f"META_PROMPT_{ts}.md"
        history_path.write_text(content, encoding="utf-8")

        self._log(f"Сформирован мета-промт экспорта системы: {main_path.name}",
                   action="export")

        return {"path": str(main_path.relative_to(self.base_dir)), "content": content}
