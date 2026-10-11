#!/usr/bin/env python3
"""Пересборка «ледяных» ассетов заставок из исходников brandbook/backgrounds/.

Воспроизводит композиции, закреплённые 12.10 (эксперимент 11.10):
  - consumables.webp   — витрина расходников на льду, без двух нижних ламп;
  - functional-modules.webp — насос lc-pump на льду, приподнят (низ y=645);
  - _ice-sec-soft.webp — прозрачный кроп льда для фона секции плиток;
  - _ice-1600x900.webp — рабочий кроп льда (оверлей hero, заставки).

Исходники: ../../brandbook/backgrounds/ice-source.jpg,
           ../../brandbook/backgrounds/consumables-showcase-source.jpg,
           ../../catalog/images/lc-pump.webp
Запуск: python3 scripts/rebuild_ice_assets.py
"""
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
BB = os.path.join(HERE, "..", "..", "brandbook", "backgrounds")
CAT_IMG = os.path.join(HERE, "..", "..", "catalog", "images")
COVERS = os.path.join(HERE, "..", "site", "assets", "cat-covers")

ICE_SRC = os.path.join(BB, "ice-source.jpg")
CONS_SRC = os.path.join(BB, "consumables-showcase-source.jpg")
PUMP_SRC = os.path.join(CAT_IMG, "lc-pump.webp")


def ice_square(size=1254):
    return Image.open(ICE_SRC).convert("RGB").resize((size, size), Image.LANCZOS)


def build_ice_crops():
    img = Image.open(ICE_SRC).convert("RGB")
    img.resize((1600, 900), Image.LANCZOS).save(
        os.path.join(COVERS, "_ice-1600x900.webp"), "WEBP", quality=82, method=6)
    # прозрачный кроп для фона секции: середина, растянуть, alpha 35% на светлой базе
    W, H = img.size
    crop = img.crop((int(W * .18), int(H * .22), int(W * .82), int(H * .78)))
    crop = crop.resize((1600, 900), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2))
    base = np.full((900, 1600, 3), (243, 248, 253), np.uint8)
    out = (np.asarray(crop).astype(float) * .35 + base.astype(float) * .65).astype(np.uint8)
    Image.fromarray(out).save(os.path.join(COVERS, "_ice-sec-soft.webp"), "WEBP", quality=82, method=6)
    print("ice-кропы: _ice-1600x900, _ice-sec-soft")


def build_consumables():
    src = Image.open(CONS_SRC).convert("RGB")
    A = np.asarray(src).astype(float)
    H, W, _ = A.shape
    gray = A.mean(2)
    mag = np.hypot(ndimage.sobel(gray, 0), ndimage.sobel(gray, 1))
    edge = ndimage.binary_dilation(mag > 40, iterations=1)
    seed = np.zeros_like(edge)
    seed[0] = seed[-1] = True
    seed[:, 0] = seed[:, -1] = True
    bg = ndimage.binary_propagation(seed & ~edge, mask=~edge)
    prod = ndimage.binary_opening(~bg, np.ones((5, 5)))
    lab, n = ndimage.label(prod)
    keep = np.zeros_like(prod)
    for i in range(1, n + 1):
        ys, _xs = np.where(lab == i)
        if len(ys) < 800 or ys.mean() / H > 0.72:  # две нижние лампы — вон
            continue
        keep |= lab == i
    blur = ndimage.uniform_filter(A, (101, 101, 1))
    diff = np.abs(A - blur).mean(2)
    core = keep & (diff > 12)
    core = ndimage.binary_fill_holes(ndimage.binary_closing(core, np.ones((5, 5))))
    lab2, n2 = ndimage.label(core)
    fin = np.zeros_like(core)
    for i in range(1, n2 + 1):
        m = lab2 == i
        if m.sum() < 500:
            continue
        ys, xs = np.where(m)
        if xs.min() > 1000:  # кювета: срезать панельную канавку над колпачком
            widths = m[:, xs.min():xs.max() + 1].sum(1)
            ycap = next((y for y in range(H) if widths[y] > 80), 0)
            m[:max(0, ycap - 4), :] = False
        fin |= m
    _composite(A, fin, os.path.join(COVERS, "consumables.webp"))
    print("consumables.webp")


def build_functional():
    p = np.asarray(Image.open(PUMP_SRC).convert("RGBA"))
    alpha = p[..., 3] > 40
    lab, n = ndimage.label(alpha)
    sizes = ndimage.sum(alpha, lab, range(1, n + 1))
    main = (lab == (int(sizes.argmax()) + 1))
    ys, xs = np.where(main)
    crop = p[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
    cm = main[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    crop[~cm] = (0, 0, 0, 0)

    W = 900
    tw = 700
    th = int(crop.shape[0] * tw / crop.shape[1])
    prod = Image.fromarray(crop).resize((tw, th), Image.LANCZOS)
    bottom, tx, ty = 645, (W - tw) // 2, 645 - th

    canvas = ice_square(900).convert("RGBA")
    pa = np.asarray(prod)[..., 3].astype(float) / 255
    sh = Image.fromarray((np.clip(pa * .35, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18))
    canvas.paste((15, 40, 90, 255), (tx + 6, ty + 26), sh)
    refl = prod.transpose(Image.FLIP_TOP_BOTTOM)
    ra = np.asarray(refl)[..., 3].astype(float) / 255
    fade = np.linspace(.16, 0, ra.shape[0])[:, None]
    refl.putalpha(Image.fromarray((ra * fade * 255).astype(np.uint8)))
    canvas.alpha_composite(refl, (tx, bottom))
    canvas.alpha_composite(prod, (tx, ty))
    canvas.convert("RGB").save(os.path.join(COVERS, "functional-modules.webp"), "WEBP", quality=80, method=6)
    print("functional-modules.webp")


def _composite(A, fin, out_path):
    alpha = ndimage.gaussian_filter(fin.astype(float), 1.5)
    shadow = ndimage.gaussian_filter(np.roll(fin, 14, 0).astype(float), 12) * .35
    ice = np.asarray(ice_square().resize((A.shape[1], A.shape[0]), Image.LANCZOS)).astype(float)
    sh = shadow[..., None]
    tint = np.array([15, 40, 90], float)
    out = ice * (1 - sh) + tint * sh
    out = out * (1 - alpha[..., None]) + A * alpha[..., None]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize(
        (900, 900), Image.LANCZOS).save(out_path, "WEBP", quality=80, method=6)


if __name__ == "__main__":
    build_ice_crops()
    build_consumables()
    build_functional()
    print("OK: ледяные ассеты пересобраны")
