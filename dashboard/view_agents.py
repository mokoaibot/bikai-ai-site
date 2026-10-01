"""view_agents.py — Агенты: список + карточка с ролью, описанием и путём в репозитории."""

from __future__ import annotations

import streamlit as st

from components import agent_card


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Субагенты</div>', unsafe_allow_html=True)
    st.title("🤖 Агенты")

    agents = state.get("agents", [])
    if not agents:
        st.info(
            "Субагенты ещё не созданы. Напишите в чат слева, например: "
            "«Создай SEO-агента для анализа ключевых слов»."
        )
        return

    col_list, col_detail = st.columns([1, 2])

    with col_list:
        st.caption("Выберите агента, чтобы открыть карточку")
        names = [a["display_name"] for a in agents]
        selected_label = st.radio("Агенты", names, label_visibility="collapsed")
        selected = next(a for a in agents if a["display_name"] == selected_label)

    with col_detail:
        agent_card(selected)
        if selected["skills"]:
            st.markdown("**🛠 Скилы:**")
            for s in selected["skills"]:
                st.markdown(f"- {s['name']}")
        if selected["knowledge_entries"]:
            st.markdown("**📚 Локальные знания:**")
            for k in selected["knowledge_entries"]:
                icon = "✅" if k["kind"] == "approved" else "⚠️"
                st.markdown(f"- {icon} {k['title']}")
