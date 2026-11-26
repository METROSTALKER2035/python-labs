"""Вимірювання швидкодії алгоритмів за допомогою time.perf_counter()."""
import random
import time
from typing import Dict, List

from .schedulers import FifoScheduler, RoundRobinScheduler, Scheduler
from .task import Task


def generate_tasks(count: int, seed: int = 2026, max_burst: int = 10,
                   max_gap: int = 3) -> List[Task]:
    """Згенерувати детермінований випадковий набір з `count` задач."""
    rng = random.Random(seed)  # власний генератор забезпечує відтворюваність
    tasks, arrival = [], 0
    for number in range(1, count + 1):
        arrival += rng.randint(0, max_gap)  # проміжок між надходженнями
        tasks.append(Task(f"P{number}", arrival, rng.randint(1, max_burst)))
    return tasks


def measure(scheduler: Scheduler, tasks: List[Task], repeats: int = 5) -> float:
    """Повернути мінімальний час одного прогону моделювання, мс."""
    best = float("inf")
    for _ in range(repeats):
        started = time.perf_counter()
        scheduler.run(tasks)
        best = min(best, time.perf_counter() - started)  # мінімум відсікає завади
    return best * 1000.0


def run_benchmark(sizes: List[int], quantum: int = 4, repeats: int = 5,
                  seed: int = 2026) -> List[Dict[str, float]]:
    """Виміряти час FIFO та RR для кожного розміру набору задач."""
    rows = []
    for size in sizes:
        tasks = generate_tasks(size, seed)
        rows.append({
            "tasks": size,
            "fifo_ms": round(measure(FifoScheduler(), tasks, repeats), 3),
            "rr_ms": round(measure(RoundRobinScheduler(quantum), tasks, repeats), 3),
        })
    return rows
