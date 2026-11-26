"""Метрики якості диспетчеризації та результат моделювання."""
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Segment:
    """Інтервал діаграми Ганта: задача (або простій) та межі в часі."""

    pid: str
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


class SimulationResult:
    """Результат моделювання: діаграма Ганта та обчислені показники."""

    def __init__(self, algorithm: str, tasks: list, segments: List[Segment]) -> None:
        self._algorithm = algorithm  # назва алгоритму
        self._tasks = tasks  # задачі зі зафіксованими часами
        self._segments = segments  # діаграма Ганта

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def segments(self) -> List[Segment]:
        return list(self._segments)  # повертаємо копію (захист стану)

    @property
    def makespan(self) -> int:
        return self._segments[-1].end if self._segments else 0

    @property
    def busy_time(self) -> int:
        return sum(s.length for s in self._segments if s.pid != "IDLE")

    @property
    def context_switches(self) -> int:
        """Кількість перемикань контексту між різними задачами."""
        pids = [s.pid for s in self._segments if s.pid != "IDLE"]
        return sum(1 for a, b in zip(pids, pids[1:]) if a != b)

    @property
    def cpu_utilization(self) -> float:
        """Завантаження процесора, % (формула 2.4)."""
        return 100.0 * self.busy_time / self.makespan if self.makespan else 0.0

    @property
    def throughput(self) -> float:
        """Пропускна здатність: задач за одиницю часу (формула 2.5)."""
        return len(self._tasks) / self.makespan if self.makespan else 0.0

    def per_task(self) -> List[Dict[str, object]]:
        """Показники кожної задачі у вигляді словників (для звіту та файлів)."""
        rows = []
        for task in self._tasks:
            turnaround = task.finish - task.arrival  # формула 2.2
            rows.append({
                "pid": task.pid,
                "arrival": task.arrival,
                "burst": task.burst,
                "start": task.first_start,
                "finish": task.finish,
                "waiting": turnaround - task.burst,  # формула 2.3
                "turnaround": turnaround,
                "response": task.first_start - task.arrival,  # формула 2.6
            })
        return rows

    def _average(self, key: str) -> float:
        rows = self.per_task()
        return sum(int(row[key]) for row in rows) / len(rows)

    @property
    def avg_waiting(self) -> float:
        return self._average("waiting")

    @property
    def avg_turnaround(self) -> float:
        return self._average("turnaround")

    @property
    def avg_response(self) -> float:
        return self._average("response")

    def summary(self) -> Dict[str, object]:
        """Зведені показники моделювання."""
        return {
            "algorithm": self._algorithm,
            "tasks": len(self._tasks),
            "makespan": self.makespan,
            "avg_waiting": round(self.avg_waiting, 2),
            "avg_turnaround": round(self.avg_turnaround, 2),
            "avg_response": round(self.avg_response, 2),
            "cpu_utilization": round(self.cpu_utilization, 2),
            "throughput": round(self.throughput, 4),
            "context_switches": self.context_switches,
        }

    def __str__(self) -> str:
        return (f"{self._algorithm}: tasks={len(self._tasks)}, makespan={self.makespan}, "
                f"avg_wait={self.avg_waiting:.2f}, switches={self.context_switches}")

    def __repr__(self) -> str:
        return f"SimulationResult(algorithm={self._algorithm!r}, tasks={len(self._tasks)})"

    def __lt__(self, other: "SimulationResult") -> bool:
        """Порівняння алгоритмів за середнім часом очікування."""
        if not isinstance(other, SimulationResult):
            return NotImplemented
        return self.avg_waiting < other.avg_waiting
