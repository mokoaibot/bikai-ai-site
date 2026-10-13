# bikai.by — дилерский сайт

Реальный сайт белорусского дилера (ООО «Сайенстех»), в отличие от
`../catalog/` — это был внутренний черновик для утверждения каталога.
Здесь: другой дизайн (светлый, современный, 2026), только русский язык,
акцент дилера (наличие/консультация/поставка), а не история бренда.

**[Скачать текущий архив сайта (ZIP)](https://github.com/mokoaibot/bikai-ai-site/raw/refs/heads/main/directions/bikai/bikai.by/site-current.zip)**

Архив автоматически пересобирается скриптом `scripts/build_site.py`.

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
  og-cover.jpg          ← JPEG только для Open Graph-превью (1200×630)
  og-cover.webp         ← прежняя WebP-версия общей карточки
  catalog-compare.html  ← сравнение фото, сохранять до проверки заказчиком
  images-new/           ← прозрачный вариант фото для сравнения, сохранять
```

## Публикация и превью ссылок

- Основной домен: https://bikai.by/; пользовательский хостинг отвечает через
  LiteSpeed. GitHub Pages `https://mokoaibot.github.io/bikai-ai-site/` — зеркало.
- В build-шаблон добавлены description, canonical, Open Graph и Twitter Card.
  Для надёжности Telegram все страницы используют общую `site/og-cover.jpg`;
  это одно разрешённое JPEG-исключение, остальные изображения — WebP.
- Пользователь уже загрузил предыдущую версию в FTP; текущий пакет с JPEG нужно
  загрузить повторно в web-root. `engine/deploy_gh_pages.py` обновляет только зеркало.
  Готовый архив (191 файл, около 4.2 MB): `/home/user/bikai-by-site-update.zip`.
- Более широкое SEO, Schema.org и регистрация в БелГИЭ / привязка ЕРИП
  остаются отдельными задачами.

## Дизайн v2 (10.10.2026)

Сайт пересобран по брендбуку v2 (design language по мотивам Mindray):
токены в `site/assets/style.css`, шрифт Source Sans 3 (локальные woff2),
в шапке и подвале — официальный wordmark (`assets/logo-wordmark.svg`),
favicon — эмблема. Пересборка: `python3 scripts/build_site.py`.
