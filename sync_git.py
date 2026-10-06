#!/usr/bin/env python3
"""
sync_git.py — лёгкая автоматизация синхронизации Monorepo с GitHub.

Токен и URL репозитория читаются из .env (никогда не хранятся в коде и
не попадают в постоянный git remote/.git/config — подставляются только
на момент выполнения pull/push). Все сообщения перед выводом в терминал
очищаются от токена (redact), чтобы он не "засветился" в логах.

Использование из терминала:
    python3 sync_git.py pull                      # скачать изменения с GitHub
    python3 sync_git.py push                       # закоммитить и отправить всё в GitHub
    python3 sync_git.py push "Текст коммита"       # push с собственным сообщением коммита
    python3 sync_git.py status                      # посмотреть состояние репозитория

Этот модуль также импортируется Оркестратором (dashboard/core.py),
чтобы синхронизацию можно было запускать текстовой командой в чате,
например: «Запушь изменения на гитхаб» или «Подтяни изменения с гитхаба».
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


# ---------------------------------------------------------------------- #
# Загрузка .env без внешних зависимостей
# ---------------------------------------------------------------------- #

def load_env(path: Path = ENV_FILE) -> dict:
    env = {}
    if not path.exists():
        return env
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


@dataclass
class GitResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class GitSyncError(RuntimeError):
    pass


class GitSync:
    """Инкапсулирует безопасную синхронизацию monorepo с GitHub."""

    def __init__(self, base_dir: Path = BASE_DIR, env: dict | None = None):
        self.base_dir = base_dir
        self.env = env if env is not None else load_env(base_dir / ".env")

        self.repo_url = self.env.get("GITHUB_REPO_URL")
        self.token = self.env.get("GITHUB_TOKEN")
        self.branch = self.env.get("GITHUB_BRANCH", "main")
        self.user_name = self.env.get("GIT_USER_NAME", "Arena Orchestrator")
        self.user_email = self.env.get("GIT_USER_EMAIL", "orchestrator@arena.local")

    # ------------------------------------------------------------------ #
    # Низкоуровневые помощники
    # ------------------------------------------------------------------ #

    def _redact(self, text: str) -> str:
        if self.token and self.token in text:
            text = text.replace(self.token, "***TOKEN***")
        return text

    def _run(self, args: list[str], check: bool = True) -> GitResult:
        proc = subprocess.run(
            ["git", *args], cwd=self.base_dir, text=True, capture_output=True
        )
        result = GitResult(proc.returncode, self._redact(proc.stdout), self._redact(proc.stderr))
        if check and not result.ok:
            raise GitSyncError(result.stderr.strip() or result.stdout.strip() or "git-команда завершилась с ошибкой")
        return result

    def _authenticated_url(self) -> str:
        if not self.repo_url:
            raise GitSyncError("GITHUB_REPO_URL не задан в .env")
        if not self.token:
            raise GitSyncError("GITHUB_TOKEN не задан в .env")
        match = re.match(r"https://(.+)", self.repo_url)
        if not match:
            raise GitSyncError("GITHUB_REPO_URL должен начинаться с https://")
        return f"https://{self.token}@{match.group(1)}"

    def _display_url(self) -> str:
        return self.repo_url or "(не задан)"

    # ------------------------------------------------------------------ #
    # Подготовка репозитория
    # ------------------------------------------------------------------ #

    def ensure_repo(self) -> list[str]:
        """Гарантирует, что это git-репозиторий с нужным remote/пользователем. Возвращает лог шагов."""
        steps = []
        if not (self.base_dir / ".git").exists():
            self._run(["init"])
            self._run(["checkout", "-B", self.branch])
            steps.append("Инициализирован новый git-репозиторий.")

        remotes = self._run(["remote"], check=False).stdout.split()
        if "origin" not in remotes:
            self._run(["remote", "add", "origin", self.repo_url])
            steps.append(f"Добавлен remote 'origin' -> {self._display_url()}")
        else:
            current = self._run(["remote", "get-url", "origin"], check=False).stdout.strip()
            if current != self.repo_url:
                self._run(["remote", "set-url", "origin", self.repo_url])
                steps.append(f"Обновлён remote 'origin' -> {self._display_url()}")

        name = self._run(["config", "user.name"], check=False).stdout.strip()
        if not name:
            self._run(["config", "user.name", self.user_name])
            steps.append(f"Установлен git user.name = {self.user_name}")

        email = self._run(["config", "user.email"], check=False).stdout.strip()
        if not email:
            self._run(["config", "user.email", self.user_email])
            steps.append(f"Установлен git user.email = {self.user_email}")

        return steps

    # ------------------------------------------------------------------ #
    # Команды
    # ------------------------------------------------------------------ #

    def _remote_branch_exists(self, auth_url: str) -> bool:
        result = self._run(["ls-remote", "--heads", auth_url, self.branch], check=False)
        return result.ok and bool(result.stdout.strip())

    def pull(self) -> dict:
        log = self.ensure_repo()
        auth_url = self._authenticated_url()

        if not self._remote_branch_exists(auth_url):
            log.append(
                f"Удалённый репозиторий ({self._display_url()}) пока пуст — ветки '{self.branch}' "
                f"там ещё нет. Нечего скачивать. Можно сразу делать push."
            )
            return {"status": "empty_remote", "log": log}

        self._run(["fetch", auth_url, f"{self.branch}:refs/remotes/origin/{self.branch}"])
        log.append(f"Получены данные с GitHub ({self._display_url()}, ветка {self.branch}).")

        current_branch = self._run(["branch", "--show-current"], check=False).stdout.strip()
        has_commits = self._run(["rev-parse", "--verify", "HEAD"], check=False).ok

        if not has_commits:
            # Первая синхронизация: локальных коммитов ещё нет — просто переключаемся на удалённую ветку.
            self._run(["reset", "--hard", f"refs/remotes/origin/{self.branch}"])
            log.append("Локальный репозиторий был пуст — переключён на содержимое GitHub.")
        else:
            merge = self._run(
                ["merge", f"refs/remotes/origin/{self.branch}", "--allow-unrelated-histories",
                 "-m", "Merge remote changes via sync_git.py"],
                check=False,
            )
            if not merge.ok:
                log.append("⚠️ Конфликт при слиянии изменений — требуется ручное разрешение.")
                return {"status": "conflict", "log": log, "details": merge.stderr}
            log.append("Изменения с GitHub слиты в локальную копию.")

        return {"status": "ok", "log": log}

    def push(self, message: str | None = None) -> dict:
        log = self.ensure_repo()

        self._run(["add", "-A"])
        commit_message = message or f"Авто-синхронизация системы: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        commit = self._run(["commit", "-m", commit_message], check=False)
        if commit.ok:
            log.append(f"Создан коммит: «{commit_message}»")
        elif "nothing to commit" in (commit.stdout + commit.stderr).lower():
            log.append("Нет новых изменений для коммита (рабочая копия чиста).")
        else:
            return {"status": "error", "log": log, "details": commit.stderr}

        auth_url = self._authenticated_url()
        push_result = self._run(["push", auth_url, f"HEAD:{self.branch}"], check=False)
        if not push_result.ok:
            log.append("⚠️ Push отклонён GitHub. Вероятно, в удалённом репозитории есть изменения, "
                        "которых нет локально — сначала выполните pull.")
            return {"status": "rejected", "log": log, "details": push_result.stderr}

        log.append(f"✅ Изменения отправлены в {self._display_url()} (ветка {self.branch}).")

        # Обновляем локальную remote-tracking ссылку и upstream, чтобы обычные
        # `git status` / `git log` в терминале корректно показывали связь с origin/<branch>.
        head_sha = self._run(["rev-parse", "HEAD"], check=False).stdout.strip()
        if head_sha:
            self._run(["update-ref", f"refs/remotes/origin/{self.branch}", head_sha], check=False)
            self._run(["branch", f"--set-upstream-to=origin/{self.branch}", self.branch], check=False)

        return {"status": "ok", "log": log}

    def status(self) -> dict:
        if not (self.base_dir / ".git").exists():
            return {"status": "no_repo", "message": "Git-репозиторий ещё не инициализирован."}
        branch = self._run(["branch", "--show-current"], check=False).stdout.strip() or "(нет коммитов)"
        porcelain = self._run(["status", "--porcelain"], check=False).stdout
        changed = [line for line in porcelain.splitlines() if line.strip()]
        remote = self._run(["remote", "get-url", "origin"], check=False).stdout.strip() or "(не задан)"
        last_commit = self._run(["log", "-1", "--pretty=%h %s (%cr)"], check=False).stdout.strip() or "ещё нет коммитов"
        return {
            "status": "ok",
            "branch": branch,
            "remote": remote,
            "changed_files": len(changed),
            "changed_preview": changed[:15],
            "last_commit": last_commit,
        }

    def check_connection(self) -> dict:
        """Проверяет, что токен действителен и репозиторий доступен (без скачивания данных)."""
        try:
            auth_url = self._authenticated_url()
        except GitSyncError as exc:
            return {"ok": False, "message": str(exc)}
        result = self._run(["ls-remote", auth_url, "HEAD"], check=False)
        if result.ok:
            return {"ok": True, "message": "Подключение к GitHub успешно, токен действителен."}
        return {"ok": False, "message": result.stderr.strip() or "Не удалось подключиться к репозиторию."}


# ---------------------------------------------------------------------- #
# CLI
# ---------------------------------------------------------------------- #

def _print_log(result: dict) -> None:
    for line in result.get("log", []):
        print(f"  • {line}")
    if result.get("details"):
        print("  Подробности:", result["details"])


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    sync = GitSync()

    if command == "pull":
        result = sync.pull()
        _print_log(result)
        sys.exit(0 if result["status"] in ("ok", "empty_remote") else 1)

    elif command == "push":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        result = sync.push(message)
        _print_log(result)
        sys.exit(0 if result["status"] == "ok" else 1)

    elif command == "status":
        result = sync.status()
        if result["status"] == "no_repo":
            print(result["message"])
        else:
            print(f"Ветка: {result['branch']}")
            print(f"Remote: {result['remote']}")
            print(f"Изменённых файлов: {result['changed_files']}")
            for line in result["changed_preview"]:
                print(f"  {line}")
            print(f"Последний коммит: {result['last_commit']}")

    elif command == "check":
        result = sync.check_connection()
        print(result["message"])
        sys.exit(0 if result["ok"] else 1)

    else:
        print(f"Неизвестная команда: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
