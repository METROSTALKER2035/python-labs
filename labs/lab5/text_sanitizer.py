#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
text_sanitizer.py - лабораторна робота №5, варіант 2 (очистка тексту).

Модуль містить базові функції очистки й нормалізації рядків журналу, які
використовує log_parser.py, та три демонстрації для теоретичної частини:
  1) очистка "брудних" рядків (BOM, нульові символи, табуляції, зайві пробіли);
  2) внутрішнє подання str за PEP 393 (1, 2 або 4 байти на символ);
  3) конкатенація += проти str.join().
Програма не приймає аргументів і не вимагає введення з клавіатури.
"""

# re - регулярний вираз для невидимих і керівних символів.
import re
# sys - sys.getsizeof та налаштування кодування виводу.
import sys
# time - вимірювання часу виконання.
import time

# Роздільники завширшки 80 символів.
SEPARATOR = "=" * 80
THIN_SEPARATOR = "-" * 80

# Символи для видалення: керівні C0 (крім \t \n \v \f \r та \x1c-\x1f, які обробляє
# split), DEL, керівні C1, нульова ширина, роздільники рядків і BOM.
INVISIBLE_CHARS = re.compile(
    r"[\x00-\x08\x0e-\x1b\x7f-\x9f\u200b-\u200f\u2028\u2029\ufeff]"
)


def strip_invisible_chars(text: str) -> str:
    """Видаляє невидимі та керівні символи (BOM, NUL, нульову ширину тощо)."""
    return INVISIBLE_CHARS.sub("", text)


def collapse_whitespace(text: str) -> str:
    """Замінює будь-які послідовності пробільних символів одним пробілом.

    split() без аргументів ріже рядок за пробільними символами (табуляція,
    перенос, кілька пробілів) і відкидає порожні частини, join() склеює назад.
    Обидві операції лінійні, а початкові й кінцеві пробіли зникають самі.
    """
    return " ".join(text.split())


def sanitize_log_line(raw_line: str) -> str:
    """Повертає очищений рядок: без невидимих символів і зайвих пробілів."""
    return collapse_whitespace(strip_invisible_chars(raw_line))


def is_skippable(line: str) -> bool:
    """True для порожнього рядка та рядка-коментаря, що починається з '#'."""
    return not line or line.startswith("#")


def truncate_text(text: str, width: int) -> str:
    """Скорочує текст до width символів, додаючи '...' наприкінці."""
    if width < 4:
        raise ValueError("ширина має бути не менша за 4")
    return text if len(text) <= width else text[: width - 3] + "..."


def concat_plus(pieces: list) -> str:
    """Склеювання оператором += (CPython часто виконує його "на місці")."""
    result = ""
    for piece in pieces:
        result += piece
    return result


def concat_plus_aliased(pieces: list) -> str:
    """Те саме, але з другим посиланням на рядок: оптимізація "на місці" вимкнена."""
    result = ""
    for piece in pieces:
        keep = result          # друге посилання змушує += створювати нову копію
        result += piece
    return result


def concat_join(pieces: list) -> str:
    """Склеювання через str.join(): один буфер, лінійний час."""
    return "".join(pieces)


def bytes_per_char(sample: str) -> float:
    """Середній розмір символу в байтах за різницею розмірів двох рядків."""
    short, long_ = sample * 10, sample * 110
    return (sys.getsizeof(long_) - sys.getsizeof(short)) / (len(long_) - len(short))


def time_ms(func, pieces: list) -> float:
    """Час одного виклику func(pieces) у мілісекундах."""
    started = time.perf_counter()
    func(pieces)
    return (time.perf_counter() - started) * 1000.0


def print_header(title: str) -> None:
    """Друкує заголовок розділу."""
    print(f"\n{title}")
    print(THIN_SEPARATOR)


def main() -> None:
    """Демонстрація очистки тексту та моделі рядків CPython."""
    print("#" * 80)
    print("# ЛР №5, варіант 2: очистка тексту (text_sanitizer)")
    print("#" * 80)

    # --- [1] очистка
    print_header("[1] Очистка рядків журналу")
    samples = [
        "  Nov  2 23:58:10   srv-web01 cron[877]: INFO: ok   ",
        "Nov 23\t01:37:45\tsrv-db01 mysqld[1530]:\tERR:  Lost connection",
        "\ufeffNov 23 00:03:12 srv-web01 sshd[2411]: ERR: Failed\x00 password",
        "Nov 23 00:04:01\u200b srv-web01 cron[877]: INFO: zero-width\r\n",
        "   \t  ",
    ]
    cleaned = []
    for raw in samples:
        clean = sanitize_log_line(raw)
        cleaned.append(clean)
        print(f"було:   {raw!r}")
        print(f"стало:  {clean!r}")
    print(f"is_skippable('') = {is_skippable('')}, "
          f"is_skippable('# коментар') = {is_skippable('# коментар')}")

    # --- [2] PEP 393
    print_header("[2] Подання str у CPython (PEP 393)")
    print(f"{'Рядок із символів':<28} {'Макс. код':>9} {'Байтів на символ':>17}")
    kinds = (("ASCII 'a'", "a"), ("Latin-1 'é'", "é"), ("кирилиця 'я'", "я"),
             ("емодзі U+1F600", "\U0001F600"))
    sizes = {}
    for label, char in kinds:
        sizes[label] = bytes_per_char(char)
        print(f"{label:<28} {'U+%04X' % ord(char):>9} {sizes[label]:>17.1f}")
    ascii_100 = sys.getsizeof("a" * 100)
    mixed_100 = sys.getsizeof("a" * 99 + "я")
    print(f"getsizeof('a'*100) = {ascii_100}, getsizeof('a'*99 + 'я') = {mixed_100}")

    # --- [3] += проти join
    print_header("[3] Склеювання рядків: += проти str.join()")
    print(f"{'Шматків':>8}  {'+=, мс':>9}  {'+= з копіями, мс':>17}  {'join, мс':>9}")
    last = None
    for count in (5000, 10000, 20000):
        pieces = ["0123456789"] * count
        t_plus = time_ms(concat_plus, pieces)
        t_alias = time_ms(concat_plus_aliased, pieces)
        t_join = time_ms(concat_join, pieces)
        print(f"{count:8d}  {t_plus:9.3f}  {t_alias:17.3f}  {t_join:9.4f}")
        last = pieces

    # --- [4] перевірки
    print_header("[4] Автоматичні перевірки")
    checks = [
        ("зайві пробіли й табуляції згортаються",
         cleaned[0] == "Nov 2 23:58:10 srv-web01 cron[877]: INFO: ok"
         and "\t" not in cleaned[1] and "  " not in cleaned[1]),
        ("BOM і NUL видаляються",
         cleaned[2] == "Nov 23 00:03:12 srv-web01 sshd[2411]: ERR: Failed password"),
        ("нульова ширина та CRLF видаляються",
         cleaned[3] == "Nov 23 00:04:01 srv-web01 cron[877]: INFO: zero-width"),
        ("рядок із самих пробілів стає порожнім", cleaned[4] == ""),
        ("ASCII - 1 байт, Latin-1 - 1, кирилиця - 2, емодзі - 4",
         [sizes[k] for k in sizes] == [1.0, 1.0, 2.0, 4.0]),
        ("один символ 'я' переводить рядок у 2-байтовий формат",
         mixed_100 - ascii_100 > 100),
        ("+=, += з копіями та join дають однаковий рядок",
         concat_plus(last) == concat_plus_aliased(last) == concat_join(last)),
        ("truncate_text скорочує довгий рядок до 10 символів",
         truncate_text("0123456789ABCDEF", 10) == "0123456..."),
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
    print(f"\nЧас виконання повного циклу аналізу тексту: {elapsed_ms:.3f} мс")
