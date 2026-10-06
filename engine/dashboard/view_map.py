"""view_map.py — «Карта системы»: дерево файлов репозитория + как я обрабатываю чат."""

from __future__ import annotations

import streamlit as st

import filemap
from components import render_metrics, esc, badge


def _pipeline_section(orchestrator) -> None:
    st.markdown('<div class="ark-card-title ark-card-title-lg">Как я обрабатываю ваше сообщение</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ark-card">
        <ul style="margin:0;padding-left:1.1rem;line-height:1.7;">
        <li><strong>Управление</strong> (проект/задача/инструкция/знание) — запускаю
        <code>cli.py chat "..."</code> → intent → запись на диск.</li>
        <li><strong>Сама работа</strong> (каталог, перевод, картинка, сайт) — делаю сам
        инструментами, без Оркестратора.</li>
        <li>После изменений — <code>run_audit()</code> → <code>system_state.json</code>.</li>
        <li>Дашборд при загрузке читает этот файл — сам ничего не пишет.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    records = orchestrator.get_recent_activity(limit=500)
    example_in = next((r for r in records if r.get("action") == "chat_in"), None)
    example_out = next((r for r in records if r.get("action") == "chat_out"), None)
    if example_in and example_out:
        with st.expander("Пример из лога"):
            st.markdown(
                f"""
                <div class="ark-chat-msg user"><strong>Вы:</strong> {esc(example_in['message'].replace('Получена команда в чате: ', ''))}</div>
                <div class="ark-chat-msg assistant"><strong>Я:</strong> {esc(example_out['message'].replace('Ответ ассистента: ', ''))}</div>
                """,
                unsafe_allow_html=True,
            )


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Что где лежит</div>', unsafe_allow_html=True)
    st.title("Карта системы")
    st.caption("Файлы и папки репозитория — вживую, из докстрингов и README.")

    tree = filemap.build_tree()
    counts = filemap.summary_counts(tree)

    render_metrics([
        (counts["dirs"], "Папок"),
        (counts["py"], "Python-скриптов"),
        (counts["md"], "Markdown-файлов"),
        (counts["hidden_files"], "В свёрнутых папках"),
    ])

    st.write("")
    _pipeline_section(orchestrator)

    st.write("")
    st.markdown('<div class="ark-card-title ark-card-title-lg">Дерево файлов</div>', unsafe_allow_html=True)

    query = st.text_input(
        "Поиск",
        placeholder="webp, build_site, telegram, instructions…",
        label_visibility="collapsed",
    )

    if query:
        results = filemap.search(tree, query)
        if not results:
            st.info("Ничего не найдено.")
        else:
            for n in results:
                type_badge = badge(filemap.TYPE_LABEL.get(n["type"], "FILE"), "todo")
                invoke_html = (
                    f'<div style="color:#7CE6A6;margin-top:0.25rem;">{filemap.esc_code(n["invoke"])}</div>'
                    if n.get("invoke") else ""
                )
                st.markdown(
                    f"""
                    <div class="ark-card">
                        {type_badge} <code>{esc(n['rel'])}</code>
                        <div style="color:#8FA398;margin-top:0.35rem;">{esc(n['desc'])}</div>
                        {invoke_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.markdown(filemap.render_tree_html(tree), unsafe_allow_html=True)
