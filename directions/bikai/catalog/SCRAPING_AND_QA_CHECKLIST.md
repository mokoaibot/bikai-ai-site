# BIKAI catalog — scraping & QA checklist

Internal process notes, specific to this project's own source-site quirks.
Nothing here was being tracked systematically until the user caught issues by
hand (missing multi-photo galleries, an invented Russian abbreviation) — this
file exists so the same checks happen automatically next time, instead of
depending on the user noticing again.

For the **general, project-agnostic version** of these lessons (reusable on
any future scraped-catalog project, not just BIKAI), see
`/home/user/playbooks/scraped-product-catalog-site-playbook.md` — that's the
file to hand to an AI agent starting a *similar but different* project.

Run through this list every time a product is **added or re-scraped**
(`scripts/build_data.py`), and re-check it any time the RU translator
(`scripts/translate_catalog.py`) is extended to a new product.

## 1. Images

- [ ] **Standing rule: every downloaded raster photo gets converted to WEBP
      (Pillow, quality=90, method=6) and the original deleted — by default,
      every time, not just when asked.** This was first done as a one-off
      request but is now a permanent step in the pipeline
      (`scripts/convert_images_to_webp.py`, run right after
      `download_images.py`). Only ask the user first if there's a reason WEBP
      might not be appropriate (e.g. a deliverable that must stay PNG for a
      third-party tool); otherwise just do it.
- [ ] Don't just grab the first `<img>`/og:image found for a product. Open the
      actual product detail page and look for a **photo carousel/swiper/
      gallery** (bikaicorp.com uses a `swiper` block with one `swiper-slide`
      per photo — count them). If there's more than one slide, capture **all**
      of them, not just the first.
  - **This check must be done for every single product, not a sample** — a
    user caught that this had only ever been verified for the one product
    that turned out to have a gallery (`gc-sampler`), never ruling out that
    others were missed too. Full audit completed 2026-10-02: fetched and
    manually inspected the source page for **all 55 catalog products** (all
    24 `bikaicorp.com` pages + all 31 `www.uvtech-cc.com` pages). Result:
    `gc-sampler` is confirmed as the **only** product with a real 2-photo
    gallery; every other product genuinely has just one photo on its source
    page — nothing else was missed. Detection pattern used for
    `bikaicorp.com`: count the markdown-image tags with alt text literally
    `$data['title']` between the breadcrumb and the "Related Products"
    section (excludes other products' thumbnails and WhatsApp/WeChat icons).
  - **`www.uvtech-cc.com` has no gallery feature at all** — every product
    template on that domain (lamps, column, cuvette, hExtractor) renders
    exactly one "Product Description" image, repeated verbatim as the
    breadcrumb thumbnail. There is no swiper/carousel there; don't spend time
    looking for one on that domain, just confirm the single image is present.
  - Some `bikaicorp.com` pages (`lc-pump`, `prep-hplc-1511-pro`,
    `2d-hplc-1511-pro`, `bio-hplc-1511-pro`, `gc-7000`) also embed a second
    image mid-description from a different upload path (`uploads/file/...`
    vs. `uploads/images/...`, empty alt text). Checked: this is a **duplicate
    stylized/marketing re-render of the same hero photo**, not a distinct
    angle — confirmed by visually comparing the two files for `prep-hplc-1511-
    pro`. Do not add these as `gallery_urls`; they are not new content.
- [ ] If two different image URLs for the "same" product are found (e.g. a
      listing-page thumbnail vs. a detail-page hero), don't assume they're
      different photos — **diff the actual downloaded bytes (md5sum)** before
      treating them as a gallery. They are often the exact same file
      re-uploaded under a new CDN timestamp.
- [ ] On uvtech-cc.com pages specifically: the CDN path always repeats a fixed
      set of site-chrome images (logo, 2 QR codes, 1 decorative banner) on
      every single product page — these recur across ALL products and are
      **not** product photos. Only the one image ID that is unique to that
      page is the real photo. (Currently confirmed: `3c3acef9...`,
      `519c16a9...`, `8f2750bb...`, `b8033e29...`, `60ffc25a...`,
      `742bf6c7...`, `153e2702...`, `13a19dbb...`, `bb3f2fce...`,
      `5a37c564...`, `0e9246b1...` are the recurring non-product IDs as of
      this writing — if the site redesigns, re-derive this list by diffing
      image IDs across a handful of product pages.)
- [ ] New product photos go through the full pipeline so they get optimized
      and deduped automatically: `build_data.py` (set `image_url=`, and
      `gallery_urls=[...]` if there's a real multi-photo gallery) →
      `download_images.py` → `convert_images_to_webp.py` (PNG→WEBP,
      deletes the PNG) → `build_db.py` → `build_site.py`.
- [ ] Every new image lands as `.webp` (converted automatically) unless it was
      downloaded as `.jpg` (left as-is per current project decision — only
      PNGs are converted; ask the user if JPGs should also be converted if
      that decision ever needs revisiting).

## 2. Russian translation (`scripts/translate_catalog.py`, `ru_glossary.py`)

- [ ] **Never invent a Russian abbreviation.** If a term needs a short form
      (e.g. an instrument-class acronym), verify the real, standard Russian
      abbreviation with a web search before using it — don't guess by
      transliterating the English acronym's meaning. (Caught once already:
      "СВЭЖХ" was a made-up, nonexistent abbreviation for UHPLC; the correct
      standard term is **УВЭЖХ** — ультравысокоэффективная жидкостная
      хроматография.)
- [ ] **Decode every technical abbreviation at least once on the page it
      appears on.** A reader shouldn't have to already know what ВЭЖХ / ГХ /
      ЖХ / МС / УВЭЖХ mean. Pattern to follow: first mention spells it out in
      full with the abbreviation in parentheses — e.g. "высокоэффективной
      жидкостной хроматографии (ВЭЖХ)" — subsequent mentions on the same page
      can use the bare abbreviation. This applies per-product-page, since each
      page is read standalone.
  - Universally-known short forms that do **not** need this treatment: УФ
    (UV), pH, and Latin-script acronyms commonly left untranslated in
    Russian scientific text (ESI, APCI, MRM, SIM, DAD, m/z, etc.).
- [ ] After writing/editing any hand-authored RU text, grep for new
      all-caps Cyrillic tokens and sanity-check each one:
      `python3 -c "import re,collections; print(collections.Counter(re.findall(r'[А-ЯЁ]{2,8}(?:-[А-ЯЁ0-9]{1,8})?', open('scripts/translate_catalog.py',encoding='utf-8').read())).most_common())"`
      — any abbreviation appearing that isn't already covered by the rule
      above needs a decode added.

## 3. General re-scrape hygiene

- [ ] Re-confirm `source_url` still resolves (sites get restructured —
      category/ID paths like `/chromatography/1.html` are not guaranteed
      stable long-term).
- [ ] Re-run the whole pipeline in order after ANY data change, and spot
      check both language trees before telling the user it's done:
      ```
      python3 scripts/build_data.py
      python3 scripts/download_images.py
      python3 scripts/convert_images_to_webp.py
      python3 scripts/translate_catalog.py
      python3 scripts/build_db.py
      python3 scripts/build_site.py
      ```
- [ ] Do an automated sweep (not just a couple of manual clicks) before
      reporting completion: every product page in both `/product/` and
      `/ru/product/`, and every image referenced in `gallery_files`/
      `image_file`, should return HTTP 200. See the one-off Python snippet
      used during QA in the project history — worth keeping as a quick
      `scripts/qa_check_links.py` if this grows beyond ad-hoc checks.
