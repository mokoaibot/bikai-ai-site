"""
core.py — ядро Оркестратора.

РЕАЛЬНАЯ АРХИТЕКТУРА (важно понимать, прежде чем читать код ниже):

Исполнитель во всей этой системе ровно ОДИН — ИИ-агент Arena.ai, работающий
в чате (тот же, кто читает этот код). Никаких независимых субагентов,
которые бы сами запускались и выполняли работу параллельно, здесь нет и
быть не может: в этом окружении нет механизма порождать отдельный
самостоятельный процесс-исполнитель.

Поэтому то, что раньше называлось "агентами", на самом деле — ПРОЕКТЫ:
именованные контейнеры контекста (роль, инструкции, накопленные знания,
задачи, логи) для разных клиентов/направлений работы. Когда пользователь
просит заняться конкретным проектом, именно этот единственный исполнитель
открывает его папку, читает `metadata.json`, `instructions.json`/
`INSTRUCTIONS.md` и `knowledge/`, и затем сам, напрямую, выполняет работу —
а не "запускает" какого-то отдельного бота.

Раньше `create_agent`/`add_skill` генерировали `agent.py` (класс-заглушку
с методом `run()`) и `skills/*.py` (функции-заглушки вида
`return "... ещё не реализован"`), которые никогда реально не исполнялись —
это создавало иллюзию отдельных работающих модулей. Это поведение
полностью убрано: вместо кода теперь создаются и читаются обычные
текстовые инструкции (`instructions.json` + человекочитаемый
`INSTRUCTIONS.md`), которые исполнитель держит в голове/перечитывает
перед работой над проектом.

Context-Driven часть не изменилась: Оркестратор принимает произвольные
текстовые команды (через handle_chat_message), с помощью "ИИ-мозга"
(brain.py) понимает намерение пользователя и материализует его
в реальной файловой структуре monorepo (projects/, global_knowledge/,
tasks.json, логи и т.д.).

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

from config import Config
from brain import Brain


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
    """
    Единственный исполнитель (ИИ-агент Arena.ai), управляемый через чат.

    "Оркестратор" здесь — не отдельная программа, принимающая решения сама
    по себе, а просто название этого файла-ядра: он хранит на диске
    структуру проектов/задач/знаний и применяет к ней команды, которые
    отдаёт исполнитель (я) по ходу разговора с пользователем.
    """

    VALID_STATUSES = ("todo", "in_progress", "done")

    def __init__(self, base_dir: Optional[Path] = None):
        self.config = Config(base_dir=base_dir)
        self.brain = Brain(self.config)

        self.base_dir = self.config.base_dir
        self.projects_dir = self.config.projects_dir
        self.global_knowledge_dir = self.config.global_knowledge_dir
        self.global_logs_dir = self.config.global_logs_dir
        self.log_file = self.config.orchestrator_log_file
        self.state_file = self.config.system_state_file

        self.tasks_file = self.base_dir / "engine" / "state" / "tasks.json"
        self.chat_history_file = self.global_logs_dir / "chat_history.json"
        self.activity_file = self.global_logs_dir / "activity.jsonl"
        self.global_knowledge_manifest = self.global_knowledge_dir / "entries.json"
        self.export_dir = self.base_dir / "shared" / "exports"
        self.settings_file = self.base_dir / "engine" / "state" / "orchestrator_settings.json"

        for d in (
            self.projects_dir,
            self.global_knowledge_dir,
            self.global_logs_dir,
            self.export_dir,
            self.tasks_file.parent,
            self.settings_file.parent,
            self.state_file.parent,
        ):
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
        "full_auto": "Полная автономия — веду проекты/инструкции/задачи сразу по ходу работы, без лишних вопросов.",
        "confirm_agents_only": "Веду инструкции и задачи сразу, но для НОВОГО проекта сначала спрашиваю подтверждение.",
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
        """Динамически импортирует engine/sync_git.py (не пакет, а скрипт)."""
        module_name = "sync_git"
        if module_name in sys.modules:
            return sys.modules[module_name]
        spec = importlib.util.spec_from_file_location(module_name, self.base_dir / "engine" / "sync_git.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def auto_push(self, reason: str = "автоматическая синхронизация") -> dict:
        """
        Выполняет push в GitHub прямо сейчас (используется и автоматикой, и
        мной вручную, когда я сам решаю, что пора сохранить прогресс).
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
        projects = [self._read_project_metadata(p) for p in self._project_dirs()]
        tasks = self._load_tasks()
        return {"projects": projects, "tasks": tasks}

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
            if action == "create_project":
                reply = self._apply_create_project(intent)
            elif action == "add_instruction":
                reply = self._apply_add_instruction(intent)
            elif action == "create_task":
                reply = self._apply_create_task(intent)
            elif action == "update_task_status":
                reply = self._apply_update_task_status(intent)
            elif action == "add_knowledge":
                reply = self._apply_add_knowledge(intent)
            elif action == "delete_project":
                reply = self._apply_delete_project(intent)
            elif action == "query_status":
                reply = self._apply_query_status()
            elif action == "empty":
                reply = "Напишите команду, например: «Заведи проект SEO для анализа ключевых слов»."
            else:
                reply = (
                    "Не удалось распознать команду. Попробуйте, например:\n"
                    "• «Заведи проект-переводчик для перевода документов»\n"
                    "• «Добавь переводчику инструкцию по работе со словарями»\n"
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

    def _apply_create_project(self, intent: dict) -> str:
        name_hint = intent.get("name") or "project"
        role = intent.get("role") or f"{name_hint.capitalize()}-проект"
        task_description = intent.get("task_description") or "Задача не уточнена."
        result = self.create_project(name_hint, role=role, task_description=task_description)
        if result["status"] == "exists":
            return f"Проект «{result['name']}» уже существует в системе (папка `{result['path']}`)."
        self.maybe_auto_push(f"создан проект {result['name']}")
        return (
            f"✅ Создан новый проектный профиль **{result['name']}**\n"
            f"- Роль (для меня в контексте этого проекта): {role}\n"
            f"- Задача: {task_description}\n"
            f"- Папка: `{result['path']}`\n"
            f"Это не отдельный бот — работу по этому проекту по-прежнему делаю я сам, "
            f"просто теперь у меня есть именованный контекст для него."
        )

    def _apply_add_instruction(self, intent: dict) -> str:
        project_name = intent.get("project")
        if not project_name:
            hint = intent.get("project_hint")
            return self._project_not_found_reply(hint)
        instruction_title = intent.get("instruction_name") or "новая инструкция"
        result = self.add_instruction(project_name, instruction_title)
        return (
            f"🛠 В проект **{project_name}** добавлена инструкция: «{result['instruction_title']}»\n"
            f"Файл: `{result['path']}` — я буду сверяться с ним, когда работаю над этим проектом."
        )

    def _apply_create_task(self, intent: dict) -> str:
        project_name = intent.get("project")
        title = intent.get("title") or "Новая задача"
        task = self.create_task(project_name, title)
        who = project_name or "без привязки к проекту"
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
        project_name = intent.get("project")
        if scope == "local" and not project_name:
            return self._project_not_found_reply(None)
        kind = intent.get("kind", "approved")
        content = intent.get("content") or "Без описания."
        entry = self.add_knowledge(scope=scope, kind=kind, content=content, project_name=project_name)
        kind_ru = "✅ успешный паттерн" if kind == "approved" else "⚠️ ошибка, которой нужно избегать"
        where = "глобальную базу" if scope == "global" else f"локальную базу проекта «{project_name}»"
        return f"📚 В {where} добавлена запись ({kind_ru}): {entry['title']}"

    def _apply_delete_project(self, intent: dict) -> str:
        project_name = intent.get("project")
        if not project_name:
            return self._project_not_found_reply(intent.get("raw_mention"))
        ok = self.delete_project(project_name)
        if ok:
            self.maybe_auto_push(f"удалён проект {project_name}")
            return f"🗑 Проект «{project_name}» и все его файлы удалены из системы."
        return f"Проект «{project_name}» не найден."

    def _apply_query_status(self) -> str:
        state = self.run_audit()
        counts = {"todo": 0, "in_progress": 0, "done": 0}
        for t in state["tasks"]:
            counts[t["status"]] = counts.get(t["status"], 0) + 1
        return (
            f"📊 Текущее состояние системы:\n"
            f"- Исполнитель: один (я), проекты ниже — это контекст, а не отдельные боты.\n"
            f"- Проектов: {state['projects_count']}\n"
            f"- Инструкций всего: {sum(p['instructions_count'] for p in state['projects'])}\n"
            f"- Задач: {len(state['tasks'])} (todo: {counts['todo']}, "
            f"в процессе: {counts['in_progress']}, готово: {counts['done']})\n"
            f"- Записей в глобальной базе знаний: {len(state['global_knowledge_entries'])}"
        )

    def _project_not_found_reply(self, hint: Optional[str]) -> str:
        projects = [self._read_project_metadata(p) for p in self._project_dirs()]
        names = ", ".join(p["name"] for p in projects) if projects else "пока нет ни одного проекта"
        hint_part = f" (искал похожее на «{hint}»)" if hint else ""
        return (
            f"Не нашёл подходящего проекта{hint_part}. Существующие проекты: {names}. "
            f"Сначала заведите проект, например: «Заведи проект {hint or 'Имя'} для ...»."
        )

    # ------------------------------------------------------------------ #
    # Работа с проектами (контейнеры контекста для единственного исполнителя)
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
        return cls._slugify(name, fallback_prefix="project")

    def _project_dirs(self) -> list[Path]:
        if not self.projects_dir.exists():
            return []
        return sorted(p for p in self.projects_dir.iterdir() if p.is_dir() and not p.name.startswith("."))

    def create_project(self, name: str, role: Optional[str] = None, task_description: str = "") -> dict:
        """
        Создаёт на диске новый проектный профиль: просто папку с метаданными,
        пустым списком инструкций и базой знаний. НИКАКОГО исполняемого кода
        (ни agent.py, ни skills/*.py) не генерируется — это сознательное
        решение: единственный исполнитель — я, и мне не нужен код-заглушка,
        чтобы "представлять" проект, достаточно текста, который я прочитаю.
        """
        safe_name = self._sanitize_name(name)
        project_path = self.projects_dir / safe_name

        if project_path.exists():
            self._log(f"Попытка создать проект '{safe_name}' отклонена: уже существует.",
                       level="WARNING", action="create_project_skipped", project=safe_name)
            return {"status": "exists", "name": safe_name, "path": str(project_path.relative_to(self.base_dir))}

        role = role or f"{name.capitalize()}-проект"

        project_path.mkdir(parents=True)
        (project_path / "knowledge").mkdir()
        (project_path / "logs").mkdir()

        (project_path / "instructions.json").write_text("[]", encoding="utf-8")
        self._render_instructions_md(project_path, safe_name, role, task_description, [])

        (project_path / "knowledge" / "notes.md").write_text(
            f"# База знаний проекта `{safe_name}`\n\n## Роль\n{role}\n\n## Задача\n{task_description}\n",
            encoding="utf-8",
        )
        (project_path / "knowledge" / "entries.json").write_text("[]", encoding="utf-8")

        created_at = datetime.now().isoformat(timespec="seconds")
        project_log_path = project_path / "logs" / f"{safe_name}.log"
        project_log_path.write_text(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] "
            f"Проект '{safe_name}' заведён в системе. Роль: {role}. Задача: {task_description}\n",
            encoding="utf-8",
        )

        metadata = {
            "name": safe_name,
            "display_name": name,
            "role": role,
            "task_description": task_description,
            "created_at": created_at,
            "path": str(project_path.relative_to(self.base_dir)),
        }
        (project_path / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        self._log(
            f"Заведён новый проект '{safe_name}' (роль: {role}).",
            action="create_project", project=safe_name,
        )
        return {"status": "created", "name": safe_name, "path": str(project_path.relative_to(self.base_dir))}

    def delete_project(self, project_name: str) -> bool:
        import shutil

        safe_name = self._sanitize_name(project_name)
        project_path = self.projects_dir / safe_name
        if not project_path.exists():
            return False
        shutil.rmtree(project_path)
        self._log(f"Проект '{safe_name}' удалён из системы.", level="WARNING",
                   action="delete_project", project=safe_name)
        return True

    def _read_project_metadata(self, project_dir: Path) -> dict:
        metadata_path = project_dir / "metadata.json"
        if metadata_path.exists():
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                data.setdefault("name", project_dir.name)
                return data
            except json.JSONDecodeError:
                pass
        return {"name": project_dir.name, "display_name": project_dir.name, "role": "", "task_description": "",
                "created_at": "", "path": str(project_dir.relative_to(self.base_dir))}

    def find_project(self, name_or_mention: str) -> Optional[dict]:
        projects = [self._read_project_metadata(p) for p in self._project_dirs()]
        safe = self._sanitize_name(name_or_mention)
        for p in projects:
            if p["name"] == safe:
                return p
        return self.brain.find_project_mention(name_or_mention, projects)

    # ------------------------------------------------------------------ #
    # Инструкции (то, что раньше называлось "скилами")
    #
    # Это ПРОСТОЙ ТЕКСТ, который читаю я сам, когда берусь за работу по
    # проекту — не отдельный исполняемый модуль и не "способность" у
    # какого-то другого бота. instructions.json хранит структурированный
    # список, INSTRUCTIONS.md — его человекочитаемое отражение.
    # ------------------------------------------------------------------ #

    @staticmethod
    def _render_instructions_md(project_path: Path, project_name: str, role: str,
                                 task_description: str, instructions: list[dict]) -> None:
        lines = [
            f"# Инструкции для проекта `{project_name}`",
            "",
            "Это не код и не отдельный бот — это памятка для меня (единственного",
            "исполнителя), которую я перечитываю перед тем, как взяться за работу",
            "по этому проекту.",
            "",
            f"## Роль в этом проекте\n{role}",
            "",
            f"## Задача\n{task_description}",
            "",
            "## Инструкции",
        ]
        if not instructions:
            lines.append("")
            lines.append("_Пока не добавлено ни одной инструкции._")
        else:
            for ins in instructions:
                lines.append("")
                lines.append(f"### {ins['name']}")
                lines.append(ins.get("description") or "_Без описания._")
        (project_path / "INSTRUCTIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def add_instruction(self, project_name: str, instruction_title: str, description: str = "") -> dict:
        project = self.find_project(project_name)
        if project is None:
            raise ValueError(f"Проект '{project_name}' не найден.")

        project_dir = self.base_dir / project["path"]
        manifest_path = project_dir / "instructions.json"

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            manifest = []

        entry = {
            "name": instruction_title,
            "description": description,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        manifest.append(entry)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        self._render_instructions_md(
            project_dir, project["name"], project.get("role", ""),
            project.get("task_description", ""), manifest,
        )

        self._log(
            f"В проект '{project['name']}' добавлена инструкция: «{instruction_title}».",
            action="add_instruction", project=project["name"],
        )
        return {
            "instruction_title": instruction_title,
            "path": str((project_dir / "INSTRUCTIONS.md").relative_to(self.base_dir)),
        }

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

    def create_task(self, project_name: Optional[str], title: str) -> dict:
        tasks = self._load_tasks()
        next_id = (max((t["id"] for t in tasks), default=0)) + 1

        resolved_project = None
        if project_name:
            project = self.find_project(project_name)
            resolved_project = project["name"] if project else project_name

        task = {
            "id": next_id,
            "project": resolved_project,
            "title": title,
            "status": "todo",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        tasks.append(task)
        self._save_tasks(tasks)

        self._log(
            f"Создана задача #{task['id']} для '{resolved_project or 'системы'}': {title}",
            action="create_task", project=resolved_project, task_id=task["id"],
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

    def add_knowledge(self, scope: str, kind: str, content: str, project_name: Optional[str] = None) -> dict:
        title = content.strip().split(". ")[0][:80] or "Новая запись"
        entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "scope": scope,
            "kind": kind,
            "title": title,
            "content": content,
            "project": None,
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
            project = self.find_project(project_name) if project_name else None
            if project is None:
                raise ValueError(f"Проект '{project_name}' не найден для локальной записи знаний.")
            entry["project"] = project["name"]
            project_dir = self.base_dir / project["path"]
            entries_path = project_dir / "knowledge" / "entries.json"
            try:
                local_manifest = json.loads(entries_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                local_manifest = []
            local_manifest.append(entry)
            entries_path.write_text(json.dumps(local_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            notes_path = project_dir / "knowledge" / "notes.md"
            kind_label = "✅ Сработало хорошо" if kind == "approved" else "⚠️ Следует избегать"
            with open(notes_path, "a", encoding="utf-8") as f:
                f.write(f"\n### {kind_label}: {title}\n{content}\n")

            self._log(f"Добавлена локальная запись знаний проекту '{project['name']}': «{title}».",
                       action="add_knowledge", scope="local", project=project["name"])

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

    def _audit_project(self, project_dir: Path) -> dict:
        metadata = self._read_project_metadata(project_dir)

        manifest_path = project_dir / "instructions.json"
        try:
            instructions = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            instructions = []

        knowledge_entries_path = project_dir / "knowledge" / "entries.json"
        try:
            knowledge_entries = json.loads(knowledge_entries_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            knowledge_entries = []

        total_log_lines = 0
        log_files = []
        logs_dir = project_dir / "logs"
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
            "path": metadata.get("path", str(project_dir.relative_to(self.base_dir))),
            "instructions": instructions,
            "instructions_count": len(instructions),
            "knowledge_entries": knowledge_entries,
            "log_files": log_files,
            "log_lines": total_log_lines,
        }

    def run_audit(self) -> dict:
        """
        Полностью пересканирует репозиторий и формирует актуальный JSON-снимок
        состояния системы (system_state.json): проекты, инструкции, задачи,
        глобальная/локальная база знаний, логи.
        """
        projects = [self._audit_project(p) for p in self._project_dirs()]
        tasks = self._load_tasks()

        state = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "executor": {
                "note": (
                    "Всю работу выполняет один ИИ-исполнитель. 'Проекты' ниже — "
                    "это контейнеры контекста (роль/инструкции/знания/задачи), "
                    "а не отдельные автономные боты."
                ),
            },
            "config": self.config.summary(),
            "settings": self.get_settings(),
            "orchestrator": {
                "log_file": str(self.log_file.relative_to(self.base_dir)),
                "log_lines": self._count_lines(self.log_file),
            },
            "global_knowledge_files": self._audit_global_knowledge_files(),
            "global_knowledge_entries": self._load_global_knowledge_entries(),
            "projects_count": len(projects),
            "projects": projects,
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
        lines.append("# МЕТА-ПРОМТ АРХИТЕКТУРЫ СИСТЕМЫ (ОДИН ИСПОЛНИТЕЛЬ + ПРОЕКТЫ)")
        lines.append("")
        lines.append(f"_Сформировано автоматически: {state['generated_at']}_")
        lines.append("")
        lines.append(
            "Это полный, самодостаточный снимок текущей архитектуры системы. "
            "ВАЖНО: это не описание мультиагентной системы ботов. Работу всегда "
            "выполняет один ИИ-исполнитель (в чате Arena.ai). «Проекты» ниже — "
            "это именованные профили контекста (роль, инструкции, задачи, "
            "накопленные знания), которые исполнитель читает перед тем, как "
            "взяться за работу по конкретному направлению. Передайте этот файл "
            "новому чистому окружению, чтобы восстановить те же проекты, "
            "инструкции, задачи и базу знаний."
        )
        lines.append("")
        lines.append("## 1. Обзор системы")
        lines.append("- Исполнитель: один (ИИ-агент), не разделяется на независимые суб-процессы.")
        lines.append(f"- Всего проектов: {state['projects_count']}")
        lines.append(f"- Всего задач: {len(state['tasks'])}")
        lines.append(f"- Записей в глобальной базе знаний: {len(state['global_knowledge_entries'])}")
        lines.append("")

        lines.append("## 2. Проекты")
        if not state["projects"]:
            lines.append("_Проекты пока не созданы._")
        for project in state["projects"]:
            lines.append(f"### 📁 {project['display_name']} (`{project['name']}`)")
            lines.append(f"- Роль (контекст для исполнителя): {project['role']}")
            lines.append(f"- Задача: {project['task_description']}")
            lines.append(f"- Путь в репозитории: `{project['path']}`")
            if project["instructions"]:
                lines.append("- Инструкции для исполнителя:")
                for ins in project["instructions"]:
                    lines.append(f"  - **{ins['name']}** — {ins.get('description') or 'без описания'}")
            if project["knowledge_entries"]:
                lines.append("- Локальная база знаний:")
                for k in project["knowledge_entries"]:
                    label = "✅" if k["kind"] == "approved" else "⚠️"
                    lines.append(f"  - {label} {k['title']}")
            lines.append("")

        lines.append("## 3. Задачи")
        if not state["tasks"]:
            lines.append("_Задач пока нет._")
        for t in state["tasks"]:
            lines.append(f"- [{t['status']}] #{t['id']} ({t.get('project') or 'без проекта'}): {t['title']}")
        lines.append("")

        lines.append("## 4. Глобальная база знаний")
        for entry in state["global_knowledge_entries"]:
            label = "✅ Паттерн" if entry["kind"] == "approved" else "⚠️ Избегать"
            lines.append(f"### {label}: {entry['title']}")
            lines.append(entry["content"])
            lines.append("")

        lines.append("## 5. Инструкция по развёртыванию в новом окружении")
        lines.append(
            "Разверните чистое ядро (`dashboard/`, `run_orchestrator.py`) "
            "рядом с тем же единственным ИИ-исполнителем, затем последовательно отправьте "
            "в чат следующие команды, чтобы воссоздать те же проектные профили:"
        )
        lines.append("")
        step = 1
        for project in state["projects"]:
            lines.append(f"{step}. Заведи проект {project['display_name']} с ролью {project['role']} "
                          f"для {project['task_description']}")
            step += 1
            for ins in project["instructions"]:
                lines.append(f"{step}. Добавь проекту {project['display_name']} инструкцию: {ins['name']}")
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
