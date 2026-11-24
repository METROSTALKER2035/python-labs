# -*- coding: utf-8 -*-
"""
Лабораторна робота №6, варіант 2 (облікові записи Active Directory).
Автор: Афанасьєв Сергій, група КІ-24-1.

Модуль виконує аудит прав і аналіз подій входу:
  * шаблони прав за відділами зберігаються у незмінних множинах frozenset;
  * фактичні права користувача порівнюються з шаблоном: перетин (законні
    права), різниця A \\ B (надлишкові права), різниця B \\ A (відсутні
    обов'язкові права), індекс Жаккара J(A, B) = |A & B| / |A | B|;
  * події входу рахує collections.Counter, топ облікових записів дає
    most_common();
  * демонстрації для теорії: методи множин «на місці» та з новим об'єктом,
    швидкість Counter порівняно зі звичайним словником.
"""
import random
import sys
import time
from collections import Counter, defaultdict

from network_inventory import create_initial_database

REPORT_WIDTH = 98
SEPARATOR = "-" * REPORT_WIDTH

# Еталонні набори прав за відділами (шаблон посади). frozenset не можна
# змінити випадково: add(), remove() та інші змінні методи в нього відсутні.
ROLE_TEMPLATES = {
    "Accounting": frozenset({"fin_read", "fin_write", "report_view"}),
    "IT": frozenset({"vpn_access", "server_admin", "backup_operator",
                     "log_view"}),
    "HR": frozenset({"hr_read", "hr_write", "report_view"}),
    "Sales": frozenset({"crm_read", "crm_write", "report_view"}),
}


# ---------------------------------------------------------------------------
# Аудит прав (множини)
# ---------------------------------------------------------------------------
def jaccard_index(actual: set, baseline: frozenset) -> float:
    """Індекс Жаккара; для двох порожніх множин за означенням дорівнює 1.0."""
    union = actual | baseline
    if not union:
        return 1.0
    return len(actual & baseline) / len(union)


def audit_user_rights(actual: set, baseline: frozenset) -> dict:
    """Порівнює фактичні права A з еталонним шаблоном B.

    Повертає законні права (A & B), надлишкові (A - B), відсутні (B - A)
    та індекс Жаккара.
    """
    return {
        "compliant": sorted(actual & baseline),
        "excess": sorted(actual - baseline),
        "missing": sorted(baseline - actual),
        "jaccard": jaccard_index(actual, baseline),
    }


def audit_directory(db: dict) -> dict:
    """Аудит усіх записів бази; ключ результату - ім'я користувача."""
    results = {}
    for username, record in db.items():
        template = ROLE_TEMPLATES.get(record["department"], frozenset())
        result = audit_user_rights(record["roles"], template)
        result["department"] = record["department"]
        result["is_active"] = record["is_active"]
        results[username] = result
    return results


# ---------------------------------------------------------------------------
# Події входу (Counter)
# ---------------------------------------------------------------------------
def build_login_events(seed: int = 6) -> list:
    """Формує детермінований потік подій входу (ім'я користувача на подію).

    Містить звичайних користувачів, вимкнений обліковий запис t.bondar і
    обліковий запис guest.temp, якого немає в каталозі.
    """
    counts = {"o.kovalenko": 12, "i.shevchenko": 9, "m.petrenko": 7,
              "d.melnyk": 5, "guest.temp": 4, "n.savchenko": 3,
              "t.bondar": 2}
    events = [user for user, number in counts.items() for _ in range(number)]
    random.Random(seed).shuffle(events)
    return events


def count_logins(events: list) -> Counter:
    """Лічильник входів за користувачем."""
    return Counter(events)


def find_suspicious_logins(counter: Counter, db: dict) -> dict:
    """Входи вимкнених і невідомих облікових записів."""
    return {
        "disabled": {u: n for u, n in counter.items()
                     if u in db and not db[u]["is_active"]},
        "unknown": {u: n for u, n in counter.items() if u not in db},
    }


# ---------------------------------------------------------------------------
# Звіти
# ---------------------------------------------------------------------------
def print_header(title: str) -> None:
    print()
    print(title)
    print(SEPARATOR)


def print_templates() -> None:
    print(f"{'Відділ':<12}{'Прав':>5}  Шаблон (frozenset)")
    print(SEPARATOR)
    for department, template in ROLE_TEMPLATES.items():
        print(f"{department:<12}{len(template):>5}  "
              f"{', '.join(sorted(template))}")
    print(SEPARATOR)


def print_audit_report(results: dict) -> None:
    print(f"{'Користувач':<14}{'Відділ':<12}{'Надлишкові':<14}"
          f"{'Відсутні':<28}{'J, %':>8}")
    print(SEPARATOR)
    for username, res in results.items():
        excess = ", ".join(res["excess"]) or "-"
        missing = ", ".join(res["missing"]) or "-"
        print(f"{username:<14}{res['department']:<12}{excess:<14}"
              f"{missing:<28}{res['jaccard'] * 100:>8.2f}")
    print(SEPARATOR)
    if not results:
        print("Облікових записів для аудиту немає")
        return
    mean = sum(r["jaccard"] for r in results.values()) / len(results)
    print(f"Середня відповідність шаблонам: {mean * 100:.2f} %")


def print_login_report(counter: Counter, top: int = 3) -> None:
    total = sum(counter.values())
    if total == 0:
        print("Подій входу немає")
        return
    print(f"Усього подій входу: {total}, облікових записів: {len(counter)}")
    print(f"{'#':>2}  {'Користувач':<14}{'Входів':>7}{'Частка':>10}")
    print(SEPARATOR)
    for place, (user, number) in enumerate(counter.most_common(top), 1):
        print(f"{place:>2}  {user:<14}{number:>7}{number / total:>10.2%}")
    print(SEPARATOR)


# ---------------------------------------------------------------------------
# Демонстрації для теорії
# ---------------------------------------------------------------------------
def demo_set_methods() -> dict:
    """Методи множин «на місці» проти методів, що повертають нову множину."""
    base = {1, 2, 3, 4, 5}
    other = {4, 5, 6}
    ident = id(base)
    size_before = sys.getsizeof(base)

    new = base - other  # оператор повертає новий об'єкт
    new2 = base.difference(other)
    print(f"base - other           -> {sorted(new)}, id збігається з base: "
          f"{id(new) == ident}")
    print(f"base.difference(other) -> {sorted(new2)}, id збігається з base: "
          f"{id(new2) == ident}")
    print(f"base після операторів: {sorted(base)} (не змінено)")

    result = base.difference_update(other)  # змінює сам об'єкт
    print(f"base.difference_update(other) -> {result}, base: "
          f"{sorted(base)}, id збігається: {id(base) == ident}")
    base |= {7, 8}  # те саме, що base.update({7, 8})
    print(f"base |= {{7, 8}}         -> {sorted(base)}, id збігається: "
          f"{id(base) == ident}")

    frozen = frozenset({1, 2})
    frozen_immutable = False
    try:
        frozen.add(3)
    except AttributeError as error:
        frozen_immutable = True
        print(f"frozenset.add(3) -> AttributeError: {error}")
    merged = frozen | {3}
    print(f"frozenset | {{3}} -> {type(merged).__name__} {sorted(merged)}")
    return {
        "operators_new_object": id(new) != ident and id(new2) != ident,
        "inplace_same_object": id(base) == ident,
        "difference_update_returns_none": result is None,
        "base_final": sorted(base),
        "size_before": size_before,
        "frozen_immutable": frozen_immutable,
        "frozen_op_type": type(merged).__name__,
    }


def best_time_ms(func, series: int = 5) -> float:
    """Найкращий із кількох вимірів, мс."""
    best = float("inf")
    for _ in range(series):
        started = time.perf_counter()
        func()
        best = min(best, time.perf_counter() - started)
    return best * 1000.0


def demo_counter_speed() -> dict:
    """Порівнює три способи підрахунку частот на великому потоці подій."""
    users = [f"user{i:03d}" for i in range(500)]
    rng = random.Random(1)
    sizes = (50_000, 200_000, 800_000)
    print(f"{'Подій':>9}  {'dict.get':>10}  {'defaultdict':>12}  "
          f"{'Counter':>9}  {'dict/Counter':>13}")
    rows = []
    for size in sizes:
        stream = [rng.choice(users) for _ in range(size)]

        def with_dict():
            freq = {}
            for item in stream:
                freq[item] = freq.get(item, 0) + 1
            return freq

        def with_defaultdict():
            freq = defaultdict(int)
            for item in stream:
                freq[item] += 1
            return freq

        def with_counter():
            return Counter(stream)

        t_dict = best_time_ms(with_dict, 3)
        t_def = best_time_ms(with_defaultdict, 3)
        t_cnt = best_time_ms(with_counter, 3)
        assert with_dict() == dict(with_counter())
        rows.append((size, t_dict, t_def, t_cnt))
        print(f"{size:>9}  {t_dict:>8.2f}мс  {t_def:>10.2f}мс  "
              f"{t_cnt:>7.2f}мс  {t_dict / t_cnt:>13.2f}")
    return {"rows": rows}


# ---------------------------------------------------------------------------
# Головна функція
# ---------------------------------------------------------------------------
def main() -> bool:
    started = time.perf_counter()
    db = create_initial_database()

    print_header("[1] Шаблони прав за відділами")
    print_templates()

    print_header("[2] Аудит прав користувачів (множини)")
    audit = audit_directory(db)
    print_audit_report(audit)

    print_header("[3] Події входу (Counter): найактивніші облікові записи")
    events = build_login_events()
    counter = count_logins(events)
    print_login_report(counter, 3)
    suspicious = find_suspicious_logins(counter, db)
    for user, number in suspicious["disabled"].items():
        print(f"УВАГА: вимкнений обліковий запис {user} має {number} входи")
    for user, number in suspicious["unknown"].items():
        print(f"УВАГА: невідомий обліковий запис {user} має {number} входи")

    print_header("[4] Методи множин: нова множина чи зміна на місці")
    sets_info = demo_set_methods()

    print_header("[5] Швидкість підрахунку: dict, defaultdict, Counter")
    speed = demo_counter_speed()

    print_header("[6] Автоматичні перевірки")
    checks = [
        ("o.kovalenko повністю відповідає шаблону (J = 1)",
         audit["o.kovalenko"]["jaccard"] == 1.0),
        ("m.petrenko: надлишкова роль domain_admin, J = 0.75",
         audit["m.petrenko"]["excess"] == ["domain_admin"]
         and audit["m.petrenko"]["jaccard"] == 0.75),
        ("i.shevchenko: 1 надлишкова, 2 відсутні, J = 0.4",
         audit["i.shevchenko"]["excess"] == ["report_view"]
         and audit["i.shevchenko"]["missing"] == ["backup_operator", "log_view"]
         and abs(audit["i.shevchenko"]["jaccard"] - 0.4) < 1e-12),
        ("n.savchenko: відсутні crm_write і report_view, J = 1/3",
         audit["n.savchenko"]["missing"] == ["crm_write", "report_view"]
         and abs(audit["n.savchenko"]["jaccard"] - 1 / 3) < 1e-12),
        ("законні права = перетин, а A | B = перетин + надлишок + відсутні",
         all(len(r["compliant"]) + len(r["excess"]) + len(r["missing"])
             == len(db[u]["roles"] | ROLE_TEMPLATES[db[u]["department"]])
             for u, r in audit.items())),
        ("J(порожня, порожня) = 1.0",
         jaccard_index(set(), frozenset()) == 1.0),
        ("J(A, порожня B) = 0.0", jaccard_index({"x"}, frozenset()) == 0.0),
        ("топ-3 за входами: o.kovalenko, i.shevchenko, m.petrenko",
         [u for u, _ in counter.most_common(3)]
         == ["o.kovalenko", "i.shevchenko", "m.petrenko"]),
        ("o.kovalenko має 12 входів із 42", counter["o.kovalenko"] == 12
         and sum(counter.values()) == 42),
        ("Counter повертає 0 для відсутнього ключа", counter["nobody"] == 0),
        ("виявлено вимкнений t.bondar і невідомий guest.temp",
         suspicious == {"disabled": {"t.bondar": 2},
                        "unknown": {"guest.temp": 4}}),
        ("оператор різниці створює новий об'єкт",
         sets_info["operators_new_object"]),
        ("difference_update() змінює об'єкт на місці й повертає None",
         sets_info["inplace_same_object"]
         and sets_info["difference_update_returns_none"]
         and sets_info["base_final"] == [1, 2, 3, 7, 8]),
        ("frozenset не має змінних методів; frozenset | set дає frozenset",
         sets_info["frozen_immutable"]
         and sets_info["frozen_op_type"] == "frozenset"),
        ("Counter швидший за dict.get на найбільшому потоці",
         speed["rows"][-1][3] < speed["rows"][-1][1]),
    ]
    for text, ok in checks:
        print(f"[{'  OK' if ok else 'FAIL'}] {text}")
    print()
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    print(f"Час виконання повного циклу аудиту: {elapsed_ms:.3f} мс")
    return all(ok for _, ok in checks)


if __name__ == "__main__":
    # Гарантуємо UTF-8 у консолі (важливо для Windows).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
