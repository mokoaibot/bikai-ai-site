"""
dashboard/app.py — минималистичный премиальный дашборд: "зеркало"
Context-Driven мультиагентной системы.

Чат в сайдбаре (chat_panel.py) — единственный способ вносить изменения.
Сам дашборд ничего не создаёт: он лишь читает system_state.json (через
Orchestrator.run_audit) и визуализирует актуальное состояние репозитория
в реальном времени.

Запуск:
    streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
"""

from __future__ import annotations

import streamlit as st

from theme import inject_css
from state import get_orchestrator
from chat_panel import render_chat

import view_overview
import view_agents
import view_tasks
import view_skills
import view_knowledge
import view_activity
import view_export

st.set_page_config(page_title="Orchestrator · Live Mirror", page_icon="🌲", layout="wide")
inject_css()

orchestrator = get_orchestrator()
state = orchestrator.run_audit()

# Material Symbols — см. https://fonts.google.com/icons (иконка на каждую вкладку)
PAGES = {
    "overview": {"label": "Обзор", "icon": ":material/dashboard:", "module": view_overview},
    "agents": {"label": "Агенты", "icon": ":material/smart_toy:", "module": view_agents},
    "tasks": {"label": "Задачи", "icon": ":material/task_alt:", "module": view_tasks},
    "skills": {"label": "Навыки", "icon": ":material/bolt:", "module": view_skills},
    "knowledge": {"label": "База знаний", "icon": ":material/auto_stories:", "module": view_knowledge},
    "activity": {"label": "Логи", "icon": ":material/receipt_long:", "module": view_activity},
    "export": {"label": "Экспорт", "icon": ":material/ios_share:", "module": view_export},
}

if "page" not in st.session_state:
    st.session_state.page = "overview"

with st.sidebar:
    st.markdown(
        '<div class="ark-logo">'
        '<span class="material-symbols-rounded" style="color:#7CE6A6;">hub</span>'
        'ORCHESTRATOR</div>'
        '<div style="color:#8FA398;font-size:0.8rem;margin-bottom:1.1rem;">'
        'Зеркало системы в реальном времени</div>',
        unsafe_allow_html=True,
    )

    for key, meta in PAGES.items():
        active = st.session_state.page == key
        if st.button(
            meta["label"],
            icon=meta["icon"],
            key=f"nav_{key}",
            type="primary" if active else "secondary",
            use_container_width=True,
        ):
            st.session_state.page = key
            st.rerun()

    st.divider()
    render_chat(orchestrator)

PAGES[st.session_state.page]["module"].render(state, orchestrator)
