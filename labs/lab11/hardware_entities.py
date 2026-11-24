# -*- coding: utf-8 -*-
"""
hardware_entities.py - лабораторна робота №11, варіант 2.

Ієрархія класів процесорних ядер:
  CPUKernel  - базовий клас: тактова частота (ГГц) та IPC (інструкцій за такт);
  SIMDKernel - похідний клас: векторний прискорювач із заданою розрядністю SIMD.

Продуктивність ядра в MFLOPS розраховується як
    P = f[ГГц] * 1000 * IPC            (для CPUKernel),
    P = f[ГГц] * 1000 * IPC * L        (для SIMDKernel, L = розрядність / 64 - кількість смуг FP64).

Оператор +  : сумування продуктивності двох ядер (результат - новий об'єкт CPUKernel);
оператор <  : порівняння за тактовою частотою.
"""

import math

#: Мінімально допустима тактова частота ядра, ГГц.
MIN_CLOCK_GHZ = 0.5

#: Допустима розрядність SIMD-блока (SSE, AVX2, AVX-512), біт.
SUPPORTED_SIMD_WIDTHS = (128, 256, 512)

#: Розрядність однієї смуги FP64, біт.
FP64_LANE_BITS = 64


def _require_number(value, label: str) -> float:
    """Перевіряє, що значення - скінченне число (bool не вважається числом)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} має бути числом, отримано {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"{label} має бути скінченним числом, отримано {value}")
    return float(value)


class CPUKernel:
    """Базовий клас: процесорне ядро (тактова частота, IPC, буфер вимірів MFLOPS)."""

    def __init__(self, kernel_id, clock_frequency_ghz, ipc, samples=None):
        if not isinstance(kernel_id, str):
            raise TypeError(f"Ідентифікатор ядра має бути рядком, отримано {type(kernel_id).__name__}")
        if not kernel_id.strip():
            raise ValueError("Ідентифікатор ядра не може бути порожнім")
        self.__kernel_id = kernel_id                    # приватний стан: _CPUKernel__kernel_id
        self.__samples = []                             # буфер вимірів продуктивності, MFLOPS
        self.clock_frequency_ghz = clock_frequency_ghz  # присвоєння йде через сеттер
        self.ipc = ipc
        for value in samples or ():
            self.append_sample(value)

    # ---------------------------------------------------------------- властивості
    @property
    def kernel_id(self) -> str:
        return self.__kernel_id                         # лише читання: сеттера немає

    @property
    def clock_frequency_ghz(self) -> float:
        return self.__clock_frequency_ghz

    @clock_frequency_ghz.setter
    def clock_frequency_ghz(self, value) -> None:
        value = _require_number(value, "Тактова частота")
        if value < MIN_CLOCK_GHZ:
            raise ValueError(f"Тактова частота ({value} ГГц) нижча за мінімальний поріг {MIN_CLOCK_GHZ} ГГц")
        self.__clock_frequency_ghz = value

    @property
    def ipc(self) -> float:
        return self.__ipc

    @ipc.setter
    def ipc(self, value) -> None:
        value = _require_number(value, "IPC")
        if value <= 0.0:
            raise ValueError(f"IPC має бути додатним, отримано {value}")
        self.__ipc = value

    @property
    def performance_mflops(self) -> float:
        """Пікова продуктивність ядра: f[МГц] * IPC."""
        return self.__clock_frequency_ghz * 1000.0 * self.__ipc

    @property
    def mean_measured_mflops(self) -> float:
        """Середня виміряна продуктивність; для порожнього буфера - 0.0."""
        return sum(self.__samples) / len(self.__samples) if self.__samples else 0.0

    @property
    def efficiency_pct(self) -> float:
        """Частка виміряної продуктивності від пікової, %."""
        return self.mean_measured_mflops / self.performance_mflops * 100.0

    # ---------------------------------------------------------------- методи
    def append_sample(self, value) -> None:
        """Додає виміряне значення продуктивності (MFLOPS) до буфера."""
        value = _require_number(value, "Відлік продуктивності")
        if value < 0.0:
            raise ValueError(f"Відлік продуктивності не може бути від'ємним: {value}")
        self.__samples.append(value)

    def _as_plain_kernel(self) -> "CPUKernel":
        """Копія у вигляді CPUKernel з тією самою продуктивністю (IPC перераховано)."""
        freq = self.clock_frequency_ghz
        return CPUKernel(self.kernel_id, freq, self.performance_mflops / (freq * 1000.0),
                         list(self.__samples))

    # ---------------------------------------------------------------- dunder-методи
    def __str__(self) -> str:
        return (f"CPU [{self.__kernel_id}] | Частота: {self.__clock_frequency_ghz:.2f} ГГц | "
                f"IPC: {self.__ipc:.2f} | Продуктивність: {self.performance_mflops:.1f} MFLOPS | "
                f"Буфер: {len(self.__samples)} відліків")

    def __repr__(self) -> str:
        return (f"{type(self).__name__}(kernel_id={self.__kernel_id!r}, "
                f"clock_frequency_ghz={self.__clock_frequency_ghz}, ipc={self.__ipc}, "
                f"samples_count={len(self.__samples)})")

    def __len__(self) -> int:
        return len(self.__samples)

    def __getitem__(self, index):
        return self.__samples[index]                    # індекс, від'ємний індекс або зріз

    def __eq__(self, other):
        if not isinstance(other, CPUKernel):
            return NotImplemented
        return (self.__kernel_id == other.__kernel_id
                and self.__clock_frequency_ghz == other.__clock_frequency_ghz)

    __hash__ = None                                     # об'єкт змінний, тож хешування вимкнено явно

    def __lt__(self, other):
        if not isinstance(other, CPUKernel):
            return NotImplemented
        return self.__clock_frequency_ghz < other.__clock_frequency_ghz

    def __add__(self, other):
        """Сумування продуктивності: нове ядро з частотою max(f1, f2) та IPC, підібраним так,
        щоб P_нове = P1 + P2; буфери об'єднуються."""
        if not isinstance(other, CPUKernel):
            return NotImplemented                       # інтерпретатор спробує other.__radd__
        freq = max(self.__clock_frequency_ghz, other.__clock_frequency_ghz)
        total = self.performance_mflops + other.performance_mflops
        combined = CPUKernel(f"{self.__kernel_id}+{other.__kernel_id}", freq, total / (freq * 1000.0))
        for value in self.__samples + other.__samples:
            combined.append_sample(value)
        return combined

    def __radd__(self, other):
        """Підтримка sum(): початкове значення 0 + ядро дає копію ядра."""
        if isinstance(other, (int, float)) and not isinstance(other, bool) and other == 0:
            return self._as_plain_kernel()
        return NotImplemented


class SIMDKernel(CPUKernel):
    """Похідний клас: векторний прискорювач, продуктивність якого множиться на кількість смуг."""

    def __init__(self, kernel_id, clock_frequency_ghz, ipc, simd_width_bits, samples=None):
        super().__init__(kernel_id, clock_frequency_ghz, ipc, samples)   # делегування базовому конструктору
        self.simd_width_bits = simd_width_bits

    @property
    def simd_width_bits(self) -> int:
        return self.__simd_width_bits

    @simd_width_bits.setter
    def simd_width_bits(self, value) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"Розрядність SIMD має бути цілим числом, отримано {type(value).__name__}")
        if value not in SUPPORTED_SIMD_WIDTHS:
            raise ValueError(f"Розрядність SIMD ({value} біт) не підтримується; "
                             f"допустимі значення: {SUPPORTED_SIMD_WIDTHS}")
        self.__simd_width_bits = value                  # _SIMDKernel__simd_width_bits

    @property
    def simd_lanes(self) -> int:
        """Кількість смуг FP64 в одному векторному регістрі."""
        return self.__simd_width_bits // FP64_LANE_BITS

    @property
    def scalar_performance_mflops(self) -> float:
        """Скалярна частина продуктивності - результат базового класу."""
        return super().performance_mflops

    @property
    def performance_mflops(self) -> float:
        return self.scalar_performance_mflops * self.simd_lanes

    def __str__(self) -> str:
        return super().__str__() + f" | SIMD: {self.__simd_width_bits} біт, смуг FP64: {self.simd_lanes}"

    def __repr__(self) -> str:
        base = super().__repr__()
        return base[:-1] + f", simd_width_bits={self.__simd_width_bits})"
