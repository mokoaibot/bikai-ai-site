#!/usr/bin/env python3
"""
run_orchestrator.py — удобный CLI для управления системой прямо из
терминала Arena AI (для тестирования без дашборда).

Напоминание: исполнитель один — ИИ-агент. "Проекты" ниже — это именованные
профили контекста, а не отдельные боты.

Главный способ управления системой — ЧАТ:

    python3 run_orchestrator.py chat "Заведи проект SEO для анализа ключевых слов"
    python3 run_orchestrator.py chat "Добавь SEO инструкцию анализа конкурентов"
    python3 run_orchestrator.py chat "Создай задачу для SEO: собрать топ-10 запросов"
    python3 run_orchestrator.py chat "Запомни паттерн: всегда проверяй источники"

Служебные команды:

    python3 run_orchestrator.py audit          # пересканировать репозиторий
    python3 run_orchestrator.py list-projects  # краткий список проектов
    python3 run_orchestrator.py export         # собрать META_PROMPT.md
    python3 run_orchestrator.py config         # сводка конфигурации/ключей
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "dashboard"))

from core import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI для Context-Driven системы с одним исполнителем (Arena AI)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat_parser = subparsers.add_parser("chat", help="Отправить текстовую команду исполнителю")
    chat_parser.add_argument("text", help="Текст команды, например: 'Заведи проект ...'")

    subparsers.add_parser("audit", help="Запустить полный аудит системы")
    subparsers.add_parser("list-projects", help="Показать список существующих проектов")
    subparsers.add_parser("export", help="Собрать META_PROMPT.md из текущей архитектуры")
    subparsers.add_parser("config", help="Показать сводку текущей конфигурации")

    args = parser.parse_args()
    orchestrator = Orchestrator()

    if args.command == "chat":
        result = orchestrator.handle_chat_message(args.text)
        print(result["reply"])
        print()
        print("--- intent ---")
        print(json.dumps(result["intent"], ensure_ascii=False, indent=2))

    elif args.command == "audit":
        state = orchestrator.run_audit()
        print(json.dumps(state, ensure_ascii=False, indent=2))

    elif args.command == "list-projects":
        state = orchestrator.run_audit()
        if not state["projects"]:
            print("Проекты пока не заведены.")
        for project in state["projects"]:
            print(
                f"- {project['name']} ({project['role']}): инструкций={project['instructions_count']}, "
                f"записей в логах={project['log_lines']}"
            )

    elif args.command == "export":
        result = orchestrator.export_meta_prompt()
        print(f"Мета-промт сохранён в {result['path']}")

    elif args.command == "config":
        print(json.dumps(orchestrator.config.summary(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
