"""view_overview.py — Обзор: дерево архитектуры, краткая статистика, последние действия."""

from __future__ import annotations

import streamlit as st

from components import render_metrics, render_tree, activity_item


def _last_push_info(orchestrator) -> str:
    """Короткая сводка о последнем Git-коммите (без обращения к сети)."""
    try:
        sync_git = orchestrator._load_sync_git_module()
        status = sync_git.GitSync(base_dir=orchestrator.base_dir).status()
        if status.get("status") != "ok":
            return "Репозиторий ещё не инициализирован."
        return f"Последний коммит: {status['last_commit']}"
    except Exception:
        return "Статус Git недоступен."


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Обзор системы</div>', unsafe_allow_html=True)
    st.title("🧠 Архитектура в реальном времени")
    st.caption(
        "Это зеркало текущего состояния репозитория. Любое изменение, которое Оркестратор "
        "применяет по вашей команде в чате Arena, мгновенно отражается здесь."
    )

    autonomy = state.get("settings", {}).get("autonomy_level", "confirm_all")
    autonomy_labels = {
        "full_auto": ("🟢", "Полная автономия", "Агенты/скилы/задачи создаются сразу по ходу работы."),
        "confirm_agents_only": ("🟡", "Подтверждение для новых агентов", "Новые агенты — по согласованию, остальное сразу."),
        "confirm_all": ("⚪", "Подтверждение для всего", "Любое изменение сначала предлагается, затем выполняется."),
    }
    icon, label, desc = autonomy_labels.get(autonomy, ("⚪", autonomy, ""))

    auto_push = state.get("settings", {}).get("auto_push", False)
    push_icon = "🟢" if auto_push else "⚪"
    push_label = "включён" if auto_push else "выключен"
    last_push = _last_push_info(orchestrator)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f'<div class="ark-card" style="display:flex;align-items:center;gap:0.6rem;height:100%;">'
            f'<span style="font-size:1.1rem;">{icon}</span>'
            f'<div><strong>Режим автономии: {label}</strong>'
            f'<div style="color:#8FA398;font-size:0.82rem;">{desc}</div></div></div>',
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f'<div class="ark-card" style="display:flex;align-items:center;gap:0.6rem;height:100%;">'
            f'<span style="font-size:1.1rem;">{push_icon}</span>'
            f'<div><strong>Авто-push в GitHub: {push_label}</strong>'
            f'<div style="color:#8FA398;font-size:0.82rem;">{last_push}</div></div></div>',
            unsafe_allow_html=True,
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
