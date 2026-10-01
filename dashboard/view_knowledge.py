"""view_knowledge.py — База знаний: глобальные и локальные карточки опыта/фидбека."""

from __future__ import annotations

import streamlit as st

from components import knowledge_card


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Опыт системы</div>', unsafe_allow_html=True)
    st.title("📚 База знаний")
    st.caption(
        "Добавляйте записи через чат: «Запомни паттерн: ...» (глобально) или "
        "«Запомни ошибку <агента>: ...» (локально для агента)."
    )

    tab_global, tab_local = st.tabs(["🌍 Глобальная", "🏠 Локальная (по агентам)"])

    with tab_global:
        entries = state.get("global_knowledge_entries", [])
        if not entries:
            st.info("Глобальная база знаний пока пуста.")
        col1, col2 = st.columns(2)
        approved = [e for e in entries if e["kind"] == "approved"]
        avoid = [e for e in entries if e["kind"] == "avoid"]
        with col1:
            st.markdown("**✅ Что сработало хорошо**")
            for e in approved:
                knowledge_card(e, "Глобально")
        with col2:
            st.markdown("**⚠️ Чего избегать**")
            for e in avoid:
                knowledge_card(e, "Глобально")

    with tab_local:
        agents = state.get("agents", [])
        any_local = any(a.get("knowledge_entries") for a in agents)
        if not any_local:
            st.info("Локальных записей знаний пока нет ни у одного агента.")
        for agent in agents:
            entries = agent.get("knowledge_entries", [])
            if not entries:
                continue
            st.markdown(f"#### 🤖 {agent['display_name']}")
            cols = st.columns(2)
            for i, e in enumerate(entries):
                with cols[i % 2]:
                    knowledge_card(e, f"Локально · {agent['display_name']}")
