# -*- coding: utf-8 -*-
"""
test_bench.py - тестовий стенд лабораторної роботи №11, варіант 2.

Сім блоків перевірок ієрархії CPUKernel -> SIMDKernel: рядкове відображення, інкапсуляція,
протокол послідовностей, арифметика, порівняння, поліморфне сортування, наслідування та MRO.
"""

import math
import sys
import time

from hardware_entities import CPUKernel, SIMDKernel

_passed = 0
_total = 0


def check(condition: bool, label: str) -> None:
    """Контрольна перевірка: рахує виконані та успішні перевірки."""
    global _passed, _total
    _total += 1
    _passed += bool(condition)
    print(f"  [{'OK' if condition else 'FAIL'}] {label}")


def section(number: int, title: str) -> None:
    print(f"\n[{number}] {title}")
    print("-" * 72)


class LegacyTimer:
    """Клас без спільного предка з CPUKernel: має лише __lt__ (качина типізація)."""

    def __init__(self, ticks):
        self.ticks = ticks

    def __lt__(self, other):
        return self.ticks < other.ticks

    def __repr__(self):
        return f"LegacyTimer({self.ticks})"


def run_oop_testbench() -> None:
    core1 = CPUKernel("CORE-0", 3.2, 4.0, [11800.0, 12150.5, 12400.0])
    core2 = CPUKernel("CORE-1", 2.4, 2.5, [5200.0, 5480.0])
    simd = SIMDKernel("AVX-CORE-0", 3.6, 4.0, 256, [48200.0, 50100.0, 51300.0, 49800.0])

    # ------------------------------------------------------------------ 1
    section(1, "Строкове відображення (__str__, __repr__)")
    for unit in (core1, core2, simd):
        print(f"  {unit}")
    print(f"  repr(core1) = {core1!r}")
    print(f"  repr(simd)  = {simd!r}")
    print(f"  Список у f-рядку (використовує __repr__): {[core2]}")
    check(str(core1).startswith("CPU [CORE-0]"), "__str__ базового класу починається з «CPU [CORE-0]»")
    check(str(simd).endswith("смуг FP64: 4"), "__str__ похідного класу доповнено рядком про SIMD")
    check(repr(core1) == "CPUKernel(kernel_id='CORE-0', clock_frequency_ghz=3.2, ipc=4.0, samples_count=3)",
          "__repr__ повертає однозначний технічний рядок")

    # ------------------------------------------------------------------ 2
    section(2, "Інкапсуляція та валідація (@property, @setter)")
    probe = CPUKernel("PROBE", 3.0, 2.0)
    probe.clock_frequency_ghz = 4.0
    print(f"  probe.clock_frequency_ghz після присвоєння 4.0: {probe.clock_frequency_ghz}")
    check(probe.clock_frequency_ghz == 4.0, "сеттер приймає коректну частоту")
    for bad, exc in ((0.2, ValueError), ("fast", TypeError), (True, TypeError), (float("nan"), ValueError)):
        try:
            probe.clock_frequency_ghz = bad
        except exc as err:
            print(f"  частота {bad!r:>6}: {type(err).__name__}: {err}")
            check(True, f"сеттер відхиляє значення {bad!r} ({exc.__name__})")
        else:
            check(False, f"сеттер відхиляє значення {bad!r}")
    try:
        probe.ipc = -1.0
    except ValueError as err:
        print(f"  IPC -1.0: ValueError: {err}")
        check(True, "сеттер IPC відхиляє від'ємне значення")
    try:
        probe.performance_mflops = 1.0
    except AttributeError:
        print("  performance_mflops = 1.0: AttributeError (властивість без сеттера)")
        check(True, "обчислювана властивість без сеттера доступна лише для читання")
    try:
        _ = probe.__clock_frequency_ghz
    except AttributeError:
        print("  probe.__clock_frequency_ghz: AttributeError (ім'я спотворено)")
        check(True, "прямий доступ до __clock_frequency_ghz неможливий")
    print(f"  probe._CPUKernel__clock_frequency_ghz = {probe._CPUKernel__clock_frequency_ghz}")
    print(f"  Атрибути екземпляра: {sorted(vars(probe))}")
    check(probe._CPUKernel__clock_frequency_ghz == 4.0, "спотворене ім'я _CPUKernel__clock_frequency_ghz доступне")
    try:
        SIMDKernel("BAD", 3.0, 2.0, 192)
    except ValueError as err:
        print(f"  SIMDKernel(..., 192): ValueError: {err}")
        check(True, "розрядність 192 біти не підтримується")

    # ------------------------------------------------------------------ 3
    section(3, "Протокол послідовностей (__len__, __getitem__)")
    print(f"  len(core1) = {len(core1)}; core1[0] = {core1[0]:.2f}; core1[-1] = {core1[-1]:.2f}")
    print(f"  core1[0:2] = {core1[0:2]}")
    print(f"  list(core1) = {list(core1)}  (ітерація через __getitem__)")
    print(f"  max(simd) = {max(simd):.1f}; середнє = {simd.mean_measured_mflops:.2f} MFLOPS; "
          f"ефективність = {simd.efficiency_pct:.2f} %")
    check(len(core1) == 3 and len(simd) == 4, "len() повертає кількість відліків буфера")
    check(core1[0] == 11800.0 and core1[-1] == 12400.0, "доступ за індексом, зокрема від'ємним")
    check(list(core1) == [11800.0, 12150.5, 12400.0], "ітерація працює без __iter__")
    try:
        core1[10]
    except IndexError as err:
        print(f"  core1[10]: IndexError: {err}")
        check(True, "вихід за межі буфера дає IndexError")

    # ------------------------------------------------------------------ 4
    section(4, "Перевантаження оператора + (сумування MFLOPS)")
    combined = core1 + core2
    print(f"  combined = core1 + core2 -> {combined}")
    print(f"  P1 + P2 = {core1.performance_mflops:.1f} + {core2.performance_mflops:.1f} = "
          f"{core1.performance_mflops + core2.performance_mflops:.1f} MFLOPS")
    check(combined.kernel_id == "CORE-0+CORE-1", "ідентифікатор об'єднаного ядра: «ID1+ID2»")
    check(combined.clock_frequency_ghz == 3.2, "частота об'єднаного ядра - максимальна з двох")
    check(math.isclose(combined.performance_mflops, 18800.0), "продуктивність дорівнює сумі: 12800 + 6000")
    check(len(combined) == 5 and len(core1) == 3 and len(core2) == 2, "буфери об'єднано (3 + 2), оригінали не змінено")
    mixed = core1 + simd
    print(f"  core1 + simd -> {mixed}")
    check(math.isclose(mixed.performance_mflops, 12800.0 + 57600.0), "сума CPUKernel і SIMDKernel: 12800 + 57600")
    total = sum([core1, core2, simd])
    print(f"  sum([core1, core2, simd]) -> {total.kernel_id}, {total.performance_mflops:.1f} MFLOPS")
    check(math.isclose(total.performance_mflops, 76400.0), "sum() працює через __radd__ (0 + ядро)")
    print(f"  core1.__add__(5) = {core1.__add__(5)!r}")
    check(core1.__add__(5) is NotImplemented, "__add__ повертає NotImplemented для чужого типу")
    for label, expr in (("core1 + 5", lambda: core1 + 5), ("5 + core1", lambda: 5 + core1)):
        try:
            expr()
        except TypeError as err:
            print(f"  {label}: TypeError: {err}")
            check(True, f"{label} завершується TypeError")

    # ------------------------------------------------------------------ 5
    section(5, "Порівняння (__eq__, __lt__)")
    twin = CPUKernel("CORE-0", 3.2, 1.0)
    print(f"  core1 == core2: {core1 == core2}; core1 == twin (той самий ID і частота): {core1 == twin}")
    print(f"  core2 < core1: {core2 < core1}; core1 < core2: {core1 < core2}; core1 > core2: {core1 > core2}")
    print(f"  core1 == 5: {core1 == 5}")
    check((core1 == core2) is False, "різні ядра не рівні")
    check((core1 == twin) is True, "рівність визначається ID та частотою")
    check((core2 < core1) is True and (core1 < core2) is False, "< порівнює за тактовою частотою")
    check((core1 > core2) is True, "оператор > працює через відображений __lt__")
    check((core1 == 5) is False, "порівняння з чужим типом дає False")
    try:
        core1 < 5
    except TypeError as err:
        print(f"  core1 < 5: TypeError: {err}")
        check(True, "core1 < 5 завершується TypeError")

    # ------------------------------------------------------------------ 6
    section(6, "Поліморфне сортування кластера через sorted()")
    cluster = [core1, core2, simd, combined]
    by_freq = sorted(cluster)
    print("  За зростанням тактової частоти (sorted без key, через __lt__):")
    for rank, unit in enumerate(by_freq, 1):
        print(f"    {rank}) {unit.kernel_id:<14}: {unit.clock_frequency_ghz:.2f} ГГц")
    by_perf = sorted(cluster, key=lambda unit: unit.performance_mflops)
    print("  Для порівняння - за зростанням продуктивності (key):")
    for rank, unit in enumerate(by_perf, 1):
        print(f"    {rank}) {unit.kernel_id:<14}: {unit.performance_mflops:.1f} MFLOPS")
    print(f"  Найшвидше ядро за частотою: {max(cluster).kernel_id}")
    check([u.kernel_id for u in by_freq] == ["CORE-1", "CORE-0", "CORE-0+CORE-1", "AVX-CORE-0"],
          "порядок за частотою (рівні частоти зберігають початковий порядок)")
    check([u.kernel_id for u in by_perf] == ["CORE-1", "CORE-0", "CORE-0+CORE-1", "AVX-CORE-0"],
          "порядок за продуктивністю")
    check(max(cluster) is simd, "max() також використовує лише __lt__")

    # ------------------------------------------------------------------ 7
    section(7, "Наслідування, super(), MRO та качина типізація")
    print(f"  MRO SIMDKernel: {' -> '.join(c.__name__ for c in SIMDKernel.__mro__)}")
    print(f"  isinstance(simd, CPUKernel) = {isinstance(simd, CPUKernel)}; "
          f"isinstance(core1, SIMDKernel) = {isinstance(core1, SIMDKernel)}")
    print(f"  simd: скалярна частина {simd.scalar_performance_mflops:.1f} MFLOPS x "
          f"{simd.simd_lanes} смуги = {simd.performance_mflops:.1f} MFLOPS")
    for unit in (core1, simd):
        print(f"  {type(unit).__name__:<10} -> performance_mflops = {unit.performance_mflops:.1f}")
    timers = sorted([LegacyTimer(30), LegacyTimer(10), LegacyTimer(20)])
    print(f"  sorted(LegacyTimer) = {timers}")
    check([c.__name__ for c in SIMDKernel.__mro__] == ["SIMDKernel", "CPUKernel", "object"], "лінеаризація MRO")
    check(isinstance(simd, CPUKernel) and not isinstance(core1, SIMDKernel), "відношення «є різновидом»")
    check(math.isclose(simd.performance_mflops, simd.scalar_performance_mflops * 4),
          "перевизначена властивість множить результат super() на кількість смуг")
    check([t.ticks for t in timers] == [10, 20, 30], "sorted() не вимагає спільного предка: достатньо __lt__")
    check(simd._SIMDKernel__simd_width_bits == 256 and simd._CPUKernel__ipc == 4.0,
          "кожен клас має власний простір спотворених імен")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 72)
    print(" ОБ'ЄКТНИЙ ТЕСТБЕНЧ ПРОЦЕСОРНИХ ЯДЕР (ЛР11, варіант 2)")
    print("=" * 72)
    start = time.perf_counter()
    run_oop_testbench()
    elapsed_ms = (time.perf_counter() - start) * 1000
    print("\n" + "=" * 72)
    print(f"  Контрольних перевірок: {_total}; успішних: {_passed}; невдалих: {_total - _passed}")
    print(f"  Час виконання тестбенчу: {elapsed_ms:.3f} мс")
    print("=" * 72)


if __name__ == "__main__":
    main()
