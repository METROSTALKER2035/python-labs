#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
series_tabulation.py - лабораторна робота №3, варіант 2 (цикли).

Завдання варіанта 2:
  1) табулювання кусочної функції f(x) з модуля branching_logic на відрізку
     [-3, 3] з кроком h = 0.25 через цикл for і range();
  2) сума ряду Тейлора функції sin(x) з точністю eps = 10^-7 через цикл while:

         sin x = sum_{k>=0} (-1)^k x^(2k+1) / (2k+1)!

     Рекурентне співвідношення (виведено у звіті):

         a_k = a_{k-1} * R(k, x),   R(k, x) = -x^2 / (2k (2k + 1)),   a_0 = x;

  3) порівняння суми з еталоном math.sin(x).
Програма не приймає аргументів і не вимагає введення з клавіатури.
"""

# math - floor, isclose, isfinite, sin, factorial.
import math
# sys - налаштування кодування виводу.
import sys
# time - вимірювання часу виконання.
import time
# NamedTuple - зручний незмінний результат підсумовування ряду.
from typing import NamedTuple

# Функція варіанта та визначення гілки беремо з модуля розгалужень.
from branching_logic import BRANCH_FORMULAS, evaluate_if_elif, segment_number

# Роздільники завширшки 80 символів.
SEPARATOR = "=" * 80
THIN_SEPARATOR = "-" * 80

# Параметри варіанта 2.
START_A = -3.0
END_B = 3.0
STEP_H = 0.25
EPSILON = 1e-7
# Запобіжник від нескінченного циклу (для |x| <= 3 вистачає 9 доданків).
MAX_ITERATIONS = 200


class SeriesResult(NamedTuple):
    """Результат підсумовування ряду."""

    total: float        # часткова сума S
    terms: int          # кількість доданих доданків
    reference: float    # еталонне значення math.sin(x)
    abs_error: float    # |S - еталон|
    converged: bool     # чи досягнуто умови |a_k| < eps


def tabulate_function(start_a: float, end_b: float, step_h: float) -> list:
    """Табулює f(x) на [a, b] з кроком h; повертає список (x, y, гілка)."""
    # Перевірка вхідних даних: крок додатний, відрізок не порожній.
    if not all(math.isfinite(v) for v in (start_a, end_b, step_h)):
        raise ValueError("a, b і h мають бути скінченними числами")
    if step_h <= 0:
        raise ValueError("крок h має бути додатним")
    if start_a > end_b:
        raise ValueError("потрібно a <= b")

    # N = floor((b - a) / h): кількість повних кроків, вузлів на один більше.
    n_steps = math.floor((end_b - start_a) / step_h)
    # Якщо через похибку float частка трохи менша за ціле, floor "губить" крок.
    span = end_b - start_a
    if math.isclose((n_steps + 1) * step_h, span, rel_tol=0.0, abs_tol=1e-9):
        n_steps += 1

    rows = []
    # range() працює лише з цілими числами, тому перебираємо цілий індекс i,
    # а дійсну координату вузла обчислюємо як x_i = a + i * h.
    for i in range(n_steps + 1):
        x = start_a + i * step_h
        # Корекція кінцевої точки: x_N має збігатися з b.
        if math.isclose(x, end_b, rel_tol=0.0, abs_tol=1e-9):
            x = end_b
        rows.append((x, evaluate_if_elif(x), segment_number(x)))
    return rows


def compute_sin_series(x: float, epsilon: float = EPSILON,
                       max_iterations: int = MAX_ITERATIONS) -> SeriesResult:
    """Сума ряду sin(x) рекурентним методом (цикл while)."""
    if not math.isfinite(x):
        raise ValueError("x має бути скінченним числом")
    if not epsilon > 0:
        raise ValueError("eps має бути додатним")
    if max_iterations < 1:
        raise ValueError("max_iterations має бути не менше 1")

    x_squared = x * x      # x^2 обчислюється один раз
    term = x               # a_0 = x
    total = 0.0            # часткова сума
    k = 0                  # номер поточного доданка a_k
    converged = False

    # Інваріант на початку кожної перевірки: total = a_0 + ... + a_{k-1},
    # а змінна term містить a_k, який ще не додано.
    while abs(term) >= epsilon and k < max_iterations:
        if not math.isfinite(term):
            # break пропускає блок else: ряд розбігається (переповнення float).
            print(f"  ! x = {x}: доданок вийшов за межі float, ряд розбігається")
            break
        total += term                                # додаємо a_k
        k += 1
        term = term * (-x_squared) / (2 * k * (2 * k + 1))   # a_k = a_{k-1} * R(k, x)
    else:
        # else виконується, лише якщо цикл завершився без break.
        converged = abs(term) < epsilon
        if not converged:
            print(f"  ! x = {x}: досягнуто max_iterations = {max_iterations}, "
                  "точність eps не гарантується")

    reference = math.sin(x)
    return SeriesResult(total, k, reference, abs(total - reference), converged)


def compute_sin_naive(x: float, epsilon: float = EPSILON,
                      max_iterations: int = MAX_ITERATIONS) -> SeriesResult:
    """Той самий ряд, але БЕЗ рекурентності: степінь і факторіал щоразу заново."""
    term = x
    total = 0.0
    k = 0
    while abs(term) >= epsilon and k < max_iterations:
        total += term
        k += 1
        n = 2 * k + 1
        # float / int: факторіал від n >= 171 не вміщується в float -> OverflowError.
        term = (-1) ** k * x ** n / math.factorial(n)
    reference = math.sin(x)
    error = abs(total - reference)
    return SeriesResult(total, k, reference, error, abs(term) < epsilon)


def print_tabulation_table(rows: list) -> None:
    """Друкує таблицю табулювання."""
    print(THIN_SEPARATOR)
    print(f"{'№':>3}  {'Вузол x':>9}  {'y = f(x)':>14}  {'Гілка':^5}  Формула")
    print(THIN_SEPARATOR)
    for i, (x, y, seg) in enumerate(rows):
        print(f"{i:3d}  {x:9.4f}  {y:14.8f}  {seg:^5d}  {BRANCH_FORMULAS[seg - 1]}")
    print(THIN_SEPARATOR)


def print_series_table(points: tuple, epsilon: float) -> list:
    """Друкує таблицю точності ряду й повертає список результатів."""
    print(THIN_SEPARATOR)
    print(f"{'x':>6}  {'S(x)':>14}  {'math.sin(x)':>14}  {'Доданків':>8}  "
          f"{'|S - sin|':>10}  <eps")
    print(THIN_SEPARATOR)
    results = []
    for x in points:
        res = compute_sin_series(x, epsilon)
        results.append(res)
        verdict = "так" if res.abs_error < epsilon else "НІ"
        print(f"{x:6.2f}  {res.total:14.10f}  {res.reference:14.10f}  "
              f"{res.terms:8d}  {res.abs_error:10.4e}  {verdict}")
    return results


def average_time_us(func, x: float, epsilon: float, repeats: int = 2000) -> float:
    """Середній час одного виклику func(x, epsilon) у мікросекундах."""
    started = time.perf_counter()
    for _ in range(repeats):
        func(x, epsilon)
    return (time.perf_counter() - started) / repeats * 1e6


def main() -> None:
    """Табулювання, ряд sin(x) та порівняння з прямим обчисленням."""
    print("#" * 80)
    print("# ЛР №3, варіант 2: табулювання та ряд Тейлора sin(x), eps = 1e-7")
    print("#" * 80)

    # --- [1] табулювання
    rows = tabulate_function(START_A, END_B, STEP_H)
    print(f"\n[1] Табулювання f(x) на [{START_A:g}, {END_B:g}], крок h = {STEP_H:g}: "
          f"N = {len(rows) - 1}, вузлів {len(rows)}")
    print_tabulation_table(rows)

    # --- [2] ряд у контрольних точках
    print(f"\n[2] Ряд sin(x), eps = {EPSILON:g}: порівняння з math.sin")
    points = (-3.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0)
    series = print_series_table(points, EPSILON)

    # --- [3] залежність від eps
    print("\n[3] Залежність кількості доданків і похибки від eps (x = 2.0)")
    print(THIN_SEPARATOR)
    print(f"{'eps':>8}  {'Доданків':>8}  {'S(x)':>16}  {'|S - sin|':>10}")
    print(THIN_SEPARATOR)
    for exponent in (1, 3, 5, 7, 9, 12):
        eps = 10.0 ** (-exponent)
        res = compute_sin_series(2.0, eps)
        print(f"{eps:8.0e}  {res.terms:8d}  {res.total:16.12f}  "
              f"{res.abs_error:10.2e}")

    # --- [4] перевірка по всій сітці
    print("\n[4] Перевірка ряду в усіх вузлах сітки табулювання")
    print(THIN_SEPARATOR)
    grid = [compute_sin_series(x, EPSILON) for x, _, _ in rows]
    worst = max(grid, key=lambda r: r.abs_error)
    worst_x = rows[grid.index(worst)][0]
    print(f"Вузлів перевірено: {len(grid)}")
    print(f"Найбільша похибка: {worst.abs_error:.4e} у вузлі x = {worst_x:g}")
    print(f"Найбільше доданків: {max(r.terms for r in grid)}")

    # --- [5] рекурентність проти прямого обчислення
    print("\n[5] Рекурентна формула проти прямого обчислення степенів і факторіалів")
    print(THIN_SEPARATOR)
    t_rec = average_time_us(compute_sin_series, 3.0, EPSILON)
    t_naive = average_time_us(compute_sin_naive, 3.0, EPSILON)
    print(f"x = 3.0, eps = 1e-07: рекурентно {t_rec:7.2f} мкс, "
          f"напряму {t_naive:7.2f} мкс, відношення {t_naive / t_rec:.2f}")
    rec_tiny = compute_sin_series(3.0, 1e-300)
    print(f"x = 3.0, eps = 1e-300, рекурентно: доданків {rec_tiny.terms}, "
          f"похибка {rec_tiny.abs_error:.2e}")
    try:
        compute_sin_naive(3.0, 1e-300)
        print("x = 3.0, eps = 1e-300, напряму: без помилки")
    except OverflowError as err:
        print(f"x = 3.0, eps = 1e-300, напряму: OverflowError: {err}")

    # --- [6] перевірки
    print("\n[6] Автоматичні перевірки")
    print(THIN_SEPARATOR)
    try:
        tabulate_function(0.0, 1.0, 0.0)
        bad_step = False
    except ValueError:
        bad_step = True
    try:
        compute_sin_series(1.0, 0.0)
        bad_eps = False
    except ValueError:
        bad_eps = True
    checks = [
        ("N = 24 і 25 вузлів", len(rows) == 25),
        ("перший вузол x = -3, останній x = 3",
         rows[0][0] == -3.0 and rows[-1][0] == 3.0),
        ("для кожного вузла |S - math.sin| < eps",
         all(r.abs_error < EPSILON for r in grid)),
        ("ряд у всіх вузлах збігся (converged)", all(r.converged for r in grid)),
        ("для x = 0 ряд дає 0 за 0 доданків", series[4].total == 0.0
         and series[4].terms == 0),
        ("ряд непарний: S(-x) = -S(x) для x = 2", compute_sin_series(-2.0).total
         == -compute_sin_series(2.0).total),
        ("h = 0 відхиляється через ValueError", bad_step),
        ("eps = 0 відхиляється через ValueError", bad_eps),
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
