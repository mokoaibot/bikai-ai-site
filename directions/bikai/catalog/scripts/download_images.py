#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download product images referenced in products.json into catalog/images/,
using a Referer header to satisfy hotlink protection (needed for the
uvtech-cc.com / omo-oss-image.thefastimg.com CDN). Re-run any time after
adding new products with new image_url / gallery_urls fields — already-
downloaded files are skipped.

Each product gets:
  - image_file  : the primary photo (e.g. "images/<slug>.ext") — unchanged
                   field name, kept for backward compatibility with existing
                   templates.
  - gallery_files: list of ALL photos for the product, primary first, then
                   any extra gallery_urls (e.g. "images/<slug>-2.ext"). Most
                   products have exactly one; a few (confirmed by inspecting
                   the live product page's photo swiper) have more.
"""
import json
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(here, "..", "data", "products.json")
img_dir = os.path.join(here, "..", "images")
os.makedirs(img_dir, exist_ok=True)

with open(data_path, encoding="utf-8") as f:
    products = json.load(f)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"


def fetch(url, referer, fpath):
    cmd = [
        "curl", "-sL", "--http1.1", "-A", UA,
        "-H", f"Referer: {referer}",
        "-o", fpath, url,
    ]
    r = subprocess.run(cmd)
    size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
    return r.returncode == 0 and size > 500, size


ok, fail = 0, 0
for p in products:
    url = p.get("image_url")
    if not url:
        continue
    referer = p.get("image_referer") or "https://bikaicorp.com/"
    gallery_files = []

    all_urls = [url] + list(p.get("gallery_urls", []))
    for i, u in enumerate(all_urls):
        ext = os.path.splitext(u.split("?")[0])[1] or ".jpg"
        fname = f"{p['slug']}{ext}" if i == 0 else f"{p['slug']}-{i+1}{ext}"
        fpath = os.path.join(img_dir, fname)
        gallery_files.append(f"images/{fname}")
        if os.path.exists(fpath) and os.path.getsize(fpath) > 500:
            continue
        success, size = fetch(u, referer, fpath)
        if success:
            ok += 1
        else:
            fail += 1
            print(f"FAILED: {p['slug']} <- {u} (size={size})", file=sys.stderr)

    p["image_file"] = gallery_files[0]
    p["gallery_files"] = gallery_files

with open(data_path, "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

n_imgs = sum(len(p.get("gallery_files", [])) for p in products)
print(f"Downloaded/verified {ok} images, {fail} failures, out of {n_imgs} total image slots across {len(products)} products.")
