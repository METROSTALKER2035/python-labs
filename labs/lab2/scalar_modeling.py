#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scalar_modeling.py - лабораторна робота №2, варіант 2 (завдання 1).

Математична модель варіанта 2:

    f(x, y) = ln(x^2 + 2) / (cos(y - x) + 1.5) + cbrt(x * e^y)

де cbrt - дійсний кубічний корінь (визначений і для від'ємних аргументів).
Результат обчислюється двома незалежними способами та перевіряється
функцією math.isclose. Додатково показано різницю math/cmath і будову float.
Програма не приймає аргументів і не вимагає введення з клавіатури.
"""

# math - дійсна математика: log, cos, exp, isclose та інші функції.
import math
# cmath - комплексна математика: головне значення кореня від'ємного числа.
import cmath
# struct - перетворення float у байти для розбору формату IEEE 754.
import struct
# sys - доступ до sys.float_info і налаштування кодування виводу.
import sys

# Роздільник завширшки 80 символів для заголовків розділів.
SEPARATOR = "=" * 80
# Тонкий роздільник для таблиць.
THIN_SEPARATOR = "-" * 80

# Відносний допуск порівняння (приблизно 9 вірних десяткових знаків).
REL_TOL = 1e-9
# Абсолютний допуск потрібен для порівняння значень, близьких до нуля.
ABS_TOL = 1e-12
# Найбільший аргумент експоненти, за якого math.exp ще не переповнюється.
MAX_EXP_ARG = 700.0


def real_cbrt(value: float) -> float:
    """Повертає дійсний кубічний корінь, у тому числі для від'ємних чисел."""
    # У Python 3.11+ є готова math.cbrt; у Python 3.10 її немає.
    if hasattr(math, "cbrt"):
        # Використовуємо вбудовану функцію, якщо вона доступна.
        return math.cbrt(value)
    # Для 3.10: корінь модуля, до якого повертаємо знак вихідного числа.
    return math.copysign(abs(value) ** (1.0 / 3.0), value)


def _check_arguments(x: float, y: float) -> None:
    """Перевіряє, що аргументи скінченні й не спричинять переповнення e^y."""
    # NaN та нескінченності не мають сенсу для моделі.
    if not (math.isfinite(x) and math.isfinite(y)):
        # Повідомляємо про некоректні вхідні дані.
        raise ValueError("x та y мають бути скінченними числами")
    # Для |y| > 700 функція exp(y) виходить за межі діапазону double.
    if abs(y) > MAX_EXP_ARG:
        # Захищаємося від OverflowError з math.exp.
        raise ValueError(f"|y| має бути не більше {MAX_EXP_ARG}")


def compute_model(x: float, y: float) -> float:
    """Обчислює f(x, y) безпосередньо за формулою варіанта 2."""
    # Перевіряємо область допустимих значень аргументів.
    _check_arguments(x, y)
    # Чисельник: натуральний логарифм від x^2 + 2 (аргумент завжди >= 2).
    numerator = math.log(x * x + 2.0)
    # Знаменник: cos(y - x) + 1.5 >= 0.5, тому ділення на нуль неможливе.
    denominator = math.cos(y - x) + 1.5
    # Підкореневий вираз другого доданка: x * e^y.
    radicand = x * math.exp(y)
    # Дріб плюс дійсний кубічний корінь.
    return numerator / denominator + real_cbrt(radicand)


def compute_model_reference(x: float, y: float) -> float:
    """Обчислює f(x, y) іншим шляхом для незалежної перевірки результату."""
    # Перевіряємо ті самі обмеження на аргументи.
    _check_arguments(x, y)
    # ln(x^2 + 2) = log1p(x^2 + 1): інша функція бібліотеки, той самий зміст.
    numerator = math.log1p(x * x + 1.0)
    # cos(y - x) розкладаємо за формулою різниці кутів.
    cos_diff = math.cos(y) * math.cos(x) + math.sin(y) * math.sin(x)
    # Знаменник дробу.
    denominator = cos_diff + 1.5
    # Корінь через логарифм: cbrt(x * e^y) = sign(x) * e^((ln|x| + y) / 3).
    if x == 0.0:
        # Логарифм нуля не визначений, а корінь з нуля дорівнює нулю.
        root = 0.0
    else:
        # Знак числа x * e^y збігається зі знаком x, бо e^y > 0.
        root = math.copysign(math.exp((math.log(abs(x)) + y) / 3.0), x)
    # Збираємо результат.
    return numerator / denominator + root


def decompose_float(value: float) -> tuple:
    """Розкладає float на знак, зсунутий порядок і мантису (IEEE 754)."""
    # Пакуємо double у 8 байтів (big-endian) і читаємо їх як ціле без знака.
    bits = struct.unpack(">Q", struct.pack(">d", value))[0]
    # Старший біт 63 - знак числа.
    sign = bits >> 63
    # Біти 62..52 (11 бітів) - зсунутий порядок (зсув 1023).
    exponent = (bits >> 52) & 0x7FF
    # Біти 51..0 (52 біти) - дробова частина мантиси.
    mantissa = bits & ((1 << 52) - 1)
    # Повертаємо три поля.
    return sign, exponent, mantissa


def print_section(title: str) -> None:
    """Друкує заголовок розділу з роздільниками."""
    # Порожній рядок перед розділом, потім заголовок і тонка лінія.
    print(f"\n{title}")
    print(THIN_SEPARATOR)


def main() -> None:
    """Точка входу: виконує завдання 1 варіанта 2 і друкує звіт."""
    # Верхній банер звіту.
    print(SEPARATOR)
    print("ЛР №2. ВАРІАНТ 2. МАТЕМАТИЧНА МОДЕЛЬ f(x, y)".center(80))
    print(SEPARATOR)

    # --- Розділ 1. Обчислення в основній точці ---
    # Основні значення параметрів моделі.
    x, y = 1.5, 0.8
    print_section("[1] ОБЧИСЛЕННЯ f(x, y) ТА ПЕРЕВІРКА math.isclose")
    # Параметри з одним знаком після коми.
    print(f"Параметри: x = {x:.1f}, y = {y:.1f}")
    # Проміжні величини для наочності.
    numerator = math.log(x * x + 2.0)
    denominator = math.cos(y - x) + 1.5
    root = real_cbrt(x * math.exp(y))
    print(f"ln(x^2 + 2)          = {numerator:14.10f}")
    print(f"cos(y - x) + 1.5     = {denominator:14.10f}")
    print(f"cbrt(x * e^y)        = {root:14.10f}")
    # Результат двома незалежними способами.
    direct = compute_model(x, y)
    control = compute_model_reference(x, y)
    print(f"f(x, y), формула     = {direct:14.10f}")
    print(f"f(x, y), контроль    = {control:14.10f}")
    # Абсолютна різниця двох способів.
    print(f"Різниця              = {abs(direct - control):.3e}")
    # Перевірка збігу з допусками REL_TOL та ABS_TOL.
    ok = math.isclose(direct, control, rel_tol=REL_TOL, abs_tol=ABS_TOL)
    print(f"math.isclose(...)    = {ok}")

    # --- Розділ 2. Таблиця контрольних точок ---
    print_section("[2] КОНТРОЛЬНІ ТОЧКИ (у тому числі x < 0 та x = 0)")
    print(f"{'x':>6} {'y':>6} | {'f (формула)':>14} | {'f (контроль)':>14} | "
          f"{'|різниця|':>9} | isclose")
    print(THIN_SEPARATOR)
    # Набір точок: від'ємний x перевіряє дійсний корінь, нулі - граничний випадок.
    points = [(1.5, 0.8), (0.0, 0.0), (-2.0, 0.3), (-1.2, -0.5), (3.0, 2.0)]
    all_ok = True
    for px, py in points:
        value_a = compute_model(px, py)
        value_b = compute_model_reference(px, py)
        same = math.isclose(value_a, value_b, rel_tol=REL_TOL, abs_tol=ABS_TOL)
        # Накопичуємо загальний результат перевірки.
        all_ok = all_ok and same
        # Абсолютна різниця двох способів для кожної точки.
        delta = abs(value_a - value_b)
        print(f"{px:6.2f} {py:6.2f} | {value_a:14.10f} | {value_b:14.10f} | "
              f"{delta:9.2e} | {same}")
    print(f"Усі точки збігаються: {all_ok}")

    # --- Розділ 3. math проти cmath ---
    print_section("[3] math ПРОТИ cmath (корінь з від'ємного числа)")
    # math.sqrt від'ємного числа не визначена в дійсних числах.
    try:
        math.sqrt(-4.0)
    except ValueError as error:
        print(f"math.sqrt(-4)        -> ValueError: {error}")
    # cmath.sqrt повертає комплексне значення.
    print(f"cmath.sqrt(-4)       = {cmath.sqrt(-4.0)}")
    # Дійсний корінь і головне комплексне значення кубічного кореня з -8.
    principal = complex(-8.0) ** (1.0 / 3.0)
    print(f"real_cbrt(-8)        = {real_cbrt(-8.0):.1f}")
    print(f"(-8+0j)**(1/3)       = {principal.real:.7f}{principal.imag:+.7f}j")
    # Модуль і аргумент головного значення (аргумент = pi/3).
    modulus, phase = cmath.polar(principal)
    print(f"|z| = {modulus:.7f}, arg z = {phase:.7f} рад (pi/3 = {math.pi / 3:.7f})")

    # --- Розділ 4. Точність float та будова IEEE 754 ---
    print_section("[4] ТОЧНІСТЬ float ТА БУДОВА IEEE 754")
    # Класичний приклад: сума 0.1 + 0.2 не дорівнює 0.3 точно.
    total = 0.1 + 0.2
    print(f"0.1 + 0.2 == 0.3          : {total == 0.3}")
    print(f"math.isclose(0.1+0.2,0.3) : {math.isclose(total, 0.3)}")
    # Машинний епсилон: відстань від 1.0 до наступного double.
    print(f"sys.float_info.epsilon    : {sys.float_info.epsilon:.3e}")
    # Точне десяткове значення, що фактично зберігається для 0.1.
    print(f"0.1 у пам'яті (25 знаків) : {0.1:.25f}")
    print(f"{'Число':<22} {'знак':>4} {'порядок':>8} {'мантиса (hex)':>15}")
    # Розбір 0.1 та результату моделі на поля IEEE 754.
    for label, number in (("0.1", 0.1), ("f(1.5, 0.8)", direct)):
        sgn, exp_bits, mant = decompose_float(number)
        print(f"{label:<22} {sgn:>4} {exp_bits:>8} {mant:>15x}")
    print(SEPARATOR)


if __name__ == "__main__":
    # Забезпечуємо коректний вивід кирилиці у консолях не з UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # Запускаємо звіт.
    main()
