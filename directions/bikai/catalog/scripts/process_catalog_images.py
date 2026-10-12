#!/usr/bin/env python3
"""v2: унификация фото каталога БЕЗ сегментации товара.
Только аккуратная обрезка по границе товара + единый холст 900x900 (#f3f8fd)
+ мягкая брендовая тень. Пиксели товара не удаляются и не перекрашиваются,
кроме почти-белого фона светлых фото (перекраска в тот же почти-белый лёд).
Старые файлы не трогаем: результат в images_new/."""
import os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "images")
DST = os.path.join(HERE, "..", "images_new")
CANVAS = 900
PAD = 0.84
ICE = np.array((243, 248, 253), dtype=np.int16)


def lum_of(a):
    return 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]


def bbox_of(mask, margin):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    h, w = mask.shape
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    mx = int((x1 - x0) * margin) + 6
    my = int((y1 - y0) * margin) + 6
    return (max(0, x0 - mx), max(0, y0 - my), min(w, x1 + mx + 1), min(h, y1 + my + 1))


def careful_crop_light(a):
    """Светлый фон: товар = цветное или не-почти-белое. Обрезаем, почти-белое -> лёд."""
    mx = a.max(axis=2).astype(np.int16)
    mn = a.min(axis=2).astype(np.int16)
    lum = lum_of(a)
    content = (mx - mn > 14) | (lum < 238)
    bb = bbox_of(content, 0.04)
    if not bb:
        return None, None
    crop = a[bb[1]:bb[3], bb[0]:bb[2]].copy()
    # почти-белый фон внутри кропа -> лёд (белый корпус прибора лишь чуть тонируется)
    cmx = crop.max(axis=2).astype(np.int16)
    cmn = crop.min(axis=2).astype(np.int16)
    clum = lum_of(crop)
    near_white = (cmx - cmn < 10) & (clum > 244)
    crop[near_white] = ICE
    mask = ~near_white
    return crop, mask


def careful_crop_dark(a):
    """Тёмный студийный фон: товар = светлые детали; крошим bbox через closing,
    чтобы тёмные части корпуса между светлыми деталями вошли в кроп.
    Пиксели не перекрашиваются — товар остаётся нетронутым."""
    lum = lum_of(a)
    bright = lum > 95
    m = Image.frombytes("L", (a.shape[1], a.shape[0]), bright.astype(np.uint8) * 255)
    m = m.filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.MinFilter(11))
    closed = np.asarray(m, dtype=bool)
    bb = bbox_of(closed, 0.05)
    if not bb:
        return None, None
    crop = a[bb[1]:bb[3], bb[0]:bb[2]].copy()
    # товар не трогаем: кроп непрозрачный, но края мягко растворяем в канву
    # (виньетка ~12% с каждой стороны) — тёмная «плашка» не торчит квадратом,
    # а вотермарки у краёв растворяются вместе с виньеткой
    ch, cw = crop.shape[:2]
    fy = np.ones(ch)
    fx = np.ones(cw)
    ny, nx = max(2, int(ch * 0.12)), max(2, int(cw * 0.12))
    ramp = np.linspace(0, 1, ny)
    fy[:ny] = ramp; fy[-ny:] = ramp[::-1]
    ramp = np.linspace(0, 1, nx)
    fx[:nx] = ramp; fx[-nx:] = ramp[::-1]
    mask = (fy[:, None] * fx[None, :]) > 0.5
    alpha = (fy[:, None] * fx[None, :])
    return crop, mask, alpha


def assemble(crop, mask, alpha=None):
    ch, cw = mask.shape
    max_side = int(CANVAS * PAD)
    k = min(max_side / cw, max_side / ch, 1.0)
    nw, nh = max(1, int(cw * k)), max(1, int(ch * k))
    im = Image.fromarray(crop.astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    if alpha is not None:
        mk = Image.fromarray((alpha * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    else:
        mk = Image.fromarray((mask * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
        mk = mk.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
    canvas = Image.new("RGB", (CANVAS, CANVAS), tuple(int(v) for v in ICE))
    ox, oy = (CANVAS - nw) // 2, (CANVAS - nh) // 2
    # мягкая тень по бренд-стандарту: blur18, сдвиг (+6,+26), (15,40,90), alpha*0.35
    sh = Image.new("L", (CANVAS, CANVAS), 0)
    sh.paste(mk, (ox + 6, oy + 26))
    sh = sh.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.35))
    canvas = Image.composite(Image.new("RGB", (CANVAS, CANVAS), (15, 40, 90)), canvas, sh)
    canvas.paste(im, (ox, oy), mk)
    return canvas


def process(path, out):
    im = Image.open(path).convert("RGB")
    if max(im.size) > 1600:
        im.thumbnail((1600, 1600))
    a = np.asarray(im, dtype=np.int16)
    corner = np.mean(np.concatenate([a[:12, :12].reshape(-1, 3), a[-12:, :12].reshape(-1, 3),
                                     a[:12, -12:].reshape(-1, 3), a[-12:, -12:].reshape(-1, 3)]), axis=0)
    lum_c = 0.299 * corner[0] + 0.587 * corner[1] + 0.114 * corner[2]
    alpha = None
    if lum_c < 110:
        crop, mask, alpha = careful_crop_dark(a)
    else:
        crop, mask = careful_crop_light(a)
    if crop is None:
        return False
    assemble(crop, mask, alpha).save(out, "webp", quality=85, method=6)
    return True


def main():
    os.makedirs(DST, exist_ok=True)
    names = sorted(f for f in os.listdir(SRC) if f.endswith(".webp"))
    ok = 0
    for f in names:
        try:
            if process(os.path.join(SRC, f), os.path.join(DST, f)):
                ok += 1
            else:
                print("SKIP:", f)
        except Exception as e:
            print("ERR:", f, e)
    print(f"OK: {ok}/{len(names)} -> {DST}")


if __name__ == "__main__":
    main()
