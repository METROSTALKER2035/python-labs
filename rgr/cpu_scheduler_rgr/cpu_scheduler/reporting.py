"""Текстові звіти для консолі: таблиця задач, діаграма Ганта, порівняння."""
from typing import Dict, List

from .metrics import SimulationResult

LINE = "=" * 78  # розділювач розділів звіту


def format_task_table(result: SimulationResult) -> str:
    """Таблиця показників кожної задачі."""
    head = f"{'PID':<6}{'Arr':>5}{'Burst':>7}{'Start':>7}{'Finish':>8}{'Wait':>7}{'TAT':>6}{'Resp':>7}"
    lines = [head, "-" * len(head)]
    for row in result.per_task():
        lines.append(f"{row['pid']:<6}{row['arrival']:>5}{row['burst']:>7}{row['start']:>7}"
                     f"{row['finish']:>8}{row['waiting']:>7}{row['turnaround']:>6}{row['response']:>7}")
    return "\n".join(lines)


def format_gantt(result: SimulationResult) -> str:
    """Діаграма Ганта у вигляді рядка сегментів та шкали часу."""
    cells = " ".join(f"[{seg.pid} {seg.start}-{seg.end}]" for seg in result.segments)
    return cells


def format_summary(result: SimulationResult) -> str:
    """Зведені показники одного алгоритму."""
    s = result.summary()
    return (f"Середній час очікування : {s['avg_waiting']:.2f}\n"
            f"Середній час обороту    : {s['avg_turnaround']:.2f}\n"
            f"Середній час відгуку    : {s['avg_response']:.2f}\n"
            f"Завантаження CPU, %     : {s['cpu_utilization']:.2f}\n"
            f"Пропускна здатність     : {s['throughput']:.4f}\n"
            f"Перемикань контексту    : {s['context_switches']}\n"
            f"Загальний час (makespan): {s['makespan']}")


def format_report(result: SimulationResult, with_gantt: bool = False) -> str:
    """Повний звіт для одного алгоритму."""
    parts = [LINE, f"Алгоритм: {result.algorithm}", LINE, format_task_table(result), "",
             format_summary(result)]
    if with_gantt:
        parts += ["", "Діаграма Ганта:", format_gantt(result)]
    return "\n".join(parts)


def format_comparison(results: List[SimulationResult]) -> str:
    """Порівняльна таблиця алгоритмів."""
    head = f"{'Алгоритм':<12}{'Wait':>8}{'TAT':>8}{'Resp':>8}{'CPU,%':>9}{'Switch':>8}"
    lines = [LINE, "Порівняння алгоритмів", LINE, head, "-" * len(head)]
    for res in results:
        s = res.summary()
        lines.append(f"{s['algorithm']:<12}{s['avg_waiting']:>8.2f}{s['avg_turnaround']:>8.2f}"
                     f"{s['avg_response']:>8.2f}{s['cpu_utilization']:>9.2f}{s['context_switches']:>8}")
    best = min(results)  # використовуємо __lt__ для вибору найкращого
    lines.append(f"Найменший середній час очікування: {best.algorithm}")
    return "\n".join(lines)


def format_benchmark(rows: List[Dict[str, float]]) -> str:
    """Таблиця результатів бенчмаркінгу."""
    head = f"{'Задач':>8}{'FIFO, мс':>12}{'RR, мс':>12}"
    lines = [LINE, "Бенчмаркінг time.perf_counter()", LINE, head, "-" * len(head)]
    for row in rows:
        lines.append(f"{row['tasks']:>8}{row['fifo_ms']:>12.3f}{row['rr_ms']:>12.3f}")
    return "\n".join(lines)
