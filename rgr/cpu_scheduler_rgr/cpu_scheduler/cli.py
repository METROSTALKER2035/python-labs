"""Інтерфейс командного рядка: розбір sys.argv, запуск моделювання, коди завершення."""
import sys
import time
from typing import Dict, List, Optional

from .benchmark import run_benchmark
from .exceptions import (CliArgumentError, DataFileFormatError, PersistenceError,
                         QuantumError, SchedulerError)
from .parser import normalize_algorithm
from .reporting import format_benchmark, format_comparison, format_report
from .schedulers import FifoScheduler, RoundRobinScheduler
from .storage import load_tasks, save_result_csv, save_result_json

EXIT_OK, EXIT_ARGS, EXIT_DATA, EXIT_IO = 0, 1, 2, 3  # коди завершення програми

HELP = """Використання: python main.py [параметри]

Параметри:
  -i, --input ФАЙЛ     вхідний файл задач (.txt, .csv, .json)
  -a, --algo АЛГОРИТМ  fifo | rr | both (за замовчуванням both)
  -q, --quantum N      квант часу для RR (за замовчуванням 4)
  -g, --gantt          вивести діаграму Ганта
      --json ФАЙЛ      зберегти результати у JSON
      --csv ФАЙЛ       зберегти результати у CSV
  -b, --bench N        бенчмаркінг для наборів до N задач (замість -i)
  -h, --help           показати цю довідку

Коди завершення: 0 - успіх, 1 - аргументи, 2 - дані, 3 - файлова система."""

VALUE_OPTIONS = {"-i": "input", "--input": "input", "-a": "algo", "--algo": "algo",
                 "-q": "quantum", "--quantum": "quantum", "--json": "json",
                 "--csv": "csv", "-b": "bench", "--bench": "bench"}
FLAG_OPTIONS = {"-g": "gantt", "--gantt": "gantt", "-h": "help", "--help": "help"}


def parse_arguments(args: List[str]) -> Dict[str, object]:
    """Розібрати список аргументів (без імені програми) у словник параметрів."""
    options: Dict[str, object] = {"input": None, "algo": "both", "quantum": 4,
                                  "json": None, "csv": None, "bench": None,
                                  "gantt": False, "help": False}
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in FLAG_OPTIONS:
            options[FLAG_OPTIONS[arg]] = True
        elif arg in VALUE_OPTIONS:
            index += 1
            if index >= len(args):
                raise CliArgumentError(f"Параметр {arg} потребує значення")
            options[VALUE_OPTIONS[arg]] = args[index]
        else:
            raise CliArgumentError(f"Невідомий параметр '{arg}'")
        index += 1
    for key in ("quantum", "bench"):  # числові параметри перетворюємо на int
        if options[key] is not None:
            try:
                options[key] = int(options[key])
            except ValueError as exc:
                raise CliArgumentError(f"Параметр --{key} має бути цілим числом") from exc
    return options


def run(options: Dict[str, object]) -> int:
    """Виконати дію, обрану параметрами; повернути код завершення."""
    if options["bench"] is not None:
        top = int(options["bench"])
        sizes = [n for n in (100, 500, 1000, 2000, 5000, 10000) if n <= top] or [top]
        print(format_benchmark(run_benchmark(sizes, int(options["quantum"]))))
        return EXIT_OK
    if not options["input"]:
        raise CliArgumentError("Не вказано вхідний файл (параметр --input)")
    tasks = load_tasks(str(options["input"]))
    kind = normalize_algorithm(str(options["algo"]))
    schedulers = []
    if kind in ("fifo", "both"):
        schedulers.append(FifoScheduler())
    if kind in ("rr", "both"):
        schedulers.append(RoundRobinScheduler(int(options["quantum"])))
    started = time.perf_counter()
    results = [sch.run(tasks) for sch in schedulers]
    elapsed = (time.perf_counter() - started) * 1000
    for res in results:
        print(format_report(res, with_gantt=bool(options["gantt"])))
        print()
    if len(results) > 1:
        print(format_comparison(results))
    if options["json"]:
        save_result_json(str(options["json"]), results)
        print(f"JSON збережено: {options['json']}")
    if options["csv"]:
        save_result_csv(str(options["csv"]), results)
        print(f"CSV збережено: {options['csv']}")
    print(f"Час моделювання: {elapsed:.3f} мс")
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входу CLI: повертає код завершення, не викликає sys.exit самостійно."""
    args = sys.argv[1:] if argv is None else argv  # аргументи беремо з sys.argv
    try:
        options = parse_arguments(args)
        if options["help"]:
            print(HELP)
            return EXIT_OK
        return run(options)
    except CliArgumentError as exc:
        print(f"Помилка аргументів: {exc}", file=sys.stderr)
        return EXIT_ARGS
    except QuantumError as exc:  # некоректний квант - помилка параметрів
        print(f"Помилка аргументів: {exc}", file=sys.stderr)
        return EXIT_ARGS
    except DataFileFormatError as exc:
        print(f"Помилка даних: {exc}", file=sys.stderr)
        return EXIT_DATA
    except PersistenceError as exc:
        print(f"Помилка файлу: {exc}", file=sys.stderr)
        return EXIT_IO
    except SchedulerError as exc:  # решта помилок предметної області
        print(f"Помилка даних: {exc}", file=sys.stderr)
        return EXIT_DATA


if __name__ == "__main__":
    sys.exit(main())
