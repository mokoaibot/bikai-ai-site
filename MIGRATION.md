# Перенос репозитория на другой GitHub-аккаунт

Готово: `KEDDE_BIKAI.bundle` — файл со всей историей репозитория (обе ветки:
`main` и `gh-pages`). Это не архив файлов, а настоящий git-репозиторий в
одном файле — можно клонировать прямо из него, без доступа к текущему
приватному репо.

## Шаг 1. Создайте новый репозиторий на новом аккаунте

На GitHub (новый аккаунт) → New repository → имя, например `KEDDE_BIKAI`.
**Важно для GitHub Pages:** если хотите бесплатный Pages — репозиторий
должен быть **Public** (на бесплатном тарифе Pages не работает на приватных
репо — это и есть причина нынешней проблемы, не только про аккаунт).
Ничего не инициализируйте (без README/.gitignore) — репозиторий должен
остаться пустым.

## Шаг 2. Скачайте `KEDDE_BIKAI.bundle` из воркспейса

Файл лежит в корне: `/home/user/KEDDE_BIKAI.bundle` (≈16 МБ). Скачайте его
к себе на компьютер.

## Шаг 3. Залейте историю в новый репозиторий

На своей машине (где есть git):

```bash
git clone KEDDE_BIKAI.bundle KEDDE_BIKAI
cd KEDDE_BIKAI
git remote remove origin
git remote add origin https://github.com/<НОВЫЙ_АККАУНТ>/KEDDE_BIKAI.git
git push origin main
git push origin gh-pages
```

Введёт логин/пароль — используйте Personal Access Token нового аккаунта
вместо пароля (GitHub → Settings → Developer settings → Personal access
tokens → Fine-grained token, права: **Contents: Read and write**, и
**Pages: Read and write**, если хотите, чтобы я тоже мог включать Pages
через API в следующий раз).

## Шаг 4. Включите Pages в новом репозитории

Settings → Pages → Source: **Deploy from a branch** → Branch: **gh-pages**
/ **(root)** → Save. Сайт появится на
`https://<НОВЫЙ_АККАУНТ>.github.io/KEDDE_BIKAI/`.

## Шаг 5. Чтобы я продолжил работать с новым репозиторием

Дайте мне (в чате, не в репозитории):
- новый `GITHUB_REPO_URL`
- новый `GITHUB_TOKEN` (тот самый Personal Access Token)

Я обновлю `.env` — дальше `python3 engine/sync_git.py push/pull` и
`python3 engine/deploy_gh_pages.py ...` будут работать с новым репозиторием
без каких-либо других изменений в коде (весь код читает креды из `.env`,
нигде не хардкодит старый адрес).

## Важное уточнение

Файлы `.env`/токены/секреты в бандл не попали — их там никогда не было
(git их не коммитит, см. `.gitignore`). В бандле только код и история.
