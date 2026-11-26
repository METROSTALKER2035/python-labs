"""Алгоритми диспетчеризації: абстрактний планувальник, FIFO та Round Robin."""
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, List, Sequence

from .exceptions import EmptyTaskSetError, QuantumError
from .metrics import Segment, SimulationResult
from .task import Task

IDLE = "IDLE"  # позначення простою процесора на діаграмі Ганта


class Scheduler(ABC):
    """Базовий клас планувальника: загальна схема моделювання (поліморфізм)."""

    def __init__(self, name: str) -> None:
        self._name = name  # приватна назва алгоритму

    @property
    def name(self) -> str:
        return self._name

    def run(self, tasks: Sequence[Task]) -> SimulationResult:
        """Виконати моделювання на копіях задач і повернути результат."""
        if not tasks:
            raise EmptyTaskSetError("Набір задач порожній")
        work = sorted(task.clone() for task in tasks)  # впорядкування за надходженням
        segments = self._simulate(work)  # конкретний алгоритм у підкласі
        return SimulationResult(self._name, work, segments)

    @abstractmethod
    def _simulate(self, tasks: List[Task]) -> List[Segment]:
        """Побудувати діаграму Ганта для впорядкованого набору задач."""

    @staticmethod
    def _append(segments: List[Segment], pid: str, start: int, end: int) -> None:
        """Додати сегмент, об'єднуючи сусідні сегменти однієї задачі."""
        if segments and segments[-1].pid == pid and segments[-1].end == start:
            segments[-1] = Segment(pid, segments[-1].start, end)
        else:
            segments.append(Segment(pid, start, end))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self._name!r})"


class FifoScheduler(Scheduler):
    """FIFO (FCFS): задачі виконуються без витіснення в порядку надходження."""

    def __init__(self) -> None:
        super().__init__("FIFO")

    def _simulate(self, tasks: List[Task]) -> List[Segment]:
        segments: List[Segment] = []
        clock = 0  # поточний модельний час
        for task in tasks:
            if clock < task.arrival:  # процесор простоює до надходження задачі
                self._append(segments, IDLE, clock, task.arrival)
                clock = task.arrival
            task.run(clock, task.burst)  # виконуємо задачу повністю
            self._append(segments, task.pid, clock, clock + task.burst)
            clock += task.burst
        return segments


class RoundRobinScheduler(Scheduler):
    """Round Robin: циклічне виконання з квантом часу та витісненням."""

    def __init__(self, quantum: int) -> None:
        if isinstance(quantum, bool) or not isinstance(quantum, int) or quantum < 1:
            raise QuantumError("Квант часу має бути цілим числом не менше 1")
        super().__init__(f"RR(q={quantum})")
        self._quantum = quantum  # приватний квант часу

    @property
    def quantum(self) -> int:
        return self._quantum

    def _simulate(self, tasks: List[Task]) -> List[Segment]:
        segments: List[Segment] = []
        queue: Deque[Task] = deque()  # черга готових задач
        clock, index, total = 0, 0, len(tasks)

        def admit() -> None:
            """Перенести до черги всі задачі, що надійшли до моменту clock."""
            nonlocal index
            while index < total and tasks[index].arrival <= clock:
                queue.append(tasks[index])
                index += 1

        admit()
        while queue or index < total:
            if not queue:  # черга порожня: простій до наступного надходження
                self._append(segments, IDLE, clock, tasks[index].arrival)
                clock = tasks[index].arrival
                admit()
            task = queue.popleft()
            step = min(self._quantum, task.remaining)  # тривалість кванта
            task.run(clock, step)
            self._append(segments, task.pid, clock, clock + step)
            clock += step
            admit()  # нові задачі потрапляють у чергу раніше за витіснену
            if not task.is_done:
                queue.append(task)  # незавершена задача йде в кінець черги
        return segments
