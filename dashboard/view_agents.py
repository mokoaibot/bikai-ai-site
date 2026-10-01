"""view_agents.py — Агенты: список + карточка с ролью, описанием и путём в репозитории."""

from __future__ import annotations

import streamlit as st

from components import agent_card, badge

KIND_LABELS = {"approved": "Подтверждено", "avoid": "Избегать"}


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Субагенты</div>', unsafe_allow_html=True)
    st.title("Агенты")

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
            st.markdown('<div class="ark-card-title">Скилы</div>', unsafe_allow_html=True)
            for s in selected["skills"]:
                st.markdown(f"- {s['name']}")
        if selected["knowledge_entries"]:
            st.markdown('<div class="ark-card-title" style="margin-top:0.6rem;">Локальные знания</div>', unsafe_allow_html=True)
            for k in selected["knowledge_entries"]:
                st.markdown(
                    f"{badge(KIND_LABELS.get(k['kind'], k['kind']), k['kind'])} {k['title']}",
                    unsafe_allow_html=True,
                )
