"""
brain.py — "ИИ-мозг" Оркестратора, слой понимания намерений (NLU) в чате.

Напоминание об архитектуре (см. также core.py): исполнитель всегда один —
ИИ-агент Arena.ai. То, что здесь называется "проектом" (раньше —
"агентом"), это просто именованный контейнер контекста. Этот модуль лишь
разбирает свободный текст пользователя в структурированное действие
(Intent); разговорный ввод по привычке может содержать и старые слова
("агент", "скил") — они распознаются как синонимы "проекта"/"инструкции",
чтобы не ломать естественную речь, но по смыслу относятся к одному и тому
же единственному исполнителю.

Стратегия разбора в два уровня:
  1) Если в окружении Arena AI доступен ключ LLM (OPENAI_API_KEY или
     ANTHROPIC_API_KEY) — пробуем честный разбор намерения моделью
     (структурированный JSON-ответ).
  2) Если ключа нет, LLM недоступен или вернул некорректный ответ —
     используем надёжный локальный эвристический разбор на правилах
     (регулярные выражения + ключевые слова русского языка).

Таким образом чат работает всегда, с ключом API или без него.
"""

from __future__ import annotations

import json
import re
from typing import Optional

try:
    import requests
except ImportError:  # requests может отсутствовать в минимальном окружении
    requests = None


# --------------------------------------------------------------------- #
# Ключевые слова / стоп-слова для эвристического разбора
#
# Намеренно распознаём ОБА поколения терминов ("проект" — новое, "агент"/
# "субагент" — старое разговорное) как синонимы одного и того же понятия:
# именованный контекстный профиль для единственного исполнителя. То же
# самое для "инструкция" (новое) и "скил"/"навык" (старое).
# --------------------------------------------------------------------- #

STOPWORDS = {
    "для", "чтобы", "и", "в", "на", "с", "со", "по", "который", "которая",
    "которое", "агента", "агенту", "агент", "агентом", "субагента",
    "субагенту", "субагент", "проекта", "проекту", "проект", "проектом",
    "скил", "скилл", "скилла", "скиллу", "навык", "навыка", "навыку",
    "инструкцию", "инструкции", "инструкция", "задачу", "задачи", "задача",
    "задачей", "знание", "знания", "паттерн", "ошибку", "ошибки", "новый",
    "новая", "новое", "его", "ее", "её", "эту", "этот", "это",
}

CREATE_PROJECT_VERBS = ("созда", "добав", "сдела", "нужен", "нужна", "нужно", "запусти", "разверн", "заведи", "завед")
PROJECT_VERB_STEMS = (
    "созда", "добав", "сдела", "нужн", "запуст", "разверн", "хочу", "хотим",
    "построй", "настрой", "открой", "оформи", "организуй", "заведи", "завед",
)
# Слово-маркер проекта/контекстного профиля (старое "агент" принимается как синоним).
PROJECT_WORDS = ("проект", "агент", "субагент")
INSTRUCTION_WORDS = ("инструкц", "скил", "навык", "инструмент")
TASK_WORDS = ("задач",)
TASK_DONE_WORDS = ("статус", "готов", "выполнен", "заверш", "отметь", "в процесс", "начал", "todo", "в очеред")
KNOWLEDGE_WORDS = ("знани", "паттерн", "сработал", "ошибк", "избега", "запомни", "фидбек", "опыт")
DELETE_WORDS = ("удали", "удалить", "снеси", "убери")
STATUS_QUERY_WORDS = ("покажи", "статус системы", "что у нас", "сколько проект", "сколько агент", "сводка", "статистика")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" \t\n.,:;!?—-")


def _first_group(pattern: str, text: str, flags=re.IGNORECASE):
    m = re.search(pattern, text, flags)
    if m:
        groups = [g for g in m.groups() if g]
        return _clean(groups[-1]) if groups else None
    return None


class Brain:
    """Слой понимания намерений: превращает текст пользователя в Intent."""

    def __init__(self, config):
        self.config = config

    # ------------------------------------------------------------------ #
    # Точка входа
    # ------------------------------------------------------------------ #

    def interpret(self, text: str, context: dict) -> dict:
        """
        Возвращает dict-намерение (intent) с ключами как минимум:
            action: str
            source: "llm" | "rules"
        и дополнительными полями в зависимости от action.
        """
        text = text.strip()
        if not text:
            return {"action": "empty", "source": "rules"}

        llm_intent = self._try_llm(text, context)
        if llm_intent is not None:
            llm_intent["source"] = "llm"
            return llm_intent

        rule_intent = self._interpret_with_rules(text, context)
        rule_intent["source"] = "rules"
        return rule_intent

    # ------------------------------------------------------------------ #
    # Уровень 1: попытка разбора через LLM (если есть ключ)
    # ------------------------------------------------------------------ #

    def _try_llm(self, text: str, context: dict) -> Optional[dict]:
        if requests is None:
            return None

        openai_key = self.config.get_key("OPENAI_API_KEY")
        anthropic_key = self.config.get_key("ANTHROPIC_API_KEY")

        system_prompt = self._build_system_prompt(context)

        if openai_key:
            try:
                return self._call_openai(openai_key, system_prompt, text)
            except Exception:
                return None
        if anthropic_key:
            try:
                return self._call_anthropic(anthropic_key, system_prompt, text)
            except Exception:
                return None
        return None

    @staticmethod
    def _build_system_prompt(context: dict) -> str:
        projects = ", ".join(p["name"] for p in context.get("projects", [])) or "пока нет проектов"
        return (
            "Ты — модуль понимания намерений (NLU) для Оркестратора. ВАЖНО: "
            "исполнитель во всей системе один — ИИ-агент. 'Проекты' — это "
            "именованные контейнеры контекста (роль/инструкции/знания/задачи) "
            "для разных направлений работы, а НЕ отдельные автономные боты. "
            "Проанализируй команду пользователя на русском и верни СТРОГО "
            "JSON без пояснений со следующими возможными action:\n"
            "create_project {name, role, task_description}\n"
            "add_instruction {project, instruction_name, description}\n"
            "create_task {project, title}\n"
            "update_task_status {task_id, status} (status: todo|in_progress|done)\n"
            "add_knowledge {scope (global|local), project, kind (approved|avoid), title, content}\n"
            "delete_project {project}\n"
            "query_status {}\n"
            "unknown {}\n"
            f"Известные существующие проекты (используй их точные имена, если команда "
            f"ссылается на один из них; пользователь может по привычке называть их "
            f"'агентами'): {projects}.\n"
            'Пример ответа: {"action": "create_project", "name": "seo", "role": "SEO-специалист", '
            '"task_description": "анализ ключевых слов"}'
        )

    @staticmethod
    def _call_openai(api_key: str, system_prompt: str, user_text: str) -> Optional[dict]:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    @staticmethod
    def _call_anthropic(api_key: str, system_prompt: str, user_text: str) -> Optional[dict]:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 400,
                "system": system_prompt + "\nОтвечай ТОЛЬКО JSON-объектом, без markdown и пояснений.",
                "messages": [{"role": "user", "content": user_text}],
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        content = resp.json()["content"][0]["text"]
        content = re.sub(r"^```(json)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
        return json.loads(content)

    # ------------------------------------------------------------------ #
    # Уровень 2: надёжный эвристический разбор (без сети и ключей)
    # ------------------------------------------------------------------ #

    @staticmethod
    def find_project_mention(text: str, projects: list[dict]) -> Optional[dict]:
        """
        Ищет упоминание известного проекта в тексте, устойчиво к падежам
        русского языка: пробует полное слово и его укороченные "основы"
        (отбрасывая 1-2 последние буквы), чтобы "переводчику"/"переводчика"
        совпадали с сохранённым проектом "переводчик".
        """
        text_lower = text.lower()
        best = None
        best_len = 0
        for project in projects:
            words = set()
            for raw in (project.get("name", ""), project.get("display_name", "")):
                raw = raw.lower().replace("_", " ").replace("-", " ")
                for word in raw.split():
                    if len(word) >= 3:
                        words.add(word)
            for word in words:
                for cut in range(0, 3):
                    stem = word[: len(word) - cut] if cut else word
                    # Полное слово проверяем всегда (даже короткое, напр. "SEO"),
                    # а укороченные "основы" — только если они не слишком короткие,
                    # чтобы не ловить случайные совпадения.
                    if cut > 0 and len(stem) < 4:
                        continue
                    if len(stem) < 2:
                        continue
                    if stem in text_lower:
                        if len(stem) > best_len:
                            best, best_len = project, len(stem)
                        break
        return best

    def _interpret_with_rules(self, text: str, context: dict) -> dict:
        lower = text.lower()
        projects = context.get("projects", [])

        has = lambda words: any(w in lower for w in words)  # noqa: E731

        # --- удаление проекта ---
        if has(DELETE_WORDS) and has(PROJECT_WORDS):
            mention = self.find_project_mention(text, projects)
            return {"action": "delete_project", "project": mention["name"] if mention else None,
                    "raw_mention": self._extract_project_name_hint(text)}

        # --- запрос статуса ---
        if has(STATUS_QUERY_WORDS) and not has(CREATE_PROJECT_VERBS):
            return {"action": "query_status"}

        # --- обновление статуса задачи ---
        if "задач" in lower and has(TASK_DONE_WORDS) and not has(("созда", "добав", "поставь", "назначь")):
            task_id = _first_group(r"задач[а-яё]*\s*(?:№|#)?\s*(\d+)", text)
            status = "done"
            if any(w in lower for w in ("в процесс", "начал", "начат")):
                status = "in_progress"
            elif any(w in lower for w in ("todo", "в очеред", "не начат")):
                status = "todo"
            return {
                "action": "update_task_status",
                "task_id": int(task_id) if task_id else None,
                "status": status,
            }

        # --- создание задачи ---
        if "задач" in lower and has(("созда", "добав", "поставь", "назначь")):
            mention = self.find_project_mention(text, projects)
            title = (
                _first_group(r"задач[а-яё]*(?:\s+для\s+[^:,]+)?\s*[:\-]\s*(.+)", text)
                or _first_group(r"(?:поставь|назначь)\s+(.+?)\s+(?:для|проекту|агенту)\s+\S+", text)
                or _first_group(r"задач[а-яё]*\s+(.+)", text)
            )
            return {
                "action": "create_task",
                "project": mention["name"] if mention else None,
                "project_hint": self._extract_project_name_hint(text),
                "title": title or _clean(text),
            }

        # --- добавление инструкции ---
        if has(INSTRUCTION_WORDS) and has(("добав", "созда", "научи", "дай")):
            mention = self.find_project_mention(text, projects)
            instruction_name = (
                _first_group(r"(?:инструкц[а-яё]*|скил[а-яё]*|навык[а-яё]*)\s+(.+)", text)
                or _clean(text)
            )
            return {
                "action": "add_instruction",
                "project": mention["name"] if mention else None,
                "project_hint": self._extract_project_name_hint(text),
                "instruction_name": instruction_name,
            }

        # --- добавление знания ---
        if has(KNOWLEDGE_WORDS) and has(("добав", "запомни", "зафиксируй", "учти", "избега")):
            kind = "avoid" if any(w in lower for w in ("ошибк", "избега", "не делай", "плохо")) else "approved"
            mention = self.find_project_mention(text, projects)
            content = (
                _first_group(r"(?:знани[а-яё]*|паттерн[а-яё]*|ошибк[а-яё]*)\s*[:\-]\s*(.+)", text)
                or _first_group(r"запомни[а-яё]*\s*[:\-]?\s*(.+)", text)
                or _clean(text)
            )
            scope = "local" if mention else "global"
            return {
                "action": "add_knowledge",
                "scope": scope,
                "project": mention["name"] if mention else None,
                "kind": kind,
                "content": content,
            }

        # --- создание проекта ---
        if has(PROJECT_WORDS) and has(CREATE_PROJECT_VERBS) and not has(INSTRUCTION_WORDS) and "задач" not in lower:
            name_hint = self._extract_project_name_hint(text)
            role = (
                _first_group(r"(?:с ролью|роль[ьи]?)\s*[:\-]?\s*([^,.\n]+)", text)
            )
            task_description = (
                _first_group(r"(?:для того,? чтобы|для|чтобы)\s+(.+)", text)
            )
            if not task_description:
                task_description = _clean(text)
            return {
                "action": "create_project",
                "name": name_hint,
                "role": role,
                "task_description": task_description,
            }

        return {"action": "unknown", "raw_text": text}

    @staticmethod
    def _extract_project_name_hint(text: str) -> Optional[str]:
        """Пытается вычленить предполагаемое имя проекта из свободного текста."""
        # Явное указание: проект по имени X / с именем X (и старое "агент" как синоним)
        explicit = _first_group(
            r"(?:проект[а-яё]*|агент[а-яё]*|субагент[а-яё]*)\s+(?:по имени|с именем|под именем|именем)\s+([A-Za-zА-Яа-яЁё0-9_\-]+)",
            text,
        )
        if explicit:
            return explicit

        # Слово в кавычках: «Имя» или "Имя"
        quoted = _first_group(r"[«\"]([^»\"]{2,30})[»\"]", text)
        if quoted:
            return quoted

        def _is_verb_or_stop(word: str) -> bool:
            low = word.lower()
            if low in STOPWORDS:
                return True
            return any(low.startswith(stem) for stem in PROJECT_VERB_STEMS)

        # Слово, слитное через дефис с "проект(а)"/"агент(а)" в любую сторону:
        # "SEO-проекта" (слово ДО) или "проекта-переводчика" (слово ПОСЛЕ).
        m = re.search(r"([A-Za-zА-Яа-яЁё0-9]+)-(?:суб)?(?:агент|проект)", text, re.IGNORECASE)
        if m and not _is_verb_or_stop(m.group(1)):
            return m.group(1)

        m = re.search(r"(?:суб)?(?:агент|проект)[а-яё]*-([A-Za-zА-Яа-яЁё0-9]+)", text, re.IGNORECASE)
        if m and not _is_verb_or_stop(m.group(1)):
            return m.group(1)

        # Слово непосредственно перед "проект(ом)" / "агент(а)" через пробел,
        # например "SEO проект" (но не глагол-команда вроде "Заведи проект").
        before = None
        m = re.search(r"([A-Za-zА-Яа-яЁё0-9]+)\s+(?:суб)?(?:агент|проект)", text, re.IGNORECASE)
        if m and not _is_verb_or_stop(m.group(1)):
            before = m.group(1)

        # Слово сразу после "проект(а)" / "агент(а)" через пробел.
        after = None
        m = re.search(r"(?:суб)?(?:агент|проект)[а-яё]*\s+([A-Za-zА-Яа-яЁё0-9]+)", text, re.IGNORECASE)
        if m and not _is_verb_or_stop(m.group(1)):
            after = m.group(1)

        # Если одно из слов начинается с заглавной буквы (похоже на имя собственное),
        # а другое — нет (похоже на прилагательное/описание), предпочитаем заглавное.
        if after and after[0].isupper() and not (before and before[0].isupper()):
            return after
        if before:
            return before
        if after:
            return after

        return None
