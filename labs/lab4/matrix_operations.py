#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
matrix_operations.py - лабораторна робота №4, варіант 2 (двовимірні списки).

Завдання варіанта 2 для матриці:
  1) згенерувати цілу матрицю A розміром M x K = 3 x 5;
  2) помножити її на вектор-стовпець X з R^5: Y = A * X (вектор із трьох елементів);
  3) знайти мінімум кожного рядка матриці A;
  4) додатково: транспонування, добуток матриць із перевіркою розмірів і пошук
     сідлових точок (мінімум у рядку та водночас максимум у стовпці).

Розміри й межі елементів беруться з кортежу CONFIG = (N, M, K, X_MIN, X_MAX),
який розпаковується паралельним присвоюванням. Матриця - це список списків.
Програма не приймає аргументів і не вимагає введення даних.
"""

# random - генерація псевдовипадкових чисел (з фіксованим seed для відтворюваності).
import random
# sys - налаштування кодування виводу та sys.getsizeof.
import sys
# time - вимірювання часу виконання.
import time

# Конфігурацію (незмінний кортеж) беремо з модуля векторів.
from vector_algorithms import CONFIG

# Роздільники завширшки 80 символів.
SEPARATOR = "=" * 80
THIN_SEPARATOR = "-" * 80

# Вектор X з R^5: дробові числа з точним двійковим поданням (кортеж незмінний).
X_VECTOR: tuple = (1.5, -0.5, 2.0, 0.25, 1.0)
# Початкове значення генератора для відтворюваного результату.
MATRIX_SEED = 2


def _shape(matrix: list) -> tuple:
    """Повертає (рядків, стовпців); відхиляє порожні та нерівні матриці."""
    if not matrix or not matrix[0]:
        raise ValueError("матриця не може бути порожньою")
    cols = len(matrix[0])
    if any(len(row) != cols for row in matrix):
        raise ValueError("усі рядки матриці мають мати однакову довжину")
    return len(matrix), cols


def generate_matrix(rows: int, cols: int, min_val: int, max_val: int) -> list:
    """Генерує матрицю rows x cols із цілих чисел на [min_val, max_val]."""
    if rows <= 0 or cols <= 0:
        raise ValueError("розміри матриці мають бути додатними")
    if min_val > max_val:
        raise ValueError("потрібно min_val <= max_val")
    # Вкладені comprehension створюють НОВИЙ список для кожного рядка.
    return [[random.randint(min_val, max_val) for _ in range(cols)]
            for _ in range(rows)]


def transpose_matrix(matrix: list) -> list:
    """Транспонування: (A^T)[j][i] = A[i][j]; з m x n виходить n x m, O(M*N)."""
    rows, cols = _shape(matrix)
    return [[matrix[i][j] for i in range(rows)] for j in range(cols)]


def multiply_matrices(a: list, b: list) -> list:
    """Добуток C = A * B: C[i][j] = sum_k A[i][k] * B[k][j], складність O(m*n*p)."""
    rows_a, cols_a = _shape(a)
    rows_b, cols_b = _shape(b)
    # Добуток визначений, лише якщо кількість стовпців A дорівнює рядків B.
    if cols_a != rows_b:
        raise ValueError(f"розміри не збігаються: {rows_a}x{cols_a} і "
                         f"{rows_b}x{cols_b}")
    return [[sum(a[i][t] * b[t][j] for t in range(cols_a)) for j in range(cols_b)]
            for i in range(rows_a)]


def matrix_vector_product(a: list, x: tuple) -> list:
    """Добуток Y = A * X: елемент Y[i] - скалярний добуток i-го рядка на X."""
    _, cols = _shape(a)
    if cols != len(x):
        raise ValueError(f"довжина X ({len(x)}) не дорівнює числу стовпців ({cols})")
    return [sum(value * weight for value, weight in zip(row, x)) for row in a]


def find_row_minima(matrix: list) -> list:
    """Мінімум кожного рядка: список кортежів (рядок, стовпець, значення)."""
    _shape(matrix)
    minima = []
    for i, row in enumerate(matrix):
        smallest = min(row)
        # index() повертає перше входження мінімуму в рядку.
        minima.append((i, row.index(smallest), smallest))
    return minima


def find_saddle_points(matrix: list) -> list:
    """Сідлові точки: елемент - мінімум свого рядка й максимум свого стовпця."""
    _shape(matrix)
    row_min = [min(row) for row in matrix]
    # zip(*matrix) віддає стовпці матриці.
    col_max = [max(col) for col in zip(*matrix)]
    return [(i, j, value)
            for i, row in enumerate(matrix)
            for j, value in enumerate(row)
            if value == row_min[i] and value == col_max[j]]


def print_matrix_formatted(matrix: list, title: str, width: int = 6) -> None:
    """Друкує матрицю із заголовком '--- title (RxC) ---'."""
    rows, cols = _shape(matrix)
    print(f"--- {title} ({rows}x{cols}) ---")
    for row in matrix:
        print("".join(f"{value:{width}}" for value in row))


def print_header(title: str) -> None:
    """Друкує заголовок розділу."""
    print(f"\n{title}")
    print(THIN_SEPARATOR)


def main() -> None:
    """Матричні операції для варіанта 2."""
    print("#" * 80)
    print("# ЛР №4, варіант 2: матриця 3x5, Y = A*X, мінімуми рядків")
    print("#" * 80)

    # --- [1] розпакування CONFIG і генерація
    n, m, k, x_min, x_max = CONFIG          # паралельне розпакування кортежу
    random.seed(MATRIX_SEED)
    matrix = generate_matrix(m, k, x_min, x_max)
    print_header("[1] Матриця A та вектор X")
    print(f"CONFIG = {CONFIG}: M = {m}, K = {k}, елементи на [{x_min}, {x_max}]")
    print(f"seed = {MATRIX_SEED}")
    print_matrix_formatted(matrix, "A")
    print(f"X = {X_VECTOR}")

    # --- [2] добуток Y = A * X і мінімуми рядків
    y_vector = matrix_vector_product(matrix, X_VECTOR)
    x_column = [[value] for value in X_VECTOR]
    y_via_matrix = multiply_matrices(matrix, x_column)
    print_header("[2] Y = A * X (вектор із M елементів)")
    for i, (row, y_value) in enumerate(zip(matrix, y_vector)):
        terms = " + ".join(f"{a}*({x:g})" if x < 0 else f"{a}*{x:g}"
                           for a, x in zip(row, X_VECTOR))
        print(f"Y[{i}] = {terms} = {y_value:g}")
    print(f"Y = {y_vector}")
    print(f"Y (через multiply_matrices, стовпець 5x1) = "
          f"{[row[0] for row in y_via_matrix]}")
    minima = find_row_minima(matrix)
    print("\nМінімум кожного рядка матриці A:")
    for i, j, value in minima:
        print(f"  рядок {i}: min = {value} (стовпець {j})")
    print(f"Вектор мінімумів: {[value for _, _, value in minima]}")

    # --- [3] транспонування та добуток матриць
    transposed = transpose_matrix(matrix)
    print_header("[3] Транспонування та добуток матриць")
    print_matrix_formatted(transposed, "A^T")
    gram = multiply_matrices(matrix, transposed)
    print_matrix_formatted(gram, "A * A^T", width=8)
    try:
        multiply_matrices(matrix, matrix)
    except ValueError as err:
        print(f"multiply_matrices(A, A) -> ValueError: {err}")

    # --- [4] сідлові точки
    print_header("[4] Сідлові точки (мінімум у рядку й максимум у стовпці)")
    test_matrix = [[3, 8, 3], [2, 6, 1], [7, 9, 5]]
    examples = (("A", matrix), ("M", test_matrix), ("E1", [[1, 2], [2, 1]]),
                ("E2", [[4, 4], [4, 4]]))
    for name, mtx in examples:
        rows, cols = _shape(mtx)
        found = find_saddle_points(mtx)
        shown = ", ".join(f"({i},{j})={v}" for i, j, v in found) or "немає"
        print(f"{name:>2} {rows}x{cols}: {mtx if name != 'A' else '(матриця A)'}")
        print(f"     сідлових точок: {len(found)}; {shown}")

    # --- [5] особливості списків і кортежів
    print_header("[5] Списки та кортежі: спільні посилання, зрізи, незмінність")
    shared = [[0] * 4] * 3
    shared[0][0] = 9
    proper = [[0] * 4 for _ in range(3)]
    proper[0][0] = 9
    print(f"[[0]*4]*3 після A[0][0] = 9:     {shared}")
    print(f"  усі рядки - один об'єкт: {shared[0] is shared[1] is shared[2]}")
    print(f"comprehension після A[0][0] = 9: {proper}")
    print(f"  рядки - різні об'єкти:   {proper[0] is not proper[1]}")
    original = [10, 20, 30, 40, 50, 60]
    piece = original[1:5]
    piece[0] = 99
    print(f"L = {original}; sub = L[1:5]; sub[0] = 99")
    print(f"  sub = {piece}, L не змінився: {original == [10, 20, 30, 40, 50, 60]}, "
          f"sub is L: {piece is original}")
    shallow = matrix[:]
    print(f"A[:] копіює лише список рядків: shallow[0] is A[0] -> "
          f"{shallow[0] is matrix[0]}")
    try:
        CONFIG[0] = 1
    except TypeError as err:
        print(f"CONFIG[0] = 1 -> TypeError: {err}")
    as_list = list(CONFIG)
    size_tuple = sys.getsizeof(CONFIG)
    size_list = sys.getsizeof(as_list)
    for _ in range(3):
        as_list.append(0)
    print(f"sys.getsizeof для 5 елементів: кортеж {size_tuple} байт, "
          f"список {size_list} байт")
    print(f"список після 3 append (8 елементів): {sys.getsizeof(as_list)} байт "
          "(запас під зростання)")

    # --- [6] перевірки
    print_header("[6] Автоматичні перевірки")
    expected_y = [sum(v * w for v, w in zip(row, X_VECTOR)) for row in matrix]
    bad_dims = bad_gen = bad_vec = False
    try:
        multiply_matrices([[1, 2]], [[1, 2]])
    except ValueError:
        bad_dims = True
    try:
        generate_matrix(0, 3, 0, 1)
    except ValueError:
        bad_gen = True
    try:
        matrix_vector_product(matrix, (1.0, 2.0))
    except ValueError:
        bad_vec = True
    checks = [
        ("розмір A дорівнює M x K = 3 x 5", (len(matrix), len(matrix[0])) == (m, k)),
        ("елементи A лежать у [X_MIN, X_MAX]",
         all(x_min <= v <= x_max for row in matrix for v in row)),
        ("Y збігається з незалежним обчисленням", y_vector == expected_y),
        ("Y збігається з добутком матриць A * X(5x1)",
         y_vector == [row[0] for row in y_via_matrix]),
        ("мінімум кожного рядка збігається з min(row)",
         [v for _, _, v in minima] == [min(row) for row in matrix]),
        ("(A^T)^T == A", transpose_matrix(transposed) == matrix),
        ("A * A^T симетрична", gram == transpose_matrix(gram)),
        ("сідлова точка тестової матриці M: (2,2) = 5",
         find_saddle_points(test_matrix) == [(2, 2, 5)]),
        ("у матриці з однаковими елементами всі 4 точки сідлові",
         len(find_saddle_points([[4, 4], [4, 4]])) == 4),
        ("спільні посилання в [[0]*4]*3: усі рядки змінились",
         shared == [[9, 0, 0, 0]] * 3),
        ("comprehension: змінився лише рядок 0", proper[1] == [0, 0, 0, 0]),
        ("несумісні розміри відхиляються через ValueError", bad_dims),
        ("нульові розміри відхиляються через ValueError", bad_gen),
        ("довжина X, що не збігається з K, відхиляється", bad_vec),
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
