"""
Модуль сканування файлової системи: пошук порожніх каталогів (варіант 2).
Освітній компонент: Програмування на Python.

Каталог вважається порожнім, якщо в усьому його піддереві немає жодного файлу:
він або зовсім не містить елементів, або містить лише такі самі порожні
підкаталоги. Символічне посилання (навіть на каталог) рахується файлом.
"""
# time - перетворення часу зміни каталогу на рядок для таблиці.
import time
# Path - об'єктний інтерфейс файлової системи (rglob, iterdir, stat, rmdir).
from pathlib import Path

# Типи порожніх каталогів, що потрапляють у звіт.
KIND_LEAF = "порожній"
KIND_NESTED = "лише підкаталоги"

# Статуси обробки каталогу під час видалення.
STATUS_SIMULATED = "СИМУЛЯЦІЯ"
STATUS_REMOVED = "ВИДАЛЕНО"
STATUS_SKIPPED = "ПРОПУЩЕНО"
STATUS_ERROR = "ПОМИЛКА"


def validate_root(raw_path: str) -> Path:
    """Перетворює рядок на абсолютний Path і перевіряє, що це безпечний каталог."""
    # resolve() робить шлях абсолютним і прибирає "." та ".." зі шляху.
    base_path = Path(raw_path).resolve()
    # Шлях має існувати, інакше немає що сканувати.
    if not base_path.exists():
        raise ValueError(f"шлях не існує: {raw_path}")
    # Сканувати можна лише каталог, а не звичайний файл.
    if not base_path.is_dir():
        raise ValueError(f"це не каталог: {raw_path}")
    # Корінь файлової системи (/ або C:\) відхиляємо з міркувань безпеки.
    if base_path == Path(base_path.anchor):
        raise ValueError("корінь файлової системи сканувати заборонено")
    # Повертаємо підтверджений абсолютний шлях.
    return base_path


def scan_empty_directories(base_path: Path) -> dict:
    """
    Один раз обходить дерево через rglob і знаходить усі порожні каталоги.
    Повертає словник: "empty" - список записів-словників, "total_dirs" -
    кількість каталогів без кореня, "total_files" - кількість не-каталогів.
    """
    # Усі каталоги дерева (без самого кореня).
    all_dirs = []
    # Лічильник елементів, що не є каталогами (файли, посилання тощо).
    total_files = 0
    # Множина каталогів, у піддереві яких є хоча б один файл.
    dirs_with_files = set()

    # Рекурсивний обхід усіх вузлів файлового дерева.
    for item in base_path.rglob("*"):
        # Символічне посилання на каталог рахуємо файлом, за ним не йдемо.
        is_real_dir = item.is_dir() and not item.is_symlink()
        # Каталог лише запам'ятовуємо як кандидата.
        if is_real_dir:
            all_dirs.append(item)
            continue
        # Усе інше - файл: збільшуємо лічильник.
        total_files += 1
        # Піднімаємося від файлу до кореня й позначаємо всіх предків.
        parent = item.parent
        while parent != base_path and parent not in dirs_with_files:
            # Предок містить файл у своєму піддереві, отже він не порожній.
            dirs_with_files.add(parent)
            parent = parent.parent

    # Результат: список записів про порожні каталоги.
    empty_records = []
    # Порядок за шляхом робить вивід відтворюваним.
    for directory in sorted(all_dirs):
        # Каталоги з файлами в піддереві пропускаємо.
        if directory in dirs_with_files:
            continue
        try:
            # iterdir() уточнює тип: порожній чи містить порожні підкаталоги.
            has_children = any(True for _ in directory.iterdir())
            # stat() дає час зміни та права доступу (st_mode).
            stat_res = directory.stat()
        except OSError as err:
            # Каталог недоступний: не можемо стверджувати, що він порожній.
            print(f"Попередження системи: Немає доступу до каталогу '{directory}': {err}")
            continue
        # Формуємо запис про каталог у стилі еталонного сканера (словник).
        empty_records.append({
            "path": directory,
            "relative_path": directory.relative_to(base_path),
            "depth": len(directory.relative_to(base_path).parts),
            "kind": KIND_NESTED if has_children else KIND_LEAF,
            "modified_at": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(stat_res.st_mtime)
            ),
            # Права доступу: 9 молодших бітів st_mode у вісімковому записі.
            "permissions": oct(stat_res.st_mode & 0o777),
        })

    # Повертаємо знайдене разом із загальною статистикою обходу.
    return {
        "empty": empty_records,
        "total_dirs": len(all_dirs),
        "total_files": total_files,
    }


def plan_removal(empty_records: list) -> list:
    """Впорядковує каталоги знизу вгору: діти завжди раніше за батьків."""
    # Найглибші каталоги йдуть першими, за рівної глибини - за шляхом.
    return sorted(empty_records, key=lambda rec: (-rec["depth"], str(rec["path"])))


def remove_empty_directories(plan: list, dry_run: bool) -> list:
    """
    Виконує або симулює видалення за планом. Видаляє лише через Path.rmdir,
    тому файли й непорожні каталоги неможливо зачепити. Повертає список
    словників зі статусом кожного каталогу.
    """
    # Підсумок обробки кожного каталогу.
    results = []
    for rec in plan:
        # Шлях до поточного каталогу.
        path = rec["path"]
        # За замовчуванням повідомлення порожнє.
        message = ""
        if dry_run:
            # Симуляція: файлову систему не змінюємо.
            status = STATUS_SIMULATED
        else:
            try:
                # Повторна перевірка: за час роботи вміст міг змінитися.
                if any(True for _ in path.iterdir()):
                    status = STATUS_SKIPPED
                    message = "каталог уже не порожній"
                else:
                    # rmdir видаляє лише порожній каталог.
                    path.rmdir()
                    status = STATUS_REMOVED
            except OSError as err:
                # Немає прав або каталог зник: фіксуємо помилку й продовжуємо.
                status = STATUS_ERROR
                message = str(err)
        # Записуємо результат для звіту.
        results.append({
            "path": path,
            "relative_path": rec["relative_path"],
            "status": status,
            "message": message,
        })
    # Повертаємо підсумок усієї операції.
    return results
