"""view_instructions.py — Инструкции: текстовые памятки по проектам."""

from __future__ import annotations

import streamlit as st

from components import instruction_card


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">По проектам</div>', unsafe_allow_html=True)
    st.title("Инструкции")

    projects = state.get("projects", [])
    all_instructions = [(p, s) for p in projects for s in p.get("instructions", [])]

    if not all_instructions:
        st.info(
            "Инструкций пока нет. Добавьте через чат, например: "
            "«Добавь <проект> инструкцию анализа конкурентов»."
        )
        return

    project_filter = st.selectbox(
        "Фильтр по проекту", ["Все проекты"] + [p["display_name"] for p in projects]
    )

    cols = st.columns(2)
    i = 0
    for project, instruction in all_instructions:
        if project_filter != "Все проекты" and project["display_name"] != project_filter:
            continue
        with cols[i % 2]:
            instruction_card(project["display_name"], instruction)
        i += 1
