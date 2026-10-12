#!/usr/bin/env python3
"""Унификация фото каталога: любой фон -> ледяной #f3f8fd, холст 900x900,
мягкая тень по бренд-стандарту, вотермарки на фоне удаляются вместе с фоном.
Старые файлы НЕ трогаем: результат пишется в images_new/."""
import os, sys
from collections import deque
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "images")
DST = os.path.join(HERE, "..", "images_new")
CANVAS = 900
PAD = 0.82  # доля канвы под товар
ICE = (243, 248, 253)


def corner_color(im):
    w, h = im.size
    patches = []
    for x, y in [(0, 0), (w - 12, 0), (0, h - 12), (w - 12, h - 12)]:
        patches.append(im.crop((x, y, x + 12, y + 12)).resize((1, 1)).getpixel((0, 0)))
    return tuple(sum(c[i] for c in patches) // 4 for i in range(3))


def bg_mask_dark(im):
    """Тёмная студийная серия: фон = градиент, восстанавливаемый медианой
    каждой строки (товар в центре не влияет на медиану). Товар = отклонение
    от медианы; вотермарки уходят как мелкие компоненты в keep_mask."""
    import numpy as np
    w, h = im.size
    corner = corner_color(im)
    plain = bg_mask(im, corner, 130)
    if sum(plain) > 0.75 * w * h:
        return plain
    a = np.asarray(im, dtype=np.int16)
    if 0.299 * corner[0] + 0.587 * corner[1] + 0.114 * corner[2] < 20:
        lum_a = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
        bg0 = lum_a < 95
        seen = bytearray(w * h)
        q = deque()
        def push(x, y):
            i = y * w + x
            if not seen[i] and bg0[y, x]:
                seen[i] = 1
                q.append((x, y))
        for x in range(w):
            push(x, 0); push(x, h - 1)
        for y in range(h):
            push(0, y); push(w - 1, y)
        while q:
            x, y = q.popleft()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    ni = ny * w + nx
                    if not seen[ni] and bg0[ny, nx]:
                        seen[ni] = 1
                        q.append((nx, ny))
        return seen
    med = np.median(a, axis=1, keepdims=True)
    dist = np.abs(a - med).sum(axis=2)
    bg0 = (dist < 90)
    seen = bytearray(w * h)
    q = deque()

    def push(x, y):
        i = y * w + x
        if not seen[i] and bg0[y, x]:
            seen[i] = 1
            q.append((x, y))

    for x in range(w):
        push(x, 0); push(x, h - 1)
    for y in range(h):
        push(0, y); push(w - 1, y)
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h:
                ni = ny * w + nx
                if not seen[ni] and bg0[ny, nx]:
                    seen[ni] = 1
                    q.append((nx, ny))
    return seen


def bg_mask(im, corner, tol):
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    q = deque()
    cr, cg, cb = corner

    def push(x, y):
        i = y * w + x
        if seen[i]:
            return
        r, g, b = px[x, y][:3]
        if abs(r - cr) + abs(g - cg) + abs(b - cb) <= tol:
            seen[i] = 1
            q.append((x, y))

    for x in range(w):
        push(x, 0); push(x, h - 1)
    for y in range(h):
        push(0, y); push(w - 1, y)
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                r, g, b = px[nx, ny][:3]
                if abs(r - cr) + abs(g - cg) + abs(b - cb) <= tol:
                    seen[ny * w + nx] = 1
                    q.append((nx, ny))
    return seen


def keep_mask(goods, w, h, rgb=None, edge=None, min_ratio=0.02, min_abs=40):
    """Оставляет связные компоненты товара площадью >= max(big*ratio, abs);
    мелкие (вотермарки, шум) выбрасывает. Память: только списки индексов."""
    lab = bytearray(w * h)
    comps = []
    for start in range(w * h):
        if not goods[start] or lab[start]:
            continue
        idxs = [start]
        lab[start] = 1
        head = 0
        while head < len(idxs):
            i = idxs[head]; head += 1
            x, y = i % w, i // w
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    ni = ny * w + nx
                    if goods[ni] and not lab[ni]:
                        lab[ni] = 1
                        idxs.append(ni)
        comps.append((len(idxs), idxs))
    comps.sort(key=lambda t: -t[0])
    if not comps:
        return bytearray(w * h)

    def stats(idxs):
        step = max(1, len(idxs) // 500)
        sat = lum = ed = cnt = 0
        for i in idxs[::step]:
            r, g, b = rgb[i]
            sat += max(r, g, b) - min(r, g, b)
            lum += 0.299 * r + 0.587 * g + 0.114 * b
            if edge is not None:
                ed += edge[i]
            cnt += 1
        return sat / cnt, lum / cnt, (ed / cnt if edge is not None else 1)

    def touches_border(idxs):
        for i in idxs[::max(1, len(idxs) // 200)]:
            x, y = i % w, i // w
            if x < 2 or y < 2 or x > w - 3 or y > h - 3:
                return True
        return False

    graydark = []
    for area, idxs in comps:
        if rgb is not None:
            st, lm, ed = stats(idxs)
            # тень/плоский фон: серый, тёмный и ГЛАДКИЙ; товар фактурный
            bad = st < 30 and lm < 190 and ed < 0.06
            # светло-серая полоса у границы = артефакт фона
            if not bad and st < 25 and lm > 200 and touches_border(idxs):
                bad = True
            # серый текст вотермарки
            if not bad and st < 20 and 120 < lm < 225 and ed < 0.2 and area < 20000:
                bad = True
            graydark.append(bad)
        else:
            graydark.append(False)
    # главная = крупнейшая НЕ серо-тёмная (иначе фон/тень станет «товаром»)
    big_i = 0
    for n, (area, idxs) in enumerate(comps):
        if not graydark[n]:
            big_i = n
            break
    big = comps[big_i][0]
    keep = bytearray(w * h)
    for n, (area, idxs) in enumerate(comps):
        if n == big_i:
            for i in idxs:
                keep[i] = 1
        elif area >= max(big * min_ratio, min_abs) and not graydark[n]:
            for i in idxs:
                keep[i] = 1
    return keep


def process(path, out):
    im = Image.open(path).convert("RGB")
    # даунскейл огромных исходников для скорости
    if max(im.size) > 1600:
        im.thumbnail((1600, 1600))
    w, h = im.size
    corner = corner_color(im)
    lum = 0.299 * corner[0] + 0.587 * corner[1] + 0.114 * corner[2]
    tol = 130 if lum < 110 else 90  # манхэттен-дистанция
    seen = bg_mask_dark(im) if lum < 110 else bg_mask(im, corner, tol)
    # маска товара
    goods = bytearray(w * h)
    for i in range(w * h):
        goods[i] = 0 if seen[i] else 1
    import numpy as np
    a = np.asarray(im, dtype=np.int16)
    e = np.zeros((h, w), dtype=np.uint8)
    ex = np.abs(a[:, 1:] - a[:, :-1]).sum(axis=2) > 40
    ey = np.abs(a[1:, :] - a[:-1, :]).sum(axis=2) > 40
    e[:, :-1] |= ex
    e[:-1, :] |= ey
    edge = e.reshape(-1)
    rgb = list(im.getdata())
    keep = keep_mask(goods, w, h, rgb=rgb, edge=edge)
    if not any(keep):
        return False
    if lum < 110:
        # эрозия->дилатация: разъединяем товар и прилипшие тени тонкими мостиками
        kim = Image.frombytes("L", (w, h), bytes(255 if k else 0 for k in keep))
        kim = kim.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
        keep = keep_mask(bytearray(kim.tobytes()), w, h, rgb=rgb, edge=edge)
        if not any(keep):
            return False
    # bbox
    xs = [i % w for i in range(w * h) if keep[i]]
    ys = [i // w for i in range(w * h) if keep[i]]
    if not xs:
        return False
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    prod = im.crop((x0, y0, x1 + 1, y1 + 1))
    mask_im = Image.frombytes("L", (w, h), bytes(255 if k else 0 for k in keep)).crop((x0, y0, x1 + 1, y1 + 1))
    # вписываем в канву
    max_side = int(CANVAS * PAD)
    pw, ph = prod.size
    k = min(max_side / pw, max_side / ph, 1.0)
    nw, nh = max(1, int(pw * k)), max(1, int(ph * k))
    prod = prod.resize((nw, nh), Image.LANCZOS)
    mask_im = mask_im.resize((nw, nh), Image.LANCZOS)
    # сглаживаем край маски
    mask_sm = mask_im.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
    canvas = Image.new("RGB", (CANVAS, CANVAS), ICE)
    ox, oy = (CANVAS - nw) // 2, (CANVAS - nh) // 2
    # мягкая тень по стандарту: blur18, сдвиг (+6,+26), цвет (15,40,90), alpha*0.35
    sh = Image.new("L", (CANVAS, CANVAS), 0)
    sh.paste(mask_sm, (ox + 6, oy + 26))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    sh_col = Image.new("RGB", (CANVAS, CANVAS), (15, 40, 90))
    sh_a = sh.point(lambda v: int(v * 0.35))
    canvas = Image.composite(sh_col, canvas, sh_a)
    canvas.paste(prod, (ox, oy), mask_sm)
    canvas.save(out, "webp", quality=85, method=6)
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
                print("SKIP (пусто):", f)
        except Exception as e:
            print("ERR:", f, e)
    print(f"OK: {ok}/{len(names)} -> {DST}")


if __name__ == "__main__":
    main()
