# Playbook: scraped product-catalog website (data → DB → bilingual static site)

**What this is:** a reusable, project-agnostic standard operating procedure
distilled from building the BIKAI product catalog (Oct 2026). Paste this
whole file as instructions to an AI agent on a *new* project that needs the
same shape of deliverable — "scrape a vendor's product line from their public
site(s), organize it into a database, publish it as a clean static website,
optionally in two languages" — and it should be able to execute the full
pipeline correctly the first time, including the mistakes already paid for
here so they aren't repeated.

Replace bracketed placeholders (`[COMPANY]`, `[SOURCE_DOMAIN]`, etc.) with the
specifics of the new project. Everything else is generic.

---

## 0. Before starting — clarify with the user

Ask (don't assume) if not already specified:
- Which source site(s) are authoritative, if more than one covers overlapping
  products (prefer the one with structured spec data over marketing-only
  pages).
- Whether pricing must be excluded (default: exclude unless explicitly asked
  to include).
- Whether a second language is needed now or might be later (affects whether
  to build the DB schema bilingual-ready from day one — cheap to do upfront,
  expensive to retrofit).
- Whether the deliverable needs to go to git/a live host, or stays a local
  review build first.

## 1. Data collection

1. For every product, capture from its own detail page (not just a listing
   page): name, short tagline, full feature list, full spec tables (as
   **structured groups of rows**, e.g. `{"title": "...", "rows": [[k, v], ...]}`
   — never flatten specs into a single paragraph; you lose the ability to
   render clean tables and to attach translations per-cell later).
2. **Check for a real multi-photo gallery before assuming one photo per
   product.** Source detail pages often use a carousel/swiper widget; count
   the actual slide elements in the raw HTML (view-source, not a markdown-ified
   fetch, which can silently collapse carousels to one image). If more than
   one distinct photo exists, capture all of them.
   - **Do this check for every single product, not a sample.** A real
     incident: on one catalog, only the one product a user happened to
     notice had a gallery was ever actually checked; it was wrongly assumed
     the rest followed the same single-photo pattern without verifying. Loop
     over the full product list and fetch every source page — there is no
     shortcut that's safe to skip, since different products on the same
     domain/template can still vary (promotional galleries are often added
     per-product by marketing, not uniformly).
   - A second embedded image elsewhere on the page (e.g. mid-description,
     different upload path/CDN folder, empty alt text) is not automatically
     a second real photo — it's often the *same* hero shot re-rendered as a
     styled marketing banner. Visually compare before adding it as a gallery
     entry (see byte-diff rule below, or just look at both renders).
3. If two URLs look like they *might* be two photos of the same item (e.g. a
   listing-page thumbnail vs. the detail-page hero), **diff the actual
   downloaded bytes (md5sum) before treating them as different photos.**
   CDNs frequently re-host the identical file under a new filename/timestamp.
4. On any multi-tenant CMS/CDN (common pattern: a handful of image IDs repeat
   across *every* product page — site logo, QR codes, share-banner, nav
   icons), identify and exclude those by diffing the image-ID set across
   several product pages; only the ID(s) unique to a given page are real
   product photos.
5. Watch for hotlink protection (403/empty body when fetched without a
   browser-like request). Test with `curl -A "<realistic UA>" -H "Referer:
   <a page on that domain>"` before assuming the asset is unreachable; record
   whatever Referer value makes it work.
6. Record the exact `source_url` per product — needed for provenance and for
   an "open original" link in the final site.

## 2. Structure the data

- Write a small Python builder script (e.g. `build_data.py`) with a helper
  like `add(**kwargs)` that applies sane defaults (`features=[]`,
  `spec_groups=[]`, `gallery_urls=[]`, `description=""`, etc.) and appends to
  a list, then dumps it to a single JSON file (e.g. `products.json`). This is
  the **single source of truth** — re-running it regenerates the JSON
  deterministically. Never hand-edit the generated JSON for permanent changes;
  edit the builder script instead (ephemeral edits like a translation pass
  that reads+rewrites the JSON are fine, see §5).
- Keep category/type taxonomy as an explicit short list (slug + display
  title), not inferred from strings scattered through the data.

## 3. Image pipeline

1. Download via a script that reads the JSON, derives a filename from the
   product slug, uses the realistic UA + per-product Referer override when
   needed, and **skips files that already exist** (idempotent, safe to re-run
   after adding new products).
2. **Standing rule: convert every downloaded raster image to WEBP and delete
   the original, as a default pipeline step — do this unprompted, every
   time**, not only when a user happens to ask. (Pillow: `im.save(path,
   "WEBP", quality=90, method=6)`.) Exception: only skip this if there's a
   concrete reason WEBP is unsuitable for the deliverable — check with the
   user in that case, don't just skip silently.
3. When a product can have multiple photos, store a `gallery_files` list
   (primary first) alongside the single `image_file` (kept for backward
   compatibility with simpler consumers). **Build any path-remapping step
   (e.g. png→webp rename) through a cache keyed by the original path**, not
   applied twice — a common bug is `image_file` and `gallery_files[0]`
   pointing at the same physical file; converting it once is correct,
   converting it twice silently no-ops the second time (file already moved)
   and leaves a stale reference.
4. If the site build copies images into a `site/`-style output directory,
   **wipe and fully recopy that directory on every build** rather than
   incrementally patching it, so deleted/renamed source files never leave
   orphaned stale copies in the published output.

## 4. Database

- Normalize into relational tables, not one wide table: `categories`,
  `products`, `product_features` (one row per feature chip), `spec_groups`
  (one row per spec-table block per product), `spec_rows` (one row per table
  row, up to 3 columns), `product_images` (one row per gallery photo,
  ordered), plus any domain-specific side table (e.g. a
  `consumable_fields`-style table for SKU/compatibility data if the catalog
  includes parts/accessories, not just whole instruments/products).
- **If bilingual support is plausible even if not requested yet, add the
  parallel `_xx` columns up front** (`name_ru`, `tagline_ru`, `title_ru`,
  `col1_ru`/`col2_ru`/`col3_ru`, etc.) — cheap to add empty now, expensive to
  migrate later. Never overwrite the original-language column; translations
  live beside it.
- Rebuild the whole DB from the JSON on every run (`DROP`/recreate), keyed so
  it's always a deterministic function of the JSON — don't hand-patch the DB
  except for quick one-off product additions that get backported to the
  builder script afterward.

## 5. Translation (when a second language is requested)

Build a **narrow, task-scoped translator** — explicitly simpler than, and not
a substitute for, any general-purpose translation agent planned for other
work. Two components:

1. **A small EN→target-language technical glossary** (dict-based, no LLM
   needed): spec-table group titles, parameter/label names, and a short list
   of common recurring value-phrase substrings. Apply it mechanically to every
   spec table. Leave numbers, units, and model/part codes untouched — don't
   try to translate those.
2. **Hand-written translations for the "headline" text** (name/tagline/
   features/description) — this is the part that benefits from real human or
   LLM judgment, so write it directly rather than running it through the
   glossary. Do this for every item; don't leave silent English fallbacks
   unless genuinely unavoidable, and report where that happens.

Hard rules, learned the hard way:
- **Never invent an abbreviation in the target language.** If a short form is
  needed, verify the real, standard abbreviation for that term with a web
  search before using it — don't derive one by translating the English
  acronym's letters literally. A made-up abbreviation reads as nonsense to a
  native speaker even though it looks plausible to a non-native generator.
- **Decode every non-obvious technical abbreviation at least once on the page
  it appears on** — full term spelled out with the abbreviation in
  parentheses at first mention, bare abbreviation afterward on that same
  page. Apply this per-page, since pages are read standalone. Abbreviations
  that are genuinely universal in that language's technical register (the
  target-language equivalent of "UV", "pH", or untranslated Latin-script
  acronyms like ESI/MS/DAD that are conventionally kept as-is) don't need
  this treatment — use judgment, but default to decoding when unsure.
- After writing translated text, grep it for abbreviation-shaped tokens and
  sanity-check each one against the rules above before shipping.
- Store the translation as a parallel structure/columns, never replacing the
  original-language content (see §4).
- Tell the user plainly, once, that a lightweight dictionary-based translator
  will leave some long/unusual phrases partially untranslated — that's
  expected for this scope, not a bug to silently hide.

## 6. Static site generation

- Generate with a lightweight, dependency-free templating approach (plain
  Python f-strings/stdlib `html.escape`, or an equivalent in another
  language) so the output is portable and trivially servable
  (`python3 -m http.server`) without a build toolchain.
- Always include: a home/index page grouped by category with a client-side
  search box, one detail page per product, and a flat **admin/QA table view**
  of the whole DB (for internal review before anything goes external) —
  explicitly note on that page it's for internal use, not public.
- If bilingual: generate a **full parallel page tree** per language (e.g.
  `site/` and `site/<lang>/`, mirrored path-for-path), not a query-param or
  client-side toggle. Share one copy of images/CSS via relative paths (the
  second language tree just needs one extra `../` hop). Put a clearly visible
  language-switch control in the shared header that links **directly to the
  matching page** in the other language (same product/same page type), not
  just back to that language's homepage.
- When a product has a photo gallery, render a simple thumbnail row under the
  main image with plain onclick JS to swap the displayed image — no JS
  framework needed for this.

## 7. QA — every single build, no exceptions

1. Maintain a **standing, committed checklist file in the project itself**
   covering exactly the mistake categories above (multi-photo galleries,
   invented abbreviations, image format conversion, stale file sync) — this
   is what turns a one-time correction into a permanent process improvement.
   Don't rely on conversation memory for this; conversation summaries can be
   compacted/lost, a repo file can't.
2. Maintain and run an **automated link/asset sweep script**: hit every
   generated page (every language) and every referenced image over HTTP,
   assert 200, fail loudly listing what broke. Run it before telling the user
   a build is done — a handful of manual spot-checks is not a substitute.
3. Document the **exact, ordered command sequence** to regenerate everything
   from scratch at the top of the project's README (data builder → image
   download → image format conversion → translation pass → DB build → site
   build → QA sweep). Any schema or pipeline change must keep this sequence
   accurate.
4. Whenever the user catches something that should have been caught
   automatically, fix it twice: once in the current project's data/code, and
   once as a new line item in the standing checklist (and, if the lesson is
   general enough, in a shared playbook like this one) — so it transfers to
   the *next* project instead of depending on the user noticing it again.

## 8. Meta-rule for the agent

Treat every corrective piece of user feedback on a build-pipeline project as
two tasks, not one: (a) fix the immediate instance, (b) encode the general
rule somewhere durable (checklist / playbook) so it applies automatically
next time, without being asked again. If a rule is specific to *this*
project's domain quirks (e.g. a particular CDN's recurring non-content image
IDs), it belongs in that project's own checklist. If it's a general practice
that would apply to any similar scraped-catalog project (e.g. "always webp,"
"always diff bytes before trusting two URLs are different images," "never
invent target-language abbreviations"), it belongs in a shared, project-
agnostic playbook like this one.
