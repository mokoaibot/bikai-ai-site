# BIKAI Product Catalog — internal review build

A standalone catalog website covering **all BIKAI-branded products** found on the manufacturer's
public sites, backed by a SQLite database, built for internal sign-off before the full BIKAI dealer
site is built.

## What's inside

```
bikai_catalog/
├── data/
│   ├── products.json        ← editable source-of-truth (one dict per product)
│   └── bikai_catalog.db     ← SQLite database generated from products.json
├── images/                  ← downloaded product photos (55 files)
├── scripts/
│   ├── build_data.py        ← defines PRODUCTS list → writes products.json
│   ├── download_images.py   ← downloads image_url → images/<slug>.<ext>
│   ├── build_db.py          ← products.json → bikai_catalog.db (SQLite)
│   └── build_site.py        ← bikai_catalog.db → site/ (static HTML)
└── site/                    ← the actual website (open site/index.html)
    ├── index.html           ← catalog home, grouped by category, with search
    ├── admin.html           ← flat sortable/filterable table of the whole DB
    ├── product/<slug>.html  ← one page per product with full specs & photos
    ├── images/              ← copy of ../images used by the site
    ├── assets/style.css     ← dark/violet theme adapted from bikaicorp.com's look
    └── ru/                  ← Russian mirror of the three page types above
        ├── index.html
        ├── admin.html
        └── product/<slug>.html
```

## Russian (RU) version

The site now has a second, Russian-language view, reachable from the **"RU — Русская версия"**
button in the header of every page (and back via **"EN — English version"** on the Russian pages).
It is a full mirror of the same 55 products — nothing is hidden or dropped in either language.

- `scripts/ru_glossary.py` — a small hand-built EN→RU technical dictionary (spec-table group titles,
  parameter names, and common recurring value phrases). Numbers, units and model/part codes are left
  untouched on purpose.
- `scripts/translate_catalog.py` — the **catalog-specific translator**: hand-written Russian for each
  product's name/tagline/feature-chips/description (55 products, written directly — this is the part
  that benefits from a human/LLM touch), plus the glossary above applied automatically to every spec
  table. Writes a `ru` sub-object into each product in `data/products.json` **alongside** the English
  fields (nothing is overwritten or replaced).
- `scripts/build_db.py` stores both languages side by side: every translatable column has a matching
  `*_ru` column (`name_ru`, `tagline_ru`, `description_ru`, `feature_ru`, spec `title_ru`/`col1_ru`/
  `col2_ru`/`col3_ru`, `life_span_ru`). The original English data is never touched.
- `scripts/build_site.py` renders both `site/` (English) and `site/ru/` (Russian) from one run.

**Important caveat:** this is intentionally a lightweight, narrow translator built only for this one
catalog draft — not the stronger, general-purpose translation agent planned for other work later. As
a result some spec-table cells (units, odd phrasing, long sentences without a glossary match) may
still show partially in English. That's expected for this draft; flag anything you'd like
prioritized for manual correction, or hold off for the more capable translator when it's built.

Regeneration order is unchanged, just re-run the same four scripts (add `translate_catalog.py` right
after `build_data.py`):
```
python3 scripts/build_data.py
python3 scripts/translate_catalog.py   # (re)writes the `ru` block into products.json
python3 scripts/download_images.py
python3 scripts/build_db.py
python3 scripts/build_site.py          # now emits site/ (EN) and site/ru/ (RU)
```

## Coverage (55 products / 7 categories)

| Category | Count | Primary source |
|---|---|---|
| Chromatography | 6 | bikaicorp.com (full spec tables) |
| Mass Spectrometry | 4 | bikaicorp.com (full spec tables) |
| Spectroscopy | 1 | bikaicorp.com |
| Functional Modules | 12 | bikaicorp.com |
| Gas Generators | 1 | bikaicorp.com |
| Sample Treatment | 1 | uvtech-cc.com (hExtractor 20 — not listed on bikaicorp.com) |
| Consumables (lamps, column, cuvette) | 30 | uvtech-cc.com (listing-page structured fields: Part No / instrument model / manufacturer / OEM part no / life span) |

Two manufacturer sources were scraped and cross-checked:
- **bikaicorp.com** — the current BIKAI corporate site; used as the primary source for all
  instrument categories because it publishes detailed, text-based specification tables (pressures,
  flow ranges, detector specs, software features, dimensions, etc.) and clean product renders.
- **uvtech-cc.com** — "UVTech" (Beijing UVTech Inc. / BIKAI's OEM manufacturer site); used for the
  Sample Treatment item and all 30 Consumables, since its listing pages already contain the
  structured lamp/consumable fields (Part No, instrument model, instrument manufacturer, OEM part
  number, life span) and bikaicorp.com does not yet list individual consumable SKUs.
- A third site, **bikai.jp** (Japanese distributor), was checked and found to be a near-duplicate of
  uvtech-cc.com's consumables list (same part numbers) — not re-scraped in full; flagged as a
  possible source for a few extra CE/semiconductor items if the catalog needs to be extended later.

Image hotlink protection note: `omo-oss-image.thefastimg.com` (uvtech-cc.com's CDN) requires a
`Referer` header pointing at a uvtech-cc.com page — `download_images.py` sets this automatically per
product via the `image_referer` field.

## Process notes / QA checklist

See **`SCRAPING_AND_QA_CHECKLIST.md`** for the standing checklist followed when
scraping or adding products — things like "check the source page for a real
multi-photo gallery before assuming one photo," "never invent a Russian
abbreviation, decode every technical one on first use," and the post-build
link/image sweep (`scripts/qa_check_links.py`). It exists specifically so
these checks happen by default next time, not only when flagged after the
fact.

## How to add a new product later

This was a hard requirement ("каталог может потом дополняться отдельными позициями"), so the
pipeline is split into small, re-runnable steps:

1. Open `scripts/build_data.py` and add one more `add(...)` call (or `add_consumable(...)` for a
   lamp/part with the 5 standard fields) with the product's slug, category, name, tagline, image
   URL, source URL, and spec tables.
2. Run, in order:
   ```
   python3 scripts/build_data.py       # regenerates data/products.json
   python3 scripts/download_images.py  # downloads only the new image(s), skips existing files
   python3 scripts/build_db.py         # rebuilds data/bikai_catalog.db from scratch
   python3 scripts/build_site.py       # regenerates site/index.html, admin.html, product pages
   ```
   All four steps are idempotent and safe to re-run at any time.
3. Alternatively, a product can be inserted directly into `data/bikai_catalog.db` with plain SQL
   (tables: `products`, `product_features`, `spec_groups`, `spec_rows`, `consumable_fields`) and then
   only `build_site.py` needs to be re-run.

## Viewing the catalog

Open `site/index.html` directly, or serve the `site/` folder with any static file server, e.g.:
```
python3 -m http.server 8080 --directory site
```

## Status

This is a **pre-approval working build**: all text, specs and photos were transcribed/downloaded
directly from BIKAI's own public sites (bikaicorp.com, uvtech-cc.com) with no invented data. No
pricing is included anywhere, per standing project rules. Not yet pushed to any git remote — it's a
local workspace deliverable pending your review before it becomes the base for the full dealer site.
