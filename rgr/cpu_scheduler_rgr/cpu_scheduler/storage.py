"""Персистентне збереження та завантаження даних у форматах TXT, CSV і JSON."""
import csv
import json
from pathlib import Path
from typing import Iterable, List

from .exceptions import DataFileFormatError, PersistenceError
from .metrics import SimulationResult
from .parser import parse_tasks
from .task import Task

CSV_FIELDS = ["pid", "arrival", "burst", "start", "finish",
              "waiting", "turnaround", "response"]  # стовпці файлу результатів


def load_tasks(path: str) -> List[Task]:
    """Завантажити набір задач із файлу .txt, .csv або .json."""
    file = Path(path)
    suffix = file.suffix.lower()
    if suffix not in (".txt", ".csv", ".json"):
        raise DataFileFormatError(f"Непідтримуване розширення '{suffix}'")
    try:
        with open(file, "r", encoding="utf-8") as handle:  # менеджер контексту
            if suffix == ".json":
                return _tasks_from_json(json.load(handle))
            return parse_tasks(handle)  # TXT та CSV читаємо рядок за рядком
    except FileNotFoundError as exc:
        raise PersistenceError(f"Файл '{path}' не знайдено") from exc
    except OSError as exc:
        raise PersistenceError(f"Помилка читання '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DataFileFormatError(f"Некоректний JSON: {exc}") from exc


def _tasks_from_json(data: object) -> List[Task]:
    """Перетворити розібраний JSON на список задач із перевіркою структури."""
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        raise DataFileFormatError("JSON має містити об'єкт з масивом 'tasks'")
    lines = []
    for item in data["tasks"]:
        try:
            lines.append(f"{item['pid']};{item['arrival']};{item['burst']}")
        except (KeyError, TypeError) as exc:
            raise DataFileFormatError(f"Елемент '{item}' не містить pid/arrival/burst") from exc
    return parse_tasks(lines)  # повторно використовуємо регулярну валідацію


def save_result_json(path: str, results: Iterable[SimulationResult]) -> None:
    """Зберегти зведені показники та показники задач у JSON."""
    payload = [{"summary": res.summary(), "tasks": res.per_task(),
                "gantt": [vars(seg) for seg in res.segments]} for res in results]
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"results": payload}, handle, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise PersistenceError(f"Не вдалося записати '{path}': {exc}") from exc


def save_result_csv(path: str, results: Iterable[SimulationResult]) -> None:
    """Зберегти показники задач для всіх алгоритмів у CSV (додаткове поле algorithm)."""
    try:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["algorithm"] + CSV_FIELDS)
            writer.writeheader()
            for res in results:
                for row in res.per_task():
                    writer.writerow({"algorithm": res.algorithm, **row})
    except OSError as exc:
        raise PersistenceError(f"Не вдалося записати '{path}': {exc}") from exc
