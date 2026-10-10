#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_site.py — генерирует сайт bikai.by (дилер BIKAI/UVTech в Беларуси,
только русский язык) из той же базы, что и внутренний каталог:
../../catalog/data/bikai_catalog.db

Это НЕ копия внутреннего catalog/site — другой дизайн, другая подача
(дилер, а не производитель: наличие/поставка/консультация, а не история
бренда) и один язык. Товарные данные не дублируются — читаются напрямую
из catalog/data/bikai_catalog.db и catalog/images/, чтобы при обновлении
каталога (build_data.py -> build_db.py) этот сайт пересобирался теми же
актуальными данными: python3 scripts/build_site.py

Товары делятся на две группы (так советует договор/КП: приборы и
расходники — две разные логики продвижения):
  - ПРИБОРЫ:    chromatography, mass-spectrometry, spectroscopy,
                functional-modules, gas-generators
  - РАСХОДНИКИ: sample-treatment, consumables
"""
import html
import os
import re
import shutil
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "..", "..", "catalog", "data", "bikai_catalog.db")
IMAGES_SRC = os.path.join(HERE, "..", "..", "catalog", "images")
SITE_DIR = os.path.join(HERE, "..", "site")
IMAGES_DST = os.path.join(SITE_DIR, "images")

INSTRUMENT_CATS = {"chromatography", "mass-spectrometry", "spectroscopy",
                    "functional-modules", "gas-generators"}
CONSUMABLE_CATS = {"sample-treatment", "consumables"}

COMPANY = {
    "name": "ООО «Сайенстех»",
    "address": "220025, г. Минск, ул. Слободская, 157-179",
    "unp": "193811157",
    "bank": "ОАО «Приорбанк»",
    "bic": "PJCBBY2X",
    "iban": "BY86PJCB30120854981000000933 (BYN)",
    "phone": "+375 44 501-06-81",
    "email": "infobox.sciencetech@gmail.com",
}

CAT_ICONS = {
    "chromatography": "⬢", "mass-spectrometry": "◆", "spectroscopy": "▣",
    "functional-modules": "⚙", "gas-generators": "◎",
    "sample-treatment": "⬡", "consumables": "●",
}


def e(s):
    return html.escape(s or "", quote=True)


def md_to_html(text):
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


def rf(row, col):
    """RU value with fallback to the English column of the same row."""
    v = row[f"{col}_ru"] if f"{col}_ru" in row.keys() else None
    return v if v else row[col]


# --------------------------------------------------------------------- #
# Load data
# --------------------------------------------------------------------- #

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

categories = cur.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
cat_by_slug = {c["slug"]: c for c in categories}
products = cur.execute("SELECT * FROM products ORDER BY id").fetchall()

os.makedirs(os.path.join(SITE_DIR, "product"), exist_ok=True)
os.makedirs(os.path.join(SITE_DIR, "catalog"), exist_ok=True)
if os.path.isdir(IMAGES_DST):
    shutil.rmtree(IMAGES_DST)
shutil.copytree(IMAGES_SRC, IMAGES_DST)

per_product = {}
for p in products:
    pid = p["id"]
    features = [rf(r, "feature") for r in cur.execute(
        "SELECT * FROM product_features WHERE product_id=? ORDER BY sort_order", (pid,))]
    groups = []
    for g in cur.execute("SELECT * FROM spec_groups WHERE product_id=? ORDER BY sort_order", (pid,)):
        rows = cur.execute("SELECT * FROM spec_rows WHERE spec_group_id=? ORDER BY sort_order", (g["id"],)).fetchall()
        groups.append({
            "title": rf(g, "title"),
            "rows": [[rf(r, "col1"), rf(r, "col2"), rf(r, "col3")] for r in rows],
        })
    images = [r["file"] for r in cur.execute(
        "SELECT * FROM product_images WHERE product_id=? ORDER BY sort_order", (pid,))]
    if not images and p["image_file"]:
        images = [p["image_file"]]
    consumable = cur.execute("SELECT * FROM consumable_fields WHERE product_id=?", (pid,)).fetchone()
    per_product[pid] = {
        "features": features, "groups": groups, "images": images, "consumable": consumable,
    }

n_products = len(products)
n_instruments = sum(1 for p in products if p["category_slug"] in INSTRUMENT_CATS)
n_consumables = n_products - n_instruments

# --------------------------------------------------------------------- #
# Layout chrome (header/footer shared by every page)
# --------------------------------------------------------------------- #

NAV = [
    ("/index.html", "Главная"),
    ("/catalog/index.html", "Каталог"),
    ("/contacts.html", "Контакты"),
]


def page_shell(title, description, depth, body, active=""):
    """depth = сколько '../' нужно до корня site/ с текущей страницы."""
    root = "../" * depth if depth else "./"
    nav_html = "\n".join(
        f'<a href="{root}{href.lstrip("/")}" class="{"active" if href==active else ""}">{e(label)}</a>'
        for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="stylesheet" href="{root}assets/style.css">
<link rel="icon" type="image/svg+xml" href="{root}assets/logo-emblem.svg">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="{root}index.html" class="brand" aria-label="BIKAI — на главную">
      <img src="{root}assets/logo-wordmark.svg" alt="BIKAI" class="brand-img">
    </a>
    <nav class="main-nav">{nav_html}</nav>
    <a href="{root}catalog/index.html#consumables" class="btn btn-ghost nav-cta">Подбор расходников</a>
    <a href="tel:{e(COMPANY['phone'].replace(' ', ''))}" class="btn btn-accent nav-cta">{e(COMPANY['phone'])}</a>
  </div>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-col">
      <div class="brand footer-brand"><img src="{root}assets/logo-wordmark.svg" alt="BIKAI" class="brand-img"></div>
      <p class="footer-lead">Официальный дилер оборудования BIKAI&nbsp;/&nbsp;UVTech в Беларуси:
      хроматографы, масс-спектрометры, спектроскопия и расходные материалы.</p>
    </div>
    <div class="footer-col">
      <h4>Разделы</h4>
      <a href="{root}catalog/index.html">Каталог приборов</a>
      <a href="{root}catalog/index.html#consumables">Расходные материалы</a>
      <a href="{root}contacts.html">Контакты</a>
    </div>
    <div class="footer-col">
      <h4>Реквизиты</h4>
      <p>{e(COMPANY['name'])}<br>
      {e(COMPANY['address'])}<br>
      УНП {e(COMPANY['unp'])}</p>
      <p>{e(COMPANY['bank'])}, БИК {e(COMPANY['bic'])}<br>
      р/с {e(COMPANY['iban'])}</p>
    </div>
    <div class="footer-col">
      <h4>Связаться</h4>
      <a href="tel:{e(COMPANY['phone'].replace(' ', ''))}">{e(COMPANY['phone'])}</a>
      <a href="mailto:{e(COMPANY['email'])}">{e(COMPANY['email'])}</a>
    </div>
  </div>
  <div class="footer-bottom">© 2026 {e(COMPANY['name'])}. Сайт — рабочая версия, наполняется.</div>
</footer>
</body>
</html>
"""


# --------------------------------------------------------------------- #
# Home page
# --------------------------------------------------------------------- #

cat_cards = ""
for c in categories:
    count = sum(1 for p in products if p["category_slug"] == c["slug"])
    if count == 0:
        continue
    group = "instrument" if c["slug"] in INSTRUMENT_CATS else "consumable"
    cat_cards += f"""
    <a class="cat-card cat-{group}" href="catalog/index.html#{e(c['slug'])}">
      <span class="cat-icon">{CAT_ICONS.get(c['slug'], '○')}</span>
      <span class="cat-name">{e(c['title_ru'] or c['title'])}</span>
      <span class="cat-count">{count} {e(ru_plural(count, 'позиция', 'позиции', 'позиций'))}</span>
    </a>"""

home_body = f"""
<section class="hero">
  <div class="hero-inner">
    <p class="eyebrow">Официальный дилер BIKAI&nbsp;/&nbsp;UVTech в Беларуси</p>
    <h1>Аналитическое оборудование BIKAI — поставка, подбор и расходные материалы в Беларуси</h1>
    <p class="hero-desc">Хроматографы, масс-спектрометры, спектроскопия и функциональные модули —
    {n_instruments} моделей приборов. Плюс {n_consumables} позиций расходных материалов и пробоподготовки
    под 11 брендов оборудования.</p>
    <div class="hero-actions">
      <a href="catalog/index.html" class="btn btn-accent btn-lg">Смотреть каталог</a>
      <a href="contacts.html" class="btn btn-outline btn-lg">Запросить консультацию</a>
    </div>
  </div>
</section>

<section class="value-props">
  <div class="vp"><span class="vp-num">{n_products}</span><span class="vp-label">товаров в каталоге</span></div>
  <div class="vp"><span class="vp-num">{n_instruments}</span><span class="vp-label">моделей приборов</span></div>
  <div class="vp"><span class="vp-num">{n_consumables}</span><span class="vp-label">позиций расходников</span></div>
  <div class="vp"><span class="vp-num">11</span><span class="vp-label">брендов оборудования для ламп</span></div>
</section>

<section class="section">
  <h2 class="section-title">Каталог по категориям</h2>
  <div class="cat-grid">{cat_cards}
  </div>
</section>

<section class="section split">
  <div class="split-col">
    <h3>Приборы</h3>
    <p>Хроматографы, масс-спектрометры, системы спектроскопии и функциональные модули —
    подбор под задачу лаборатории, консультация перед покупкой, демонстрация методик.</p>
    <a href="catalog/index.html#instruments" class="link-arrow">Перейти к приборам →</a>
  </div>
  <div class="split-col">
    <h3>Расходные материалы</h3>
    <p>Лампы и расходники под Waters, Agilent, Shimadzu, Hitachi, Beckman, AB SCIEX, Perkin Elmer,
    HACH, JASCO, PUXI, Analytik Jena — поиск по парт-номеру или модели прибора.</p>
    <a href="catalog/index.html#consumables" class="link-arrow">Подобрать расходник →</a>
  </div>
</section>

<section class="cta-banner">
  <h2>Нужна консультация по подбору оборудования?</h2>
  <p>Напишите нам — поможем подобрать прибор или расходник под вашу методику и уточним сроки поставки.</p>
  <a href="contacts.html" class="btn btn-accent btn-lg">Связаться с нами</a>
</section>
"""

with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(page_shell(
        "BIKAI.by — дилер оборудования BIKAI/UVTech в Беларуси",
        "Официальный дилер BIKAI/UVTech в Беларуси: хроматографы, масс-спектрометры, "
        "спектроскопия, функциональные модули и расходные материалы.",
        depth=0, body=home_body, active="/index.html",
    ))

# --------------------------------------------------------------------- #
# Catalog page (grouped: instruments first, consumables second)
# --------------------------------------------------------------------- #


def product_card(p):
    img = per_product[p["id"]]["images"]
    img_src = f"../images/{os.path.basename(img[0])}" if img else ""
    name = rf(p, "name")
    tagline = rf(p, "tagline")
    extra = ""
    cons = per_product[p["id"]]["consumable"]
    if cons and cons["part_no"]:
        extra = f'<span class="card-partno">Артикул: {e(cons["part_no"])}</span>'
    return f"""
    <a class="product-card" href="../product/{e(p['slug'])}.html" data-name="{e(name.lower())}">
      <div class="product-card-img"><img src="{img_src}" alt="{e(name)}" loading="lazy"></div>
      <div class="product-card-body">
        <div class="product-card-name">{e(name)}</div>
        <div class="product-card-tagline">{e(tagline)}</div>
        {extra}
      </div>
    </a>"""


def category_block(slug):
    c = cat_by_slug[slug]
    items = [p for p in products if p["category_slug"] == slug]
    if not items:
        return ""
    cards = "".join(product_card(p) for p in items)
    return f"""
    <div class="cat-section" id="{e(slug)}">
      <h3 class="cat-section-title">{CAT_ICONS.get(slug,'○')} {e(c['title_ru'] or c['title'])}
        <span class="cat-section-count">{len(items)}</span></h3>
      <div class="product-grid">{cards}
      </div>
    </div>"""


instrument_blocks = "".join(category_block(c["slug"]) for c in categories if c["slug"] in INSTRUMENT_CATS)
consumable_blocks = "".join(category_block(c["slug"]) for c in categories if c["slug"] in CONSUMABLE_CATS)

catalog_body = f"""
<section class="catalog-head">
  <p class="eyebrow">Приборы и расходные материалы</p>
  <h1>Каталог BIKAI / UVTech</h1>
  <p>{n_products} позиций: {n_instruments} приборов и {n_consumables} расходных материалов.</p>
  <input id="search" class="search-box" type="search" placeholder="Поиск по названию или артикулу…" oninput="filterCards(this.value)">
</section>

<section class="section" id="instruments">
  <h2 class="section-title">Приборы</h2>
  {instrument_blocks}
</section>

<section class="section" id="consumables">
  <h2 class="section-title">Расходные материалы и пробоподготовка</h2>
  {consumable_blocks}
</section>

<script>
function filterCards(q) {{
  q = q.trim().toLowerCase();
  document.querySelectorAll('.product-card').forEach(function(card) {{
    var hay = card.dataset.name + ' ' + card.textContent.toLowerCase();
    card.style.display = hay.indexOf(q) === -1 ? 'none' : '';
  }});
  document.querySelectorAll('.cat-section').forEach(function(sec) {{
    var visible = sec.querySelectorAll('.product-card:not([style*="display: none"])').length;
    sec.style.display = visible === 0 && q !== '' ? 'none' : '';
  }});
}}
</script>
"""

with open(os.path.join(SITE_DIR, "catalog", "index.html"), "w", encoding="utf-8") as f:
    f.write(page_shell(
        "Каталог — BIKAI.by",
        "Полный каталог BIKAI/UVTech: приборы и расходные материалы с поиском по названию и артикулу.",
        depth=1, body=catalog_body, active="/catalog/index.html",
    ))

# --------------------------------------------------------------------- #
# Product pages
# --------------------------------------------------------------------- #

CONSUMABLE_LABELS = {
    "part_no": "Артикул BIKAI", "instrument_model": "Модель прибора",
    "instrument_manufacturer": "Производитель прибора",
    "original_part_no": "Оригинальный номер детали", "life_span": "Ресурс",
}

for p in products:
    pid = p["id"]
    data = per_product[pid]
    name = rf(p, "name")
    tagline = rf(p, "tagline")
    description = rf(p, "description")
    is_instrument = p["category_slug"] in INSTRUMENT_CATS
    c = cat_by_slug[p["category_slug"]]

    gallery_html = "".join(
        f'<img src="../images/{os.path.basename(g)}" alt="{e(name)}" loading="lazy">' for g in data["images"]
    ) or '<div class="no-image">Фото уточняется</div>'

    features_html = "".join(f"<li>{e(f)}</li>" for f in data["features"])
    features_block = f'<ul class="feature-list">{features_html}</ul>' if features_html else ""

    groups_html = ""
    for g in data["groups"]:
        rows_html = "".join(
            "<tr>" + "".join(f"<td>{e(col)}</td>" for col in row if col is not None) + "</tr>"
            for row in g["rows"]
        )
        groups_html += f"""
        <div class="spec-group">
          <h4>{e(g['title'])}</h4>
          <table class="spec-table"><tbody>{rows_html}</tbody></table>
        </div>"""

    consumable_html = ""
    cons = data["consumable"]
    if cons:
        rows = []
        for key in ("part_no", "instrument_model", "instrument_manufacturer", "original_part_no"):
            if cons[key]:
                rows.append((CONSUMABLE_LABELS[key], cons[key]))
        life = cons["life_span_ru"] or cons["life_span"]
        if life:
            rows.append((CONSUMABLE_LABELS["life_span"], life))
        rows_html = "".join(f"<tr><td>{e(k)}</td><td>{e(v)}</td></tr>" for k, v in rows)
        consumable_html = f"""
        <div class="spec-group">
          <h4>Совместимость и артикул</h4>
          <table class="spec-table"><tbody>{rows_html}</tbody></table>
        </div>"""

    cta_html = (
        '<a href="../contacts.html" class="btn btn-accent btn-lg">Запросить консультацию</a>'
        if is_instrument else
        '<a href="../contacts.html" class="btn btn-accent btn-lg">Уточнить наличие и цену</a>'
    )

    body = f"""
<nav class="breadcrumbs"><a href="../catalog/index.html">Каталог</a> / {e(c['title_ru'] or c['title'])} / {e(name)}</nav>
<section class="product-hero">
  <div class="product-gallery">{gallery_html}</div>
  <div class="product-info">
    <p class="eyebrow">{e(c['title_ru'] or c['title'])}</p>
    <h1>{e(name)}</h1>
    <p class="product-tagline">{e(tagline)}</p>
    {features_block}
    <div class="product-cta">{cta_html}
      <span class="product-cta-note">Статус регистрации и наличие уточняйте по запросу</span>
    </div>
  </div>
</section>
<section class="product-body">
  <div class="product-description">{md_to_html(description)}</div>
  {consumable_html}
  {groups_html}
</section>
"""
    with open(os.path.join(SITE_DIR, "product", f"{p['slug']}.html"), "w", encoding="utf-8") as f:
        f.write(page_shell(f"{name} — BIKAI.by", tagline or name, depth=1, body=body))

# --------------------------------------------------------------------- #
# Contacts page
# --------------------------------------------------------------------- #

contacts_body = f"""
<section class="contacts-head">
  <p class="eyebrow">Связаться с нами</p>
  <h1>Контакты</h1>
  <p>Напишите или позвоните — поможем подобрать прибор или расходный материал, уточним сроки поставки.</p>
</section>
<section class="contacts-grid">
  <div class="contacts-card">
    <h3>Связаться напрямую</h3>
    <p><a href="tel:{e(COMPANY['phone'].replace(' ', ''))}">{e(COMPANY['phone'])}</a></p>
    <p><a href="mailto:{e(COMPANY['email'])}">{e(COMPANY['email'])}</a></p>
  </div>
  <div class="contacts-card">
    <h3>Реквизиты</h3>
    <p>{e(COMPANY['name'])}<br>{e(COMPANY['address'])}<br>УНП {e(COMPANY['unp'])}</p>
    <p>{e(COMPANY['bank'])}<br>БИК {e(COMPANY['bic'])}<br>р/с {e(COMPANY['iban'])}</p>
  </div>
</section>
"""

with open(os.path.join(SITE_DIR, "contacts.html"), "w", encoding="utf-8") as f:
    f.write(page_shell(
        "Контакты — BIKAI.by",
        "Контакты и реквизиты официального дилера BIKAI/UVTech в Беларуси.",
        depth=0, body=contacts_body, active="/contacts.html",
    ))

print(f"OK: {n_products} товаров ({n_instruments} приборов, {n_consumables} расходников) -> {SITE_DIR}")
