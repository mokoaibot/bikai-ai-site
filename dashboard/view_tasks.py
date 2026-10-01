"""view_tasks.py — Задачи: канбан-доска со статусами todo / in_progress / done."""

from __future__ import annotations

import streamlit as st

from components import task_row


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Управление работой</div>', unsafe_allow_html=True)
    st.title("📋 Задачи")
    st.caption(
        "Ставьте задачи через чат: «Создай задачу для <агент>: ...». "
        "Меняйте статус командой: «Отметь задачу 3 как готово»."
    )

    tasks = state.get("tasks", [])
    if not tasks:
        st.info("Задач пока нет.")
        return

    columns = {"todo": "🗂 К выполнению", "in_progress": "⚙️ В процессе", "done": "✅ Готово"}
    cols = st.columns(3)
    for col, (status, title) in zip(cols, columns.items()):
        with col:
            st.subheader(title)
            filtered = [t for t in tasks if t["status"] == status]
            if not filtered:
                st.caption("Пусто")
            for t in filtered:
                task_row(t)
