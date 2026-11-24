#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
log_parser.py - лабораторна робота №5, варіант 2 (Linux Syslog).

Формат запису журналу:

    Month Day HH:MM:SS Hostname Daemon_Name[PID]: SEVERITY: Message

де SEVERITY - INFO або ERR. Завдання варіанта 2: виділити процеси, що записали
помилки ERR, і згрупувати записи за Daemon_Name. Конвеєр обробки:

    очистка рядка -> регулярний вираз з іменованими групами -> валідація
    -> групування -> табличний звіт з вирівнюванням через f-рядки.

Програма читає файл input_logs.txt (UTF-8), не приймає аргументів і не вимагає
введення з клавіатури.
"""

# re - скомпільовані регулярні вирази.
import re
# sys - налаштування кодування виводу.
import sys
# time - вимірювання часу виконання.
import time
# Path - шлях до вхідного файлу.
from pathlib import Path

# Очистка рядків і скорочення тексту для таблиць.
from text_sanitizer import is_skippable, sanitize_log_line, truncate_text

# Ширина звіту та роздільники.
REPORT_WIDTH = 98
SEPARATOR = "=" * REPORT_WIDTH
THIN_SEPARATOR = "-" * REPORT_WIDTH

# Регулярний вираз компілюється один раз (поза циклом читання файлу).
# Прапорець VERBOSE дозволяє коментувати кожну частину шаблону.
LOG_PATTERN = re.compile(
    r"""
    ^(?P<month>[A-Z][a-z]{2})\s+            # місяць: три літери (Nov)
    (?P<day>\d{1,2})\s+                      # день місяця: одна-дві цифри
    (?P<time>\d{2}:\d{2}:\d{2})\s+           # час HH:MM:SS
    (?P<hostname>[A-Za-z0-9][A-Za-z0-9.-]*)\s+   # ім'я вузла
    (?P<daemon>[A-Za-z0-9_][A-Za-z0-9_.-]*)  # ім'я процесу (Daemon_Name)
    \[(?P<pid>\d{1,7})\]:\s+                 # PID у квадратних дужках і двокрапка
    (?P<severity>INFO|ERR):\s+               # рівень важливості
    (?P<message>.+)$                         # повідомлення до кінця рядка
    """,
    re.VERBOSE,
)

# Допоміжні шаблони: кандидат у IPv4-адресу та коректне ім'я вузла.
# Перед адресою не може стояти цифра або "цифра.", після неї - цифра або ".цифра",
# тому фрагмент довшої послідовності (1.2.3.4.5) адресою не вважається.
IPV4_CANDIDATE = re.compile(r"(?<!\d)(?<!\d\.)(?:\d{1,3}\.){3}\d{1,3}(?!\d|\.\d)")
HOSTNAME_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?")

# Кількість днів у місяці (рік у syslog відсутній, тому лютий має 29 днів).
DAYS_IN_MONTH = {"Jan": 31, "Feb": 29, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30,
                 "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31}
# Найбільший PID у Linux за замовчуванням (kernel.pid_max на 64-бітних системах).
PID_MAX = 4_194_304


def find_validation_errors(record: dict) -> list:
    """Повертає список причин невалідності запису (порожній список - усе гаразд)."""
    errors = []
    month, day = record["month"], record["day"]
    if month not in DAYS_IN_MONTH:
        errors.append(f"місяць '{month}' не існує")
    elif not 1 <= day <= DAYS_IN_MONTH[month]:
        errors.append(f"день {day} неможливий для місяця {month}")
    hours, minutes, seconds = (int(part) for part in record["time"].split(":"))
    if hours > 23 or minutes > 59 or seconds > 59:
        errors.append(f"час {record['time']} поза діапазоном")
    if not 1 <= record["pid"] <= PID_MAX:
        errors.append(f"PID {record['pid']} поза діапазоном 1..{PID_MAX}")
    if not HOSTNAME_PATTERN.fullmatch(record["hostname"]):
        errors.append(f"ім'я вузла '{record['hostname']}' некоректне")
    return errors


def validate_extracted_data(record: dict) -> bool:
    """True, якщо всі поля запису лежать у допустимих діапазонах."""
    return not find_validation_errors(record)


def extract_ipv4(message: str) -> tuple:
    """Знаходить IPv4-адреси в тексті; повертає (коректні, з октетом поза 0..255)."""
    valid, invalid = [], []
    # finditer віддає об'єкти збігів по одному й не будує проміжний список рядків.
    for match in IPV4_CANDIDATE.finditer(message):
        address = match.group(0)
        octets = [int(part) for part in address.split(".")]
        in_range = all(0 <= octet <= 255 for octet in octets)
        (valid if in_range else invalid).append(address)
    return valid, invalid


def parse_telemetry_file(file_path: Path, stats: dict = None) -> list:
    """Читає журнал і повертає список коректних записів (словників).

    Якщо передано словник stats, у нього записуються лічильники рядків.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Файл журналу не знайдено: {file_path}")
    counters = {"lines": 0, "skipped": 0, "malformed": 0, "invalid": 0, "valid": 0}
    records = []
    with file_path.open(encoding="utf-8") as handle:
        for line_num, raw_line in enumerate(handle, start=1):
            counters["lines"] += 1
            line = sanitize_log_line(raw_line)
            if is_skippable(line):
                counters["skipped"] += 1
                continue
            match = LOG_PATTERN.search(line)
            if match is None:
                counters["malformed"] += 1
                print(f"Помилка парсингу: Рядок {line_num} не відповідає формату: "
                      f"'{truncate_text(line, 60)}'")
                continue
            record = match.groupdict()
            # Числові поля перетворюємо на int до перевірки діапазонів.
            record["day"] = int(record["day"])
            record["pid"] = int(record["pid"])
            record["line_num"] = line_num
            errors = find_validation_errors(record)
            if errors:
                counters["invalid"] += 1
                print(f"Попередження: Рядок {line_num} містить невалідні параметри: "
                      f"{'; '.join(errors)}.")
                continue
            counters["valid"] += 1
            records.append(record)
    if stats is not None:
        stats.update(counters)
    return records


def group_by_daemon(records: list) -> dict:
    """Групує записи за Daemon_Name: {ім'я: список записів у порядку появи}."""
    groups = {}
    for record in records:
        groups.setdefault(record["daemon"], []).append(record)
    return groups


def timestamp_of(record: dict) -> str:
    """Часова мітка запису у вигляді 'Nov 23 01:15:02'."""
    return f"{record['month']} {record['day']:>2} {record['time']}"


def generate_ascii_report(records: list) -> None:
    """Друкує таблицю всіх коректних записів журналу."""
    print(SEPARATOR)
    print(f"{'ЗВІТ ЖУРНАЛУ LINUX SYSLOG':^{REPORT_WIDTH}}")
    print(SEPARATOR)
    print(f"{'№':>3}  {'Час':<15}  {'Вузол':<10}  {'Процес[PID]':<20}  "
          f"{'Рівень':<6}  Повідомлення")
    print(THIN_SEPARATOR)
    for record in records:
        process = f"{record['daemon']}[{record['pid']}]"
        print(f"{record['line_num']:>3}  {timestamp_of(record):<15}  "
              f"{record['hostname']:<10}  {process:<20}  {record['severity']:<6}  "
              f"{truncate_text(record['message'], 34)}")
    print(THIN_SEPARATOR)


def print_error_groups(groups: dict) -> None:
    """Друкує процеси з ERR, згруповані за Daemon_Name (спочатку найбільше ERR)."""
    print(SEPARATOR)
    print(f"{'ПРОЦЕСИ З ПОМИЛКАМИ ERR (групування за Daemon_Name)':^{REPORT_WIDTH}}")
    print(SEPARATOR)
    print(f"{'Процес':<16}{'ERR':>5}{'INFO':>6}{'% ERR':>8}  {'PID з ERR':<24}"
          f"Перша й остання ERR")
    print(THIN_SEPARATOR)
    ranked = []
    for daemon, items in groups.items():
        errors = [item for item in items if item["severity"] == "ERR"]
        if errors:
            ranked.append((daemon, items, errors))
    # Спочатку процеси з найбільшою кількістю помилок, за рівності - за назвою.
    ranked.sort(key=lambda row: (-len(row[2]), row[0]))
    for daemon, items, errors in ranked:
        pids = ", ".join(str(pid) for pid in sorted({e["pid"] for e in errors}))
        share = 100.0 * len(errors) / len(items)
        span = f"{timestamp_of(errors[0])} .. {timestamp_of(errors[-1])}"
        print(f"{daemon:<16}{len(errors):>5}{len(items) - len(errors):>6}"
              f"{share:>7.1f}%  {pids:<24}{span}")
    print(THIN_SEPARATOR)
    for daemon, _, errors in ranked:
        print(f"{daemon} - помилок: {len(errors)}")
        for error in errors:
            line = f"  {timestamp_of(error)}  [{error['pid']}]  {error['message']}"
            print(truncate_text(line, REPORT_WIDTH))


def print_statistics(records: list, groups: dict, stats: dict) -> tuple:
    """Друкує підсумкову статистику й повертає (унікальні IP, некоректні IP)."""
    errors = [r for r in records if r["severity"] == "ERR"]
    counts = {}
    bad_addresses = []
    for record in errors:
        good, bad = extract_ipv4(record["message"])
        for address in good:
            counts[address] = counts.get(address, 0) + 1
        bad_addresses.extend(bad)
    daemons_with_err = {r["daemon"] for r in errors}
    worst = max(daemons_with_err, default="-",
                key=lambda d: sum(r["severity"] == "ERR" for r in groups[d]))
    worst_count = sum(r["severity"] == "ERR" for r in groups[worst]) if errors else 0
    print(SEPARATOR)
    print(f"{'ПІДСУМКОВА СТАТИСТИКА ЖУРНАЛУ':^{REPORT_WIDTH}}")
    print(SEPARATOR)
    print(f"Прочитано рядків:                  {stats['lines']:>4}")
    print(f"  пропущено (порожні, коментарі):  {stats['skipped']:>4}")
    print(f"  не відповідають формату:         {stats['malformed']:>4}")
    print(f"  містять невалідні параметри:     {stats['invalid']:>4}")
    print(f"Коректних записів:                 {stats['valid']:>4}")
    print(f"  INFO: {len(records) - len(errors):>3}   ERR: {len(errors):>3}   "
          f"частка ERR: {100.0 * len(errors) / max(len(records), 1):.1f}%")
    print(f"Процесів, що записали ERR:         {len(daemons_with_err):>4}")
    print(f"Найбільше ERR у процесі:           {worst} ({worst_count})")
    print(f"IPv4 у повідомленнях ERR: коректних унікальних {len(counts)}, "
          f"некоректних {len(bad_addresses)}")
    for address, number in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {address:<16} згадок: {number}")
    for address in bad_addresses:
        print(f"  {address:<16} некоректна адреса (октет поза 0..255)")
    print(THIN_SEPARATOR)
    return counts, bad_addresses


def backtracking_demo() -> list:
    """Порівнює безпечний шаблон із '(a+)+$' на рядку 'aa...ab' (backtracking)."""
    dangerous = re.compile(r"(a+)+$")
    safe = re.compile(r"a+$")
    rows = []
    for length in (16, 18, 20, 22):
        text = "a" * length + "b"
        started = time.perf_counter()
        dangerous.search(text)
        slow = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        safe.search(text)
        fast = (time.perf_counter() - started) * 1000.0
        rows.append((length, slow, fast))
    return rows


def main() -> None:
    """Повний цикл: читання, розбір, групування, звіт і статистика."""
    print("#" * REPORT_WIDTH)
    print("# ЛР №5, варіант 2: аналіз журналу Linux Syslog (процеси з ERR)")
    print("#" * REPORT_WIDTH)
    log_path = Path(__file__).with_name("input_logs.txt")
    stats = {}
    print(f"\n[1] Читання файлу {log_path.name} (повідомлення про пошкоджені рядки)")
    print(THIN_SEPARATOR)
    records = parse_telemetry_file(log_path, stats)
    print(f"\n[2] Таблиця коректних записів ({len(records)})")
    generate_ascii_report(records)
    groups = group_by_daemon(records)
    print("\n[3] Групування за Daemon_Name")
    print_error_groups(groups)
    print("\n[4] Підсумкова статистика")
    counts, bad_addresses = print_statistics(records, groups, stats)

    print("\n[5] Катастрофічне повернення: '(a+)+$' проти 'a+$' на рядку 'aa...ab'")
    print(THIN_SEPARATOR)
    print(f"{'Довжина':>8}  {'(a+)+$, мс':>12}  {'a+$, мс':>10}")
    rows = backtracking_demo()
    for length, slow, fast in rows:
        print(f"{length:8d}  {slow:12.3f}  {fast:10.4f}")

    print("\n[6] Автоматичні перевірки")
    print(THIN_SEPARATOR)
    err_daemons = sorted({r["daemon"] for r in records if r["severity"] == "ERR"})
    try:
        parse_telemetry_file(Path("no_such_file.txt"))
        missing_ok = False
    except FileNotFoundError:
        missing_ok = True
    ok_record = {"month": "Feb", "day": 29, "time": "23:59:59", "pid": 1,
                 "hostname": "srv-01"}
    checks = [
        ("усього прочитано 29 рядків", stats["lines"] == 29),
        ("лічильники рядків узгоджені",
         stats["skipped"] + stats["malformed"] + stats["invalid"] + stats["valid"]
         == stats["lines"]),
        ("2 рядки не відповідають формату (без PID, рівень WARN)",
         stats["malformed"] == 2),
        ("3 рядки з невалідними параметрами (день, година, PID)",
         stats["invalid"] == 3),
        ("ERR записали рівно 5 процесів",
         err_daemons == ["kubelet", "mysqld", "nginx", "smartd", "sshd"]),
        ("кожен запис у групі має ім'я цієї групи",
         all(r["daemon"] == name for name, items in groups.items() for r in items)),
        ("усі групи разом містять усі записи",
         sum(len(items) for items in groups.values()) == len(records)),
        ("запис із табуляціями розібрано після очистки",
         any(r["daemon"] == "mysqld" and r["time"] == "01:37:45" for r in records)),
        ("кирилиця в повідомленні збережена",
         any("Помилка отримання образу" in r["message"] for r in records)),
        ("IP 999.10.10.10 визнано некоректним", bad_addresses == ["999.10.10.10"]),
        ("203.0.113.9 згадано 3 рази", counts.get("203.0.113.9") == 3),
        ("29 лютого вважається допустимою датою", validate_extracted_data(ok_record)),
        ("відсутній файл дає FileNotFoundError", missing_ok),
        ("повернення назад: час (a+)+$ зростає, a+$ майже не змінюється",
         rows[-1][1] > 4 * rows[0][1] and rows[-1][2] < 5.0),
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
