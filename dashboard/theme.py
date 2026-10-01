"""
theme.py — визуальная тема дашборда: глубокая хвойно-зелёная палитра,
матовый тёмный фон и светло-зелёные акценты. Инжектится один раз в
app.py через inject_css().
"""

import streamlit as st

# Палитра
BG = "#0A0F0C"            # почти чёрный с зелёным подтоном
BG_PANEL = "#111A15"      # матовые панели/карточки
BG_PANEL_2 = "#16211B"    # чуть светлее панели (hover, вложенность)
BORDER = "#24352B"        # тонкие границы
TEXT = "#E9EFEA"          # основной текст (матовый светлый)
TEXT_MUTED = "#8FA398"    # приглушённый серо-зелёный текст
ACCENT = "#7CE6A6"        # светлая хвойная зелень (акцент)
ACCENT_DIM = "#3E7A5B"    # приглушённый зелёный (второстепенные акценты)
ACCENT_SOFT_BG = "rgba(124, 230, 166, 0.08)"
DANGER = "#E67C7C"
WARNING = "#E6C97C"


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, sans-serif !important;
        }}

        .stApp {{
            background: radial-gradient(1200px 800px at 10% -10%, #0E1712 0%, {BG} 45%) !important;
            color: {TEXT};
        }}

        section[data-testid="stSidebar"] {{
            background: {BG_PANEL} !important;
            border-right: 1px solid {BORDER};
        }}

        #MainMenu, footer, header[data-testid="stHeader"] {{
            background: transparent;
        }}

        h1, h2, h3, h4 {{
            color: {TEXT} !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }}

        p, span, label, li {{
            color: {TEXT};
        }}

        .ark-eyebrow {{
            color: {ACCENT};
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}

        .ark-card {{
            background: {BG_PANEL};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 0.9rem;
        }}

        .ark-card:hover {{
            border-color: {ACCENT_DIM};
        }}

        .ark-metric {{
            background: {BG_PANEL};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 1rem 1.2rem;
            text-align: left;
        }}
        .ark-metric .num {{
            font-size: 2rem;
            font-weight: 700;
            color: {ACCENT};
            line-height: 1.1;
        }}
        .ark-metric .label {{
            color: {TEXT_MUTED};
            font-size: 0.82rem;
            margin-top: 0.2rem;
        }}

        .ark-badge {{
            display: inline-block;
            padding: 0.18rem 0.6rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            border: 1px solid {BORDER};
            color: {TEXT_MUTED};
        }}
        .ark-badge.todo {{ color: {TEXT_MUTED}; border-color: {BORDER}; }}
        .ark-badge.in_progress {{ color: {WARNING}; border-color: {WARNING}; background: rgba(230,201,124,0.08); }}
        .ark-badge.done {{ color: {ACCENT}; border-color: {ACCENT}; background: {ACCENT_SOFT_BG}; }}
        .ark-badge.approved {{ color: {ACCENT}; border-color: {ACCENT}; background: {ACCENT_SOFT_BG}; }}
        .ark-badge.avoid {{ color: {DANGER}; border-color: {DANGER}; background: rgba(230,124,124,0.08); }}

        /* --- Дерево архитектуры --- */
        .ark-tree details {{
            margin: 0.15rem 0 0.15rem 0;
        }}
        .ark-tree summary {{
            cursor: pointer;
            list-style: none;
            padding: 0.55rem 0.8rem;
            border-radius: 10px;
            font-weight: 600;
            color: {TEXT};
            border: 1px solid transparent;
        }}
        .ark-tree summary::-webkit-details-marker {{ display: none; }}
        .ark-tree summary:hover {{
            background: {ACCENT_SOFT_BG};
            border-color: {ACCENT_DIM};
        }}
        .ark-tree .tree-root > summary {{
            background: {BG_PANEL_2};
            border: 1px solid {BORDER};
            font-size: 1.05rem;
        }}
        .ark-tree .tree-children {{
            margin-left: 1.3rem;
            padding-left: 0.9rem;
            border-left: 1px dashed {BORDER};
        }}
        .ark-tree .tree-agent > summary {{
            background: rgba(124,230,166,0.04);
        }}
        .ark-tree .tree-leaf {{
            padding: 0.35rem 0.8rem;
            margin-left: 1.3rem;
            color: {TEXT_MUTED};
            font-size: 0.88rem;
            border-left: 1px dashed {BORDER};
        }}
        .ark-tree .tree-meta {{
            color: {TEXT_MUTED};
            font-weight: 400;
            font-size: 0.82rem;
        }}

        /* --- Чат --- */
        .ark-chat-msg {{
            border-radius: 12px;
            padding: 0.55rem 0.85rem;
            margin-bottom: 0.5rem;
            font-size: 0.88rem;
            line-height: 1.4;
        }}
        .ark-chat-msg.user {{
            background: {ACCENT_SOFT_BG};
            border: 1px solid {ACCENT_DIM};
        }}
        .ark-chat-msg.assistant {{
            background: {BG_PANEL_2};
            border: 1px solid {BORDER};
        }}

        div[data-testid="stChatInput"] textarea {{
            background: {BG_PANEL_2} !important;
            color: {TEXT} !important;
        }}

        hr {{
            border-color: {BORDER} !important;
        }}

        .ark-log-line {{
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            font-size: 0.78rem;
            color: {TEXT_MUTED};
            padding: 0.15rem 0;
            border-bottom: 1px dotted {BORDER};
        }}

        .ark-logo {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {TEXT};
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.2rem;
        }}
        .ark-logo .dot {{
            width: 10px; height: 10px; border-radius: 50%;
            background: {ACCENT};
            box-shadow: 0 0 10px {ACCENT};
            display: inline-block;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
