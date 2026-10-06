"""view_overview.py — Обзор: дерево архитектуры, краткая статистика, последние действия."""

from __future__ import annotations

import streamlit as st

from components import render_metrics, render_tree, activity_item, status_dot


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
    st.title("Архитектура в реальном времени")
    st.caption("Текущее состояние репозитория — обновляется мгновенно.")

    autonomy = state.get("settings", {}).get("autonomy_level", "confirm_all")
    autonomy_labels = {
        "full_auto": ("Полная автономия", "Проекты/инструкции/задачи создаются сразу по ходу работы.", True),
        "confirm_agents_only": ("Подтверждение для новых проектов", "Новые проекты — по согласованию, остальное сразу.", False),
        "confirm_all": ("Подтверждение для всего", "Любое изменение сначала предлагается, затем выполняется.", False),
    }
    label, desc, is_on = autonomy_labels.get(autonomy, (autonomy, "", False))

    auto_push = state.get("settings", {}).get("auto_push", False)
    push_label = "включён" if auto_push else "выключен"
    last_push = _last_push_info(orchestrator)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f'<div class="ark-card" style="display:flex;align-items:center;gap:0.6rem;height:100%;">'
            f'{status_dot(is_on)}'
            f'<div><strong>Режим автономии: {label}</strong>'
            f'<div style="color:#8FA398;font-size:0.82rem;">{desc}</div></div></div>',
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f'<div class="ark-card" style="display:flex;align-items:center;gap:0.6rem;height:100%;">'
            f'{status_dot(auto_push)}'
            f'<div><strong>Авто-push в GitHub: {push_label}</strong>'
            f'<div style="color:#8FA398;font-size:0.82rem;">{last_push}</div></div></div>',
            unsafe_allow_html=True,
        )

    tasks = state.get("tasks", [])
    done = sum(1 for t in tasks if t["status"] == "done")
    total_instructions = sum(p["instructions_count"] for p in state.get("projects", []))

    render_metrics([
        (state.get("projects_count", 0), "Проектов"),
        (total_instructions, "Инструкций"),
        (f"{done}/{len(tasks)}", "Задач выполнено"),
        (len(state.get("global_knowledge_entries", [])), "Записей знаний"),
    ])

    st.write("")
    col_tree, col_activity = st.columns([2, 1])

    with col_tree:
        st.markdown('<div class="ark-card-title ark-card-title-lg">Дерево связей</div>', unsafe_allow_html=True)
        render_tree(state)

    with col_activity:
        st.markdown('<div class="ark-card-title ark-card-title-lg">Последние действия</div>', unsafe_allow_html=True)
        records = orchestrator.get_recent_activity(limit=10)
        if not records:
            st.caption("Пока нет записей активности.")
        for r in records:
            activity_item(r)
