"""
chat_panel.py — лента команд (read-only "зеркало" чата).

ВАЖНО: это НЕ интерфейс управления. Управление системой происходит в чате
с Оркестратором в Arena (та беседа, где пользователь разговаривает с
ИИ-агентом напрямую — это и есть "мозг" системы). Здесь, в дашборде, мы
только отображаем историю уже выполненных команд (chat_history.json),
которую ведёт orchestrator.core.Orchestrator.handle_chat_message().

Так дашборд остаётся честным "зеркалом": он ничего не решает и не
принимает ввод — он просто показывает, что Оркестратор уже сделал.
"""

from __future__ import annotations

import streamlit as st

from components import esc


def render_chat(orchestrator) -> None:
    """Показывает последние команды и ответы Оркестратора (без возможности ввода)."""
    st.markdown(
        '<div class="ark-logo">'
        '<span class="material-symbols-rounded" style="color:#7CE6A6;font-size:20px;">forum</span>'
        'Лента команд</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Управление системой происходит в чате с Оркестратором в Arena. "
        "Здесь — только журнал уже выполненных команд (зеркало)."
    )

    history = orchestrator.get_chat_history()

    chat_box = st.container(height=380)
    with chat_box:
        if not history:
            st.markdown(
                '<div class="ark-chat-msg assistant">Команд пока не было. Напишите Оркестратору '
                "в основном чате Arena, например: «Создай SEO-агента для анализа ключевых слов» — "
                "и результат появится здесь и во всех разделах дашборда.</div>",
                unsafe_allow_html=True,
            )
        for msg in history[-60:]:
            role_class = "user" if msg["role"] == "user" else "assistant"
            prefix = "🧑 Команда" if msg["role"] == "user" else "🧠 Оркестратор"
            text = esc(msg["text"]).replace("\n", "<br/>")
            st.markdown(
                f'<div class="ark-chat-msg {role_class}"><strong>{prefix}:</strong><br/>{text}</div>',
                unsafe_allow_html=True,
            )
