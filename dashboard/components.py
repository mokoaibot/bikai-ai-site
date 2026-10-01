"""
components.py — переиспользуемые визуальные блоки дашборда
(дерево архитектуры, метрики, карточки, статусы).

Стиль — строгий и монохромный: без эмодзи и стоковых иконок,
состояние передаётся цветом текста/рамки и короткими подписями.

Терминология: исполнитель всегда один (ИИ-агент). "Проекты" — контейнеры
контекста (роль/инструкции/знания) для разных направлений работы, а не
отдельные автономные боты. "Инструкции" — обычный текст, который
исполнитель читает и применяет сам, а не код отдельного модуля.
"""

from __future__ import annotations

import html

import streamlit as st


def esc(text: str) -> str:
    return html.escape(str(text or ""))


def metric_card(num, label: str) -> str:
    return f"""
    <div class="ark-metric">
        <div class="num">{esc(num)}</div>
        <div class="label">{esc(label)}</div>
    </div>
    """


def render_metrics(items: list[tuple]) -> None:
    cols = st.columns(len(items))
    for col, (num, label) in zip(cols, items):
        with col:
            st.markdown(metric_card(num, label), unsafe_allow_html=True)


def badge(text: str, kind: str = "todo") -> str:
    return f'<span class="ark-badge {kind}">{esc(text)}</span>'


def status_dot(on: bool) -> str:
    state = "on" if on else "off"
    return f'<span class="ark-status-dot {state}"></span>'


def render_tree(state: dict) -> None:
    """Рендерит дерево: Исполнитель -> Проекты -> Инструкции (без иконок)."""
    projects = state.get("projects", [])
    html_parts = ['<div class="ark-tree">']
    html_parts.append(
        '<details open class="tree-root"><summary>Исполнитель (я) '
        f'<span class="tree-meta">· проектов: {len(projects)}</span></summary>'
    )
    html_parts.append('<div class="tree-children">')

    if not projects:
        html_parts.append(
            '<div class="tree-leaf">Проектов пока нет — заведите первый через чат слева.</div>'
        )
    else:
        for project in projects:
            instructions = project.get("instructions", [])
            html_parts.append(
                f'<details open class="tree-agent"><summary>{esc(project["display_name"])} '
                f'<span class="tree-meta">· {esc(project.get("role",""))} · инструкций: {len(instructions)} · '
                f'логов: {project.get("log_lines",0)}</span></summary>'
            )
            html_parts.append('<div class="tree-children">')
            if instructions:
                for s in instructions:
                    html_parts.append(f'<div class="tree-leaf">{esc(s["name"])}</div>')
            else:
                html_parts.append('<div class="tree-leaf">инструкций пока нет</div>')
            html_parts.append('</div></details>')

    html_parts.append('</div></details></div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def project_card(project: dict) -> None:
    instructions = project.get("instructions", [])
    knowledge = project.get("knowledge_entries", [])
    st.markdown(
        f"""
        <div class="ark-card">
            <div class="ark-eyebrow">Проект (контекст для единственного исполнителя)</div>
            <div class="ark-card-title ark-card-title-lg">{esc(project['display_name'])}</div>
            <p style="color:#8FA398;margin:0 0 0.5rem 0;">{esc(project.get('role',''))}</p>
            <p style="margin:0 0 0.6rem 0;">{esc(project.get('task_description',''))}</p>
            <div class="ark-meta-list">
                <span>Путь: <code>{esc(project.get('path',''))}</code></span>
                <span>Создан: {esc(project.get('created_at','—'))}</span>
                <span>Инструкций: {len(instructions)}</span>
                <span>Знаний: {len(knowledge)}</span>
                <span>Логов: {project.get('log_lines', 0)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def instruction_card(project_display_name: str, instruction: dict) -> None:
    st.markdown(
        f"""
        <div class="ark-card">
            <div class="ark-eyebrow">Инструкция · {esc(project_display_name)}</div>
            <div class="ark-card-title">{esc(instruction['name'])}</div>
            <p style="color:#8FA398;margin:0;">{esc(instruction.get('description') or 'без описания')}</p>
            <div class="ark-meta-list">
                <span>Создано: {esc(instruction.get('created_at','—'))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def knowledge_card(entry: dict, scope_label: str) -> None:
    kind = entry.get("kind", "approved")
    kind_badge = badge("Подтверждено" if kind == "approved" else "Избегать", kind)
    st.markdown(
        f"""
        <div class="ark-card">
            <div class="ark-eyebrow">{esc(scope_label)}</div>
            {kind_badge}
            <div class="ark-card-title" style="margin-top:0.4rem;">{esc(entry.get('title',''))}</div>
            <p style="color:#8FA398;margin:0;">{esc(entry.get('content',''))}</p>
            <div class="ark-meta-list"><span>{esc(entry.get('created_at','—'))}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


STATUS_LABELS = {"todo": "", "in_progress": "в процессе", "done": "готово"}


def task_list_row(task: dict) -> None:
    """Компактная строка списка задач: id, проект, заголовок, простой статус."""
    status = task.get("status", "todo")
    status_text = STATUS_LABELS.get(status, status)
    status_class = f"ark-task-status {status}"
    st.markdown(
        f"""
        <div class="ark-list-row">
            <span class="ark-list-id">#{task['id']}</span>
            <span class="ark-list-title">{esc(task['title'])}</span>
            <span class="ark-list-agent">{esc(task.get('project') or '—')}</span>
            <span class="{status_class}">{esc(status_text)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


ACTION_LABELS = {
    "system_init": "Инициализация",
    "create_project": "Заведён проект",
    "create_project_skipped": "Проект пропущен",
    "delete_project": "Удалён проект",
    "add_instruction": "Добавлена инструкция",
    "create_task": "Создана задача",
    "update_task": "Обновлена задача",
    "add_knowledge": "Добавлено знание",
    "chat_in": "Команда",
    "chat_out": "Ответ",
    "export": "Экспорт",
    "settings_change": "Настройки",
    "auto_push": "Авто-push",
    "auto_push_failed": "Авто-push: ошибка",
    "error": "Ошибка",
    "info": "Инфо",
}


def activity_item(record: dict) -> None:
    action = record.get("action", "info")
    label = ACTION_LABELS.get(action, action)
    st.markdown(
        f"""
        <div class="ark-log-line">
            <span class="ark-tag">{esc(label)}</span>
            <span style="color:#8FA398;">{esc(record.get('timestamp',''))}</span>
            — {esc(record.get('message',''))}
        </div>
        """,
        unsafe_allow_html=True,
    )
