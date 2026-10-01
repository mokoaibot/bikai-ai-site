"""
view_export.py — Экспорт: сборка всей архитектуры и базы знаний в единый
структурированный Markdown (Мета-Промт) для развёртывания системы в новом
чистом окружении.
"""

from __future__ import annotations

import streamlit as st


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Перенос системы</div>', unsafe_allow_html=True)
    st.title("Экспорт (Мета-Промт)")
    st.caption(
        "Соберите всю текущую архитектуру — проекты, инструкции, задачи и базу знаний — "
        "в один Markdown-файл. Исполнитель остаётся тем же единственным ИИ-агентом; "
        "файл лишь восстанавливает контекстные профили проектов в новом окружении."
    )

    if st.button("Сгенерировать мета-промт системы", type="primary"):
        with st.spinner("Собираю архитектуру в единый документ..."):
            result = orchestrator.export_meta_prompt()
        st.success(f"Готово! Сохранено в `{result['path']}`")
        st.session_state["_export_content"] = result["content"]

    export_path = orchestrator.export_dir / "META_PROMPT.md"
    content = st.session_state.get("_export_content")
    if content is None and export_path.exists():
        content = export_path.read_text(encoding="utf-8")

    if content:
        st.download_button(
            "Скачать META_PROMPT.md",
            data=content,
            file_name="META_PROMPT.md",
            mime="text/markdown",
        )
        with st.expander("Предпросмотр документа", expanded=True):
            st.markdown(content)
    else:
        st.info("Мета-промт ещё не сформирован.")
