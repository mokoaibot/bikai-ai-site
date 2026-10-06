#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert all downloaded PNG product photos (catalog/images/*.png) to WEBP and
delete the original PNGs — per explicit request: smaller files, same visual
quality, one consistent web format. JPGs are left as-is (not requested).

Run after download_images.py and before build_db.py / build_site.py:
    python3 download_images.py && python3 convert_images_to_webp.py && ...

Updates products.json so every "image_file" / "gallery_files" entry that
pointed at a .png now points at the matching .webp — nothing else changes.
Safe to re-run (skips files that no longer exist / are already webp).
"""
import json
import os

from PIL import Image

here = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(here, "..", "data", "products.json")
img_dir = os.path.join(here, "..", "images")

with open(data_path, encoding="utf-8") as f:
    products = json.load(f)


def png_to_webp(png_path):
    webp_path = os.path.splitext(png_path)[0] + ".webp"
    with Image.open(png_path) as im:
        # Preserve transparency where present (RGBA), otherwise RGB.
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
        im.save(webp_path, "WEBP", quality=90, method=6)
    return webp_path


# Cache so the same physical file (e.g. image_file == gallery_files[0] for
# single-photo products) is only converted/deleted once, not twice.
_cache = {}


def remap(rel_path):
    """images/foo.png -> images/foo.webp, converting the file on disk too."""
    if not rel_path or not rel_path.lower().endswith(".png"):
        return rel_path
    if rel_path in _cache:
        return _cache[rel_path]
    abs_png = os.path.join(here, "..", rel_path)
    if not os.path.exists(abs_png):
        _cache[rel_path] = rel_path
        return rel_path
    abs_webp = png_to_webp(abs_png)
    os.remove(abs_png)
    new_path = os.path.relpath(abs_webp, os.path.join(here, "..")).replace(os.sep, "/")
    _cache[rel_path] = new_path
    return new_path


converted = 0
for p in products:
    before = p.get("image_file")
    after = remap(before)
    if after != before:
        converted += 1
    p["image_file"] = after

    gallery = p.get("gallery_files") or ([before] if before else [])
    p["gallery_files"] = [remap(g) for g in gallery]

with open(data_path, "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

remaining_png = [f for f in os.listdir(img_dir) if f.lower().endswith(".png")]
print(f"Converted {converted} PNG -> WEBP (originals deleted). Remaining .png files in images/: {len(remaining_png)}")
if remaining_png:
    print("  (not referenced by any product.image_file/gallery_files, left alone):", remaining_png)
