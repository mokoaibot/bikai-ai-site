#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick post-build QA sweep: hits every EN + RU product/admin/index page and
every image referenced in products.json against a running local server, and
reports anything that doesn't return HTTP 200.

Usage (with the site already being served, e.g. `python3 -m http.server 8080`
from inside catalog/site/):
    python3 scripts/qa_check_links.py [base_url]
    (base_url defaults to http://localhost:8080)

Exits non-zero if anything failed, so it can be used as a build gate.
"""
import json
import os
import sys
import urllib.request

here = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(here, "..", "data", "products.json")
base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"

with open(data_path, encoding="utf-8") as f:
    products = json.load(f)


def check(url):
    try:
        r = urllib.request.urlopen(url, timeout=5)
        return r.status == 200
    except Exception as ex:
        return str(ex)


bad = []
checked = 0

for path in ["/index.html", "/admin.html", "/ru/index.html", "/ru/admin.html", "/assets/style.css"]:
    checked += 1
    result = check(base + path)
    if result is not True:
        bad.append((base + path, result))

for p in products:
    slug = p["slug"]
    for path in [f"/product/{slug}.html", f"/ru/product/{slug}.html"]:
        checked += 1
        result = check(base + path)
        if result is not True:
            bad.append((base + path, result))
    for img in p.get("gallery_files") or ([p["image_file"]] if p.get("image_file") else []):
        checked += 1
        result = check(f"{base}/{img}")
        if result is not True:
            bad.append((f"{base}/{img}", result))

print(f"Checked {checked} URLs against {base}.")
if bad:
    print(f"FAILED ({len(bad)}):")
    for url, result in bad:
        print(f"  {url} -> {result}")
    sys.exit(1)
else:
    print("All OK (200).")
