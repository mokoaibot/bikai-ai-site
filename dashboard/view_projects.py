"""
view_projects.py — Проекты: список + карточка с ролью, описанием и путём в
репозитории.

Исполнитель всегда один (я, ИИ-агент). Каждый проект — это именованный
профиль контекста (не отдельный бот), который я открываю и перечитываю,
когда берусь за работу по этому направлению.
"""

from __future__ import annotations

import streamlit as st

from components import project_card, badge

KIND_LABELS = {"approved": "Подтверждено", "avoid": "Избегать"}


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Контекстные профили</div>', unsafe_allow_html=True)
    st.title("Проекты")
    st.caption(
        "Это не отдельные автономные боты — работу по каждому проекту всегда выполняю я "
        "сам, просто у каждого направления есть свой контекст: роль, инструкции и знания."
    )

    projects = state.get("projects", [])
    if not projects:
        st.info(
            "Проекты ещё не заведены. Напишите в чат слева, например: "
            "«Заведи проект SEO для анализа ключевых слов»."
        )
        return

    col_list, col_detail = st.columns([1, 2])

    with col_list:
        st.caption("Выберите проект, чтобы открыть карточку")
        names = [p["display_name"] for p in projects]
        selected_label = st.radio("Проекты", names, label_visibility="collapsed")
        selected = next(p for p in projects if p["display_name"] == selected_label)

    with col_detail:
        project_card(selected)
        if selected["instructions"]:
            st.markdown('<div class="ark-card-title">Инструкции, которые я держу в голове для этого проекта</div>', unsafe_allow_html=True)
            for s in selected["instructions"]:
                st.markdown(f"- **{s['name']}** — {s.get('description') or 'без описания'}")
        if selected["knowledge_entries"]:
            st.markdown('<div class="ark-card-title" style="margin-top:0.6rem;">Локальные знания</div>', unsafe_allow_html=True)
            for k in selected["knowledge_entries"]:
                st.markdown(
                    f"{badge(KIND_LABELS.get(k['kind'], k['kind']), k['kind'])} {k['title']}",
                    unsafe_allow_html=True,
                )
