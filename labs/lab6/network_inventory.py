# -*- coding: utf-8 -*-
"""
Лабораторна робота №6, варіант 2 (облікові записи Active Directory).
Автор: Афанасьєв Сергій, група КІ-24-1.

Модуль виконує інвентаризацію облікових записів за допомогою словників:
  * структура бази: Username -> {email, department, roles (set), is_active};
  * операції CRUD: додавання, оновлення через update(), видалення через pop();
  * безпечне читання атрибутів через get() і setdefault();
  * інвертований індекс «роль -> список користувачів» (dict comprehension);
  * демонстрації для теорії: порядок вставки, зростання таблиці, хешованість,
    час пошуку O(1) у словнику проти лінійного пошуку в списку.
"""
import sys
import time

# Ширина текстового звіту (кількість символів у рядку).
REPORT_WIDTH = 98
SEPARATOR = "-" * REPORT_WIDTH


# ---------------------------------------------------------------------------
# Створення та зміна бази
# ---------------------------------------------------------------------------
def create_initial_database() -> dict:
    """Повертає початкову базу з шести облікових записів AD.

    Ключ - ім'я користувача (sAMAccountName), значення - вкладений словник.
    Ролі зберігаються у множині set: порядок не важливий, дублікатів немає.
    """
    return {
        "o.kovalenko": {
            "email": "o.kovalenko@corp.example.com",
            "department": "Accounting",
            "roles": {"fin_read", "fin_write", "report_view"},
            "is_active": True,
        },
        "m.petrenko": {
            "email": "m.petrenko@corp.example.com",
            "department": "Accounting",
            "roles": {"fin_read", "fin_write", "report_view", "domain_admin"},
            "is_active": True,
        },
        "i.shevchenko": {
            "email": "i.shevchenko@corp.example.com",
            "department": "IT",
            "roles": {"vpn_access", "server_admin", "report_view"},
            "is_active": True,
        },
        "t.bondar": {
            "email": "t.bondar@corp.example.com",
            "department": "HR",
            "roles": {"hr_read", "hr_write", "report_view"},
            "is_active": False,
        },
        "d.melnyk": {
            "email": "d.melnyk@corp.example.com",
            "department": "Sales",
            "roles": {"crm_read", "crm_write", "report_view", "vpn_access"},
            "is_active": True,
        },
        "n.savchenko": {
            "email": "n.savchenko@corp.example.com",
            "department": "Sales",
            "roles": {"crm_read"},
            "is_active": True,
        },
    }


def add_user(db: dict, username: str, email: str, department: str,
             roles: set, is_active: bool = True) -> bool:
    """Додає нового співробітника. Повертає False, якщо ім'я вже зайняте."""
    if username in db:
        print(f"Попередження: обліковий запис {username} уже існує")
        return False
    db[username] = {
        "email": email,
        "department": department,
        "roles": set(roles),  # копія, щоб не ділити множину з викликачем
        "is_active": is_active,
    }
    return True


def update_user(db: dict, username: str, **changes) -> bool:
    """Оновлює атрибути запису методом dict.update()."""
    record = db.get(username)  # get() не викидає KeyError
    if record is None:
        print(f"Попередження: обліковий запис {username} не знайдено")
        return False
    record.update(changes)
    return True


def remove_user(db: dict, username: str):
    """Видаляє обліковий запис через pop(); None, якщо запису немає."""
    removed = db.pop(username, None)
    if removed is None:
        print(f"Попередження: обліковий запис {username} відсутній, "
              f"видаляти нічого")
    return removed


def get_attribute(db: dict, username: str, attribute: str,
                  default="не вказано"):
    """Безпечне читання атрибута: get() замість квадратних дужок."""
    return db.get(username, {}).get(attribute, default)


def ensure_manager(db: dict, username: str, default="не призначено") -> str:
    """Гарантує наявність поля manager через setdefault().

    Якщо ключа немає, setdefault() вставляє значення й повертає його;
    якщо ключ є, повертає існуюче значення й нічого не перезаписує.
    """
    return db[username].setdefault("manager", default)


# ---------------------------------------------------------------------------
# Інвертований індекс
# ---------------------------------------------------------------------------
def build_role_index(db: dict) -> dict:
    """Будує індекс «роль -> відсортований список користувачів».

    Dict comprehension: зовнішній цикл іде за унікальними ролями,
    внутрішній вибирає користувачів, які мають цю роль.
    """
    all_roles = {role for rec in db.values() for role in rec["roles"]}
    return {
        role: sorted(user for user, rec in db.items() if role in rec["roles"])
        for role in sorted(all_roles)
    }


# ---------------------------------------------------------------------------
# Звіти
# ---------------------------------------------------------------------------
def print_header(title: str) -> None:
    print()
    print(title)
    print(SEPARATOR)


def print_database_report(db: dict) -> None:
    """Друкує таблицю облікових записів із вирівнюванням f-рядками."""
    print(f"{'ІНВЕНТАРИЗАЦІЯ ОБЛІКОВИХ ЗАПИСІВ AD':^{REPORT_WIDTH}}")
    print(SEPARATOR)
    print(f"{'Username':<14}{'Email':<32}{'Відділ':<12}Активний")
    print(SEPARATOR)
    for username, rec in db.items():
        status = "так" if rec["is_active"] else "ні"
        roles = ", ".join(sorted(rec["roles"]))
        print(f"{username:<14}{rec['email']:<32}{rec['department']:<12}"
              f"{status}")
        print(f"{'':<14}ролі: {roles}")
    print(SEPARATOR)
    active = sum(rec["is_active"] for rec in db.values())
    print(f"Усього записів: {len(db)}, активних: {active}, "
          f"вимкнених: {len(db) - active}")


def print_role_index(index: dict) -> None:
    print(f"{'Роль':<16}{'К-сть':>6}  Користувачі")
    print(SEPARATOR)
    for role, users in index.items():
        print(f"{role:<16}{len(users):>6}  {', '.join(users)}")
    print(SEPARATOR)
    busiest = max(index, key=lambda r: len(index[r]))
    print(f"Найпоширеніша роль: {busiest} (користувачів: {len(index[busiest])})")


# ---------------------------------------------------------------------------
# Демонстрації для теорії
# ---------------------------------------------------------------------------
def time_us(func, repeat: int = 2000) -> float:
    """Середній час виклику func у мікросекундах (мінімум із 5 серій)."""
    best = float("inf")
    for _ in range(5):
        started = time.perf_counter()
        for _ in range(repeat):
            func()
        best = min(best, (time.perf_counter() - started) / repeat)
    return best * 1e6


def demo_dict_internals() -> dict:
    """Показує порядок вставки, зростання таблиці та правило хешованості."""
    results = {}

    # 1. Порядок вставки зберігається; видалений і доданий знову ключ - в кінці.
    ordered = {"a": 1, "b": 2, "c": 3}
    del ordered["b"]
    ordered["b"] = 4
    results["order"] = list(ordered)
    print_header("[5] Порядок вставки та компактний словник")
    print(f"Ключі після del 'b' і повторної вставки: {results['order']}")

    # 2. Розмір словника росте стрибками при переповненні таблиці.
    print(f"{'Записів':>8}  {'getsizeof, байт':>16}")
    sizes = {}
    probe = {}
    for count in range(0, 45):
        if count:
            probe[f"user{count}"] = count
        if count in (0, 1, 5, 6, 10, 11, 21, 22, 42, 43):
            sizes[count] = sys.getsizeof(probe)
            print(f"{count:>8}  {sizes[count]:>16}")
    results["sizes"] = sizes

    # 3. Хешованість: незмінні об'єкти допустимі, змінні - ні.
    print_header("[6] Хешованість ключів і елементів множини")
    checks = {}
    for label, factory in (("tuple (1, 2)", lambda: (1, 2)),
                           ("frozenset({1, 2})", lambda: frozenset({1, 2})),
                           ("list [1, 2]", lambda: [1, 2]),
                           ("set {1, 2}", lambda: {1, 2})):
        try:
            hash(factory())
            verdict = "хешований, може бути ключем"
            checks[label] = True
        except TypeError as error:
            verdict = f"TypeError: {error}"
            checks[label] = False
        print(f"{label:<20}{verdict}")
    same = hash(frozenset({1, 2, 3})) == hash(frozenset({3, 2, 1}))
    print(f"hash(frozenset({{1,2,3}})) == hash(frozenset({{3,2,1}})): {same}")
    results["hashable"] = checks
    results["frozenset_order_free"] = same

    # 4. get() не змінює словник, setdefault() вставляє значення.
    print_header("[7] get() проти setdefault()")
    sample = {"x": 1}
    got = sample.get("y", 0)
    print(f"get('y', 0)        -> {got}, словник: {sample}")
    put = sample.setdefault("y", 0)
    print(f"setdefault('y', 0) -> {put}, словник: {sample}")
    again = sample.setdefault("y", 99)
    print(f"setdefault('y', 99)-> {again}, значення не перезаписано")
    results["get_vs_setdefault"] = (got, put, again, sample)
    return results


def demo_lookup_time() -> list:
    """Порівнює пошук ключа в словнику та елемента в списку."""
    print_header("[8] Час пошуку: dict O(1) проти list O(N)")
    print(f"{'N':>9}  {'dict, мкс':>11}  {'list, мкс':>11}  {'list/dict':>10}")
    rows = []
    for size in (1_000, 10_000, 100_000):
        keys = [f"user{i}" for i in range(size)]
        table = dict.fromkeys(keys, True)
        target = keys[-1]  # найгірший випадок для лінійного пошуку
        t_dict = time_us(lambda: target in table, 5000)
        t_list = time_us(lambda: target in keys, 20 if size > 10_000 else 200)
        rows.append((size, t_dict, t_list))
        print(f"{size:>9}  {t_dict:>11.4f}  {t_list:>11.2f}  "
              f"{t_list / t_dict:>10.0f}")
    return rows


# ---------------------------------------------------------------------------
# Головна функція
# ---------------------------------------------------------------------------
def main() -> bool:
    started = time.perf_counter()
    db = create_initial_database()

    print_header("[1] Початковий стан бази")
    print_database_report(db)

    print_header("[2] Операції CRUD")
    # Create: новий співробітник відділу IT.
    add_user(db, "v.lysenko", "v.lysenko@corp.example.com", "IT",
             {"vpn_access", "server_admin", "backup_operator", "log_view"})
    print("Додано: v.lysenko (IT)")
    add_user(db, "v.lysenko", "dup@corp.example.com", "IT", set())
    # Update: у m.petrenko забираємо надлишкову роль і змінюємо пошту.
    update_user(db, "m.petrenko",
                email="m.petrenko@corp.example.org",
                roles={"fin_read", "fin_write", "report_view"})
    print("Оновлено: m.petrenko (update: email, roles)")
    update_user(db, "x.unknown", department="IT")
    # Delete: звільненого співробітника видаляємо через pop().
    gone = remove_user(db, "t.bondar")
    print(f"Видалено: t.bondar (відділ {gone['department']})")
    remove_user(db, "t.bondar")
    # Безпечне читання.
    print(f"get(): пошта d.melnyk = {get_attribute(db, 'd.melnyk', 'email')}")
    print(f"get(): телефон d.melnyk = {get_attribute(db, 'd.melnyk', 'phone')}")
    print(f"get(): атрибут неіснуючого x.unknown = "
          f"{get_attribute(db, 'x.unknown', 'email')}")
    first = ensure_manager(db, "d.melnyk")
    db["d.melnyk"]["manager"] = "o.kovalenko"
    second = ensure_manager(db, "d.melnyk", "інший")
    print(f"setdefault(): manager до призначення = {first}, після = {second}")
    del db["d.melnyk"]["manager"]  # повертаємо структуру запису до 4 полів

    print_header("[3] Стан бази після змін")
    print_database_report(db)

    print_header("[4] Інвертований індекс «роль -> користувачі»")
    index = build_role_index(db)
    print_role_index(index)

    internals = demo_dict_internals()
    lookup = demo_lookup_time()

    print_header("[9] Автоматичні перевірки")
    checks = [
        ("у базі 6 записів (6 + 1 додано - 1 видалено)", len(db) == 6),
        ("дублікат v.lysenko не перезаписав запис",
         db["v.lysenko"]["email"] == "v.lysenko@corp.example.com"),
        ("pop() видалив t.bondar", "t.bondar" not in db),
        ("update() змінив пошту m.petrenko",
         db["m.petrenko"]["email"].endswith(".org")),
        ("роль domain_admin зникла з індексу", "domain_admin" not in index),
        ("report_view мають 4 користувачі", len(index["report_view"]) == 4),
        ("індекс узгоджений з базою",
         all(user in db and role in db[user]["roles"]
             for role, users in index.items() for user in users)),
        ("кожен користувач має ролі, що увійшли до індексу",
         all(any(user in users for users in index.values())
             for user in db)),
        ("порядок вставки після del і повторної вставки",
         internals["order"] == ["a", "c", "b"]),
        ("list і set не хешуються, tuple і frozenset хешуються",
         internals["hashable"] == {"tuple (1, 2)": True,
                                   "frozenset({1, 2})": True,
                                   "list [1, 2]": False,
                                   "set {1, 2}": False}),
        ("hash(frozenset) не залежить від порядку",
         internals["frozenset_order_free"]),
        ("setdefault() не перезаписує існуюче значення",
         internals["get_vs_setdefault"][2] == 0),
        ("поле manager прибрано, запис знову має 4 поля",
         all(len(rec) == 4 for rec in db.values())),
        ("пошук у dict швидший за list на 100 000 елементів",
         lookup[-1][2] > 100 * lookup[-1][1]),
    ]
    for text, ok in checks:
        print(f"[{'  OK' if ok else 'FAIL'}] {text}")
    print()
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    print(f"Час виконання повного циклу інвентаризації: {elapsed_ms:.3f} мс")
    return all(ok for _, ok in checks)


if __name__ == "__main__":
    # Гарантуємо UTF-8 у консолі (важливо для Windows).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
