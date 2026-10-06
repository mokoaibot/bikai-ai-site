"""view_tasks.py — Задачи: компактный список со статусами todo / in_progress / done."""

from __future__ import annotations

import streamlit as st

from components import task_list_row


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Управление работой</div>', unsafe_allow_html=True)
    st.title("Задачи")
    st.caption(
        "Ставьте задачи через чат: «Создай задачу для <проект>: ...». "
        "Меняйте статус командой: «Отметь задачу 3 как готово»."
    )

    tasks = state.get("tasks", [])
    if not tasks:
        st.info("Задач пока нет.")
        return

    sections = [
        ("todo", "К выполнению"),
        ("in_progress", "В процессе"),
        ("done", "Готово"),
    ]

    for status, title in sections:
        filtered = [t for t in tasks if t["status"] == status]
        st.markdown(
            f'<div class="ark-eyebrow" style="margin-top:0.8rem;">{title} · {len(filtered)}</div>',
            unsafe_allow_html=True,
        )
        if not filtered:
            st.caption("Пусто")
            continue
        for t in filtered:
            task_list_row(t)
