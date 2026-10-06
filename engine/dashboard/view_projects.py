"""view_projects.py — Проекты: карточка + дерево направлений работы
(переводы/сайт/SEO/брендбук) с файлами и промтами по каждому."""

from __future__ import annotations

import json

import streamlit as st

import filemap
from components import project_card, badge, esc

KIND_LABELS = {"approved": "Подтверждено", "avoid": "Избегать"}

STATUS_LABELS = {
    "done": ("done", "готово"),
    "in_progress": ("in_progress", "в процессе"),
    "not_started": ("todo", "не начато"),
}


def _load_prompts(project_path: str) -> list[dict]:
    path = filemap.BASE_DIR / project_path / "prompts.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _file_node_html(rel: str) -> str:
    info = filemap.describe_path(rel)
    type_badge = f'<span class="ark-tag">{filemap.TYPE_LABEL.get(info["type"], "FILE")}</span>'
    summary = f'<summary>{type_badge} <code>{esc(rel)}</code></summary>'
    inner = [f'<div class="tree-leaf">{esc(info["desc"])}</div>']
    if info.get("invoke"):
        inner.append(
            f'<div class="tree-leaf" style="color:#7CE6A6;">'
            f'<strong>Используется:</strong> {filemap.esc_code(info["invoke"])}</div>'
        )
    if info.get("collapsed_count") is not None and info["type"] == "dir":
        inner.append(f'<div class="tree-leaf">Файлов внутри: {info["collapsed_count"]}.</div>')
    return f'<details>{summary}<div class="tree-children">{"".join(inner)}</div></details>'


def _prompt_node_html(prompt: dict) -> str:
    exact_note = (
        ""
        if prompt.get("exact", True)
        else f'<div class="tree-leaf" style="color:#E6C97C;">⚠ {esc(prompt.get("note", "Реконструировано по памяти, не дословно."))}</div>'
    )
    summary = f'<summary><span class="ark-tag">PROMPT</span> {esc(prompt["title"])}</summary>'
    inner = (
        f'<div class="tree-leaf">Инструмент: {esc(prompt.get("tool", "—"))}</div>'
        f'<div class="tree-leaf" style="color:#E9EFEA;">«{esc(prompt.get("prompt", ""))}»</div>'
        f'{exact_note}'
    )
    return f'<details>{summary}<div class="tree-children">{inner}</div></details>'


def _render_workstreams(instructions: list[dict], prompts: list[dict]) -> None:
    if not instructions:
        st.info(
            "Направлений работы пока нет. Добавьте через чат: "
            "«Добавь <проект> инструкцию <название>»."
        )
        return

    html_parts = ['<div class="ark-tree">']
    for ins in instructions:
        status = ins.get("status", "in_progress")
        badge_kind, status_label = STATUS_LABELS.get(status, ("in_progress", status))
        files = ins.get("files", [])
        own_prompts = [p for p in prompts if p.get("used_for") in files]

        summary = (
            f'<summary>{esc(ins["name"])} '
            f'<span class="tree-meta">· {badge(status_label, badge_kind)} · файлов: {len(files)}'
            f'{" · промтов: " + str(len(own_prompts)) if own_prompts else ""}</span></summary>'
        )
        inner = [f'<div class="tree-leaf">{esc(ins.get("description") or "без описания")}</div>']
        if not files:
            inner.append('<div class="tree-leaf">Файлов пока не привязано — работа по направлению ещё не начиналась.</div>')
        for rel in files:
            inner.append(_file_node_html(rel))
        for p in own_prompts:
            inner.append(_prompt_node_html(p))

        html_parts.append(
            f'<details class="tree-agent">{summary}'
            f'<div class="tree-children">{"".join(inner)}</div></details>'
        )
    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render(state: dict, orchestrator) -> None:
    st.markdown('<div class="ark-eyebrow">Контекстные профили</div>', unsafe_allow_html=True)
    st.title("Проекты")
    st.caption("Контекст по направлениям: роль, инструкции, знания.")

    projects = state.get("projects", [])
    if not projects:
        st.info(
            "Проекты ещё не заведены. Напишите в чат слева, например: "
            "«Заведи проект SEO для анализа ключевых слов»."
        )
        return

    col_list, col_detail = st.columns([1, 2])

    with col_list:
        st.caption("Выберите проект, чтобы открыть карточку")
        names = [p["display_name"] for p in projects]
        selected_label = st.radio("Проекты", names, label_visibility="collapsed")
        selected = next(p for p in projects if p["display_name"] == selected_label)

    with col_detail:
        project_card(selected)

        prompts = _load_prompts(selected.get("path", ""))

        st.markdown(
            '<div class="ark-card-title ark-card-title-lg" style="margin-top:0.4rem;">'
            'Направления работы</div>',
            unsafe_allow_html=True,
        )
        _render_workstreams(selected.get("instructions", []), prompts)

        if selected["knowledge_entries"]:
            st.markdown('<div class="ark-card-title" style="margin-top:0.6rem;">Локальные знания</div>', unsafe_allow_html=True)
            for k in selected["knowledge_entries"]:
                st.markdown(
                    f"{badge(KIND_LABELS.get(k['kind'], k['kind']), k['kind'])} {k['title']}",
                    unsafe_allow_html=True,
                )
