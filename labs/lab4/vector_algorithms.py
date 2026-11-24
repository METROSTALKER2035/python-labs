#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
vector_algorithms.py - лабораторна робота №4, варіант 2 (одновимірні списки).

Завдання варіанта 2 для вектора:
  1) згенерувати вектор V із N = 20 цілих чисел на відрізку [0, 100];
  2) залишити лише числа, кратні 5 (list comprehension);
  3) відсортувати результат методом бульбашки (Bubble Sort) без .sort().

Параметри генерації передаються незмінним кортежем CONFIG = (N, M, K, X_MIN, X_MAX)
і розпаковуються паралельним присвоюванням. Модуль matrix_operations.py імпортує
цей самий кортеж. Програма не приймає аргументів і не вимагає введення даних.
"""

# random - генерація псевдовипадкових чисел (з фіксованим seed для відтворюваності).
import random
# sys - налаштування кодування виводу.
import sys
# time - вимірювання часу виконання.
import time
# NamedTuple - зручний незмінний результат сортування зі статистикою.
from typing import NamedTuple

# Роздільники завширшки 80 символів.
SEPARATOR = "=" * 80
THIN_SEPARATOR = "-" * 80

# Конфігурація варіанта 2: (N, M, K, X_MIN, X_MAX).
# N - довжина вектора, M x K - розмір матриці, [X_MIN, X_MAX] - межі елементів.
# Кортеж незмінний, тому його безпечно передавати між модулями.
CONFIG: tuple = (20, 3, 5, 0, 100)
# Дільник для фільтрації за умовою варіанта (кратні 5).
DIVISOR = 5
# Початкове значення генератора для відтворюваного результату.
VECTOR_SEED = 11


class SortStats(NamedTuple):
    """Результат сортування разом зі статистикою роботи алгоритму."""

    result: list        # відсортований список (нова копія)
    comparisons: int    # кількість порівнянь сусідніх елементів
    swaps: int          # кількість обмінів
    passes: int         # кількість виконаних проходів


def generate_random_vector(length: int, min_val: int, max_val: int) -> list:
    """Генерує список із length випадкових цілих чисел на [min_val, max_val]."""
    if length <= 0:
        raise ValueError("довжина вектора має бути додатною")
    if min_val > max_val:
        raise ValueError("потрібно min_val <= max_val")
    # list comprehension швидший за цикл з append: використовує LIST_APPEND.
    return [random.randint(min_val, max_val) for _ in range(length)]


def filter_multiples(vector: list, divisor: int = DIVISOR) -> list:
    """Повертає елементи, кратні divisor, зберігаючи їх порядок (число 0 кратне)."""
    if divisor == 0:
        raise ValueError("дільник не може дорівнювати нулю")
    return [value for value in vector if value % divisor == 0]


def bubble_sort_manual(input_list: list, passes: list = None) -> SortStats:
    """Сортування методом бульбашки за зростанням, O(N^2), стійке.

    Працює з копією, тому вхідний список не змінюється. Якщо передано
    список passes, до нього додається знімок після кожного проходу.
    """
    data = list(input_list)       # поверхнева копія
    size = len(data)
    comparisons = swaps = passes_done = 0
    # Після кожного проходу найбільший елемент "спливає" на кінець діапазону,
    # тому правий кордон end щоразу зменшується на 1.
    for end in range(size - 1, 0, -1):
        swapped = False
        for j in range(end):
            comparisons += 1
            if data[j] > data[j + 1]:
                # Обмін через паралельне присвоювання кортежів без temp.
                data[j], data[j + 1] = data[j + 1], data[j]
                swaps += 1
                swapped = True
        passes_done += 1
        if passes is not None:
            passes.append(data[:])
        # Обмінів не було: список уже впорядкований, продовжувати немає сенсу.
        if not swapped:
            break
    return SortStats(data, comparisons, swaps, passes_done)


def average_time_ms(func, data: list, repeats: int) -> float:
    """Середній час одного виклику func(data) у мілісекундах."""
    started = time.perf_counter()
    for _ in range(repeats):
        func(data)
    return (time.perf_counter() - started) / repeats * 1000.0


def print_header(title: str) -> None:
    """Друкує заголовок розділу."""
    print(f"\n{title}")
    print(THIN_SEPARATOR)


def main() -> None:
    """Обробка вектора для варіанта 2."""
    print("#" * 80)
    print("# ЛР №4, варіант 2: вектор, фільтр кратних 5, Bubble Sort")
    print("#" * 80)

    # --- [1] конфігурація: паралельне розпакування кортежу
    n, m, k, x_min, x_max = CONFIG
    random.seed(VECTOR_SEED)
    print_header("[1] Конфігурація CONFIG = (N, M, K, X_MIN, X_MAX)")
    print(f"CONFIG = {CONFIG}")
    print(f"N = {n}, M = {m}, K = {k}, X_MIN = {x_min}, X_MAX = {x_max}")
    print(f"seed = {VECTOR_SEED}, фільтр: кратні {DIVISOR}")

    # --- [2] генерація
    vector = generate_random_vector(n, x_min, x_max)
    print_header(f"[2] Початковий вектор V (довжина {len(vector)})")
    print(f"V = {vector}")

    # --- [3] фільтрація
    filtered = filter_multiples(vector)
    print_header(f"[3] Фільтрація: елементи, кратні {DIVISOR} (list comprehension)")
    print(f"Залишено {len(filtered)} з {len(vector)} елементів")
    print(f"Відфільтрований вектор: {filtered}")

    # --- [4] Bubble Sort
    print_header("[4] Bubble Sort (без .sort()): стан після кожного проходу")
    snapshots = []
    before_sort = list(filtered)      # контрольна копія для перевірки
    stats = bubble_sort_manual(filtered, snapshots)
    print(f"{'Старт':>8}: {filtered}")
    for number, snap in enumerate(snapshots, 1):
        print(f"{'Прохід ' + str(number):>8}: {snap}")
    print(f"Результат: {stats.result}")
    print(f"Порівнянь: {stats.comparisons}, обмінів: {stats.swaps}, "
          f"проходів: {stats.passes}")

    # --- [5] порівняння з Timsort
    print_header("[5] Bubble Sort проти sorted() (Timsort) на випадкових векторах")
    print(f"{'N':>6}  {'Порівнянь':>10}  {'Bubble, мс':>11}  {'sorted, мс':>11}  "
          f"{'Відношення':>10}")
    rng = random.Random(2026)
    timing_ok = True
    for size in (100, 200, 400, 800):
        big = [rng.randint(x_min, x_max) for _ in range(size)]
        t_bubble = average_time_ms(bubble_sort_manual, big, 5)
        t_timsort = average_time_ms(sorted, big, 200)
        same = bubble_sort_manual(big).result == sorted(big)
        timing_ok = timing_ok and same
        comps = bubble_sort_manual(big).comparisons
        print(f"{size:6d}  {comps:10d}  {t_bubble:11.3f}  {t_timsort:11.4f}  "
              f"{t_bubble / t_timsort:10.1f}")

    # --- [6] індексація та вставка
    print_header("[6] PyListObject: індексація O(1) проти insert(0, x) O(N)")
    big_list = list(range(100_000))
    started = time.perf_counter()
    for _ in range(200_000):
        big_list[50_000]
    t_index = (time.perf_counter() - started) / 200_000 * 1e9
    started = time.perf_counter()
    for _ in range(200):
        big_list.insert(0, 0)
    t_insert = (time.perf_counter() - started) / 200 * 1e6
    print(f"L[50000]:     {t_index:9.1f} нс на операцію")
    print(f"L.insert(0):  {t_insert:9.1f} мкс на операцію (N = 100000)")

    # --- [7] перевірки
    print_header("[7] Автоматичні перевірки")
    vec_ok = all(v % DIVISOR == 0 for v in filtered)
    bad_length = bad_range = bad_divisor = False
    try:
        generate_random_vector(0, 0, 1)
    except ValueError:
        bad_length = True
    try:
        generate_random_vector(5, 10, 1)
    except ValueError:
        bad_range = True
    try:
        filter_multiples([1, 2], 0)
    except ValueError:
        bad_divisor = True
    checks = [
        ("усі елементи вектора лежать у [X_MIN, X_MAX]",
         all(x_min <= v <= x_max for v in vector)),
        ("у відфільтрованому векторі всі числа кратні 5", vec_ok),
        ("результат Bubble Sort збігається з sorted()",
         stats.result == sorted(filtered)),
        ("вхідний список не змінено після сортування", filtered == before_sort),
        ("Bubble Sort збігається з sorted() на великих векторах", timing_ok),
        ("порожній список сортується без помилок",
         bubble_sort_manual([]).result == []),
        ("length = 0 відхиляється через ValueError", bad_length),
        ("min_val > max_val відхиляється через ValueError", bad_range),
        ("divisor = 0 відхиляється через ValueError", bad_divisor),
    ]
    for text, ok in checks:
        print(f"[{'  OK' if ok else 'FAIL'}] {text}")


if __name__ == "__main__":
    # Гарантуємо UTF-8 у консолі (важливо для Windows).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    started = time.perf_counter()
    main()
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    print(f"\nЗагальний час виконання розрахунків: {elapsed_ms:.3f} мс")
