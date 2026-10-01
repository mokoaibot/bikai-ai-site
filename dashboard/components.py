"""
components.py — переиспользуемые визуальные блоки дашборда
(дерево архитектуры, метрики, карточки, статусы).

Стиль — строгий и монохромный: без эмодзи и стоковых иконок,
состояние передаётся цветом текста/рамки и короткими подписями.
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
    """Рендерит дерево: Оркестратор -> Агенты -> Скилы (без иконок)."""
    agents = state.get("agents", [])
    html_parts = ['<div class="ark-tree">']
    html_parts.append(
        '<details open class="tree-root"><summary>Оркестратор '
        f'<span class="tree-meta">· агентов: {len(agents)}</span></summary>'
    )
    html_parts.append('<div class="tree-children">')

    if not agents:
        html_parts.append(
            '<div class="tree-leaf">Субагентов пока нет — создайте первого через чат слева.</div>'
        )
    else:
        for agent in agents:
            skills = agent.get("skills", [])
            html_parts.append(
                f'<details open class="tree-agent"><summary>{esc(agent["display_name"])} '
                f'<span class="tree-meta">· {esc(agent.get("role",""))} · скилов: {len(skills)} · '
                f'логов: {agent.get("log_lines",0)}</span></summary>'
            )
            html_parts.append('<div class="tree-children">')
            if skills:
                for s in skills:
                    html_parts.append(f'<div class="tree-leaf">{esc(s["name"])}</div>')
            else:
                html_parts.append('<div class="tree-leaf">скилов пока нет</div>')
            html_parts.append('</div></details>')

    html_parts.append('</div></details></div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def agent_card(agent: dict) -> None:
    skills = agent.get("skills", [])
    knowledge = agent.get("knowledge_entries", [])
    st.markdown(
        f"""
        <div class="ark-card">
            <div class="ark-eyebrow">Субагент</div>
            <div class="ark-card-title ark-card-title-lg">{esc(agent['display_name'])}</div>
            <p style="color:#8FA398;margin:0 0 0.5rem 0;">{esc(agent.get('role',''))}</p>
            <p style="margin:0 0 0.6rem 0;">{esc(agent.get('task_description',''))}</p>
            <div class="ark-meta-list">
                <span>Путь: <code>{esc(agent.get('path',''))}</code></span>
                <span>Создан: {esc(agent.get('created_at','—'))}</span>
                <span>Скилов: {len(skills)}</span>
                <span>Знаний: {len(knowledge)}</span>
                <span>Логов: {agent.get('log_lines', 0)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def skill_card(agent_display_name: str, skill: dict) -> None:
    st.markdown(
        f"""
        <div class="ark-card">
            <div class="ark-eyebrow">Скил · {esc(agent_display_name)}</div>
            <div class="ark-card-title">{esc(skill['name'])}</div>
            <p style="color:#8FA398;margin:0;">{esc(skill.get('description') or 'без описания')}</p>
            <div class="ark-meta-list">
                <span>Файл: <code>{esc(skill.get('file',''))}</code></span>
                <span>Создан: {esc(skill.get('created_at','—'))}</span>
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
    """Компактная строка списка задач: id, агент, заголовок, простой статус."""
    status = task.get("status", "todo")
    status_text = STATUS_LABELS.get(status, status)
    status_class = f"ark-task-status {status}"
    st.markdown(
        f"""
        <div class="ark-list-row">
            <span class="ark-list-id">#{task['id']}</span>
            <span class="ark-list-title">{esc(task['title'])}</span>
            <span class="ark-list-agent">{esc(task.get('agent') or '—')}</span>
            <span class="{status_class}">{esc(status_text)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


ACTION_LABELS = {
    "system_init": "Инициализация",
    "create_agent": "Создан агент",
    "create_agent_skipped": "Агент пропущен",
    "delete_agent": "Удалён агент",
    "add_skill": "Добавлен скил",
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
