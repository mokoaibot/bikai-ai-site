# bikai.by — дилерский сайт

Реальный сайт белорусского дилера (ООО «Сайенстех»), в отличие от
`../catalog/` — это был внутренний черновик для утверждения каталога.
Здесь: другой дизайн (светлый, современный, 2026), только русский язык,
акцент дилера (наличие/консультация/поставка), а не история бренда.

## Как пересобрать

```
python3 scripts/build_site.py
```

Данные о товарах не дублируются — скрипт читает их напрямую из
`../catalog/data/bikai_catalog.db` и `../catalog/images/`. Значит, при
обновлении каталога (`catalog/scripts/build_data.py` → `build_db.py`)
этот сайт пересобирается уже актуальными данными этой же командой.

## Структура

```
site/
  index.html          ← главная
  catalog/index.html  ← каталог: Приборы + Расходные материалы, поиск
  product/<slug>.html ← 55 карточек товара
  contacts.html        ← контакты + реквизиты ООО «Сайенстех»
  assets/style.css     ← вся стилистика
  images/               ← копия фото из catalog/images
  og-cover.webp         ← карточка Open Graph (1200×630)
  catalog-compare.html  ← сравнение фото, сохранять до проверки заказчиком
  images-new/           ← прозрачный вариант фото для сравнения, сохранять
```

## Публикация и превью ссылок

- Основной домен: https://bikai.by/; пользовательский хостинг отвечает через
  LiteSpeed. GitHub Pages `https://mokoaibot.github.io/bikai-ai-site/` — зеркало.
- В build-шаблон добавлены description, canonical, Open Graph и Twitter Card;
  карточки товаров используют фото товара. Общая карточка — `site/og-cover.webp`.
- Для обновления основного хостинга нужен upload результата `site/` в web-root;
  `engine/deploy_gh_pages.py` обновляет только зеркало. Текущий архив для
  ручной загрузки: `/home/user/bikai-by-site-update.zip`.
- Более широкое SEO, Schema.org и регистрация в БелГИЭ / привязка ЕРИП
  остаются отдельными задачами.

## Дизайн v2 (10.10.2026)

Сайт пересобран по брендбуку v2 (design language по мотивам Mindray):
токены в `site/assets/style.css`, шрифт Source Sans 3 (локальные woff2),
в шапке и подвале — официальный wordmark (`assets/logo-wordmark.svg`),
favicon — эмблема. Пересборка: `python3 scripts/build_site.py`.
