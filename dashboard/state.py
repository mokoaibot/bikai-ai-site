"""
state.py — доступ дашборда к ядру Оркестратора: кэширует Orchestrator,
обновляет state через run_audit().
"""

from __future__ import annotations

import streamlit as st

from core import Orchestrator


@st.cache_resource(show_spinner=False)
def get_orchestrator() -> Orchestrator:
    # base_dir=None -> Config сам вычислит корень репозитория
    # (на уровень выше dashboard/, где лежит этот файл).
    return Orchestrator(base_dir=None)


def refresh_state() -> dict:
    """Пересканировать репозиторий и вернуть свежий снимок состояния."""
    orchestrator = get_orchestrator()
    return orchestrator.run_audit()
