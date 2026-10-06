#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build catalog/data/bikai_catalog.db (SQLite) from catalog/data/products.json.

Schema (bilingual: every translatable column has an EN original plus a
parallel *_ru column holding the Russian translation produced by
scripts/translate_catalog.py; the English data is never overwritten):
  categories(slug PK, title, title_ru, sort_order)
  products(id PK, slug UNIQUE, category_slug FK, name, name_ru, tagline,
           tagline_ru, description, description_ru, image_file, image_url,
           source_url)
  product_features(id PK, product_id FK, feature, feature_ru, sort_order)
  spec_groups(id PK, product_id FK, title, title_ru, sort_order)
  spec_rows(id PK, spec_group_id FK, col1, col1_ru, col2, col2_ru, col3,
            col3_ru, sort_order)
  consumable_fields(product_id PK/FK, part_no, instrument_model,
                     instrument_manufacturer, original_part_no, life_span,
                     life_span_ru)

To add a product later: either (a) edit products.json + re-run build_data.py
(if adding via the python source) and this script, or (b) INSERT directly
into this SQLite file — both are supported, this script only INSERTs rows
that don't already exist (keyed on product slug) so it's safe to re-run.
A newly added product will simply have NULL/empty *_ru columns until
scripts/translate_catalog.py is run again for it.
"""
import json
import os
import sqlite3

here = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(here, "..", "data", "products.json")
db_path = os.path.join(here, "..", "data", "bikai_catalog.db")

CATEGORIES = [
    ("chromatography", "Chromatography", "Хроматография", 1),
    ("mass-spectrometry", "Mass Spectrometry", "Масс-спектрометрия", 2),
    ("spectroscopy", "Spectroscopy", "Спектроскопия", 3),
    ("functional-modules", "Functional Modules", "Функциональные модули", 4),
    ("gas-generators", "Gas Generators", "Генераторы газов", 5),
    ("sample-treatment", "Sample Treatment", "Пробоподготовка", 6),
    ("consumables", "Consumables", "Расходные материалы", 7),
]

with open(data_path, encoding="utf-8") as f:
    products = json.load(f)

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.executescript(
    """
    CREATE TABLE categories (
        slug TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        title_ru TEXT,
        sort_order INTEGER NOT NULL
    );
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        category_slug TEXT NOT NULL REFERENCES categories(slug),
        name TEXT NOT NULL,
        name_ru TEXT,
        tagline TEXT,
        tagline_ru TEXT,
        description TEXT,
        description_ru TEXT,
        image_file TEXT,
        image_url TEXT,
        source_url TEXT
    );
    CREATE TABLE product_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL REFERENCES products(id),
        feature TEXT NOT NULL,
        feature_ru TEXT,
        sort_order INTEGER NOT NULL
    );
    CREATE TABLE spec_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL REFERENCES products(id),
        title TEXT,
        title_ru TEXT,
        sort_order INTEGER NOT NULL
    );
    CREATE TABLE spec_rows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spec_group_id INTEGER NOT NULL REFERENCES spec_groups(id),
        col1 TEXT, col1_ru TEXT,
        col2 TEXT, col2_ru TEXT,
        col3 TEXT, col3_ru TEXT,
        sort_order INTEGER NOT NULL
    );
    CREATE TABLE consumable_fields (
        product_id INTEGER PRIMARY KEY REFERENCES products(id),
        part_no TEXT,
        instrument_model TEXT,
        instrument_manufacturer TEXT,
        original_part_no TEXT,
        life_span TEXT,
        life_span_ru TEXT
    );
    CREATE TABLE product_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL REFERENCES products(id),
        file TEXT NOT NULL,
        sort_order INTEGER NOT NULL
    );
    """
)

cur.executemany("INSERT INTO categories (slug, title, title_ru, sort_order) VALUES (?, ?, ?, ?)", CATEGORIES)

for p in products:
    ru = p.get("ru", {}) or {}
    ru_spec_groups = ru.get("spec_groups", [])

    cur.execute(
        "INSERT INTO products (slug, category_slug, name, name_ru, tagline, tagline_ru, description, "
        "description_ru, image_file, image_url, source_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (p["slug"], p["category"], p["name"], ru.get("name"), p.get("tagline", ""), ru.get("tagline"),
         p.get("description", ""), ru.get("description"), p.get("image_file", ""), p.get("image_url", ""),
         p.get("source_url", "")),
    )
    pid = cur.lastrowid

    gallery = p.get("gallery_files") or ([p.get("image_file")] if p.get("image_file") else [])
    for gi, imgfile in enumerate(gallery):
        cur.execute(
            "INSERT INTO product_images (product_id, file, sort_order) VALUES (?, ?, ?)",
            (pid, imgfile, gi),
        )

    ru_features = ru.get("features") or []
    for i, feat in enumerate(p.get("features", [])):
        feat_ru = ru_features[i] if i < len(ru_features) else None
        cur.execute(
            "INSERT INTO product_features (product_id, feature, feature_ru, sort_order) VALUES (?, ?, ?, ?)",
            (pid, feat, feat_ru, i),
        )

    for gi, group in enumerate(p.get("spec_groups", [])):
        ru_group = ru_spec_groups[gi] if gi < len(ru_spec_groups) else {}
        cur.execute(
            "INSERT INTO spec_groups (product_id, title, title_ru, sort_order) VALUES (?, ?, ?, ?)",
            (pid, group.get("title", ""), ru_group.get("title"), gi),
        )
        gid = cur.lastrowid
        ru_rows = ru_group.get("rows", []) if ru_group else []
        for ri, row in enumerate(group.get("rows", [])):
            row = list(row) + [None] * (3 - len(row))
            ru_row = ru_rows[ri] if ri < len(ru_rows) else [None, None, None]
            ru_row = list(ru_row) + [None] * (3 - len(ru_row))
            cur.execute(
                "INSERT INTO spec_rows (spec_group_id, col1, col1_ru, col2, col2_ru, col3, col3_ru, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (gid, row[0], ru_row[0], row[1], ru_row[1], row[2], ru_row[2], ri),
            )

    cf = p.get("consumable")
    if cf:
        cur.execute(
            "INSERT INTO consumable_fields (product_id, part_no, instrument_model, instrument_manufacturer, "
            "original_part_no, life_span, life_span_ru) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pid, cf.get("part_no"), cf.get("instrument_model"), cf.get("instrument_manufacturer"),
             cf.get("original_part_no"), cf.get("life_span"), ru.get("life_span")),
        )

conn.commit()
n_products = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
n_cats = cur.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
n_ru = cur.execute("SELECT COUNT(*) FROM products WHERE name_ru IS NOT NULL AND name_ru != ''").fetchone()[0]
n_imgs = cur.execute("SELECT COUNT(*) FROM product_images").fetchone()[0]
n_multi = cur.execute(
    "SELECT COUNT(*) FROM (SELECT product_id FROM product_images GROUP BY product_id HAVING COUNT(*) > 1)"
).fetchone()[0]
conn.close()
print(
    f"Built {db_path}: {n_cats} categories, {n_products} products ({n_ru} with RU translation), "
    f"{n_imgs} total photos ({n_multi} product(s) with a multi-photo gallery)."
)
