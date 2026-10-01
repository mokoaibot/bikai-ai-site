"""view_skills.py — Навыки: карточки атомарных скилов, привязанных к агентам."""

from __future__ import annotations

import streamlit as st

from components import skill_card


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Инструменты агентов</div>', unsafe_allow_html=True)
    st.title("🛠 Навыки")

    agents = state.get("agents", [])
    all_skills = [(a, s) for a in agents for s in a.get("skills", [])]

    if not all_skills:
        st.info(
            "Скилов пока нет. Добавьте через чат, например: "
            "«Добавь <агент> скилл анализа конкурентов»."
        )
        return

    agent_filter = st.selectbox(
        "Фильтр по агенту", ["Все агенты"] + [a["display_name"] for a in agents]
    )

    cols = st.columns(2)
    i = 0
    for agent, skill in all_skills:
        if agent_filter != "Все агенты" and agent["display_name"] != agent_filter:
            continue
        with cols[i % 2]:
            skill_card(agent["display_name"], skill)
        i += 1
