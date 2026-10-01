"""
state.py — доступ дашборда к ядру Оркестратора. Дашборд ничего не создаёт
напрямую: он лишь читает system_state.json (через run_audit) и вызывает
Orchestrator.handle_chat_message() для чата — единственного канала
управления системой.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from orchestrator.core import Orchestrator  # noqa: E402


@st.cache_resource(show_spinner=False)
def get_orchestrator() -> Orchestrator:
    return Orchestrator(base_dir=BASE_DIR)


def refresh_state() -> dict:
    """Пересканировать репозиторий и вернуть свежий снимок состояния."""
    orchestrator = get_orchestrator()
    return orchestrator.run_audit()
