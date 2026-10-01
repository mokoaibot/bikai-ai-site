"""
dashboard/app.py — минималистичный премиальный дашборд: "зеркало"
Context-Driven системы с ОДНИМ исполнителем.

Исполнитель — ИИ-агент, работающий в чате Arena (тот же, кто читает этот
код). "Проекты" ниже — не отдельные автономные боты, а именованные профили
контекста (роль, инструкции, знания, задачи) для разных направлений
работы. Управление системой происходит в чате с этим исполнителем (вне
этого дашборда). Сам дашборд ничего не создаёт: он лишь читает
system_state.json (через Orchestrator.run_audit) и визуализирует
актуальное состояние репозитория в реальном времени.

Запуск:
    streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
"""

from __future__ import annotations

import streamlit as st

from theme import inject_css
from state import get_orchestrator

import view_overview
import view_projects
import view_tasks
import view_instructions
import view_knowledge
import view_activity
import view_export

st.set_page_config(page_title="Orchestrator · Live Mirror", layout="wide")
inject_css()

orchestrator = get_orchestrator()
state = orchestrator.run_audit()

# Одни и те же иконки используются и в раскрытом сайдбаре (иконка + текст),
# и в свёрнутой иконочной панели (только иконка) — чтобы разделы было легко
# соотнести между собой в обоих состояниях.
PAGES = {
    "overview": {"label": "Обзор", "icon": ":material/space_dashboard:", "module": view_overview},
    "projects": {"label": "Проекты", "icon": ":material/folder:", "module": view_projects},
    "tasks": {"label": "Задачи", "icon": ":material/checklist:", "module": view_tasks},
    "instructions": {"label": "Инструкции", "icon": ":material/bolt:", "module": view_instructions},
    "knowledge": {"label": "База знаний", "icon": ":material/menu_book:", "module": view_knowledge},
    "activity": {"label": "Логи", "icon": ":material/history:", "module": view_activity},
    "export": {"label": "Экспорт", "icon": ":material/ios_share:", "module": view_export},
}

if "page" not in st.session_state:
    st.session_state.page = "overview"


def _go(key: str) -> None:
    st.session_state.page = key
    st.rerun()


with st.sidebar:
    st.markdown(
        '<div class="ark-logo"><span class="dot"></span>ORCHESTRATOR</div>'
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
            _go(key)

# Свёрнутая иконочная панель: невидима, пока боковая панель раскрыта;
# появляется и остаётся кликабельной, когда пользователь сворачивает
# боковую панель стандартной стрелкой Streamlit.
with st.container(key="ark_rail"):
    for key, meta in PAGES.items():
        active = st.session_state.page == key
        if st.button(
            "",
            icon=meta["icon"],
            key=f"rail_{key}",
            type="primary" if active else "secondary",
            help=meta["label"],
        ):
            _go(key)

PAGES[st.session_state.page]["module"].render(state, orchestrator)
