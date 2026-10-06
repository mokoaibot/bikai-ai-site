"""
state.py — доступ дашборда к ядру Оркестратора: кэширует Orchestrator,
обновляет state через run_audit().
"""

from __future__ import annotations

import streamlit as st

from core import Orchestrator


@st.cache_resource(show_spinner=False)
def get_orchestrator() -> Orchestrator:
    return Orchestrator(base_dir=BASE_DIR)


def refresh_state() -> dict:
    """Пересканировать репозиторий и вернуть свежий снимок состояния."""
    orchestrator = get_orchestrator()
    return orchestrator.run_audit()
