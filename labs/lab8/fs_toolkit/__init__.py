"""
Пакет системних утиліт аудиту файлової системи fs_toolkit.
Освітній компонент: Програмування на Python.
"""
# Імпорт функцій пошуку та видалення з модуля сканування.
from .scanner import (
    validate_root,
    scan_empty_directories,
    plan_removal,
    remove_empty_directories,
)
# Імпорт функцій форматування звіту.
from .reporter import (
    print_empty_report,
    print_removal_report,
    print_summary,
)

# Суворий експорт публічного інтерфейсу пакета
__all__ = [
    "validate_root",
    "scan_empty_directories",
    "plan_removal",
    "remove_empty_directories",
    "print_empty_report",
    "print_removal_report",
    "print_summary",
]
