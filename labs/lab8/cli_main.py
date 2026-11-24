"""
Головна точка входу консольної утиліти empty_dir_cleaner (варіант 2).
Здійснює ручний розбір параметрів командного рядка sys.argv та диспетчеризацію завдань.
Освітній компонент: Програмування на Python.
"""
# sys - список аргументів командного рядка sys.argv та завершення sys.exit().
import sys
# time - вимір часу виконання операції.
import time

# Імпорт публічного інтерфейсу з власного пакета fs_toolkit.
from fs_toolkit import (
    validate_root,
    scan_empty_directories,
    plan_removal,
    remove_empty_directories,
    print_empty_report,
    print_removal_report,
    print_summary,
)


def print_usage_help() -> None:
    """Виводить інструкцію з використання утиліти командного рядка."""
    usage_text = """
ВИКОРИСТАННЯ:
    python cli_main.py --path <каталог> [--dry-run]

ПАРАМЕТРИ:
    --path    : (Обов'язковий) Абсолютний або відносний шлях до каталогу пошуку.
    --dry-run : (Опціональний) Лише показати й симулювати видалення, нічого не змінюючи.
    --help, -h : Виведення цієї інформаційної довідки.

ПРИКЛАДИ:
    python cli_main.py --path ./test_sandbox --dry-run
    python cli_main.py --path ./test_sandbox

УВАГА: без --dry-run порожні каталоги видаляються безповоротно.
"""
    print(usage_text)


def parse_cli_arguments(args_list: list[str]) -> dict:
    """
    Здійснює ручний розбір списку аргументів командного рядка sys.argv.
    Повертає словник виділених параметрів конфігурації.
    """
    # Значення за замовчуванням: шлях не заданий, видалення справжнє.
    config = {
        "path": None,
        "dry_run": False,
    }
    # Довідка: прапорці --help / -h або запуск без параметрів (лише argv[0]).
    if "--help" in args_list or "-h" in args_list or len(args_list) <= 1:
        print_usage_help()
        sys.exit(0)
    # Індекс 0 займає ім'я скрипта, тому розбір починається з індексу 1.
    i = 1
    while i < len(args_list):
        arg = args_list[i]
        if arg == "--path":
            # Після --path має йти значення, яке не є іншим прапорцем.
            if i + 1 < len(args_list) and not args_list[i + 1].startswith("--"):
                if config["path"] is not None:
                    print("Помилка синтаксису: Параметр '--path' вказано двічі.")
                    sys.exit(1)
                config["path"] = args_list[i + 1]
                i += 2
            else:
                print("Помилка синтаксису: Після прапорця '--path' необхідно вказати шлях до каталогу.")
                sys.exit(1)
        elif arg == "--dry-run":
            # Прапорець без значення: вмикає режим симуляції.
            config["dry_run"] = True
            i += 1
        else:
            # Будь-який інший аргумент є помилкою.
            print(f"Помилка: Невідомий параметр командного рядка '{arg}'.")
            print_usage_help()
            sys.exit(1)
    # Обов'язковий параметр --path має бути заданий.
    if config["path"] is None:
        print("Помилка: Обов'язковий параметр '--path' не вказано.")
        print_usage_help()
        sys.exit(1)
    return config


def main() -> None:
    """Головна функція диспетчеризації CLI-утиліти."""
    # 1. Розбір вхідних параметрів командного рядка.
    cli_config = parse_cli_arguments(sys.argv)
    dry_run = cli_config["dry_run"]
    t_start = time.perf_counter()

    # 2. Перевірка шляху: некоректний шлях - помилка аргументів (код 2).
    try:
        base_path = validate_root(cli_config["path"])
    except ValueError as val_err:
        print(f"Помилка аргументів: {val_err}")
        sys.exit(2)

    # 3. Пошук порожніх каталогів і їх видалення (або симуляція).
    try:
        scan = scan_empty_directories(base_path)
        plan = plan_removal(scan["empty"])
        results = remove_empty_directories(plan, dry_run)
    except Exception as general_err:
        print(f"Критичний збій виконання: {general_err}")
        sys.exit(3)

    # 4. Формування та друк звіту.
    print_empty_report(scan, str(base_path), dry_run)
    print_removal_report(results, dry_run)
    print_summary(scan, results, dry_run)
    t_elapsed = time.perf_counter() - t_start
    print(f"Операцію успішно завершено за {t_elapsed * 1000:.3f} мс.")
    sys.exit(0)


if __name__ == "__main__":
    # Коректний вивід кирилиці в консолях, що не використовують UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    main()
