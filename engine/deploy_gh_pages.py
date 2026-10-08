#!/usr/bin/env python3
"""
deploy_gh_pages.py — публикует статический сайт в ветку `gh-pages` репозитория
(без отдельного workflow-файла: текущий GitHub-токен не имеет scope `workflow`,
поэтому Actions недоступны — публикуем напрямую через git push в ветку).

Использование:
    python3 engine/deploy_gh_pages.py directions/bikai/bikai.by/site

Один раз вручную нужно включить Pages в настройках репозитория:
Settings -> Pages -> Source: "Deploy from a branch" -> Branch: gh-pages / (root).
Дальше просто перезапускать этот скрипт после каждого обновления сайта.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_git  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Использование: python3 engine/deploy_gh_pages.py <папка_сайта>")
        sys.exit(1)

    src = Path(sys.argv[1]).resolve()
    if not src.is_dir():
        print(f"Папка не найдена: {src}")
        sys.exit(1)

    gs = sync_git.GitSync(base_dir=sync_git.BASE_DIR)
    url = gs._authenticated_url()

    tmp = Path("/tmp/ghpages_deploy")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    subprocess.run(["bash", "-c", f"cp -r '{src}'/. '{tmp}'/"], check=True)
    (tmp / ".nojekyll").touch()

    def run(args):
        r = subprocess.run(args, cwd=tmp, capture_output=True, text=True)
        shown = [a if a != url else "***URL-WITH-TOKEN***" for a in args]
        print(" ".join(shown), "->", r.returncode)
        out = gs._redact(r.stdout) + gs._redact(r.stderr)
        if out.strip():
            print(out.strip())
        return r

    run(["git", "init", "-q", "-b", "gh-pages"])
    run(["git", "config", "user.name", gs.user_name])
    run(["git", "config", "user.email", gs.user_email])
    run(["git", "add", "-A"])
    run(["git", "commit", "-q", "-m", "Deploy site"])
    res = run(["git", "push", "-f", url, "gh-pages:gh-pages"])

    if res.returncode == 0:
        print("✅ Опубликовано в ветку gh-pages.")
    else:
        print("❌ Push не удался, см. вывод выше.")
        sys.exit(1)


if __name__ == "__main__":
    main()
