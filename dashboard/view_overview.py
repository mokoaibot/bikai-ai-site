"""view_overview.py — Обзор: дерево архитектуры, краткая статистика, последние действия."""

from __future__ import annotations

import streamlit as st

from components import render_metrics, render_tree, activity_item


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Обзор системы</div>', unsafe_allow_html=True)
    st.title("🧠 Архитектура в реальном времени")
    st.caption(
        "Это зеркало текущего состояния репозитория. Любое изменение, сделанное через чат, "
        "мгновенно отражается здесь."
    )

    tasks = state.get("tasks", [])
    done = sum(1 for t in tasks if t["status"] == "done")
    total_skills = sum(a["skills_count"] for a in state.get("agents", []))

    render_metrics([
        (state.get("agents_count", 0), "Субагентов"),
        (total_skills, "Скилов"),
        (f"{done}/{len(tasks)}", "Задач выполнено"),
        (len(state.get("global_knowledge_entries", [])), "Записей знаний"),
    ])

    st.write("")
    col_tree, col_activity = st.columns([2, 1])

    with col_tree:
        st.subheader("🗂️ Дерево связей")
        render_tree(state)

    with col_activity:
        st.subheader("📜 Последние действия")
        records = orchestrator.get_recent_activity(limit=10)
        if not records:
            st.caption("Пока нет записей активности.")
        for r in records:
            activity_item(r)
