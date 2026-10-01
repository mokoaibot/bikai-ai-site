"""
chat_panel.py — единственный интерфейс управления системой.

Рендерится в сайдбаре на каждой странице дашборда: пользователь пишет
текстовую команду, Orchestrator.handle_chat_message() интерпретирует её
("ИИ-мозг" из orchestrator.brain) и применяет изменения к файловой системе
monorepo. Дашборд после этого просто перечитывает state и перерисовывается.
"""

from __future__ import annotations

import streamlit as st

from components import esc

EXAMPLES = [
    "Создай SEO-агента для анализа ключевых слов",
    "Добавь SEO скилл анализа конкурентов",
    "Создай задачу для SEO: собрать топ-10 запросов",
    "Запомни паттерн: всегда проверяй источники",
]


def render_chat(orchestrator) -> None:
    st.markdown(
        '<div class="ark-eyebrow">Управление системой</div>'
        '<div class="ark-logo"><span class="dot"></span>Командный чат</div>',
        unsafe_allow_html=True,
    )
    st.caption("Единственный инструмент управления. Просто опишите, что нужно сделать.")

    history = orchestrator.get_chat_history()

    chat_box = st.container(height=380)
    with chat_box:
        if not history:
            st.markdown(
                '<div class="ark-chat-msg assistant">👋 Привет! Я Оркестратор. Опишите, какого '
                "агента создать, какой скилл добавить или какую задачу поставить — я сам пойму "
                "и применю изменения к системе.</div>",
                unsafe_allow_html=True,
            )
        for msg in history[-60:]:
            role_class = "user" if msg["role"] == "user" else "assistant"
            prefix = "🧑 Вы" if msg["role"] == "user" else "🧠 Оркестратор"
            text = esc(msg["text"]).replace("\n", "<br/>")
            st.markdown(
                f'<div class="ark-chat-msg {role_class}"><strong>{prefix}:</strong><br/>{text}</div>',
                unsafe_allow_html=True,
            )

    with st.expander("💡 Примеры команд", expanded=False):
        for ex in EXAMPLES:
            st.markdown(f"- _{ex}_")

    user_input = st.chat_input("Например: «Создай агента для ...»")
    if user_input:
        with st.spinner("Оркестратор обрабатывает команду..."):
            orchestrator.handle_chat_message(user_input)
        st.rerun()
