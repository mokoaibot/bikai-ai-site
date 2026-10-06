"""view_knowledge.py — База знаний: подтверждённые паттерны и то, чего избегать."""

from __future__ import annotations

import streamlit as st

from components import knowledge_card, render_metrics


def _dedupe_content(title: str, content: str) -> str:
    """Если content начинается с повтора title (так исторически писались
    записи), убираем дублирующее начало — короче и легче читать."""
    t = (title or "").strip().rstrip(".")
    c = (content or "").strip()
    if t and c.lower().startswith(t.lower()):
        rest = c[len(t):].lstrip(" .:—-")
        if rest:
            return rest[0].upper() + rest[1:]
    return c


def _matches(entry: dict, query: str) -> bool:
    if not query:
        return True
    q = query.lower()
    return q in entry.get("title", "").lower() or q in entry.get("content", "").lower()


def _section(title: str, entries: list[dict], query: str) -> None:
    approved = [e for e in entries if e.get("kind") == "approved" and _matches(e, query)]
    avoid = [e for e in entries if e.get("kind") == "avoid" and _matches(e, query)]
    if not approved and not avoid:
        return

    st.markdown(
        f'<div class="ark-card-title ark-card-title-lg" style="margin-top:1rem;">{title}</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"✅ Подтверждено · {len(approved)}")
        for e in approved:
            entry = dict(e)
            entry["content"] = _dedupe_content(e.get("title", ""), e.get("content", ""))
            knowledge_card(entry)
    with col2:
        st.caption(f"⚠ Избегать · {len(avoid)}")
        for e in avoid:
            entry = dict(e)
            entry["content"] = _dedupe_content(e.get("title", ""), e.get("content", ""))
            knowledge_card(entry)


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Опыт системы</div>', unsafe_allow_html=True)
    st.title("База знаний")
    st.caption("Через чат: «Запомни паттерн: ...» или «Запомни ошибку <проекта>: ...».")

    global_entries = state.get("global_knowledge_entries", [])
    projects = state.get("projects", [])
    local_entries = [e for p in projects for e in p.get("knowledge_entries", [])]
    all_entries = global_entries + local_entries

    if not all_entries:
        st.info("База знаний пока пуста.")
        return

    render_metrics([
        (len(all_entries), "Всего"),
        (sum(1 for e in all_entries if e.get("kind") == "approved"), "Подтверждено"),
        (sum(1 for e in all_entries if e.get("kind") == "avoid"), "Избегать"),
        (sum(1 for p in projects if p.get("knowledge_entries")), "Проектов с записями"),
    ])

    query = st.text_input(
        "Поиск",
        placeholder="например: расходники, SEO, канал…",
        label_visibility="collapsed",
    )

    _section("Глобально", global_entries, query)
    for project in projects:
        entries = project.get("knowledge_entries", [])
        if entries:
            _section(project["display_name"], entries, query)
