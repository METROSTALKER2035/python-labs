"""
Модуль форматування та консольного виведення результатів пошуку порожніх каталогів.
Освітній компонент: Програмування на Python.
"""
# Типи для анотацій параметрів функцій модуля.
from typing import List, Dict

# Ширина звіту в символах: збігається з довжиною рядка таблиці.
REPORT_WIDTH = 96
# Рядки-роздільники: подвійна лінія для розділів, тонка - для таблиць.
HEADER_SEP = "=" * REPORT_WIDTH
ROW_SEP = "-" * REPORT_WIDTH
# Ширина колонки з відносним шляхом каталогу.
PATH_WIDTH = 28


def _short_path(relative_path) -> str:
    """Повертає відносний шлях зі скісною рискою в кінці; довгі шляхи скорочує."""
    # as_posix() дає однаковий запис шляху на Windows і Linux.
    text = relative_path.as_posix() + "/"
    # Занадто довгий шлях обрізаємо зліва, щоб не зламати геометрію таблиці.
    if len(text) > PATH_WIDTH:
        text = f"...{text[-(PATH_WIDTH - 3):]}"
    return text


def print_empty_report(scan: Dict, search_root: str, dry_run: bool) -> None:
    """Друкує таблицю знайдених порожніх каталогів."""
    # Назва режиму роботи для шапки звіту.
    mode_name = "симуляція (--dry-run)" if dry_run else "справжнє видалення"
    print("\n" + HEADER_SEP)
    print(f"{'ЗВІТ ПОШУКУ ПОРОЖНІХ КАТАЛОГІВ':^{REPORT_WIDTH}}")
    print(HEADER_SEP)
    print(f"Базова директорія пошуку: {search_root}")
    print(f"Режим роботи: {mode_name}")
    print(ROW_SEP)
    # Шапка таблиці: номер, шлях, глибина, тип, час зміни, права.
    print(
        f"| {'№':^3} | {'Каталог':<{PATH_WIDTH}} | {'Глиб.':^5} | "
        f"{'Тип':<16} | {'Дата модифікації':^19} | {'Права':^6} |"
    )
    print(ROW_SEP)
    # Якщо порожніх каталогів немає, повідомляємо про це окремим рядком.
    if not scan["empty"]:
        print(f"{'Порожніх каталогів не знайдено':^{REPORT_WIDTH}}")
    # Один рядок таблиці на кожен каталог.
    for idx, rec in enumerate(scan["empty"], start=1):
        print(
            f"| {idx:^3d} | {_short_path(rec['relative_path']):<{PATH_WIDTH}} | "
            f"{rec['depth']:^5d} | {rec['kind']:<16} | "
            f"{rec['modified_at']:^19} | {rec['permissions']:^6} |"
        )
    print(HEADER_SEP)


def print_removal_report(results: List[Dict], dry_run: bool) -> None:
    """Друкує перелік каталогів у порядку видалення із статусом кожного."""
    # Заголовок залежить від режиму.
    title = "СИМУЛЯЦІЯ ВИДАЛЕННЯ (--dry-run)" if dry_run else "ВИДАЛЕННЯ ПОРОЖНІХ КАТАЛОГІВ"
    print(f"{title:^{REPORT_WIDTH}}")
    print(ROW_SEP)
    # Колонка примітки займає решту ширини рядка (96 - 23 - 28 - 3 = 42).
    note_width = REPORT_WIDTH - 23 - PATH_WIDTH - 3
    # Шапка таблиці: номер, статус, каталог, примітка.
    print(f"| {'№':^3} | {'Статус':<10} | {'Каталог':<{PATH_WIDTH}} | {'Примітка':<{note_width}} |")
    print(ROW_SEP)
    if not results:
        print(f"{'Немає каталогів для обробки':^{REPORT_WIDTH}}")
    for idx, res in enumerate(results, start=1):
        # Примітка заповнюється лише для пропусків і помилок.
        note = res["message"][:note_width]
        print(
            f"| {idx:^3d} | {res['status']:<10} | "
            f"{_short_path(res['relative_path']):<{PATH_WIDTH}} | {note:<{note_width}} |"
        )
    print(HEADER_SEP)


def print_summary(scan: Dict, results: List[Dict], dry_run: bool) -> None:
    """Друкує підсумкову статистику сканування й обробки."""
    # Кількість порожніх каталогів і їхня частка від усіх каталогів.
    empty_count = len(scan["empty"])
    total_dirs = scan["total_dirs"]
    percent = (empty_count / total_dirs * 100.0) if total_dirs else 0.0
    # Підрахунок результатів за статусами.
    def count(status: str) -> int:
        return sum(1 for res in results if res["status"] == status)
    print(f"{'ПІДСУМКОВА СТАТИСТИКА':^{REPORT_WIDTH}}")
    print(ROW_SEP)
    print(f" Каталогів усього (без кореня):   {total_dirs:>6d}")
    print(f" Файлів та посилань усього:       {scan['total_files']:>6d}")
    print(f" Порожніх каталогів:              {empty_count:>6d} ({percent:.1f} %)")
    if dry_run:
        print(f" Буде видалено (симуляція):      {count('СИМУЛЯЦІЯ'):>6d}")
        print(" Файлову систему не змінено.")
    else:
        print(f" Видалено:                        {count('ВИДАЛЕНО'):>6d}")
        print(f" Пропущено:                       {count('ПРОПУЩЕНО'):>6d}")
        print(f" Помилок:                         {count('ПОМИЛКА'):>6d}")
    print(HEADER_SEP + "\n")
