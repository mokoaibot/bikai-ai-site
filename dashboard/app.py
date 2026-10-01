"""
dashboard/app.py — минималистичный премиальный дашборд: "зеркало"
Context-Driven мультиагентной системы.

Единственный инструмент управления системой — чат в сайдбаре (chat_panel.py).
Дашборд ничего не создаёт сам: он лишь читает system_state.json (через
Orchestrator.run_audit) и визуализирует актуальное состояние репозитория.

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

st.set_page_config(page_title="Orchestrator · Control Tower", page_icon="🌲", layout="wide")
inject_css()

orchestrator = get_orchestrator()
state = orchestrator.run_audit()

PAGES = {
    "Обзор": view_overview,
    "Агенты": view_agents,
    "Задачи": view_tasks,
    "Навыки": view_skills,
    "База знаний": view_knowledge,
    "Логи": view_activity,
    "Экспорт": view_export,
}

ICONS = {
    "Обзор": "🧠",
    "Агенты": "🤖",
    "Задачи": "📋",
    "Навыки": "🛠",
    "База знаний": "📚",
    "Логи": "📜",
    "Экспорт": "📤",
}

with st.sidebar:
    st.markdown(
        '<div class="ark-logo"><span class="dot"></span>ORCHESTRATOR</div>'
        '<div style="color:#8FA398;font-size:0.8rem;margin-bottom:1rem;">Context-Driven Control Tower</div>',
        unsafe_allow_html=True,
    )

    page_label = st.radio(
        "Навигация",
        list(PAGES.keys()),
        format_func=lambda p: f"{ICONS[p]}  {p}",
        label_visibility="collapsed",
    )

    st.divider()
    render_chat(orchestrator)

page_module = PAGES[page_label]
page_module.render(state, orchestrator)
