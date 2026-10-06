"""filemap.py — живой сканер файловой структуры репозитория для вкладки
«Карта системы»: папки, .py/.md файлы, конфиги.

Описания: .py — первый абзац докстринга (ast.get_docstring); .md — заголовок
+ первый абзац; остальное — CURATED_DESC ниже (у JSON/БД/логов докстрингов
нет). Карта обновляется сама при изменении кода; вручную поддерживаются
только CURATED_DESC/INVOCATION для не-кодовых файлов.
"""

from __future__ import annotations

import ast
import html
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    current = start if start.is_dir() else start.parent
    for _ in range(8):
        if (current / ".git").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return start.resolve().parent.parent.parent


BASE_DIR = _find_repo_root(Path(__file__).resolve())

# Папки, которые не показываем вообще (служебные/системные, не часть
# архитектуры, которую имеет смысл объяснять пользователю).
EXCLUDE_DIRS = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".venv", ".cache", ".streamlit", "node_modules",
}

# Папки, у которых МНОГО однотипных сгенерированных/бинарных файлов —
# разворачивать их по одному файлу бессмысленно, показываем одной строкой.
COLLAPSE_DIRS = {
    "directions/bikai/catalog/images": "Фото товаров (WEBP/PNG) — наполняет download_images.py.",
    "directions/bikai/catalog/site": "Собранный сайт каталога (EN + site/ru/) — генерирует build_site.py.",
    "directions/bikai/raw_inputs": "Файлы от клиента (бриф/договор) — не код.",
    "shared/exports/history": "Архив прежних META_PROMPT.md, по файлу на экспорт.",
}

# Описания папок, которые не самоочевидны из содержимого (нет README).
DIR_DESCRIPTIONS = {
    "": "Корень monorepo. Начни с README.md — там главная инструкция и ссылки на остальное.",
    "directions": "По одной папке на каждое направление/клиента (сейчас: bikai).",
    "directions/bikai": "Всё по BIKAI: инструкции, знания, логи, сырые файлы клиента, сам сайт-каталог.",
    "directions/bikai/catalog": "Сайт-каталог BIKAI: скрипты сборки, данные, фото, готовый сайт.",
    "directions/bikai/catalog/scripts": "Ручной пайплайн пересборки каталога — 8 скриптов, запускаются по очереди.",
    "directions/bikai/catalog/data": "Исходные данные каталога: JSON-источник и собранная из него SQLite-база.",
    "directions/bikai/knowledge": "Опыт именно по BIKAI (approved/avoid), отдельно от общего.",
    "directions/bikai/logs": "Лог действий именно по BIKAI.",
    "directions/bikai/raw_inputs": "Файлы, которые прислал клиент по BIKAI (ТЗ, договор и т.п.).",
    "shared": "Общее для всех направлений: знания, логи, методички, экспорт — не привязано к одному клиенту.",
    "shared/knowledge": "Знания уровня всей системы, не привязаны к направлению.",
    "shared/logs": "Общесистемные логи: история чата и лента событий по всем направлениям.",
    "shared/exports": "Снимки архитектуры системы одним Markdown-файлом — для переноса в другую сессию.",
    "shared/playbooks": "Общие методички по типам задач, переиспользуются между направлениями.",
    "engine": "Техника: движок (бывший «оркестратор») + Streamlit-дашборд + файлы состояния. Сюда можно не заглядывать.",
    "engine/dashboard": "Код движка (core/brain/config.py) + Streamlit-интерфейс поверх него.",
    "engine/state": "Файлы состояния движка: system_state.json, tasks.json, orchestrator_settings.json.",
    "local_dropzone": "«Приёмная» для файлов, загружаемых вручную — я разбираю их по папкам directions/*/raw_inputs.",
}

# Руками собранные описания для файлов без докстринга/заголовка
# (JSON/БД/логи/конфиги).
CURATED_DESC = {
    "README.md": "Главная инструкция: что это за репозиторий и куда идти дальше.",
    "engine/state/system_state.json": "Снимок состояния системы (run_audit()): направления, задачи, знания, логи, настройки.",
    "engine/state/tasks.json": "Единый список задач по всем направлениям.",
    "engine/state/orchestrator_settings.json": "Настройки: autonomy_level (самостоятельность) и auto_push (авто-пуш в GitHub).",
    "requirements.txt": "Зависимости дашборда (streamlit, requests). Не сохраняются между запусками песочницы.",
    ".env": "Реальные секреты (токены/ключи). Не коммитится, не показывается.",
    ".env.example": "Шаблон .env — какие переменные нужно заполнить.",
    ".gitignore": "Что Git должен игнорировать (прежде всего .env).",
    "directions/bikai/metadata.json": "Паспорт направления BIKAI: роль, задача, дата создания.",
    "directions/bikai/instructions.json": "Инструкции BIKAI структурированно — то же, что в INSTRUCTIONS.md.",
    "directions/bikai/INSTRUCTIONS.md": "Инструкции BIKAI текстом — перечитываю перед работой по направлению.",
    "directions/bikai/knowledge/entries.json": "Локальные записи опыта BIKAI: approved/avoid.",
    "directions/bikai/knowledge/notes.md": "Те же локальные знания BIKAI читаемыми заметками.",
    "directions/bikai/logs/bikai.log": "Лог действий по направлению BIKAI.",
    "shared/knowledge/approved_patterns.md": "Глобальные паттерны, которые сработали.",
    "shared/knowledge/avoid_mistakes.md": "Глобальные ошибки, которые нельзя повторять.",
    "shared/knowledge/entries.json": "Те же глобальные знания структурированно.",
    "shared/logs/orchestrator.log": "Построчный лог всех действий системы.",
    "shared/logs/activity.jsonl": "Та же история, но в JSON — источник вкладок «Логи»/«Обзор».",
    "shared/logs/chat_history.json": "История сообщений чата с движком.",
    "directions/bikai/catalog/data/products.json": "Данные каталога — товар на словарь (55 шт.). Источник правды.",
    "directions/bikai/catalog/data/bikai_catalog.db": "SQLite-база из products.json (двуязычная), читает build_site.py.",
    "shared/exports/META_PROMPT.md": "Последний снимок архитектуры — из вкладки «Экспорт».",
    "directions/bikai/catalog/bikai_telegram_logo.png": "Логотип BIKAI для Telegram-канала (без текста).",
    "directions/bikai/catalog/README.md": "README каталога: структура, порядок пересборки, покрытие.",
    "directions/bikai/prompts.json": "Журнал реальных промтов для генераций (картинки/тексты) по направлению.",
}

# Как вызывается файл — то, что нельзя вытащить из докстринга.
INVOCATION = {
    "engine/run_orchestrator.py": "`python3 engine/run_orchestrator.py chat \"текст\"` — так я веду направления/задачи/инструкции/знания.",
    "engine/sync_git.py": "Руками (`python3 engine/sync_git.py push|pull|status`) и автоматически из core.py при auto_push().",
    "engine/dashboard/core.py": "Импортируется run_orchestrator.py и dashboard/state.py как класс Orchestrator.",
    "engine/dashboard/brain.py": "Импортируется core.py — разбирает текст в intent (LLM или ключевые слова).",
    "engine/dashboard/config.py": "Импортируется core.py и brain.py — ключи API и пути репозитория.",
    "engine/dashboard/app.py": "`streamlit run engine/dashboard/app.py --server.port 8501 --server.address 0.0.0.0`.",
    "engine/dashboard/state.py": "Импортируется app.py — кэширует Orchestrator на процесс дашборда.",
    "engine/dashboard/theme.py": "Импортируется один раз в app.py (inject_css()) — только CSS.",
    "engine/dashboard/components.py": "Импортируется каждым view_*.py — общие визуальные блоки.",
    "engine/dashboard/filemap.py": "Импортируется view_map.py — сканирует файлы для этой вкладки.",
    "directions/bikai/catalog/scripts/build_data.py": "Шаг 1: `python3 scripts/build_data.py` → products.json.",
    "directions/bikai/catalog/scripts/translate_catalog.py": "Шаг 2: `python3 scripts/translate_catalog.py` → ru-блок в products.json.",
    "directions/bikai/catalog/scripts/ru_glossary.py": "Не запускается отдельно — импортируется translate_catalog.py.",
    "directions/bikai/catalog/scripts/download_images.py": "Шаг 3: `python3 scripts/download_images.py` → фото в images/.",
    "directions/bikai/catalog/scripts/convert_images_to_webp.py": "Шаг 4: `python3 scripts/convert_images_to_webp.py` → PNG→WEBP.",
    "directions/bikai/catalog/scripts/build_db.py": "Шаг 5: `python3 scripts/build_db.py` → bikai_catalog.db.",
    "directions/bikai/catalog/scripts/build_site.py": "Шаг 6: `python3 scripts/build_site.py` → site/ (EN+RU).",
    "directions/bikai/catalog/scripts/qa_check_links.py": "Шаг 7, QA: `python3 scripts/qa_check_links.py` (нужен локальный сервер).",
}

VIEW_PAGE_LABEL = {
    "engine/dashboard/view_map.py": "Карта системы",
    "engine/dashboard/view_overview.py": "Обзор",
    "engine/dashboard/view_projects.py": "Проекты",
    "engine/dashboard/view_tasks.py": "Задачи",
    "engine/dashboard/view_instructions.py": "Инструкции",
    "engine/dashboard/view_knowledge.py": "База знаний",
    "engine/dashboard/view_activity.py": "Логи",
    "engine/dashboard/view_export.py": "Экспорт",
}

TYPE_LABEL = {
    "dir": "DIR", "py": "PY", "md": "MD", "json": "JSON", "jsonl": "JSONL",
    "log": "LOG", "db": "DB", "img": "IMG", "env": "ENV", "cfg": "CFG",
    "html": "HTML", "css": "CSS", "txt": "TXT", "other": "FILE",
}

SUFFIX_TYPE = {
    ".py": "py", ".md": "md", ".json": "json", ".jsonl": "jsonl",
    ".log": "log", ".db": "db", ".sqlite": "db",
    ".png": "img", ".jpg": "img", ".jpeg": "img", ".webp": "img", ".svg": "img",
    ".html": "html", ".css": "css", ".txt": "txt",
}


def _file_type(path: Path) -> str:
    if path.name in (".env", ".env.example"):
        return "env"
    if path.name == ".gitignore":
        return "cfg"
    return SUFFIX_TYPE.get(path.suffix.lower(), "other")


def _py_doc(path: Path) -> str:
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
        doc = ast.get_docstring(tree)
    except Exception:
        doc = None
    if not doc:
        return "Без докстринга — описание недоступно автоматически."
    # Первый абзац (до пустой строки), в одну строку.
    first_para = doc.strip().split("\n\n")[0]
    first_para = " ".join(line.strip() for line in first_para.splitlines())
    return first_para[:420] + ("…" if len(first_para) > 420 else "")


def _md_doc(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return "Markdown-файл."
    title = None
    paragraph_lines: list[str] = []
    seen_title = False
    for line in lines:
        stripped = line.strip()
        if not seen_title and stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            seen_title = True
            continue
        if seen_title:
            if not stripped:
                if paragraph_lines:
                    break
                continue
            if stripped.startswith("#") or stripped.startswith("```"):
                if paragraph_lines:
                    break
                continue
            paragraph_lines.append(stripped)
    paragraph = " ".join(paragraph_lines)
    text = title or ""
    if paragraph:
        text = f"{text}. {paragraph}" if text else paragraph
    text = text.strip() or "Markdown-файл без заголовка."
    return text[:420] + ("…" if len(text) > 420 else "")


def _count_files(path: Path) -> int:
    try:
        return sum(1 for p in path.rglob("*") if p.is_file())
    except Exception:
        return 0


def _node(path: Path, depth: int) -> dict:
    rel = path.relative_to(BASE_DIR).as_posix() if path != BASE_DIR else ""

    if path.is_dir():
        if rel in COLLAPSE_DIRS:
            return {
                "name": path.name or ".",
                "rel": rel,
                "type": "dir",
                "desc": COLLAPSE_DIRS[rel],
                "invoke": None,
                "collapsed_count": _count_files(path),
                "children": [],
            }
        try:
            entries = sorted(
                path.iterdir(),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except Exception:
            entries = []
        children = []
        for entry in entries:
            if entry.is_dir() and entry.name in EXCLUDE_DIRS:
                continue
            if entry.name.startswith(".") and entry.is_dir() and entry.name not in (".git",):
                # скрытые директории кроме явно разрешённых выше уже отфильтрованы EXCLUDE_DIRS;
                # остальные скрытые папки (если появятся) тоже пропускаем, чтобы не плодить шум.
                if entry.name not in COLLAPSE_DIRS:
                    continue
            children.append(_node(entry, depth + 1))
        return {
            "name": path.name or "repo",
            "rel": rel,
            "type": "dir",
            "desc": DIR_DESCRIPTIONS.get(rel, ""),
            "invoke": None,
            "collapsed_count": None,
            "children": children,
        }

    return _describe_file(path, rel)


def _describe_file(path: Path, rel: str) -> dict:
    ftype = _file_type(path)
    if rel in CURATED_DESC:
        desc = CURATED_DESC[rel]
    elif ftype == "py":
        desc = _py_doc(path)
    elif ftype == "md":
        desc = _md_doc(path)
    else:
        desc = CURATED_DESC.get(rel, "")

    invoke = INVOCATION.get(rel)
    if invoke is None and ftype == "py" and rel.startswith("dashboard/view_"):
        label = VIEW_PAGE_LABEL.get(rel, path.name)
        invoke = f"Импортируется app.py и вызывается как render(state, orchestrator), когда в меню выбран пункт «{label}»."

    return {
        "name": path.name,
        "rel": rel,
        "type": ftype,
        "desc": desc,
        "invoke": invoke,
        "collapsed_count": None,
        "children": [],
    }


def describe_path(rel: str) -> dict:
    """Публичный помощник: описание ОДНОГО файла/папки по относительному
    пути — используется там, где нужна карточка конкретного файла в отрыве
    от полного дерева (например, список файлов внутри направления работы
    на вкладке «Проекты»)."""
    path = BASE_DIR / rel
    if not path.exists():
        return {
            "name": rel.rsplit("/", 1)[-1], "rel": rel, "type": "other",
            "desc": "Файл ещё не существует.", "invoke": None,
            "collapsed_count": None, "children": [],
        }
    if path.is_dir():
        if rel in COLLAPSE_DIRS:
            return {
                "name": path.name, "rel": rel, "type": "dir",
                "desc": COLLAPSE_DIRS[rel], "invoke": None,
                "collapsed_count": _count_files(path), "children": [],
            }
        return {
            "name": path.name, "rel": rel, "type": "dir",
            "desc": DIR_DESCRIPTIONS.get(rel, f"Папка, {_count_files(path)} файлов."),
            "invoke": None, "collapsed_count": _count_files(path), "children": [],
        }
    return _describe_file(path, rel)


def build_tree() -> dict:
    """Сканирует BASE_DIR заново при каждом вызове — карта всегда живая."""
    return _node(BASE_DIR, 0)


def flatten(node: dict, trail: str = "") -> list[dict]:
    """Плоский список всех узлов (для поиска/фильтра)."""
    out = [node]
    for child in node.get("children", []):
        out.extend(flatten(child))
    return out


def summary_counts(node: dict) -> dict:
    """Короткая сводка для метрик вкладки: папки / .py / .md / остальные
    явно перечисленные файлы + сколько файлов спрятано в свёрнутых папках."""
    flat = flatten(node)
    dirs = sum(1 for n in flat if n["type"] == "dir" and n["rel"] != "" and n.get("collapsed_count") is None)
    pys = sum(1 for n in flat if n["type"] == "py")
    mds = sum(1 for n in flat if n["type"] == "md")
    listed_files = sum(1 for n in flat if n["type"] != "dir")
    hidden_files = sum(n.get("collapsed_count") or 0 for n in flat if n.get("collapsed_count") is not None)
    return {
        "dirs": dirs,
        "py": pys,
        "md": mds,
        "listed_files": listed_files,
        "hidden_files": hidden_files,
    }


def _esc(text) -> str:
    return html.escape(str(text or ""))


def _esc_code(text) -> str:
    """Экранирует текст, затем превращает `...` в <code>...</code>."""
    import re
    escaped = html.escape(str(text or ""))
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)


# Публичные алиасы для использования из других view_*.py модулей.
esc = _esc
esc_code = _esc_code


def _render_node_html(node: dict, open_dirs: bool) -> str:
    ftype = node["type"]
    label = TYPE_LABEL.get(ftype, "FILE")
    name = _esc(node["name"])

    if ftype == "dir":
        if node.get("collapsed_count") is not None:
            summary = (
                f'<summary><span class="ark-tag">{label}</span> {name} '
                f'<span class="tree-meta">· {node["collapsed_count"]} файлов, свёрнуто</span></summary>'
            )
            body = f'<div class="tree-children"><div class="tree-leaf">{_esc(node["desc"])}</div></div>'
            return f'<details class="tree-agent">{summary}{body}</details>'

        count_label = f'{len(node["children"])} элементов' if node["children"] else "пусто"
        summary = (
            f'<summary><span class="ark-tag">{label}</span> {name or "repo /"} '
            f'<span class="tree-meta">· {count_label}</span></summary>'
        )
        inner_parts = []
        if node["desc"]:
            inner_parts.append(f'<div class="tree-leaf">{_esc(node["desc"])}</div>')
        for child in node["children"]:
            inner_parts.append(_render_node_html(child, open_dirs=False))
        body = f'<div class="tree-children">{"".join(inner_parts)}</div>'
        open_attr = " open" if open_dirs else ""
        return f'<details class="tree-agent"{open_attr}>{summary}{body}</details>'

    # Файл: сворачиваемая карточка с описанием + (если есть) инструкцией вызова.
    summary = f'<summary><span class="ark-tag">{label}</span> {name}</summary>'
    inner = [f'<div class="tree-leaf">{_esc(node["desc"])}</div>']
    if node.get("invoke"):
        inner.append(
            f'<div class="tree-leaf" style="color:#7CE6A6;">'
            f'<strong>Используется:</strong> {_esc_code(node["invoke"])}</div>'
        )
    body = f'<div class="tree-children">{"".join(inner)}</div>'
    return f'<details>{summary}{body}</details>'


def render_tree_html(node: dict) -> str:
    return f'<div class="ark-tree"><details open class="tree-root">' + \
        f'<summary>repo / <span class="tree-meta">· корень</span></summary>' + \
        f'<div class="tree-children">' + \
        "".join(_render_node_html(child, open_dirs=True) for child in node["children"]) + \
        "</div></details></div>"


def search(node: dict, query: str) -> list[dict]:
    query = query.strip().lower()
    if not query:
        return []
    results = []
    for n in flatten(node):
        if n["rel"] == "":
            continue
        haystack = f'{n["rel"]} {n["desc"]}'.lower()
        if query in haystack:
            results.append(n)
    return results
