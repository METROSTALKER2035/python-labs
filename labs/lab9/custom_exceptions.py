# -*- coding: utf-8 -*-
"""
custom_exceptions.py - лабораторна робота №9, варіант 2 (модуль швидкісного АЦП).

Ієрархія користувацьких винятків для валідації конфігурації АЦП:

    Exception
     └── ADCValidationError          базовий доменний клас (код 1000)
          ├── SamplingRateError      частота вибірки поза 1..100 МГц (код 1001)
          └── InputOverloadError     вхідна напруга поза -2.5..+2.5 В (код 1002)

Усі класи успадковують Exception, а не BaseException, щоб не перехоплювати
системні винятки KeyboardInterrupt і SystemExit.
"""

import time

# Межі робочих параметрів АЦП за варіантом 2.
SAMPLING_MIN_MHZ = 1.0
SAMPLING_MAX_MHZ = 100.0
INPUT_MIN_V = -2.5
INPUT_MAX_V = 2.5


class ADCValidationError(Exception):
    """Базовий виняток валідації модуля АЦП: код помилки та час виникнення."""

    def __init__(self, message: str, error_code: int = 1000) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        # Час фіксується в момент створення винятку, а не в момент його обробки.
        self.timestamp = time.strftime("%H:%M:%S")

    def __str__(self) -> str:
        return f"[ERR-{self.error_code}] ({self.timestamp}) {self.message}"


class SamplingRateError(ADCValidationError):
    """Частота вибірки виходить за допустимий діапазон 1 ... 100 МГц."""

    def __init__(self, sampling_rate_mhz: float,
                 min_mhz: float = SAMPLING_MIN_MHZ,
                 max_mhz: float = SAMPLING_MAX_MHZ) -> None:
        self.sampling_rate_mhz = sampling_rate_mhz
        self.min_mhz = min_mhz
        self.max_mhz = max_mhz
        super().__init__(
            f"Частота вибірки {sampling_rate_mhz} МГц поза діапазоном "
            f"[{min_mhz}; {max_mhz}] МГц",
            error_code=1001,
        )


class InputOverloadError(ADCValidationError):
    """Вхідна напруга виходить за допустимий діапазон -2.5 ... +2.5 В."""

    def __init__(self, input_voltage: float,
                 min_v: float = INPUT_MIN_V,
                 max_v: float = INPUT_MAX_V) -> None:
        self.input_voltage = input_voltage
        self.min_v = min_v
        self.max_v = max_v
        super().__init__(
            f"Вхідна напруга {input_voltage} В поза діапазоном "
            f"[{min_v}; {max_v}] В: перевантаження входу АЦП",
            error_code=1002,
        )
