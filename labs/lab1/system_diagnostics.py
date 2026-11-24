#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Лабораторна робота № 1
Дисципліна: «Програмування на Python»
Спеціальність: F7 «Комп'ютерна інженерія»
Тема: Розгортання інфраструктури розробки: Miniconda, VS Code, Git/GitHub
      та базові режими виконання Python

Студент: Афанасьєв Сергій, група КІ 24-1
Варіант: 2 — «Інспекція версій середовища»

Діагностичний модуль виводить звіт про стан інтерпретатора CPython:

  1. Метадані платформи та інтерпретатора (еталонна частина).
  2. ІНДИВІДУАЛЬНЕ ЗАВДАННЯ (варіант 2): інспекція версії інтерпретатора
     за допомогою  sys.version_info,  platform.python_build()  та
     sys.hexversion  з аналізом мікроверсії (micro) CPython.
  3. Розміри скалярних об'єктів у пам'яті (sys.getsizeof).
  4. Перевірка кешу малих цілих чисел (Small Integer Cache, [-5, 256]).

Запуск:
    python system_diagnostics.py            # текстовий звіт
"""

import argparse
import json
import os
import platform
import re
import sys
import time

# ---------------------------------------------------------------------------
# Константи
# ---------------------------------------------------------------------------

#: Мінімальна версія інтерпретатора, яку вимагає environment.yml (python=3.10).
REQUIRED_VERSION = (3, 10)

#: Діапазон кешу малих цілих у CPython (включно): [-5, 256].
SMALL_INT_CACHE_RANGE = (-5, 256)

#: Розшифровка 4-бітного поля «рівень релізу» у sys.hexversion
#: (відповідає макросам PY_RELEASE_LEVEL_* у Include/patchlevel.h).
RELEASE_LEVELS = {
    0xA: "alpha",
    0xB: "beta",
    0xC: "candidate",
    0xF: "final",
}

#: Назви місяців для розбору дати збірки з platform.python_build().
_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


# ---------------------------------------------------------------------------
# 1. Метадані платформи та інтерпретатора
# ---------------------------------------------------------------------------

def collect_environment_metadata() -> dict:
    """Збирає загальні метадані операційної системи та інтерпретатора."""
    return {
        "os_name": platform.system(),                 # Linux / Windows / Darwin
        "os_release": platform.release(),             # версія ядра / ОС
        "architecture": platform.architecture()[0],   # розрядність: 32bit / 64bit
        "machine": platform.machine(),                # x86_64, AMD64, arm64 ...
        "processor": platform.processor() or "n/a",   # на деяких ОС порожній рядок
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "compiler": platform.python_compiler().strip(),
        "byte_order": sys.byteorder,                  # little / big
        "executable": sys.executable,                 # шлях до активного інтерпретатора
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV", "не активовано"),
        "recursion_limit": sys.getrecursionlimit(),
        "switch_interval_s": sys.getswitchinterval(), # інтервал перемикання потоків (GIL)
    }


# ---------------------------------------------------------------------------
# 2. ВАРІАНТ 2: Інспекція версій середовища
# ---------------------------------------------------------------------------

def decode_hexversion(hexversion: int) -> dict:
    """
    Розкладає sys.hexversion на складові.

    Формат — 32-бітне число 0xMMmmPPLS (макрос PY_VERSION_HEX):
        MM — major  (біти 31..24)
        mm — minor  (біти 23..16)
        PP — micro  (біти 15..8)
        L  — рівень релізу: 0xA alpha, 0xB beta, 0xC candidate, 0xF final (біти 7..4)
        S  — серійний номер (alpha/beta/candidate) (біти 3..0)

    Приклад: 0x030A14F0 -> 3.10.20 final, serial 0.
    """
    level_code = (hexversion >> 4) & 0xF
    return {
        "hexversion": hexversion,
        "hex": f"0x{hexversion:08x}",
        "major": (hexversion >> 24) & 0xFF,
        "minor": (hexversion >> 16) & 0xFF,
        "micro": (hexversion >> 8) & 0xFF,
        "level_code": level_code,
        "releaselevel": RELEASE_LEVELS.get(level_code, "unknown"),
        "serial": hexversion & 0xF,
    }


def parse_build_date(build_date: str):
    """
    Розбирає рядок дати збірки з platform.python_build()[1], напр.
    'Jul 18 2026 17:02:35' або 'Jun  4 2024 11:12:09'.
    Повертає кортеж (рік, місяць, день, 'HH:MM:SS') або None, якщо формат
    нестандартний (різні збірки CPython можуть форматувати дату по-різному).
    """
    match = re.match(r"^\s*([A-Za-z]{3})\s+(\d{1,2})\s+(\d{4})(?:\s+(\d{1,2}:\d{2}:\d{2}))?", build_date)
    if not match or match.group(1).capitalize() not in _MONTHS:
        return None
    month = _MONTHS[match.group(1).capitalize()]
    return int(match.group(3)), month, int(match.group(2)), match.group(4) or ""


def classify_micro(version_info) -> str:
    """Словесна оцінка мікроверсії (micro) за номером і рівнем релізу."""
    if version_info.releaselevel != "final":
        return (f"передрелізна збірка ({version_info.releaselevel}, "
                f"serial {version_info.serial}): micro ще не стабільний")
    if version_info.micro == 0:
        return "початковий стабільний реліз гілки (x.y.0), без виправлень"
    return (f"супроводжуваний реліз гілки "
            f"(випусків виправлень після x.y.0: {version_info.micro})")


def inspect_version() -> dict:
    """
    Індивідуальне завдання (варіант 2): інспекція версії CPython.

    Використовує:
      * sys.version_info      — іменований кортеж (major, minor, micro, releaselevel, serial);
      * platform.python_build() — кортеж (номер збірки, дата збірки);
      * sys.hexversion        — версія у вигляді одного 32-бітного числа.

    Додатково виконує перехресну перевірку трьох джерел між собою та
    аналізує мікроверсію (micro) інтерпретатора.
    """
    vi = sys.version_info
    decoded = decode_hexversion(sys.hexversion)
    build_no, build_date = platform.python_build()

    # Перехресні перевірки: всі джерела мають описувати ту саму версію.
    checks = {
        "hexversion співпадає з version_info":
            (decoded["major"], decoded["minor"], decoded["micro"],
             decoded["releaselevel"], decoded["serial"]) == tuple(vi),
        "platform.python_version() співпадає з version_info":
            platform.python_version_tuple()[:3] == tuple(str(x) for x in vi[:3]),
        "sys.version починається з major.minor.micro":
            sys.version.startswith(f"{vi.major}.{vi.minor}.{vi.micro}"),
        f"версія >= {'.'.join(map(str, REQUIRED_VERSION))} (вимога environment.yml)":
            vi >= REQUIRED_VERSION,
        "sys.hexversion >= PY_VERSION_HEX мінімальної версії":
            sys.hexversion >= (REQUIRED_VERSION[0] << 24 | REQUIRED_VERSION[1] << 16 | 0xF0),
    }
    if platform.python_implementation() == "CPython":
        checks["sys.implementation.version == sys.version_info"] = tuple(sys.implementation.version) == tuple(vi)

    return {
        "version_info": {
            "major": vi.major,
            "minor": vi.minor,
            "micro": vi.micro,
            "releaselevel": vi.releaselevel,
            "serial": vi.serial,
            "as_string": f"{vi.major}.{vi.minor}.{vi.micro}",
        },
        "python_build": {
            "build_number": build_no,
            "build_date": build_date,
            "build_date_parsed": parse_build_date(build_date),
        },
        "hexversion": decoded,
        "micro_analysis": {
            "micro": vi.micro,
            "classification": classify_micro(vi),
            "is_final_release": vi.releaselevel == "final",
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "full_version_string": sys.version.replace("\n", " "),
    }


# ---------------------------------------------------------------------------
# 3. Розміри об'єктів у пам'яті
# ---------------------------------------------------------------------------

def calculate_memory_footprint() -> dict:
    """
    Повертає розмір (у байтах) базових об'єктів за sys.getsizeof().

    Увага: розмір int(0) залежить від версії CPython. У CPython 3.10 нуль не
    має жодної «цифри» (ob_size = 0) і займає 24 байти, тоді як будь-яке
    ненульове мале число (1, 2, ... 2**30-1) займає 28 байтів. Починаючи з
    CPython 3.11 нуль теж займає 28 байтів. Тому в таблицю додано рядок int (1).
    """
    return {
        "int (0)": sys.getsizeof(0),
        "int (1)": sys.getsizeof(1),
        "int (2**64)": sys.getsizeof(2 ** 64),
        "float": sys.getsizeof(1.0),
        "complex": sys.getsizeof(1j),
        "bool": sys.getsizeof(True),
        "None": sys.getsizeof(None),
        "str (порожній)": sys.getsizeof(""),
        "str (20 ASCII)": sys.getsizeof("a" * 20),
        "list (порожній)": sys.getsizeof([]),
        "tuple (порожній)": sys.getsizeof(()),
        "dict (порожній)": sys.getsizeof({}),
        "set (порожня)": sys.getsizeof(set()),
    }


# ---------------------------------------------------------------------------
# 4. Кеш малих цілих чисел
# ---------------------------------------------------------------------------

def verify_integer_cache() -> list:
    """
    Перевіряє, чи CPython повторно використовує той самий об'єкт для малих цілих.

    Значення створюються під час виконання через int(str(v)): так ми уникаємо
    «згортання» однакових літералів у одну константу на етапі компіляції,
    яке дало б хибний результат «True» навіть для 257 та 1000.
    Обидва посилання утримуються у змінних, щоб id() не повторно
    використовувався після звільнення пам'яті.
    """
    results = []
    for value in (-5, 0, 100, 256, 257, 1000):
        first = int(str(value))
        second = int(str(value))
        results.append({
            "value": value,
            "id_first": id(first),
            "id_second": id(second),
            "same_object": first is second,
        })
    return results


# ---------------------------------------------------------------------------
# Форматований вивід
# ---------------------------------------------------------------------------

def _line(char: str = "=", width: int = 72) -> str:
    return char * width


def print_formatted_report(show_header: bool = True) -> None:
    """Друкує повний текстовий звіт діагностики."""
    meta = collect_environment_metadata()
    ver = inspect_version()
    memory = calculate_memory_footprint()
    cache = verify_integer_cache()

    if show_header:
        print(_line())
        print(" ЗВІТ ПРО ДІАГНОСТИКУ СЕРЕДОВИЩА PYTHON — ЛБ № 1, варіант 2")
        print(_line())

    # --- 1. Платформа ------------------------------------------------------
    print("\n[1] ПЛАТФОРМА ТА ІНТЕРПРЕТАТОР")
    print(_line("-"))
    print(f"  Система       : {meta['os_name']} {meta['os_release']} ({meta['architecture']})")
    print(f"  Архітектура   : {meta['machine']}, процесор: {meta['processor']}")
    print(f"  Порядок байтів: {meta['byte_order']}-endian")
    print(f"  Інтерпретатор : {meta['python_implementation']} {meta['python_version']}")
    print(f"  Компілятор    : {meta['compiler']}")
    print(f"  Шлях          : {meta['executable']}")
    print(f"  Conda-середов.: {meta['conda_env']}")
    print(f"  Ліміт рекурсії: {meta['recursion_limit']}")
    print(f"  Інтервал GIL  : {meta['switch_interval_s']} с")

    # --- 2. Варіант 2 -------------------------------------------------------
    vi = ver["version_info"]
    hx = ver["hexversion"]
    pb = ver["python_build"]
    print("\n[2] ІНСПЕКЦІЯ ВЕРСІЙ СЕРЕДОВИЩА (ВАРІАНТ 2)")
    print(_line("-"))
    print("  sys.version_info:")
    print(f"      major        = {vi['major']}")
    print(f"      minor        = {vi['minor']}")
    print(f"      micro        = {vi['micro']}   <-- мікроверсія")
    print(f"      releaselevel = {vi['releaselevel']}")
    print(f"      serial       = {vi['serial']}")
    print(f"      рядок версії = {vi['as_string']}")
    print("  platform.python_build():")
    print(f"      номер збірки = {pb['build_number']}")
    print(f"      дата збірки  = {pb['build_date']}")
    if pb["build_date_parsed"]:
        y, m, d, t = pb["build_date_parsed"]
        print(f"      розібрана    = {y:04d}-{m:02d}-{d:02d} {t}".rstrip())
    print("  sys.hexversion:")
    print(f"      значення     = {hx['hexversion']} ({hx['hex']})")
    print(f"      розшифровка  = major {hx['major']:#04x} | minor {hx['minor']:#04x} | "
          f"micro {hx['micro']:#04x} | level {hx['level_code']:#x} | serial {hx['serial']:#x}")
    print(f"      тобто        = {hx['major']}.{hx['minor']}.{hx['micro']} "
          f"{hx['releaselevel']} (serial {hx['serial']})")
    print("  Аналіз мікроверсії:")
    print(f"      micro = {vi['micro']} -> {ver['micro_analysis']['classification']}")
    print("  Перехресні перевірки:")
    for name, ok in ver["checks"].items():
        print(f"      [{'OK' if ok else 'FAIL'}] {name}")
    print(f"  Підсумок перевірок: {'ВСІ ПРОЙДЕНО' if ver['all_checks_passed'] else 'Є ПОМИЛКИ'}")

    # --- 3. Пам'ять ------------------------------------------------------------
    print("\n[3] РОЗМІРИ ОБ'ЄКТІВ У ПАМ'ЯТІ (sys.getsizeof)")
    print(_line("-"))
    obj_title = "Об'єкт"
    print(f"  {obj_title:<22}{'Байт':>8}")
    for name, size in memory.items():
        print(f"  {name:<22}{size:>8}")

    # --- 4. Кеш малих цілих -------------------------------------------------------
    low, high = SMALL_INT_CACHE_RANGE
    print(f"\n[4] КЕШ МАЛИХ ЦІЛИХ ЧИСЕЛ (діапазон [{low}, {high}])")
    print(_line("-"))
    same_title = "Той самий об'єкт"
    print(f"  {'Значення':>9}  {'id #1':>16}  {'id #2':>16}  {same_title:<16}")
    for row in cache:
        print(f"  {row['value']:>9}  {row['id_first']:>16}  {row['id_second']:>16}  "
              f"{str(row['same_object']):<16}")


def build_json_report() -> dict:
    """Збирає всі розділи у один словник (для --json та для ноутбука)."""
    return {
        "platform": collect_environment_metadata(),
        "version_inspection": inspect_version(),
        "memory_footprint": calculate_memory_footprint(),
        "integer_cache": verify_integer_cache(),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Діагностика середовища Python (ЛБ № 1, варіант 2).")
    parser.add_argument("--json", action="store_true", help="вивести звіт у форматі JSON")
    args = parser.parse_args(argv)

    # Гарантуємо коректне виведення кирилиці, навіть коли stdout перенаправлено
    # (на Windows у перенаправленому потоці може бути кодування cp1251/cp866).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    start = time.perf_counter()
    if args.json:
        print(json.dumps(build_json_report(), ensure_ascii=False, indent=2, default=str))
        return 0

    print_formatted_report()
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"\n{_line()}")
    print(f" Час виконання діагностики: {elapsed_ms:.4f} мс")
    print(_line())
    return 0 if inspect_version()["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
