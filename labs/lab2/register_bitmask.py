#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
register_bitmask.py - лабораторна робота №2, варіант 2 (завдання 2).

Модель 16-бітного регістра передавача UART:

    біти 15..12  UART_BAUD  (4 біти, 0..15)   код швидкості
    біт  11      TX_BUSY    (1 біт,  0..1)    передавач зайнятий
    біти 10..2   FIFO_CNT   (9 бітів, 0..511) кількість байтів у FIFO
    біти 1..0    MODE       (2 біти, 0..3)    режим роботи

Програма пакує поля у слово, розпаковує їх, змінює прапорець TX_BUSY
(set / clear / toggle) і перевіряє, що змінюється лише цільовий біт.
Програма не приймає аргументів і не вимагає введення з клавіатури.
"""

# sys - для sys.getsizeof та налаштування кодування виводу.
import sys

# Роздільники завширшки 80 символів.
SEPARATOR = "=" * 80
THIN_SEPARATOR = "-" * 80

# Зсув (номер молодшого біта) та маска для кожного поля регістра.
UART_BAUD_SHIFT, UART_BAUD_MASK = 12, 0xF      # 4 біти: 0b1111
TX_BUSY_SHIFT, TX_BUSY_MASK = 11, 0x1          # 1 біт:  0b1
FIFO_CNT_SHIFT, FIFO_CNT_MASK = 2, 0x1FF       # 9 бітів: 0b1_1111_1111
MODE_SHIFT, MODE_MASK = 0, 0x3                 # 2 біти: 0b11
# Маска всіх 16 бітів регістра; потрібна після операції інверсії ~.
REGISTER_MASK = 0xFFFF
# Маска одиничного біта TX_BUSY у складі всього слова (0x0800).
TX_BUSY_BIT = TX_BUSY_MASK << TX_BUSY_SHIFT


def _check_range(name: str, value: int, max_value: int) -> None:
    """Перевіряє, що value є цілим числом у діапазоні 0..max_value."""
    # Тип має бути int (bool теж підходить, бо є підкласом int).
    if not isinstance(value, int):
        # Некоректний тип значення поля.
        raise ValueError(f"{name} має бути цілим числом")
    # Значення має вміщуватися у відведену кількість бітів.
    if not 0 <= value <= max_value:
        # Повідомляємо допустимий діапазон.
        raise ValueError(f"{name} має бути в діапазоні 0..{max_value}")


def pack_uart_register(uart_baud: int, tx_busy: bool, fifo_cnt: int,
                       mode: int) -> int:
    """Пакує поля передавача в 16-бітне слово за допомогою зсувів і |."""
    # Перевіряємо діапазони всіх полів, щоб поле не зачепило сусіднє.
    _check_range("uart_baud", uart_baud, UART_BAUD_MASK)
    _check_range("fifo_cnt", fifo_cnt, FIFO_CNT_MASK)
    _check_range("mode", mode, MODE_MASK)
    # Прапорець зводимо до 0 або 1.
    busy_bit = 1 if tx_busy else 0
    # Кожне поле зсуваємо на своє місце й об'єднуємо побітовим АБО.
    return ((uart_baud << UART_BAUD_SHIFT)
            | (busy_bit << TX_BUSY_SHIFT)
            | (fifo_cnt << FIFO_CNT_SHIFT)
            | (mode << MODE_SHIFT))


def unpack_uart_register(register_val: int) -> dict:
    """Розпаковує слово у словник полів (зсув вправо та маска &)."""
    # Слово має вміщуватися у 16 бітів.
    _check_range("register_val", register_val, REGISTER_MASK)
    # Для кожного поля: зсув до молодших розрядів, потім відсікання маскою.
    return {
        "uart_baud": (register_val >> UART_BAUD_SHIFT) & UART_BAUD_MASK,
        "tx_busy": bool((register_val >> TX_BUSY_SHIFT) & TX_BUSY_MASK),
        "fifo_cnt": (register_val >> FIFO_CNT_SHIFT) & FIFO_CNT_MASK,
        "mode": (register_val >> MODE_SHIFT) & MODE_MASK,
    }


def set_tx_busy(register_val: int) -> int:
    """Встановлює TX_BUSY = 1 побітовим АБО з маскою біта 11."""
    # Перевіряємо коректність вхідного слова.
    _check_range("register_val", register_val, REGISTER_MASK)
    # АБО залишає інші біти без змін і зводить біт 11 в одиницю.
    return register_val | TX_BUSY_BIT


def clear_tx_busy(register_val: int) -> int:
    """Скидає TX_BUSY = 0: A & ~mask, результат обмежується 16 бітами."""
    # Перевіряємо коректність вхідного слова.
    _check_range("register_val", register_val, REGISTER_MASK)
    # ~mask - від'ємне число в Python, тому додаємо & 0xFFFF (16 бітів).
    return register_val & ~TX_BUSY_BIT & REGISTER_MASK


def toggle_tx_busy(register_val: int) -> int:
    """Інвертує TX_BUSY побітовим виключним АБО з маскою біта 11."""
    # Перевіряємо коректність вхідного слова.
    _check_range("register_val", register_val, REGISTER_MASK)
    # XOR з одиницею змінює біт на протилежний, з нулем - не змінює.
    return register_val ^ TX_BUSY_BIT


def changed_bits(before: int, after: int) -> int:
    """Повертає маску бітів, що відрізняються між двома станами регістра."""
    # XOR дає одиниці саме в тих розрядах, де значення різні.
    return before ^ after


def verify_round_trip_exhaustive() -> bool:
    """Перевіряє pack(unpack(r)) == r для всіх 65536 значень регістра."""
    # Перебираємо кожне можливе 16-бітне слово.
    for register_val in range(REGISTER_MASK + 1):
        # Розпаковуємо слово у поля.
        fields = unpack_uart_register(register_val)
        # Пакуємо поля назад.
        repacked = pack_uart_register(fields["uart_baud"], fields["tx_busy"],
                                      fields["fifo_cnt"], fields["mode"])
        # Будь-яка розбіжність означає помилку у масках чи зсувах.
        if repacked != register_val:
            return False
    # Усі 65536 слів пройшли перевірку.
    return True


def format_register(value: int) -> str:
    """Форматує слово у вигляді BIN | HEX для таблиць."""
    # 16 бітів двійкового запису, потім чотири шістнадцяткові цифри.
    return f"0b{value:016b} | 0x{value:04X}"


def print_section(title: str) -> None:
    """Друкує заголовок розділу з роздільниками."""
    # Порожній рядок перед розділом, потім заголовок і тонка лінія.
    print(f"\n{title}")
    print(THIN_SEPARATOR)


def main() -> None:
    """Точка входу: виконує завдання 2 варіанта 2 і друкує звіт."""
    # Верхній банер звіту.
    print(SEPARATOR)
    print("ЛР №2. ВАРІАНТ 2. РЕГІСТР UART: УПАКУВАННЯ ТА TX_BUSY".center(80))
    print(SEPARATOR)

    # --- Розділ 1. Структура регістра ---
    print_section("[1] СТРУКТУРА 16-БІТНОГО РЕГІСТРА")
    print(f"{'Поле':<10} {'Біти':>6} {'Зсув':>5} {'Маска':>7} {'Ширина':>7}"
          f" {'Діапазон':>10}")
    # Таблиця полів: назва, біти, зсув, маска, ширина, діапазон значень.
    layout = (("UART_BAUD", "15..12", UART_BAUD_SHIFT, UART_BAUD_MASK, 4),
              ("TX_BUSY", "11", TX_BUSY_SHIFT, TX_BUSY_MASK, 1),
              ("FIFO_CNT", "10..2", FIFO_CNT_SHIFT, FIFO_CNT_MASK, 9),
              ("MODE", "1..0", MODE_SHIFT, MODE_MASK, 2))
    for name, bits, shift, mask, width in layout:
        print(f"{name:<10} {bits:>6} {shift:>5} {'0x%X' % mask:>7} {width:>7}"
              f" {'0..%d' % mask:>10}")

    # --- Розділ 2. Упакування ---
    print_section("[2] УПАКУВАННЯ ПОЛІВ ПЕРЕДАВАЧА")
    # Початкові значення полів варіанта.
    baud, busy, fifo, mode = 9, True, 300, 2
    print(f"UART_BAUD={baud}, TX_BUSY={int(busy)}, FIFO_CNT={fifo}, MODE={mode}")
    # Внесок кожного поля у слово до об'єднання.
    print(f"UART_BAUD << 12 = 0x{baud << UART_BAUD_SHIFT:04X}")
    print(f"TX_BUSY   << 11 = 0x{int(busy) << TX_BUSY_SHIFT:04X}")
    print(f"FIFO_CNT  <<  2 = 0x{fifo << FIFO_CNT_SHIFT:04X}")
    print(f"MODE      <<  0 = 0x{mode << MODE_SHIFT:04X}")
    # Підсумкове слово в чотирьох системах числення.
    register = pack_uart_register(baud, busy, fifo, mode)
    print(f"DEC: {register:d}")
    print(f"HEX: 0x{register:04X}")
    print(f"BIN: 0b{register:016b}")
    print(f"OCT: 0o{register:06o}")

    # --- Розділ 3. Розпакування ---
    print_section("[3] РОЗПАКУВАННЯ ТА ПЕРЕВІРКА ПОЛІВ")
    fields = unpack_uart_register(register)
    # Очікувані значення збігаються з тими, що пакували.
    expected = {"uart_baud": baud, "tx_busy": busy, "fifo_cnt": fifo,
                "mode": mode}
    print(f"{'Поле':<10} {'Отримано':>9} {'Очікувано':>10} {'Статус':>8}")
    for key, value in fields.items():
        status = "OK" if value == expected[key] else "FAIL"
        print(f"{key:<10} {str(value):>9} {str(expected[key]):>10} {status:>8}")

    # --- Розділ 4. Операції з прапорцем TX_BUSY ---
    print_section("[4] ОПЕРАЦІЇ З TX_BUSY (біт 11)")
    print(f"{'Операція':<18} {'BIN':<18} | {'HEX':<6} | TX_BUSY | змінені біти")
    # Послідовність станів: вихідний, після clear, після set, після двох toggle.
    cleared = clear_tx_busy(register)
    restored = set_tx_busy(cleared)
    toggled = toggle_tx_busy(register)
    toggled_back = toggle_tx_busy(toggled)
    steps = (("початковий", register, register),
             ("clear_tx_busy", cleared, register),
             ("set_tx_busy", restored, cleared),
             ("toggle (1-й)", toggled, register),
             ("toggle (2-й)", toggled_back, toggled))
    only_bit_11 = True
    for label, value, previous in steps:
        # Маска змінених бітів відносно попереднього стану.
        diff = changed_bits(previous, value)
        busy_now = int(unpack_uart_register(value)["tx_busy"])
        print(f"{label:<18} {format_register(value)} | {busy_now:^7} | "
              f"0x{diff:04X}")
        # Операція має змінювати лише біт 11 (або нічого - для початкового).
        only_bit_11 = only_bit_11 and diff in (0, TX_BUSY_BIT)
    # Ідемпотентність: повторне скидання вже скинутого прапорця нічого не змінює.
    print(f"clear(clear(r)) == clear(r)       : {clear_tx_busy(cleared) == cleared}")
    print(f"Змінюється лише біт 11 (0x0800)  : {only_bit_11}")
    print(f"Інші біти збережено (0x{cleared & ~TX_BUSY_BIT & REGISTER_MASK:04X})"
          f"        : {cleared == register & ~TX_BUSY_BIT & REGISTER_MASK}")
    # Інверсія ~ дає від'ємне число; маска 0xFFFF повертає 16-бітне доповнення.
    print(f"~0x{register:04X}  = {~register}")
    print(f"~0x{register:04X} & 0xFFFF = 0x{~register & REGISTER_MASK:04X}")

    # --- Розділ 5. Ефективність упакування ---
    print_section("[5] ЕФЕКТИВНІСТЬ УПАКУВАННЯ")
    # Розмір одного упакованого цілого та чотирьох окремих об'єктів у Python.
    packed_size = sys.getsizeof(register)
    separate_size = sum(sys.getsizeof(v) for v in (baud, busy, fifo, mode))
    print(f"Один int з упакованим словом       : {packed_size:>4} байт")
    print(f"Чотири окремі об'єкти (int, bool)  : {separate_size:>4} байт")
    # У C-структурі: 16 бітів проти чотирьох 32-бітних int.
    print("Корисні дані регістра              :   16 біт (2 байти)")
    print("Чотири поля як int32 у C           :  128 біт (16 байт)")
    print(f"Економія в апаратному поданні      : {(128 - 16) / 128:.1%}")

    # --- Розділ 6. Вичерпна перевірка ---
    print_section("[6] ВИЧЕРПНА ПЕРЕВІРКА pack(unpack(r)) == r")
    print(f"Перевірено значень: {REGISTER_MASK + 1}")
    print(f"Результат: {'OK' if verify_round_trip_exhaustive() else 'FAIL'}")
    print(SEPARATOR)


if __name__ == "__main__":
    # Забезпечуємо коректний вивід кирилиці у консолях не з UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # Запускаємо звіт.
    main()
