# -*- coding: utf-8 -*-
"""
device_validator.py - лабораторна робота №9, варіант 2 (модуль швидкісного АЦП).

Багаторівнева валідація конфігурації АЦП за принципом EAFP та тестовий стенд
стійкості до відмов з розрахунком коефіцієнта програмного відновлення:

    P_recovery = N_handled / N_total_faults

Конвеєр валідації: наявність ключів -> перетворення типів -> межі частоти
вибірки -> межі вхідної напруги -> результат (частота Найквіста).
"""

import sys
import time
from collections import Counter
from typing import Any, Dict, List, Tuple

from custom_exceptions import (
    SAMPLING_MAX_MHZ,
    SAMPLING_MIN_MHZ,
    INPUT_MAX_V,
    INPUT_MIN_V,
    ADCValidationError,
    InputOverloadError,
    SamplingRateError,
)

REQUIRED_KEYS = ("sampling_rate_mhz", "input_voltage")

# Безпечна конфігурація Fail-Safe: мінімальна частота, вхід відключено.
SAFE_MODE = {"sampling_rate_mhz": SAMPLING_MIN_MHZ, "input_voltage": 0.0}


def _to_float(config: Dict[str, Any], key: str) -> float:
    """Перетворює параметр на float; помилку типу загортає в ADCValidationError."""
    try:
        return float(config[key])
    except (ValueError, TypeError) as type_err:
        # Ланцюжок винятків (PEP 3134): першопричина збережеться в __cause__.
        raise ADCValidationError(
            f"Параметр '{key}' неможливо перетворити на число: {config[key]!r}",
            error_code=1003,
        ) from type_err


def validate_adc_configuration(config: Dict[str, Any]) -> float:
    """
    Перевіряє конфігурацію АЦП і повертає частоту Найквіста (fs / 2) у МГц.

    Генерує KeyError (відсутній ключ), ADCValidationError (код 1003, помилка типу),
    SamplingRateError (1001) та InputOverloadError (1002).
    """
    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise KeyError(f"Відсутні обов'язкові ключі конфігурації: {', '.join(missing)}")

    sampling_rate = _to_float(config, "sampling_rate_mhz")
    input_voltage = _to_float(config, "input_voltage")

    # Порівняння записано у вигляді not (a <= x <= b), щоб NaN теж відхилявся.
    if not (SAMPLING_MIN_MHZ <= sampling_rate <= SAMPLING_MAX_MHZ):
        raise SamplingRateError(sampling_rate)
    if not (INPUT_MIN_V <= input_voltage <= INPUT_MAX_V):
        raise InputOverloadError(input_voltage)

    return sampling_rate / 2.0


def _enter_safe_mode(reason: str) -> None:
    """Імітує перехід АЦП у безпечний режим після перехопленої помилки."""
    print(f"    [Fail-Safe] {reason}: безпечний режим "
          f"(fs = {SAFE_MODE['sampling_rate_mhz']} МГц, вхід відключено)")


def run_fault_tolerance_testbench(test_cases: List[Tuple[str, Dict[str, Any]]]) -> None:
    """Прогоняє набори через валідатор і друкує метрики стійкості до відмов."""
    total = len(test_cases)
    successes = 0
    handled = 0
    audits = 0
    by_type: Counter = Counter()

    for number, (title, config) in enumerate(test_cases, start=1):
        print(f"\n--- Тест {number}/{total}: {title}")
        print(f"    Вхід: {config}")
        try:
            nyquist = validate_adc_configuration(config)
        # except йдуть від найспецифічніших класів до загальних: інакше
        # ADCValidationError перехопив би і SamplingRateError, і InputOverloadError.
        except SamplingRateError as err:
            handled += 1
            by_type["SamplingRateError"] += 1
            print(f"    [ПОМИЛКА] {err}")
            print(f"    Поля: sampling_rate_mhz={err.sampling_rate_mhz}, "
                  f"min_mhz={err.min_mhz}, max_mhz={err.max_mhz}")
            _enter_safe_mode("порушено межі частоти")
        except InputOverloadError as err:
            handled += 1
            by_type["InputOverloadError"] += 1
            print(f"    [ПОМИЛКА] {err}")
            print(f"    Поля: input_voltage={err.input_voltage}, "
                  f"min_v={err.min_v}, max_v={err.max_v}")
            _enter_safe_mode("перевантаження входу")
        except ADCValidationError as err:
            handled += 1
            by_type["ADCValidationError"] += 1
            print(f"    [ПОМИЛКА] {err}")
            cause = err.__cause__
            if cause is not None:
                print(f"    Першопричина (__cause__): {type(cause).__name__}: {cause}")
            _enter_safe_mode("некоректний тип параметра")
        except KeyError as err:
            handled += 1
            by_type["KeyError"] += 1
            print(f"    [ПОМИЛКА] KeyError: {err.args[0]}")
            _enter_safe_mode("неповна конфігурація")
        else:
            successes += 1
            print(f"    [ОК] Конфігурацію прийнято, частота Найквіста: {nyquist:.2f} МГц")
        finally:
            audits += 1
            print(f"    [finally] Аудит #{audits}: ресурси АЦП звільнено")

    faults = total - successes
    recovery = handled / faults * 100.0 if faults else 100.0
    print("\n" + "=" * 72)
    print(" ПІДСУМКОВІ МЕТРИКИ СТІЙКОСТІ ДО ВІДМОВ")
    print("=" * 72)
    print(f"  Усього наборів            : {total}")
    print(f"  Успішних                  : {successes}")
    print(f"  Нештатних ситуацій        : {faults}")
    print(f"  Оброблених збоїв          : {handled}")
    for name, count in sorted(by_type.items()):
        print(f"    {name:<22}: {count}")
    print(f"  Спрацювань блоку finally  : {audits}")
    print(f"  P_recovery                : {recovery:.2f}%")


def main() -> None:
    # Гарантуємо коректне виведення кирилиці при перенаправленні потоку.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    test_cases = [
        ("номінальний режим", {"sampling_rate_mhz": 50.0, "input_voltage": 1.2}),
        ("граничні значення діапазонів", {"sampling_rate_mhz": 100.0, "input_voltage": -2.5}),
        ("частота вибірки вища за максимум", {"sampling_rate_mhz": 150.0, "input_voltage": 0.5}),
        ("частота вибірки нижча за мінімум", {"sampling_rate_mhz": 0.5, "input_voltage": -1.0}),
        ("перевантаження входу (додатна напруга)", {"sampling_rate_mhz": 25.0, "input_voltage": 3.1}),
        ("перевантаження входу (від'ємна напруга)", {"sampling_rate_mhz": 25.0, "input_voltage": -2.9}),
        ("пошкоджене значення частоти (рядок)",
         {"sampling_rate_mhz": "CORRUPTED_VALUE", "input_voltage": 1.0}),
        ("відсутнє значення напруги (None)", {"sampling_rate_mhz": 10.0, "input_voltage": None}),
        ("неповна конфігурація (немає input_voltage)", {"sampling_rate_mhz": 10.0}),
    ]

    print("=" * 72)
    print(" ТЕСТОВИЙ СТЕНД ВАЛІДАЦІЇ МОДУЛЯ ШВИДКІСНОГО АЦП (ЛР9, варіант 2)")
    print(f" Межі: частота {SAMPLING_MIN_MHZ} ... {SAMPLING_MAX_MHZ} МГц, "
          f"напруга {INPUT_MIN_V} ... +{INPUT_MAX_V} В")
    print("=" * 72)

    start = time.perf_counter()
    run_fault_tolerance_testbench(test_cases)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"\n  Час виконання тестбенчу: {elapsed_ms:.2f} мс")
    print("=" * 72)


if __name__ == "__main__":
    main()
