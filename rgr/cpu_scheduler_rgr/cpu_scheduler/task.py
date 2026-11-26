"""Модель задачі (процесу) з інкапсуляцією та перевантаженими операторами."""
from __future__ import annotations

from typing import Optional, Union

from .exceptions import TaskValueError

MAX_TIME = 10 ** 6  # верхня межа для часових параметрів, од. часу


class Task:
    """Задача у черзі процесора: ідентифікатор, момент надходження, тривалість."""

    def __init__(self, pid: str, arrival: int, burst: int) -> None:
        self._pid = ""  # приватний ідентифікатор
        self._arrival = 0  # приватний момент надходження
        self._burst = 1  # приватна тривалість виконання
        self._remaining = 1  # залишок часу виконання
        self._first_start: Optional[int] = None  # момент першого запуску
        self._finish: Optional[int] = None  # момент завершення
        self.pid = pid  # присвоєння виконує валідацію у сеттері
        self.arrival = arrival
        self.burst = burst

    # ---------- властивості (інкапсуляція) ----------
    @property
    def pid(self) -> str:
        return self._pid

    @pid.setter
    def pid(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise TaskValueError("Ідентифікатор задачі має бути непорожнім рядком")
        self._pid = value.strip().upper()  # нормалізація до верхнього регістру

    @property
    def arrival(self) -> int:
        return self._arrival

    @arrival.setter
    def arrival(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TaskValueError("Момент надходження має бути цілим числом")
        if not 0 <= value <= MAX_TIME:
            raise TaskValueError(f"Момент надходження поза межами [0; {MAX_TIME}]")
        self._arrival = value

    @property
    def burst(self) -> int:
        return self._burst

    @burst.setter
    def burst(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TaskValueError("Тривалість має бути цілим числом")
        if not 1 <= value <= MAX_TIME:
            raise TaskValueError(f"Тривалість поза межами [1; {MAX_TIME}]")
        self._burst = value
        self._remaining = value  # зміна тривалості скидає залишок

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def first_start(self) -> Optional[int]:
        return self._first_start

    @property
    def finish(self) -> Optional[int]:
        return self._finish

    @property
    def is_done(self) -> bool:
        return self._remaining == 0

    # ---------- службові методи стану ----------
    def run(self, start: int, amount: int) -> int:
        """Виконати задачу `amount` одиниць часу, починаючи з моменту `start`."""
        if amount <= 0 or amount > self._remaining:
            raise TaskValueError("Некоректна кількість одиниць часу для виконання")
        if self._first_start is None:
            self._first_start = start  # фіксуємо перший запуск
        self._remaining -= amount  # зменшуємо залишок
        if self._remaining == 0:
            self._finish = start + amount  # фіксуємо момент завершення
        return self._remaining

    def reset(self) -> None:
        """Повернути задачу у початковий стан перед новим моделюванням."""
        self._remaining = self._burst
        self._first_start = None
        self._finish = None

    def clone(self) -> "Task":
        """Створити незалежну копію з початковим станом."""
        return Task(self._pid, self._arrival, self._burst)

    # ---------- dunder-методи ----------
    def __str__(self) -> str:
        return f"{self._pid}(arrival={self._arrival}, burst={self._burst})"

    def __repr__(self) -> str:
        return f"Task(pid={self._pid!r}, arrival={self._arrival}, burst={self._burst})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented  # інші типи порівнювати не можна
        return (self._pid, self._arrival, self._burst) == (
            other._pid, other._arrival, other._burst)

    def __hash__(self) -> int:
        return hash((self._pid, self._arrival, self._burst))

    def __lt__(self, other: "Task") -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        # порядок черги: спочатку момент надходження, потім ідентифікатор
        return (self._arrival, self._pid) < (other._arrival, other._pid)

    def __add__(self, other: Union["Task", int]) -> int:
        """Сума тривалостей двох задач (або задачі та числа)."""
        if isinstance(other, Task):
            return self._burst + other._burst
        if isinstance(other, int) and not isinstance(other, bool):
            return self._burst + other
        return NotImplemented

    __radd__ = __add__  # дозволяє використовувати sum(tasks)

    def __sub__(self, other: "Task") -> int:
        """Різниця моментів надходження двох задач."""
        if isinstance(other, Task):
            return self._arrival - other._arrival
        return NotImplemented
