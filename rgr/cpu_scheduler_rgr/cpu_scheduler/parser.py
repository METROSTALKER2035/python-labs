"""Імпорт, валідація та нормалізація вхідних даних за допомогою модуля re."""
import re
from typing import Iterable, List, Optional

from .exceptions import (CliArgumentError, DuplicateTaskError, EmptyTaskSetError,
                         TaskFormatError)
from .task import Task

# шаблон рядка задачі: ідентифікатор, надходження, тривалість; роздільник ; , або пробіл
TASK_LINE = re.compile(
    r"^\s*(?P<pid>[A-Za-z][A-Za-z0-9_]{0,7})"
    r"\s*[;,\s]\s*(?P<arrival>\d{1,7})"
    r"\s*[;,\s]\s*(?P<burst>\d{1,7})\s*$"
)
COMMENT = re.compile(r"\s*#.*$")  # коментар до кінця рядка
HEADER = re.compile(r"^\s*pid\b", re.IGNORECASE)  # рядок заголовка CSV
ALGO_FIFO = re.compile(r"^(fifo|fcfs)$", re.IGNORECASE)
ALGO_RR = re.compile(r"^(rr|round[-_ ]?robin)$", re.IGNORECASE)
ALGO_BOTH = re.compile(r"^(both|all)$", re.IGNORECASE)


def parse_task_line(line: str, line_no: int = 1) -> Optional[Task]:
    """Розібрати один рядок; порожні рядки та коментарі повертають None."""
    clean = COMMENT.sub("", line)  # прибираємо коментар
    if not clean.strip() or HEADER.match(clean):
        return None  # пропускаємо порожні рядки та заголовок
    match = TASK_LINE.match(clean)
    if match is None:
        raise TaskFormatError(line_no, line)  # рядок не відповідає шаблону
    return Task(match["pid"], int(match["arrival"]), int(match["burst"]))


def parse_tasks(lines: Iterable[str]) -> List[Task]:
    """Розібрати послідовність рядків у список задач із перевіркою унікальності."""
    tasks: List[Task] = []
    seen = set()  # множина вже зустрінутих ідентифікаторів
    for number, line in enumerate(lines, start=1):
        task = parse_task_line(line, number)
        if task is None:
            continue
        if task.pid in seen:
            raise DuplicateTaskError(f"Дублікат ідентифікатора {task.pid} (рядок {number})")
        seen.add(task.pid)
        tasks.append(task)
    if not tasks:
        raise EmptyTaskSetError("Вхідні дані не містять жодної задачі")
    return tasks


def normalize_algorithm(name: str) -> str:
    """Привести назву алгоритму до канонічного вигляду: fifo, rr або both."""
    text = name.strip()
    if ALGO_FIFO.match(text):
        return "fifo"
    if ALGO_RR.match(text):
        return "rr"
    if ALGO_BOTH.match(text):
        return "both"
    raise CliArgumentError(f"Невідомий алгоритм '{name}' (допустимо: fifo, rr, both)")
