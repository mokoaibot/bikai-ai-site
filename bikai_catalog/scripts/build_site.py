#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the static BIKAI catalog website from catalog/data/bikai_catalog.db
into catalog/site/ (English) AND catalog/site/ru/ (Russian), from one run.

The Russian tree mirrors the English one path-for-path (site/ru/index.html,
site/ru/admin.html, site/ru/product/{slug}.html) and reuses the same shared
assets (site/assets/, site/images/) via relative paths one level deeper.
Every page gets a language-switch button in the header that links to its
counterpart in the other tree.

Re-run after build_db.py whenever products.json / the DB changes.
"""
import html
import os
import re
import shutil
import sqlite3

here = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(here, "..", "data", "bikai_catalog.db")
site_dir = os.path.join(here, "..", "site")
ru_site_dir = os.path.join(site_dir, "ru")
images_src_dir = os.path.join(here, "..", "images")
images_dst_dir = os.path.join(site_dir, "images")
os.makedirs(os.path.join(site_dir, "product"), exist_ok=True)
os.makedirs(os.path.join(ru_site_dir, "product"), exist_ok=True)

# Re-sync site/images/ from the canonical images/ folder every build, so
# renamed/converted/removed files (e.g. PNG -> WEBP) never leave stale
# copies behind.
if os.path.isdir(images_dst_dir):
    shutil.rmtree(images_dst_dir)
shutil.copytree(images_src_dir, images_dst_dir)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

categories = cur.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
products = cur.execute("SELECT * FROM products ORDER BY id").fetchall()


def e(s):
    return html.escape(s or "", quote=True)


def md_to_html(text):
    """Very small markdown-ish renderer: **bold**, blank-line paragraphs."""
    if not text:
        return ""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    out = []
    for p in paras:
        p = e(p)
        p = p.replace("\n", "<br>")
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        out.append(f"<p>{p}</p>")
    return "\n".join(out)


def ru_plural(n, one, few, many):
    n100 = n % 100
    n10 = n % 10
    if 11 <= n100 <= 14:
        return many
    if n10 == 1:
        return one
    if 2 <= n10 <= 4:
        return few
    return many


def cat_title(c, lang):
    return (c["title_ru"] if lang == "ru" and c["title_ru"] else c["title"])


def prod_field(p, lang, col):
    """Return the lang-appropriate value for a products-table column,
    falling back to the English original if no RU translation exists."""
    if lang == "ru":
        v = p[f"{col}_ru"]
        if v:
            return v
    return p[col]


CAT_ICONS = {
    "chromatography": "⬢",
    "mass-spectrometry": "◆",
    "spectroscopy": "▣",
    "functional-modules": "⚙",
    "gas-generators": "◎",
    "sample-treatment": "⬡",
    "consumables": "●",
}

UI = {
    "en": {
        "html_lang": "en",
        "site_title": "BIKAI Product Catalog",
        "brand_small": "Product Catalog",
        "admin_link": "Admin view",
        "lang_switch": "RU — Русская версия",
        "hero_title": "BIKAI Product Catalog",
        "hero_desc": (
            "Full lineup of BIKAI-branded analytical instruments and consumables — chromatography, mass "
            "spectrometry, spectroscopy, functional modules, gas generators, sample treatment and consumables — "
            "compiled from the manufacturer sources for internal review and sign-off."
        ),
        "search_placeholder": "Search products by name…",
        "products_label": "products",
        "categories_label": "categories",
        "items_word": lambda n: "item" if n == 1 else "items",
        "breadcrumb_catalog": "Catalog",
        "view_source": "View original source page ↗",
        "compat_table_title": "Compatibility &amp; Part Data",
        "consumable_labels": {
            "part_no": "Part No.",
            "instrument_model": "Instrument model",
            "instrument_manufacturer": "Instrument manufacturer",
            "original_part_no": "Original product number",
            "life_span": "Life span",
        },
        "footer": (
            "Internal BIKAI product catalog — compiled for approval. Sources: uvtech-cc.com (primary "
            "manufacturer site) &amp; bikaicorp.com (brand site). Not for external publication."
        ),
        "admin_title": "Admin: Database View",
        "admin_desc_tmpl": (
            "Flat view of every row in <code>bikai_catalog.db</code> (table <code>products</code>, joined with "
            "<code>consumable_fields</code> and a count of <code>spec_rows</code>) — for quick internal QA before "
            "sign-off. {n_products} products across {n_categories} categories. To add a new product later: "
            "append it to <code>catalog/scripts/build_data.py</code> (or insert a row directly into the SQLite "
            "file) and re-run <code>build_db.py</code> + <code>build_site.py</code>."
        ),
        "admin_search_placeholder": "Filter table…",
        "admin_cols": ["Category", "Name", "Part No.", "Instrument mfr.", "Instrument model", "# spec rows", "Source", "Slug"],
        "admin_source_link": "source ↗",
    },
    "ru": {
        "html_lang": "ru",
        "site_title": "Каталог продукции BIKAI",
        "brand_small": "Каталог продукции",
        "admin_link": "Админ-вид",
        "lang_switch": "EN — English version",
        "hero_title": "Каталог продукции BIKAI",
        "hero_desc": (
            "Полная линейка приборов и расходных материалов под брендом BIKAI — хроматография, "
            "масс-спектрометрия, спектроскопия, функциональные модули, генераторы газов, пробоподготовка "
            "и расходные материалы — составлено по материалам производителей для внутреннего обзора и "
            "утверждения."
        ),
        "search_placeholder": "Поиск по названию…",
        "products_label": "товаров",
        "categories_label": "категорий",
        "items_word": lambda n: ru_plural(n, "позиция", "позиции", "позиций"),
        "breadcrumb_catalog": "Каталог",
        "view_source": "Открыть страницу первоисточника ↗",
        "compat_table_title": "Совместимость и данные детали",
        "consumable_labels": {
            "part_no": "Артикул BIKAI",
            "instrument_model": "Модель прибора",
            "instrument_manufacturer": "Производитель прибора",
            "original_part_no": "Оригинальный номер детали",
            "life_span": "Ресурс",
        },
        "footer": (
            "Внутренний каталог продукции BIKAI — составлен для утверждения. Источники: uvtech-cc.com "
            "(основной сайт производителя) и bikaicorp.com (сайт бренда). Не для внешней публикации. "
            "Русская версия — черновой машинный перевод (упрощённый словарный переводчик для этой "
            "задачи), часть технических значений может оставаться на английском."
        ),
        "admin_title": "Админ: вид базы данных",
        "admin_desc_tmpl": (
            "Плоское представление всех строк <code>bikai_catalog.db</code> (таблица <code>products</code>, "
            "объединённая с <code>consumable_fields</code> и количеством строк <code>spec_rows</code>) — для "
            "быстрой внутренней проверки перед утверждением. {n_products} товаров в {n_categories} категориях. "
            "Чтобы добавить новый товар позже: добавьте его в <code>catalog/scripts/build_data.py</code> (или "
            "вставьте строку напрямую в файл SQLite) и заново запустите <code>build_db.py</code> + "
            "<code>build_site.py</code>."
        ),
        "admin_search_placeholder": "Фильтр по таблице…",
        "admin_cols": ["Категория", "Название", "Артикул", "Производитель", "Модель прибора", "Строк характеристик", "Источник", "Slug"],
        "admin_source_link": "источник ↗",
    },
}

HEAD = """<!doctype html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{asset_root}assets/style.css">
</head>
<body>
"""


def header(lang, nav_root, asset_root, lang_switch_href):
    ui = UI[lang]
    nav_items = "".join(
        f'<a href="{nav_root}index.html#{c["slug"]}" class="nav-link">{CAT_ICONS.get(c["slug"],"")} {e(cat_title(c, lang))}</a>'
        for c in categories
    )
    return f"""
<header class="site-header">
  <div class="header-inner">
    <a href="{nav_root}index.html" class="brand">BIK<span>AI</span><small>{e(ui['brand_small'])}</small></a>
    <nav class="main-nav">{nav_items}</nav>
    <a href="{lang_switch_href}" class="lang-switch">{e(ui['lang_switch'])}</a>
    <a href="{nav_root}admin.html" class="admin-link">{e(ui['admin_link'])}</a>
  </div>
</header>
"""


def footer(lang):
    ui = UI[lang]
    return f"""
<footer class="site-footer">
  <p>{ui['footer']}</p>
</footer>
</body>
</html>
"""


def build_index(lang, out_path, nav_root, asset_root, lang_switch_href):
    ui = UI[lang]
    sections_html = []
    for c in categories:
        cat_products = [p for p in products if p["category_slug"] == c["slug"]]
        cards = []
        for p in cat_products:
            name = prod_field(p, lang, "name")
            tagline = prod_field(p, lang, "tagline") or ""
            if len(tagline) > 110:
                tagline = tagline[:107] + "…"
            extra = ""
            cf = cur.execute("SELECT * FROM consumable_fields WHERE product_id=?", (p["id"],)).fetchone()
            if cf:
                extra = f'<div class="card-meta">{e(cf["instrument_manufacturer"])} · {e(cf["instrument_model"])}</div>'
            cards.append(f"""
            <a class="card" href="product/{p['slug']}.html" data-name="{e(name.lower())}">
              <div class="card-img"><img src="{asset_root}{e(p['image_file'])}" alt="{e(name)}" loading="lazy"></div>
              <div class="card-body">
                <h3>{e(name)}</h3>
                {extra}
                <p>{e(tagline)}</p>
              </div>
            </a>""")
        n = len(cat_products)
        sections_html.append(f"""
        <section class="category-section" id="{c['slug']}">
          <div class="category-heading">
            <span class="cat-icon">{CAT_ICONS.get(c['slug'],'')}</span>
            <h2>{e(cat_title(c, lang))}</h2>
            <span class="cat-count">{n} {ui['items_word'](n)}</span>
          </div>
          <div class="card-grid">
            {''.join(cards)}
          </div>
        </section>""")

    index_html = HEAD.format(html_lang=ui["html_lang"], title=ui["site_title"], asset_root=asset_root) \
        + header(lang, nav_root, asset_root, lang_switch_href) + f"""
<main class="container">
  <section class="hero">
    <h1>{e(ui['hero_title'])}</h1>
    <p>{ui['hero_desc']}</p>
    <input id="search" class="search-box" type="search" placeholder="{e(ui['search_placeholder'])}" oninput="filterCards(this.value)">
    <div class="hero-stats">
      <div><strong>{len(products)}</strong><span>{e(ui['products_label'])}</span></div>
      <div><strong>{len(categories)}</strong><span>{e(ui['categories_label'])}</span></div>
    </div>
  </section>
  {''.join(sections_html)}
</main>
""" + footer(lang)

    index_html += """
<script>
function filterCards(q){
  q = q.trim().toLowerCase();
  document.querySelectorAll('.card').forEach(function(card){
    var name = card.getAttribute('data-name') || '';
    card.style.display = (!q || name.indexOf(q) !== -1) ? '' : 'none';
  });
  document.querySelectorAll('.category-section').forEach(function(sec){
    var anyVisible = Array.from(sec.querySelectorAll('.card')).some(function(c){return c.style.display !== 'none';});
    sec.style.display = anyVisible ? '' : 'none';
  });
}
</script>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(index_html)


def build_product_pages(lang, out_dir, nav_root, asset_root, lang_switch_href_tmpl):
    ui = UI[lang]
    for p in products:
        cat = next(c for c in categories if c["slug"] == p["category_slug"])
        name = prod_field(p, lang, "name")
        tagline = prod_field(p, lang, "tagline")
        description = prod_field(p, lang, "description")

        feat_col = "feature_ru" if lang == "ru" else "feature"
        features = cur.execute(
            f"SELECT feature, feature_ru FROM product_features WHERE product_id=? ORDER BY sort_order", (p["id"],)
        ).fetchall()
        groups = cur.execute(
            "SELECT * FROM spec_groups WHERE product_id=? ORDER BY sort_order", (p["id"],)
        ).fetchall()
        cf = cur.execute("SELECT * FROM consumable_fields WHERE product_id=?", (p["id"],)).fetchone()
        images = cur.execute(
            "SELECT file FROM product_images WHERE product_id=? ORDER BY sort_order", (p["id"],)
        ).fetchall()
        image_files = [r["file"] for r in images] or [p["image_file"]]

        thumbs_html = ""
        if len(image_files) > 1:
            thumbs = "".join(
                f'<img src="{asset_root}{e(f)}" class="thumb{" active" if i == 0 else ""}" '
                f'onclick="document.getElementById(\'main-product-img\').src=this.src;'
                f'document.querySelectorAll(\'.thumb\').forEach(function(t){{t.classList.remove(\'active\')}});'
                f'this.classList.add(\'active\')">'
                for i, f in enumerate(image_files)
            )
            thumbs_html = f'<div class="thumb-row">{thumbs}</div>'

        features_html = ""
        if features:
            chips = "".join(
                f'<span class="chip">{e(f[feat_col] if lang == "ru" and f[feat_col] else f["feature"])}</span>'
                for f in features
            )
            features_html = f'<div class="chip-row">{chips}</div>'

        consumable_html = ""
        if cf:
            labels = ui["consumable_labels"]
            life_span = cf["life_span"]
            if lang == "ru" and cf["life_span_ru"]:
                life_span = cf["life_span_ru"]
            rows = [
                (labels["part_no"], cf["part_no"]),
                (labels["instrument_model"], cf["instrument_model"]),
                (labels["instrument_manufacturer"], cf["instrument_manufacturer"]),
                (labels["original_part_no"], cf["original_part_no"]),
                (labels["life_span"], life_span),
            ]
            trs = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in rows if v)
            consumable_html = f"""
            <div class="spec-group">
              <h3>{ui['compat_table_title']}</h3>
              <table class="spec-table"><tbody>{trs}</tbody></table>
            </div>"""

        groups_html = []
        for g in groups:
            rows = cur.execute(
                "SELECT * FROM spec_rows WHERE spec_group_id=? ORDER BY sort_order", (g["id"],)
            ).fetchall()
            if not rows:
                continue

            def col(r, base):
                if lang == "ru" and r[f"{base}_ru"]:
                    return r[f"{base}_ru"]
                return r[base]

            has_col3 = any(r["col3"] for r in rows)
            header_row = rows[0]
            body_rows = rows[1:] if len(rows) > 1 else []
            thead = f"<tr><th>{e(col(header_row,'col1'))}</th><th>{e(col(header_row,'col2'))}</th>" + \
                    (f"<th>{e(col(header_row,'col3'))}</th>" if has_col3 else "") + "</tr>"
            trs = ""
            for r in body_rows:
                trs += f"<tr><td>{e(col(r,'col1'))}</td><td>{e(col(r,'col2'))}</td>" + \
                       (f"<td>{e(col(r,'col3'))}</td>" if has_col3 else "") + "</tr>"
            title = col(g, "title") if g["title"] else ""
            title_html = f"<h3>{e(title)}</h3>" if title else ""
            groups_html.append(f"""
            <div class="spec-group">
              {title_html}
              <table class="spec-table"><thead>{thead}</thead><tbody>{trs}</tbody></table>
            </div>""")

        desc_html = md_to_html(description) if description else ""

        lang_switch_href = lang_switch_href_tmpl.format(slug=p["slug"])

        page = HEAD.format(html_lang=ui["html_lang"], title=f"{e(name)} — BIKAI Catalog", asset_root=asset_root) \
            + header(lang, nav_root, asset_root, lang_switch_href) + f"""
<main class="container product-page">
  <nav class="breadcrumb">
    <a href="{nav_root}index.html">{e(ui['breadcrumb_catalog'])}</a> / <a href="{nav_root}index.html#{cat['slug']}">{e(cat_title(cat, lang))}</a> / {e(name)}
  </nav>
  <div class="product-hero">
    <div class="product-image">
      <img id="main-product-img" src="{asset_root}{e(image_files[0])}" alt="{e(name)}">
      {thumbs_html}
    </div>
    <div class="product-intro">
      <span class="cat-badge">{CAT_ICONS.get(cat['slug'],'')} {e(cat_title(cat, lang))}</span>
      <h1>{e(name)}</h1>
      <p class="tagline">{e(tagline)}</p>
      {features_html}
      <a class="source-link" href="{e(p['source_url'])}" target="_blank" rel="noopener">{e(ui['view_source'])}</a>
    </div>
  </div>

  {"<div class='description'>" + desc_html + "</div>" if desc_html else ""}

  {consumable_html}
  {''.join(groups_html)}

</main>
""" + footer(lang)

        with open(os.path.join(out_dir, f"{p['slug']}.html"), "w", encoding="utf-8") as f:
            f.write(page)


def build_admin(lang, out_path, nav_root, asset_root, lang_switch_href):
    ui = UI[lang]
    admin_rows = []
    for p in products:
        cat = next(c for c in categories if c["slug"] == p["category_slug"])
        name = prod_field(p, lang, "name")
        cf = cur.execute("SELECT * FROM consumable_fields WHERE product_id=?", (p["id"],)).fetchone()
        part_no = cf["part_no"] if cf else ""
        model = cf["instrument_model"] if cf else ""
        manu = cf["instrument_manufacturer"] if cf else ""
        n_specs = cur.execute(
            "SELECT COUNT(*) c FROM spec_rows sr JOIN spec_groups sg ON sr.spec_group_id=sg.id WHERE sg.product_id=?",
            (p["id"],),
        ).fetchone()["c"]
        admin_rows.append(f"""<tr>
          <td>{e(cat_title(cat, lang))}</td>
          <td><a href="product/{p['slug']}.html">{e(name)}</a></td>
          <td>{e(part_no)}</td>
          <td>{e(manu)}</td>
          <td>{e(model)}</td>
          <td>{n_specs}</td>
          <td><a href="{e(p['source_url'])}" target="_blank" rel="noopener">{e(ui['admin_source_link'])}</a></td>
          <td><code>{e(p['slug'])}</code></td>
        </tr>""")

    admin_desc = ui["admin_desc_tmpl"].format(n_products=len(products), n_categories=len(categories))
    cols_html = "".join(f"<th>{e(c)}</th>" for c in ui["admin_cols"])

    admin_html = HEAD.format(html_lang=ui["html_lang"], title=f"{ui['admin_link']} — BIKAI Catalog", asset_root=asset_root) \
        + header(lang, nav_root, asset_root, lang_switch_href) + f"""
<main class="container">
  <section class="hero hero-admin">
    <h1>{e(ui['admin_title'])}</h1>
    <p>{admin_desc}</p>
    <input id="admin-search" class="search-box" type="search" placeholder="{e(ui['admin_search_placeholder'])}" oninput="filterTable(this.value)">
  </section>
  <table class="admin-table" id="admin-table">
    <thead><tr>
      {cols_html}
    </tr></thead>
    <tbody>
      {''.join(admin_rows)}
    </tbody>
  </table>
</main>
<script>
function filterTable(q){{
  q = q.trim().toLowerCase();
  document.querySelectorAll('#admin-table tbody tr').forEach(function(tr){{
    tr.style.display = (!q || tr.textContent.toLowerCase().indexOf(q) !== -1) ? '' : 'none';
  }});
}}
</script>
""" + footer(lang)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(admin_html)


# ---------------------------------------------------------------------------
# English tree (site/) — asset_root == nav_root (site/ IS the asset root)
# ---------------------------------------------------------------------------
build_index("en", os.path.join(site_dir, "index.html"), nav_root="", asset_root="", lang_switch_href="ru/index.html")
build_product_pages(
    "en", os.path.join(site_dir, "product"), nav_root="../", asset_root="../",
    lang_switch_href_tmpl="../ru/product/{slug}.html",
)
build_admin("en", os.path.join(site_dir, "admin.html"), nav_root="", asset_root="", lang_switch_href="ru/admin.html")

# ---------------------------------------------------------------------------
# Russian tree (site/ru/) — asset_root = nav_root + "../" (assets live one
# level up, in the shared site/ directory)
# ---------------------------------------------------------------------------
build_index("ru", os.path.join(ru_site_dir, "index.html"), nav_root="", asset_root="../", lang_switch_href="../index.html")
build_product_pages(
    "ru", os.path.join(ru_site_dir, "product"), nav_root="../", asset_root="../../",
    lang_switch_href_tmpl="../../product/{slug}.html",
)
build_admin("ru", os.path.join(ru_site_dir, "admin.html"), nav_root="", asset_root="../", lang_switch_href="../admin.html")

conn.close()
print(
    f"Built site: {len(products)} product pages x2 langs + index.html + admin.html (EN) in {site_dir}\n"
    f"            + mirrored RU tree in {ru_site_dir}"
)
