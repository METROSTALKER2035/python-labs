# -*- coding: utf-8 -*-
"""
Лабораторна робота №7, варіант 2 (сортування злиттям, Merge Sort).
Автор: Афанасьєв Сергій, група КІ-24-1.

Модуль містить:
  * рекурсивне сортування злиттям: масив ділиться навпіл до базового випадку
    (довжина 0 або 1), після чого два впорядковані підмасиви зливаються;
  * клас DepthTracker: облік глибини стека через менеджер контексту, перевірка
    безпечного ліміту та коректне зменшення лічильника при виході з кадру;
  * ітеративний аналог (знизу вгору) і порівняння швидкодії з sorted();
  * аналітику: рекурентне співвідношення T(n) = 2T(n/2) + Theta(n) і оцінка за
    основною теоремою, перевірка межі кількості порівнянь.
"""
import math
import random
import sys
import time
from typing import Callable, Optional

REPORT_WIDTH = 98
SEPARATOR = "-" * REPORT_WIDTH
# Безпечний ліміт нижчий за sys.getrecursionlimit() (за замовчуванням 1000),
# щоб лишився запас кадрів для коду, який викликає сортування.
SAFE_DEPTH_LIMIT = 900


class DepthLimitError(RuntimeError):
    """Перевищено безпечний ліміт глибини рекурсії."""


class DepthTracker:
    """Лічильник глибини стека з підтримкою оператора with.

    __enter__ збільшує поточну глибину, __exit__ зменшує її за будь-якого
    виходу з кадру (у тому числі через виняток), тому лічильник не "тече".
    """

    def __init__(self, limit: int = SAFE_DEPTH_LIMIT) -> None:
        self.limit = limit
        self.current = 0
        self.maximum = 0
        self.calls = 0

    def __enter__(self) -> "DepthTracker":
        if self.current + 1 > self.limit:
            # Кадр не приймається, лічильник не змінюється: __exit__ не
            # викликається, якщо __enter__ завершився винятком.
            raise DepthLimitError(
                f"глибина рекурсії перевищила безпечний ліміт {self.limit}")
        self.current += 1
        self.calls += 1
        if self.current > self.maximum:
            self.maximum = self.current
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self.current -= 1
        return False  # винятки не гасимо


class SortStats:
    """Кількість порівнянь елементів під час злиття."""

    def __init__(self) -> None:
        self.comparisons = 0


# ---------------------------------------------------------------------------
# Сортування злиттям
# ---------------------------------------------------------------------------
def merge(left: list, right: list, stats: Optional[SortStats] = None,
          key: Optional[Callable] = None) -> list:
    """Зливає два впорядковані списки в один (стійко: при рівності - лівий)."""
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        a = left[i] if key is None else key(left[i])
        b = right[j] if key is None else key(right[j])
        if stats is not None:
            stats.comparisons += 1
        if a <= b:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])   # один із хвостів порожній
    result.extend(right[j:])
    return result


def merge_sort(items: list, tracker: Optional[DepthTracker] = None,
               stats: Optional[SortStats] = None,
               key: Optional[Callable] = None) -> list:
    """Рекурсивне сортування злиттям. Повертає новий список."""
    if tracker is None:
        tracker = DepthTracker()
    with tracker:                      # кадр входить у лічильник глибини
        if len(items) <= 1:            # базовий випадок: 0 або 1 елемент
            return list(items)
        middle = len(items) // 2
        left = merge_sort(items[:middle], tracker, stats, key)
        right = merge_sort(items[middle:], tracker, stats, key)
        return merge(left, right, stats, key)


def merge_sort_iterative(items: list, stats: Optional[SortStats] = None,
                         key: Optional[Callable] = None) -> list:
    """Ітеративний аналог: злиття відрізків ширини 1, 2, 4, ... знизу вгору."""
    data = list(items)
    width = 1
    while width < len(data):
        merged = []
        for start in range(0, len(data), 2 * width):
            merged.extend(merge(data[start:start + width],
                                data[start + width:start + 2 * width],
                                stats, key))
        data = merged
        width *= 2
    return data


# ---------------------------------------------------------------------------
# Аналітика
# ---------------------------------------------------------------------------
def expected_depth(n: int) -> int:
    """Кількість кадрів merge_sort по найглибшому шляху: ceil(log2 n) + 1."""
    return 1 if n <= 1 else math.ceil(math.log2(n)) + 1


def worst_case_comparisons(n: int) -> int:
    """Верхня межа порівнянь: n*ceil(log2 n) - 2^ceil(log2 n) + 1."""
    if n <= 1:
        return 0
    k = math.ceil(math.log2(n))
    return n * k - 2 ** k + 1


def master_theorem(a: int, b: int, degree: float) -> str:
    """Оцінка T(n) = a*T(n/b) + Theta(n^degree) за основною теоремою."""
    critical = math.log(a, b)
    if abs(degree - critical) < 1e-12:
        return f"Theta(n^{degree:g} * log n)"
    if degree < critical:
        return f"Theta(n^{critical:g})"
    return f"Theta(n^{degree:g})"


# ---------------------------------------------------------------------------
# Допоміжні функції звітів
# ---------------------------------------------------------------------------
def print_header(title: str) -> None:
    print()
    print(title)
    print(SEPARATOR)


def best_time_ms(func, series: int = 3) -> float:
    best = float("inf")
    for _ in range(series):
        started = time.perf_counter()
        func()
        best = min(best, time.perf_counter() - started)
    return best * 1000.0


def naive_recursion(depth: int) -> int:
    """Лінійна рекурсія без захисту: на великій глибині дає RecursionError."""
    return 0 if depth == 0 else 1 + naive_recursion(depth - 1)


def guarded_recursion(depth: int, tracker: DepthTracker) -> int:
    """Та сама рекурсія під контролем DepthTracker."""
    with tracker:
        return 0 if depth == 0 else 1 + guarded_recursion(depth - 1, tracker)


# ---------------------------------------------------------------------------
# Головна функція
# ---------------------------------------------------------------------------
def main() -> bool:
    started = time.perf_counter()
    rng = random.Random(7)

    print_header("[1] Аналіз: рекурентне співвідношення та основна теорема")
    print("T(n) = 2*T(n/2) + f(n), f(n) = Theta(n) - злиття двох половин")
    print(f"a = 2, b = 2, log_b(a) = {math.log(2, 2):g}, f(n) = Theta(n^1)")
    verdict = master_theorem(2, 2, 1)
    print(f"f(n) = Theta(n^log_b(a)): випадок 2 основної теореми, T(n) = {verdict}")
    print(f"Ліміт CPython: sys.getrecursionlimit() = {sys.getrecursionlimit()}, "
          f"безпечний ліміт трекера = {SAFE_DEPTH_LIMIT}")

    print_header("[2] Приклад сортування малого масиву")
    sample = [38, 27, 43, 3, 9, 82, 10, 3]
    tracker = DepthTracker()
    stats = SortStats()
    result = merge_sort(sample, tracker, stats)
    print(f"Вхід:        {sample}")
    print(f"Результат:   {result}")
    print(f"sorted():    {sorted(sample)}")
    print(f"Збігається:  {result == sorted(sample)}")
    print(f"Викликів merge_sort: {tracker.calls}, максимальна глибина: "
          f"{tracker.maximum}, порівнянь: {stats.comparisons}, "
          f"лічильник після виходу: {tracker.current}")

    print_header("[3] Глибина стека та кількість порівнянь")
    print(f"{'n':>9}{'глибина':>9}{'ceil(log2 n)+1':>16}{'викликів':>10}"
          f"{'порівнянь':>11}{'межа':>11}")
    print(SEPARATOR)
    depth_rows = []
    for n in (1, 2, 10, 1000, 100_000):
        data = [rng.randint(0, 10 ** 6) for _ in range(n)]
        tr, st = DepthTracker(), SortStats()
        out = merge_sort(data, tr, st)
        assert out == sorted(data)
        bound = worst_case_comparisons(n)
        depth_rows.append((n, tr.maximum, expected_depth(n), tr.calls,
                           st.comparisons, bound, tr.current))
        print(f"{n:>9}{tr.maximum:>9}{expected_depth(n):>16}{tr.calls:>10}"
              f"{st.comparisons:>11}{bound:>11}")
    print(SEPARATOR)

    print_header("[4] Швидкодія: рекурсивний, ітеративний, sorted()")
    print(f"{'n':>9}{'рекурсія, мс':>14}{'ітерація, мс':>14}{'sorted, мс':>12}"
          f"{'рекурс./sorted':>16}{'нс/(n log2 n)':>15}")
    print(SEPARATOR)
    timing_rows = []
    for n in (1_000, 10_000, 100_000):
        data = [rng.randint(0, 10 ** 6) for _ in range(n)]
        t_rec = best_time_ms(lambda: merge_sort(data))
        t_it = best_time_ms(lambda: merge_sort_iterative(data))
        t_py = best_time_ms(lambda: sorted(data))
        per_unit = t_rec * 1e6 / (n * math.log2(n))
        timing_rows.append((n, t_rec, t_it, t_py, per_unit))
        print(f"{n:>9}{t_rec:>14.3f}{t_it:>14.3f}{t_py:>12.3f}"
              f"{t_rec / t_py:>16.1f}{per_unit:>15.1f}")
    print(SEPARATOR)

    print_header("[5] Контроль глибини та RecursionError")
    tr = DepthTracker(limit=5)
    caught_limit = False
    try:
        merge_sort(list(range(100, 0, -1)), tr)
    except DepthLimitError as error:
        caught_limit = True
        print(f"Merge Sort, ліміт 5: DepthLimitError: {error}")
    print(f"Лічильник після винятку: {tr.current} (максимум {tr.maximum})")
    tr2 = DepthTracker()
    guarded_error = False
    try:
        guarded_recursion(2000, tr2)
    except DepthLimitError as error:
        guarded_error = True
        print(f"guarded_recursion(2000): DepthLimitError: {error}")
    print(f"Досягнута глибина: {tr2.maximum}, після винятку: {tr2.current}")
    native_error = False
    try:
        naive_recursion(sys.getrecursionlimit() + 50)
    except RecursionError as error:
        native_error = True
        print(f"naive_recursion({sys.getrecursionlimit() + 50}): RecursionError: "
              f"{error}")

    print_header("[6] Автоматичні перевірки")
    checks = []
    ok_random = True
    for _ in range(300):
        data = [rng.randint(-50, 50) for _ in range(rng.randint(0, 60))]
        ok_random &= merge_sort(data) == sorted(data)
        ok_random &= merge_sort_iterative(data) == sorted(data)
    checks.append(("300 випадкових масивів: обидва алгоритми = sorted()",
                   ok_random))
    checks.append(("порожній масив і масив з одного елемента",
                   merge_sort([]) == [] and merge_sort([5]) == [5]
                   and merge_sort_iterative([]) == []))
    pairs = [(rng.randint(0, 3), idx) for idx in range(200)]
    stable = merge_sort(pairs, key=lambda p: p[0])
    checks.append(("сортування стійке: рівні ключі зберігають порядок",
                   stable == sorted(pairs, key=lambda p: p[0])))
    vals = [3, 1, 2]
    merge_sort(vals)
    checks.append(("вхідний список не змінюється", vals == [3, 1, 2]))
    checks.append(("вже впорядкований і зворотний масиви",
                   merge_sort(list(range(50))) == list(range(50))
                   and merge_sort(list(range(50, 0, -1))) == list(range(1, 51))))
    checks.append(("глибина = ceil(log2 n) + 1 для всіх n із таблиці",
                   all(r[1] == r[2] for r in depth_rows)))
    checks.append(("кількість викликів = 2n - 1 для всіх n із таблиці",
                   all(r[3] == 2 * r[0] - 1 for r in depth_rows)))
    checks.append(("порівнянь не більше за межу n*ceil(log2 n) - 2^ceil + 1",
                   all(r[4] <= r[5] for r in depth_rows)))
    checks.append(("лічильник глибини після кожного сортування дорівнює 0",
                   all(r[6] == 0 for r in depth_rows)))
    checks.append(("штучний ліміт 5 дає DepthLimitError і лічильник 0",
                   caught_limit and tr.current == 0))
    checks.append(("guarded_recursion зупиняється на межі 900 до RecursionError",
                   guarded_error and tr2.maximum == SAFE_DEPTH_LIMIT
                   and tr2.current == 0))
    checks.append(("без захисту виникає RecursionError", native_error))
    checks.append(("основна теорема: Theta(n^1 * log n)",
                   verdict == "Theta(n^1 * log n)"))
    spread = max(r[4] for r in timing_rows) / min(r[4] for r in timing_rows)
    checks.append(("t/(n log n) майже стале (розкид менше 2 разів)", spread < 2))
    checks.append(("sorted() швидший за Python-реалізацію на 100 000",
                   timing_rows[-1][3] < timing_rows[-1][1]))
    for text, ok in checks:
        print(f"[{'  OK' if ok else 'FAIL'}] {text}")
    print()
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    print(f"Час виконання рекурсивних алгоритмів: {elapsed_ms:.3f} мс")
    return all(ok for _, ok in checks)


if __name__ == "__main__":
    # Гарантуємо UTF-8 у консолі (важливо для Windows).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
