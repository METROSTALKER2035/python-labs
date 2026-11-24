#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
branching_logic.py - лабораторна робота №3, варіант 2 (розгалуження).

Кусочно-неперервна функція варіанта 2:

            | cos(x^2) + 1,    x < -1         (гілка 1)
    f(x) =  | x^3 + 2x,        -1 <= x <= 1   (гілка 2)
            | cbrt(x - 1),     x > 1          (гілка 3)

Модуль показує три речі:
  1) вибір гілки через if-elif-else та через тернарний вираз;
  2) розриви функції на межах гілок;
  3) коротку схему обчислення (short-circuit) операторів and / or.
Програма не приймає аргументів і не вимагає введення з клавіатури.
"""

# math - cos, isfinite, copysign та інші функції.
import math
# sys - налаштування кодування виводу.
import sys
# time - вимірювання часу виконання програми.
import time

# Роздільники завширшки 80 символів.
SEPARATOR = "=" * 80
THIN_SEPARATOR = "-" * 80

# Межі гілок: x < LEFT -> гілка 1; LEFT <= x <= RIGHT -> гілка 2;
# x > RIGHT -> гілка 3.
LEFT = -1.0
RIGHT = 1.0

# Підписи гілок для таблиць (індекс = номер гілки - 1).
BRANCH_FORMULAS = ("cos(x^2) + 1", "x^3 + 2x", "cbrt(x - 1)")


def real_cbrt(value: float) -> float:
    """Дійсний кубічний корінь, у тому числі для від'ємних чисел.

    У Python 3.10 немає math.cbrt (вона з'явилась у 3.11), а вираз
    (-8.0) ** (1 / 3) повертає комплексне число. Тому беремо корінь
    із модуля й повертаємо знак аргумента. Так результат однаковий
    у всіх версіях Python.
    """
    return math.copysign(abs(value) ** (1.0 / 3.0), value)


def branch_one(x: float) -> float:
    """Гілка 1 (x < -1): cos(x^2) + 1."""
    return math.cos(x * x) + 1.0


def branch_two(x: float) -> float:
    """Гілка 2 (-1 <= x <= 1): x^3 + 2x."""
    return x * x * x + 2.0 * x


def branch_three(x: float) -> float:
    """Гілка 3 (x > 1): cbrt(x - 1)."""
    return real_cbrt(x - 1.0)


def _check_argument(x: float) -> None:
    """Відхиляє NaN і нескінченності."""
    # Для NaN усі порівняння хибні, тож без перевірки він потрапив би в else.
    if not math.isfinite(x):
        raise ValueError("x має бути скінченним числом")


def segment_number(x: float) -> int:
    """Повертає номер гілки (1, 2 або 3) за допомогою if-elif-else."""
    _check_argument(x)
    if x < LEFT:
        segment = 1
    elif x <= RIGHT:
        segment = 2
    else:
        segment = 3
    return segment


def evaluate_if_elif(x: float) -> float:
    """Значення f(x) через інструкцію if-elif-else."""
    _check_argument(x)
    if x < LEFT:
        y = branch_one(x)
    elif x <= RIGHT:
        y = branch_two(x)
    else:
        y = branch_three(x)
    return y


def evaluate_ternary(x: float) -> float:
    """Значення f(x) через вкладений тернарний вираз.

    Тернарний вираз обчислює лише вибрану гілку: інші функції не викликаються.
    """
    _check_argument(x)
    return (branch_one(x) if x < LEFT
            else branch_two(x) if x <= RIGHT
            else branch_three(x))


def ratio_exceeds(numerator: float, denominator: float, limit: float) -> bool:
    """True, якщо numerator / denominator > limit.

    Оператор and ледачий: за denominator == 0 перший операнд хибний, тому
    ділення не виконується і ZeroDivisionError не виникає.
    """
    return denominator != 0 and numerator / denominator > limit


def ratio_exceeds_eager(numerator: float, denominator: float, limit: float) -> bool:
    """Те саме, але з побітовим &: він обчислює ОБИДВА операнди."""
    return bool((denominator != 0) & (numerator / denominator > limit))


def short_circuit_counter() -> dict:
    """Рахує виклики допоміжної функції під and / or (ілюстрація лінивості)."""
    calls = {"count": 0}

    def costly() -> bool:
        # Лічильник показує, скільки разів операнд справді обчислювався.
        calls["count"] += 1
        return True

    result = {}
    result["False and costly()"] = (False and costly(), calls["count"])
    calls["count"] = 0
    result["True or costly()"] = (True or costly(), calls["count"])
    calls["count"] = 0
    result["True and costly()"] = (True and costly(), calls["count"])
    calls["count"] = 0
    result["False or costly()"] = (False or costly(), calls["count"])
    return result


def jump_at(boundary: float, left_func, right_func) -> tuple:
    """Значення двох гілок у точці стику та стрибок (права мінус ліва)."""
    left_value = left_func(boundary)
    right_value = right_func(boundary)
    return left_value, right_value, right_value - left_value


def print_header(title: str) -> None:
    """Друкує заголовок розділу."""
    print(SEPARATOR)
    print(title)
    print(SEPARATOR)


def main() -> None:
    """Демонстрація розгалужень для варіанта 2."""
    print("#" * 80)
    print("# ЛР №3, варіант 2: розгалуження (if-elif-else, тернарний вираз)")
    print("#" * 80)

    # --- [1] гілки в характерних точках
    print("\n[1] Значення f(x) у характерних точках (if-elif-else, тернарний вираз)")
    print(THIN_SEPARATOR)
    print(f"{'x':>6}  {'Гілка':^5}  {'Формула':<13}  {'if-elif-else':>14}  "
          f"{'тернарний':>14}  Збіг")
    print(THIN_SEPARATOR)
    points = (-3.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0)
    all_equal = True
    for x in points:
        seg = segment_number(x)
        y_if = evaluate_if_elif(x)
        y_ter = evaluate_ternary(x)
        same = y_if == y_ter
        all_equal = all_equal and same
        print(f"{x:6.2f}  {seg:^5d}  {BRANCH_FORMULAS[seg - 1]:<13}  {y_if:14.8f}  "
              f"{y_ter:14.8f}  {'так' if same else 'НІ'}")

    # --- [2] розриви на межах
    print("\n[2] Розриви функції на межах гілок (стрибок = права - ліва)")
    print(THIN_SEPARATOR)
    print(f"{'Межа x':>7}  {'ліва гілка':>12}  {'права гілка':>12}  {'стрибок':>12}")
    print(THIN_SEPARATOR)
    for boundary, left_f, right_f in ((LEFT, branch_one, branch_two),
                                      (RIGHT, branch_two, branch_three)):
        lv, rv, jump = jump_at(boundary, left_f, right_f)
        print(f"{boundary:7.1f}  {lv:12.8f}  {rv:12.8f}  {jump:12.8f}")
    print("Функція кусочно-неперервна: на кожній межі розрив першого роду.")

    # --- [3] short-circuit
    print("\n[3] Коротка схема обчислення (short-circuit)")
    print(THIN_SEPARATOR)
    print(f"ratio_exceeds(10, 2, 3)        -> {ratio_exceeds(10, 2, 3)}")
    print(f"ratio_exceeds(10, 0, 3)        -> {ratio_exceeds(10, 0, 3)}"
          "   (ділення не виконано)")
    try:
        ratio_exceeds_eager(10, 0, 3)
    except ZeroDivisionError as err:
        print(f"ratio_exceeds_eager(10, 0, 3)  -> ZeroDivisionError: {err}")
    for expr, (value, calls) in short_circuit_counter().items():
        print(f"{expr:<20} -> {str(value):<5} викликів costly(): {calls}")

    # --- [4] покриття гілок на сітці
    print("\n[4] Покриття гілок на сітці [-3, 3] з кроком 0.25")
    print(THIN_SEPARATOR)
    counts = [0, 0, 0]
    for i in range(25):
        counts[segment_number(-3.0 + 0.25 * i) - 1] += 1
    for number, (formula, count) in enumerate(zip(BRANCH_FORMULAS, counts), 1):
        print(f"Гілка {number}: {formula:<13} вузлів: {count}")
    print(f"Усього вузлів: {sum(counts)}")

    # --- [5] перевірки
    print("\n[5] Автоматичні перевірки")
    print(THIN_SEPARATOR)
    checks = [
        ("if-elif-else і тернарний вираз дають однакові значення", all_equal),
        ("гілки покривають усі 25 вузлів сітки", sum(counts) == 25),
        ("f(-1) береться з гілки 2 (нестрога межа): -3", branch_two(-1.0) == -3.0
         and evaluate_if_elif(-1.0) == -3.0),
        ("f(1) береться з гілки 2: 3", evaluate_if_elif(1.0) == 3.0),
        ("f(2) = cbrt(1) = 1", evaluate_if_elif(2.0) == 1.0),
        ("real_cbrt(-8) = -2", math.isclose(real_cbrt(-8.0), -2.0, rel_tol=1e-12)),
    ]
    try:
        segment_number(float("nan"))
        nan_rejected = False
    except ValueError:
        nan_rejected = True
    checks.append(("NaN відхиляється через ValueError", nan_rejected))
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
