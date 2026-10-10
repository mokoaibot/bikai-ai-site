# hero_originals — чистые исходники ДО обработки

Необработанные оригиналы для самостоятельной компоновки hero-слайдов.
Ничем не правлены: без вырезания фона, кропов и инпейнта.
Рядом лежит `hero_sources/` — моя попытка обработки (с косяками, для справки).

## Баннеры bikaicorp.com (главная, верхний слайдер)

| Файл | Источник |
|---|---|
| `banner-hplc-uhplc-pro-series.png` (1896×830) | https://bikaicorp.com/uploads/images/20260701/20260701185927753084.png |
| `banner-uvvis-ultra-3000.png` (1896×830) | https://bikaicorp.com/uploads/images/20260618/20260618094924240260.png |
| `banner-uhplc1521-hplc1511.png` (1347×1167) | https://bikaicorp.com/uploads/images/20260807/20260807102340933358.png |

## Продуктовые фото (каталог, оригиналы производителя)

| Файл | Что на фото | Источник |
|---|---|---|
| `lamp-waters-2487.jpg` | лампа D2, тёмный фон, водяной знак BIKAI | https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/17e0e2f9-cd4e-44ea-91fb-b4d1fdb6b489.jpg |
| `lamp-pe-lambda-d2.jpg` | лампа D2 с кронштейном | …/bd6da430-ba52-4d46-a264-5c827bdc6344.jpg |
| `lamp-knauer-2501.jpg` | лампа KNAUER | …/b7a1740c-1903-4a6f-b35f-e89294e84914.jpg |
| `lamp-agilent-1290-dad.jpg` | лампа Agilent 1290 DAD | …/d3436759-88d1-4cf7-95cc-301c61a7be39.jpg |
| `lamp-shimadzu-lc2030-2040.jpg` | лампа Shimadzu LC-2030/2040 | …/705c62f0-e722-4ba6-9cf5-7bfa737e91e6.jpg |
| `lamp-thermofisher-u3000-tungsten.jpg` | лампа тангаловая Thermo U3000 | …/b59a6515-a42a-4bbd-9d96-18766c4ec6d7.jpg |
| `equivalent-lamp.webp` | лампа в коробке Hamamatsu, чёрный фон | …/64179b26-2a50-408c-b1e9-e39671da2d73.png |
| `column.jpg` | колонки хроматографические, белый фон | …/9178baa2-03af-4d13-b930-7ef02ff851db.jpg |
| `cuvette.jpg` | кювета, белый фон | …/78b68a87-82e1-4f24-80dc-8d4bfc314d4d.jpg |
| `tq-1620.webp` | масс-спектрометр TQ 1620, прозрачный фон | https://bikaicorp.com/uploads/images/20260922/20260922131543680163.png |
| `consumables-scene-blue.png` | витрина расходников, голубая студийная сцена (от заказчика) | загрузка пользователя |
| `consumables-catalog-black.png` | каталожная коллекция расходников на чёрном (от заказчика) | загрузка пользователя |

(полные URL — в таблице базы `catalog/data/bikai_catalog.db`, поле image_url)

## Замечания для обработки

- Фото ламп: тёмный градиентный фон + полупрозрачный водяной знак BIKAI по центру и краям.
- `equivalent-lamp.webp`: чёрный фон, без водяного знака, но с коробкой Hamamatsu.
- Готовый результат кладётся в `bikai.by/site/assets/hero/<slug>.jpg`
  (slug: `chromatography`, `mass-spectrometry`, `spectroscopy`, `consumables`),
  затем `python3 scripts/build_site.py`.
