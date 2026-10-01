"""
components.py — переиспользуемые визуальные блоки дашборда
(дерево архитектуры, метрики, карточки, бейджи).
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


def render_tree(state: dict) -> None:
    """Рендерит интерактивное дерево: Оркестратор -> Агенты -> Скилы."""
    agents = state.get("agents", [])
    html_parts = ['<div class="ark-tree">']
    html_parts.append('<details open class="tree-root"><summary>🧠 Главный Оркестратор '
                       f'<span class="tree-meta">· агентов: {len(agents)}</span></summary>')
    html_parts.append('<div class="tree-children">')

    if not agents:
        html_parts.append(
            '<div class="tree-leaf">Субагентов пока нет — создайте первого через чат слева 👈</div>'
        )
    else:
        for agent in agents:
            skills = agent.get("skills", [])
            html_parts.append(
                f'<details open class="tree-agent"><summary>🤖 {esc(agent["display_name"])} '
                f'<span class="tree-meta">· {esc(agent.get("role",""))} · скилов: {len(skills)} · '
                f'логов: {agent.get("log_lines",0)}</span></summary>'
            )
            html_parts.append('<div class="tree-children">')
            if skills:
                for s in skills:
                    html_parts.append(f'<div class="tree-leaf">🛠 {esc(s["name"])}</div>')
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
            <div class="ark-eyebrow">СУБАГЕНТ</div>
            <h4 style="margin:0 0 0.3rem 0;">🤖 {esc(agent['display_name'])}</h4>
            <p style="color:#8FA398;margin:0 0 0.5rem 0;">{esc(agent.get('role',''))}</p>
            <p style="margin:0 0 0.6rem 0;">{esc(agent.get('task_description',''))}</p>
            <p style="font-size:0.8rem;color:#8FA398;margin:0;">
                📁 <code>{esc(agent.get('path',''))}</code><br/>
                🕒 создан: {esc(agent.get('created_at','—'))}<br/>
                🛠 скилов: {len(skills)} &nbsp;·&nbsp; 📚 знаний: {len(knowledge)} &nbsp;·&nbsp;
                📜 логов: {agent.get('log_lines', 0)}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def skill_card(agent_display_name: str, skill: dict) -> None:
    st.markdown(
        f"""
        <div class="ark-card">
            <div class="ark-eyebrow">СКИЛ · {esc(agent_display_name)}</div>
            <h4 style="margin:0 0 0.3rem 0;">🛠 {esc(skill['name'])}</h4>
            <p style="color:#8FA398;margin:0;">{esc(skill.get('description') or 'без описания')}</p>
            <p style="font-size:0.78rem;color:#8FA398;margin-top:0.4rem;">
                📄 <code>{esc(skill.get('file',''))}</code> &nbsp;·&nbsp; создан: {esc(skill.get('created_at','—'))}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def knowledge_card(entry: dict, scope_label: str) -> None:
    kind = entry.get("kind", "approved")
    kind_badge = badge("✅ сработало" if kind == "approved" else "⚠️ избегать", kind)
    st.markdown(
        f"""
        <div class="ark-card">
            <div class="ark-eyebrow">{esc(scope_label)}</div>
            {kind_badge}
            <h4 style="margin:0.4rem 0 0.3rem 0;">{esc(entry.get('title',''))}</h4>
            <p style="color:#8FA398;margin:0;">{esc(entry.get('content',''))}</p>
            <p style="font-size:0.75rem;color:#8FA398;margin-top:0.4rem;">🕒 {esc(entry.get('created_at','—'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def task_row(task: dict) -> None:
    status_labels = {"todo": "К выполнению", "in_progress": "В процессе", "done": "Готово"}
    status = task.get("status", "todo")
    st.markdown(
        f"""
        <div class="ark-card" style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <span style="color:#8FA398;font-size:0.8rem;">#{task['id']} · {esc(task.get('agent') or 'без агента')}</span>
                <h4 style="margin:0.2rem 0 0 0;">{esc(task['title'])}</h4>
            </div>
            <div>{badge(status_labels.get(status, status), status)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


ACTION_ICONS = {
    "system_init": "🟢",
    "create_agent": "🤖",
    "create_agent_skipped": "⚪",
    "delete_agent": "🗑",
    "add_skill": "🛠",
    "create_task": "📋",
    "update_task": "🔄",
    "add_knowledge": "📚",
    "chat_in": "💬",
    "chat_out": "🤝",
    "export": "📤",
    "error": "⚠️",
    "info": "ℹ️",
}


def activity_item(record: dict) -> None:
    icon = ACTION_ICONS.get(record.get("action", "info"), "•")
    st.markdown(
        f"""
        <div class="ark-log-line">
            <strong style="color:#7CE6A6;">{icon}</strong>
            &nbsp;<span style="color:#8FA398;">{esc(record.get('timestamp',''))}</span>
            &nbsp;— {esc(record.get('message',''))}
        </div>
        """,
        unsafe_allow_html=True,
    )
