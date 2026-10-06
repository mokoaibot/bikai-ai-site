"""view_activity.py — Логи: подробный таймлайн всех системных действий."""

from __future__ import annotations

import streamlit as st

from components import activity_item


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Журнал системы</div>', unsafe_allow_html=True)
    st.title("Логи и активность")
    st.caption("Каждое действие Оркестратора фиксируется здесь с таймстемпом.")

    records = orchestrator.get_recent_activity(limit=300)
    if not records:
        st.info("Активности пока нет.")
    else:
        for r in records:
            activity_item(r)

    with st.expander("Сырой лог global_logs/orchestrator.log"):
        log_path = orchestrator.log_file
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8").splitlines()
            st.code("\n".join(lines[-200:]) or "Лог пуст.", language="log")
        else:
            st.caption("Файл лога не найден.")
