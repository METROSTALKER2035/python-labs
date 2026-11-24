# -*- coding: utf-8 -*-
"""
telemetry_pipeline.py - лабораторна робота №10, варіант 2 (моніторинг серверів ЦОД).

Файловий конвеєр із трьох етапів:
  1. CSV: servers.csv -> cleaned_servers.csv (csv.DictReader / csv.DictWriter);
     відбираються рядки із завантаженням CPU > 80 %, рахується середній обсяг вільної RAM.
  2. BIN: firmware_sample.bin - перевірка магічної сигнатури 0x4E4F4445 ('NODE'),
     версії та розміру корисного блоку через seek() і tell().
  3. JSON: station_snapshot.json - зведений стан системи (json.dump, indent=4).

Усі файли відкриваються через менеджер контексту with, шляхи будуються відносно
каталогу скрипта, тому програму можна запускати з будь-якого каталогу.
"""

import csv
import io
import json
import os
import sys
import time
from pathlib import Path

#: Магічна сигнатура BIN-файлу варіанта 2: 0x4E4F4445, ASCII 'NODE'.
FIRMWARE_MAGIC_HEADER = bytes([0x4E, 0x4F, 0x44, 0x45])

#: Поріг завантаження CPU: відбираються лише рядки, де завантаження строго більше.
CPU_LOAD_THRESHOLD_PCT = 80.0

REQUIRED_COLUMNS = ("Timestamp", "Server_ID", "CPU_Load_Pct", "RAM_Free_GB")


# ---------------------------------------------------------------------------
# Етап 1. CSV
# ---------------------------------------------------------------------------

def process_csv_telemetry(input_csv_path: Path, output_csv_path: Path) -> dict:
    """
    Читає servers.csv, залишає рядки з CPU_Load_Pct > 80 %, записує їх у новий CSV
    з додатковою колонкою Overload_Margin_Pct і повертає статистику.
    """
    if not input_csv_path.exists():
        raise FileNotFoundError(f"Вхідний CSV-файл не знайдено: {input_csv_path}")

    total_rows = invalid_rows = normal_rows = 0
    cleaned_rows = []
    free_ram_values = []

    # newline="" обов'язковий для модуля csv: він сам обробляє символи переносу рядка.
    with open(input_csv_path, "r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        missing = [name for name in REQUIRED_COLUMNS if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"У заголовку CSV відсутні колонки: {', '.join(missing)}")

        for row in reader:
            total_rows += 1
            try:
                cpu_load = float(row["CPU_Load_Pct"])
                free_ram = float(row["RAM_Free_GB"])
            except (ValueError, TypeError):
                invalid_rows += 1          # нечислове значення, напр. "N/A"
                continue
            if not (0.0 <= cpu_load <= 100.0) or free_ram < 0.0:
                invalid_rows += 1          # фізично неможливі значення
                continue

            if cpu_load > CPU_LOAD_THRESHOLD_PCT:
                cleaned_rows.append({
                    "Timestamp": row["Timestamp"],
                    "Server_ID": row["Server_ID"],
                    "CPU_Load_Pct": f"{cpu_load:.2f}",
                    "RAM_Free_GB": f"{free_ram:.2f}",
                    "Overload_Margin_Pct": f"{cpu_load - CPU_LOAD_THRESHOLD_PCT:.2f}",
                })
                free_ram_values.append(free_ram)
            else:
                normal_rows += 1

    with open(output_csv_path, "w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["Timestamp", "Server_ID", "CPU_Load_Pct", "RAM_Free_GB", "Overload_Margin_Pct"],
        )
        writer.writeheader()
        writer.writerows(cleaned_rows)

    average_ram = sum(free_ram_values) / len(free_ram_values) if free_ram_values else 0.0
    peak_cpu = max((float(r["CPU_Load_Pct"]) for r in cleaned_rows), default=0.0)
    return {
        "total_read_rows": total_rows,
        "invalid_rows_skipped": invalid_rows,
        "normal_rows_skipped": normal_rows,
        "overloaded_rows_saved": len(cleaned_rows),
        "average_free_ram_gb": average_ram,
        "peak_cpu_load_pct": peak_cpu,
    }


# ---------------------------------------------------------------------------
# Етап 2. BIN
# ---------------------------------------------------------------------------

def verify_binary_firmware(bin_path: Path) -> dict:
    """
    Перевіряє заголовок BIN-файлу: 4 байти сигнатури, 2 байти версії (major, minor),
    далі корисний блок. Розмір блоку визначається через tell() і seek().
    """
    if not bin_path.exists():
        raise FileNotFoundError(f"Бінарний файл не знайдено: {bin_path}")

    with open(bin_path, "rb") as image:
        image.seek(0)                                  # whence = os.SEEK_SET
        header = image.read(len(FIRMWARE_MAGIC_HEADER))
        if header != FIRMWARE_MAGIC_HEADER:
            raise ValueError(
                f"Невірна магічна сигнатура: очікувалось {FIRMWARE_MAGIC_HEADER.hex().upper()}, "
                f"отримано {header.hex().upper() or 'порожній заголовок'}"
            )

        version_bytes = image.read(2)
        if len(version_bytes) < 2:
            raise ValueError("Файл обірвано: немає байтів версії мікропрограми")
        major, minor = version_bytes

        payload_offset = image.tell()                  # позиція після заголовка: 6
        payload = image.read()                         # корисний блок до кінця файлу
        payload_size = image.tell() - payload_offset   # розмір блоку через tell()
        total_size = image.seek(0, os.SEEK_END)        # повний розмір: seek повертає позицію

    return {
        "magic_signature_hex": "0x" + FIRMWARE_MAGIC_HEADER.hex().upper(),
        "magic_signature_ascii": FIRMWARE_MAGIC_HEADER.decode("ascii"),
        "firmware_version": f"v{major}.{minor}",
        "total_image_size_bytes": total_size,
        "payload_offset_bytes": payload_offset,
        "payload_size_bytes": payload_size,
        "payload_hex": payload.hex(" ").upper(),
        # Якщо сигнатура не збіглась, виняток уже виник вище, тому тут завжди True.
        "is_signature_valid": True,
    }


# ---------------------------------------------------------------------------
# Етап 3. JSON
# ---------------------------------------------------------------------------

def export_system_snapshot(output_json_path: Path, csv_stats: dict, bin_stats: dict) -> None:
    """Зводить результати CSV і BIN в один словник і зберігає його у JSON."""
    snapshot = {
        "station_metadata": {
            "facility_name": "Data Center Hall A, rack monitoring",
            "snapshot_generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pipeline_version": "1.0.0",
        },
        "server_telemetry_summary": {
            "total_read_rows": csv_stats["total_read_rows"],
            "invalid_rows_skipped": csv_stats["invalid_rows_skipped"],
            "normal_rows_skipped": csv_stats["normal_rows_skipped"],
            "overloaded_rows_saved": csv_stats["overloaded_rows_saved"],
            "cpu_load_threshold_pct": CPU_LOAD_THRESHOLD_PCT,
            "average_free_ram_gb": round(csv_stats["average_free_ram_gb"], 4),
            "peak_cpu_load_pct": csv_stats["peak_cpu_load_pct"],
        },
        "node_firmware_audit": bin_stats,
    }
    with open(output_json_path, "w", encoding="utf-8") as target:
        json.dump(snapshot, target, indent=4, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Демонстрації до контрольних питань
# ---------------------------------------------------------------------------

def demonstrate_context_manager_safety(path: Path) -> bool:
    """Виняток усередині with не залишає файл відкритим: __exit__ закриває потік."""
    try:
        with open(path, "r", encoding="utf-8") as stream:
            stream.readline()
            _ = 1 / 0                                  # імітація збою під час обробки
    except ZeroDivisionError:
        pass
    return stream.closed


def demonstrate_text_mode_seek() -> str:
    """У текстовому режимі seek() на довільний байт усередині символу UTF-8 небезпечний."""
    wrapper = io.TextIOWrapper(io.BytesIO("Жовтень".encode("utf-8")), encoding="utf-8")
    wrapper.seek(1)                                    # байт 1 - середина двобайтної літери «Ж»
    try:
        return repr(wrapper.read())
    except UnicodeDecodeError as err:
        return f"UnicodeDecodeError: {err.reason}"


# ---------------------------------------------------------------------------
# Головна функція
# ---------------------------------------------------------------------------

def main() -> None:
    # Коректне виведення кирилиці й у перенаправленому потоці (на Windows - cp1251/cp866).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    base = Path(__file__).resolve().parent
    csv_in, csv_out = base / "servers.csv", base / "cleaned_servers.csv"
    bin_in, json_out = base / "firmware_sample.bin", base / "station_snapshot.json"

    print("=" * 72)
    print(" ФАЙЛОВИЙ КОНВЕЄР ТЕЛЕМЕТРІЇ ЦОД (ЛР10, варіант 2)")
    print("=" * 72)
    start = time.perf_counter()

    print("\n[1] CSV: відбір серверів із CPU > "
          f"{CPU_LOAD_THRESHOLD_PCT:.0f} %")
    print("-" * 72)
    csv_stats = process_csv_telemetry(csv_in, csv_out)
    print(f"  Прочитано рядків          : {csv_stats['total_read_rows']}")
    print(f"  Пошкоджених пропущено     : {csv_stats['invalid_rows_skipped']}")
    print(f"  Нормальних пропущено      : {csv_stats['normal_rows_skipped']}")
    print(f"  Перевантажених збережено  : {csv_stats['overloaded_rows_saved']}")
    print(f"  Середня вільна RAM        : {csv_stats['average_free_ram_gb']:.3f} ГБ")
    print(f"  Пікове завантаження CPU   : {csv_stats['peak_cpu_load_pct']:.2f} %")
    print(f"  Вихідний файл             : {csv_out.name}")

    print("\n[2] BIN: аудит заголовка мікропрограми")
    print("-" * 72)
    bin_stats = verify_binary_firmware(bin_in)
    print(f"  Сигнатура                 : {bin_stats['magic_signature_hex']} "
          f"('{bin_stats['magic_signature_ascii']}')")
    print(f"  Версія                    : {bin_stats['firmware_version']}")
    print(f"  Повний розмір             : {bin_stats['total_image_size_bytes']} байтів")
    print(f"  Зсув корисного блоку      : {bin_stats['payload_offset_bytes']}")
    print(f"  Розмір корисного блоку    : {bin_stats['payload_size_bytes']} байтів")
    print(f"  Корисний блок             : {bin_stats['payload_hex']}")

    print("\n[3] JSON: збереження зведеного стану")
    print("-" * 72)
    export_system_snapshot(json_out, csv_stats, bin_stats)
    print(f"  Файл                      : {json_out.name}")

    print("\n[4] Демонстрації до контрольних питань")
    print("-" * 72)
    print(f"  with + ZeroDivisionError  : файл закрито = {demonstrate_context_manager_safety(csv_in)}")
    print(f"  seek(1) у текстовому UTF-8: {demonstrate_text_mode_seek()}")

    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"\n  Час виконання конвеєра: {elapsed_ms:.3f} мс")
    print("=" * 72)


if __name__ == "__main__":
    main()
