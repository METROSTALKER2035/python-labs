# -*- coding: utf-8 -*-
"""
Лабораторна робота №7, варіант 2 (метрики надійності вузлів).
Автор: Афанасьєв Сергій, група КІ-24-1.

Модуль містить:
  * калькулятор метрик надійності зі змінною сигнатурою
    calculate_reliability_metrics(*nodes, **options): дані вузлів приходять
    через *args, параметри розрахунку - через **kwargs зі значеннями за
    замовчуванням, некоректні записи відхиляються з причиною;
  * багатокритеріальне lambda-сортування вузлів: CPU_Usage за спаданням,
    а за рівних значень RAM_Free за зростанням;
  * конвеєр filter/map з lambda-виразами;
  * демонстрації для теорії: передача аргументів, правило LEGB, global і
    nonlocal, UnboundLocalError, типи *args та **kwargs, обмеження lambda.
"""
import math
import sys
import time
from typing import NamedTuple, Optional, Union

REPORT_WIDTH = 98
SEPARATOR = "-" * REPORT_WIDTH
INF = float("inf")

# Значення за замовчуванням для **options (приклад застосування kwargs).
DEFAULT_OPTIONS = {
    "mttr_hours": 2.0,   # середній час відновлення вузла, год
    "cpu_limit": 90.0,   # поріг перевантаження процесора, %
}


class NodeRecord(NamedTuple):
    """Коректний запис про вузол (після валідації)."""
    node_id: str
    cpu_usage: float      # завантаження CPU, %
    ram_free_mb: int      # вільна оперативна пам'ять, МБ
    uptime_hours: float   # напрацювання за період, год
    failures: int         # кількість відмов за період


class NodeMetrics(NamedTuple):
    """Запис вузла разом з розрахованими метриками надійності."""
    node_id: str
    cpu_usage: float
    ram_free_mb: int
    uptime_hours: float
    failures: int
    mtbf: float           # середнє напрацювання на відмову, год (inf без відмов)
    failure_rate: float   # інтенсивність відмов lambda = failures / uptime
    availability: float   # коефіцієнт готовності A = MTBF / (MTBF + MTTR)


# ---------------------------------------------------------------------------
# Валідація та розрахунок
# ---------------------------------------------------------------------------
def _is_number(value) -> bool:
    """Число, але не bool (True - це int у Python, але тут воно не підходить)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_node(raw) -> Union[NodeRecord, str]:
    """Перевіряє один запис. Повертає NodeRecord або текст причини відмови."""
    if not isinstance(raw, (tuple, list)) or len(raw) != 5:
        return "очікується кортеж із 5 полів"
    node_id, cpu, ram, uptime, failures = raw
    if not isinstance(node_id, str) or not node_id.strip():
        return "node_id має бути непорожнім рядком"
    if not _is_number(cpu) or not 0.0 <= cpu <= 100.0:  # NaN не проходить
        return "CPU_Usage має бути числом 0..100 %"
    if isinstance(ram, bool) or not isinstance(ram, int) or ram < 0:
        return "RAM_Free має бути цілим числом >= 0"
    if not _is_number(uptime) or not math.isfinite(uptime) or uptime <= 0:
        return "Uptime має бути додатним числом"
    if (isinstance(failures, bool) or not isinstance(failures, int)
            or failures < 0):
        return "Failures має бути цілим числом >= 0"
    return NodeRecord(node_id.strip(), float(cpu), ram, float(uptime), failures)


def compute_metrics(record: NodeRecord, mttr_hours: float) -> NodeMetrics:
    """MTBF = Uptime / Failures; A = MTBF / (MTBF + MTTR) = 1 / (1 + lambda*MTTR)."""
    rate = record.failures / record.uptime_hours
    mtbf = INF if record.failures == 0 else record.uptime_hours / record.failures
    availability = 1.0 / (1.0 + rate * mttr_hours)
    return NodeMetrics(*record, mtbf=mtbf, failure_rate=rate,
                       availability=availability)


def sort_nodes(nodes):
    """CPU_Usage за спаданням, а за рівних значень RAM_Free за зростанням."""
    return sorted(nodes, key=lambda n: (-n.cpu_usage, n.ram_free_mb))


def calculate_reliability_metrics(*nodes, **options) -> dict:
    """Калькулятор метрик надійності зі змінною сигнатурою.

    Параметри:
        *nodes   - записи (node_id, cpu_usage, ram_free_mb, uptime_hours,
                   failures); кількість довільна, збираються в кортеж;
        **options - mttr_hours (за замовчуванням 2.0) і cpu_limit (90.0);
                   невідомі ключі відхиляються з TypeError.

    Повертає словник з ключами nodes (відсортовані NodeMetrics), rejected
    (позиція, запис, причина), summary та options.
    """
    unknown = sorted(set(options) - set(DEFAULT_OPTIONS))
    if unknown:
        raise TypeError(f"невідомі параметри: {', '.join(unknown)}")
    settings = {**DEFAULT_OPTIONS, **options}  # значення за замовчуванням
    mttr, limit = settings["mttr_hours"], settings["cpu_limit"]
    if not _is_number(mttr) or not math.isfinite(mttr) or mttr < 0:
        raise ValueError("mttr_hours має бути числом >= 0")
    if not _is_number(limit) or not 0 < limit <= 100:
        raise ValueError("cpu_limit має бути числом у діапазоні (0, 100]")

    valid, rejected = [], []
    for position, raw in enumerate(nodes, start=1):
        checked = validate_node(raw)
        if isinstance(checked, str):
            rejected.append((position, raw, checked))
        else:
            valid.append(compute_metrics(checked, settings["mttr_hours"]))

    ordered = sort_nodes(valid)
    total_uptime = sum(n.uptime_hours for n in ordered)
    total_failures = sum(n.failures for n in ordered)
    fleet_rate = total_failures / total_uptime if total_uptime else 0.0
    summary = {
        "accepted": len(ordered),
        "rejected": len(rejected),
        "total_uptime": total_uptime,
        "total_failures": total_failures,
        "fleet_mtbf": INF if total_failures == 0 else total_uptime / total_failures,
        "fleet_availability": 1.0 / (1.0 + fleet_rate * settings["mttr_hours"]),
        "mean_cpu": (sum(n.cpu_usage for n in ordered) / len(ordered)
                     if ordered else 0.0),
        "overloaded": [n.node_id for n in
                       filter(lambda n: n.cpu_usage > limit, ordered)],
    }
    return {"nodes": ordered, "rejected": rejected, "summary": summary,
            "options": settings}


def build_sample_nodes() -> list:
    """Тестові дані: коректні вузли (з рівними CPU і RAM) та хибні записи."""
    return [
        ("srv-app01", 78.5, 2048, 720.0, 1),
        ("srv-app02", 78.5, 1024, 695.5, 2),     # рівний CPU: менше RAM - раніше
        ("srv-db01", 91.2, 4096, 720.0, 0),
        ("srv-db02", 91.2, 8192, 710.0, 1),
        ("srv-web01", 45.0, 3072, 720.0, 0),
        ("srv-web02", 45.0, 3072, 650.0, 3),     # рівні CPU і RAM: порядок збережено
        ("srv-cache1", 63.4, 512, 480.0, 4),
        ("srv-mq01", 12.8, 6144, 720.0, 0),
        ("srv-bk01", 33.3, 1536, 300.0, 1),
        ("srv-bad1", 140.0, 1024, 100.0, 1),     # CPU > 100 %
        ("srv-bad2", 50.0, -5, 100.0, 0),        # від'ємна RAM
        ("srv-bad3", 50.0, 1024, 0, 0),          # нульове напрацювання
        ("srv-bad4", 50.0, 1024),                # лише три поля
    ]


# ---------------------------------------------------------------------------
# Форматування звітів
# ---------------------------------------------------------------------------
def print_header(title: str) -> None:
    print()
    print(title)
    print(SEPARATOR)


def format_mtbf(value: float) -> str:
    return "inf" if value == INF else f"{value:.1f}"


def print_metrics_table(nodes) -> None:
    print(f"{'#':>2}  {'Вузол':<12}{'CPU, %':>7}{'RAM, МБ':>9}{'Uptime, год':>12}"
          f"{'Відмов':>8}{'MTBF, год':>11}{'A, %':>9}")
    print(SEPARATOR)
    for place, n in enumerate(nodes, start=1):
        print(f"{place:>2}  {n.node_id:<12}{n.cpu_usage:>7.1f}{n.ram_free_mb:>9}"
              f"{n.uptime_hours:>12.1f}{n.failures:>8}{format_mtbf(n.mtbf):>11}"
              f"{n.availability * 100:>9.3f}")
    print(SEPARATOR)


def print_rejected(rejected) -> None:
    for position, raw, reason in rejected:
        print(f"Попередження: запис №{position} відхилено: {reason}")
        print(f"    дані: {raw!r}")


def print_summary(result: dict) -> None:
    s, opt = result["summary"], result["options"]
    print(f"Прийнято записів: {s['accepted']}, відхилено: {s['rejected']}")
    print(f"Параметри: MTTR = {opt['mttr_hours']} год, "
          f"поріг CPU = {opt['cpu_limit']} %")
    print(f"Сумарне напрацювання: {s['total_uptime']:.1f} год, "
          f"відмов: {s['total_failures']}")
    print(f"MTBF парку: {format_mtbf(s['fleet_mtbf'])} год, "
          f"готовність парку: {s['fleet_availability'] * 100:.3f} %")
    print(f"Середнє завантаження CPU: {s['mean_cpu']:.2f} %")
    print(f"Перевантажені вузли (CPU > {opt['cpu_limit']} %): "
          f"{', '.join(s['overloaded']) or 'немає'}")


# ---------------------------------------------------------------------------
# Демонстрації для теорії
# ---------------------------------------------------------------------------
_COUNTER = 0  # глобальна змінна для демонстрації global


def demo_namespaces() -> dict:
    """Передача об'єктів, LEGB, global/nonlocal, UnboundLocalError."""
    out = {}

    # 1. Передача за посиланням на об'єкт.
    def bump(number, items, other):
        number += 1                 # перез'язує локальне ім'я, int незмінний
        items.append("x")           # змінює спільний об'єкт
        other = other + ["y"]       # створює новий список, зовнішній не змінюється
        return number, items, other

    n, lst, lst2 = 10, ["a"], ["a"]
    bump(n, lst, lst2)
    out["int_unchanged"] = n == 10
    out["append_visible"] = lst == ["a", "x"]
    out["rebind_invisible"] = lst2 == ["a"]
    print(f"Після виклику: n = {n}, lst = {lst}, lst2 = {lst2}")

    # 2. LEGB: Local -> Enclosing -> Global -> Built-in.
    level = "global"

    def outer():
        level = "enclosing"

        def inner():
            return level            # знайдено в Enclosing

        def inner_local():
            level = "local"
            return level

        return inner(), inner_local(), len("abc")   # len - Built-in

    found = outer()
    out["legb"] = found == ("enclosing", "local", 3)
    print(f"LEGB: inner -> {found[0]}, local -> {found[1]}, "
          f"built-in len('abc') -> {found[2]}, глобальна level = {level}")

    # 3. global і nonlocal.
    def bump_global():
        global _COUNTER
        _COUNTER += 1

    def make_counter():
        count = 0

        def step():
            nonlocal count
            count += 1
            return count
        return step

    bump_global()
    bump_global()
    step = make_counter()
    step()
    out["global_nonlocal"] = (_COUNTER, step()) == (2, 2)
    print(f"global: _COUNTER = {_COUNTER}; nonlocal: лічильник замикання = 2")

    # 4. UnboundLocalError: ім'я присвоюється в тілі, тому воно локальне.
    def broken():
        value = _COUNTER + 1        # _COUNTER вважається локальним нижче
        _COUNTER = value            # noqa: F841
        return value

    try:
        broken()
        out["unbound"] = False
    except UnboundLocalError as error:
        out["unbound"] = True
        print(f"UnboundLocalError: {error}")

    # 5. Типи *args та **kwargs.
    def probe(*args, **kwargs):
        return type(args).__name__, type(kwargs).__name__

    out["varargs_types"] = probe(1, 2, a=3) == ("tuple", "dict")
    print(f"*args -> {probe(1, 2, a=3)[0]}, **kwargs -> {probe(1, 2, a=3)[1]}")

    # 6. Lambda: об'єкт функції без імені, лише вираз.
    square = lambda x: x * x        # noqa: E731
    out["lambda_name"] = square.__name__ == "<lambda>"
    try:
        compile("lambda x: (y = x)", "<demo>", "eval")
        out["lambda_no_statements"] = False
    except SyntaxError:
        out["lambda_no_statements"] = True
    late = [lambda: i for i in range(3)]
    early = [lambda i=i: i for i in range(3)]
    out["late_binding"] = [f() for f in late] == [2, 2, 2]
    out["early_binding"] = [f() for f in early] == [0, 1, 2]
    print(f"lambda.__name__ = {square.__name__!r}; присвоєння у lambda - SyntaxError")
    print(f"Пізнє зв'язування: {[f() for f in late]}, "
          f"значення за замовчуванням: {[f() for f in early]}")
    return out


# ---------------------------------------------------------------------------
# Головна функція
# ---------------------------------------------------------------------------
def main() -> bool:
    started = time.perf_counter()
    raw_nodes = build_sample_nodes()

    print_header("[1] Вхідні дані та валідація (*args)")
    print(f"Передано записів через *nodes: {len(raw_nodes)}")
    result = calculate_reliability_metrics(*raw_nodes)
    print_rejected(result["rejected"])
    print(f"Коректних записів: {result['summary']['accepted']}")

    print_header("[2] Метрики надійності, CPU за спаданням, RAM за зростанням")
    print_metrics_table(result["nodes"])

    print_header("[3] Підсумок за парком вузлів")
    print_summary(result)

    print_header("[4] Параметри **options")
    custom = calculate_reliability_metrics(*raw_nodes, mttr_hours=8.0,
                                           cpu_limit=75.0)
    print(f"mttr_hours = 8.0: готовність парку "
          f"{custom['summary']['fleet_availability'] * 100:.3f} % "
          f"(за замовчуванням {result['summary']['fleet_availability'] * 100:.3f} %)")
    print(f"cpu_limit = 75.0: перевантажені вузли: "
          f"{', '.join(custom['summary']['overloaded'])}")
    errors = []
    for bad in ({"speed": 1}, {"mttr_hours": -1}, {"cpu_limit": 0}):
        try:
            calculate_reliability_metrics(*raw_nodes, **bad)
        except (TypeError, ValueError) as error:
            errors.append(type(error).__name__)
            print(f"{bad} -> {type(error).__name__}: {error}")
    empty = calculate_reliability_metrics()
    print(f"Без вузлів: прийнято {empty['summary']['accepted']}, "
          f"готовність парку {empty['summary']['fleet_availability'] * 100:.1f} %")

    print_header("[5] Lambda-сортування, стійкість, filter/map")
    nodes = result["nodes"]
    two_pass = sorted(sorted(nodes, key=lambda n: n.ram_free_mb),
                      key=lambda n: n.cpu_usage, reverse=True)
    short = lambda seq: ", ".join(n.node_id.removeprefix("srv-") for n in seq)
    print(f"Ключ (-CPU, RAM):   {short(nodes)}")
    print(f"Два проходи sorted: {short(two_pass)}")
    print(f"Результати збігаються: {nodes == two_pass}")
    fast = list(map(lambda n: f"{n.node_id}:{n.availability * 100:.2f}",
                    filter(lambda n: n.failures == 0, nodes)))
    print(f"Вузли без відмов (filter + map, A, %): {', '.join(fast)}")
    worst = min(nodes, key=lambda n: n.availability)
    print(f"Найнижча готовність: {worst.node_id} "
          f"({worst.availability * 100:.3f} %), "
          f"MTBF {format_mtbf(worst.mtbf)} год")

    print_header("[6] Простори імен, LEGB, *args/**kwargs, lambda")
    scopes = demo_namespaces()

    print_header("[7] Автоматичні перевірки")
    ids = [n.node_id for n in nodes]
    by_id = {n.node_id: n for n in nodes}
    checks = [
        ("9 коректних і 4 відхилені записи",
         result["summary"]["accepted"] == 9 and result["summary"]["rejected"] == 4),
        ("порядок: CPU за спаданням, за рівних CPU - RAM за зростанням",
         ids == ["srv-db01", "srv-db02", "srv-app02", "srv-app01", "srv-cache1",
                 "srv-web01", "srv-web02", "srv-bk01", "srv-mq01"]),
        ("lambda-сортування = двопрохідному (стійкість)", nodes == two_pass),
        ("повністю рівні за CPU та RAM вузли зберігають вхідний порядок",
         ids.index("srv-web01") < ids.index("srv-web02")),
        ("MTBF srv-app02 = 695.5 / 2 = 347.75 год",
         abs(by_id["srv-app02"].mtbf - 347.75) < 1e-9),
        ("вузол без відмов: MTBF = inf, готовність 100 %",
         by_id["srv-db01"].mtbf == INF and by_id["srv-db01"].availability == 1.0),
        ("A(srv-cache1) = 1 / (1 + 4/480 * 2) = 0.98361",
         abs(by_id["srv-cache1"].availability - 1 / (1 + 4 / 480 * 2)) < 1e-12),
        ("перевантажені вузли: srv-db01, srv-db02",
         result["summary"]["overloaded"] == ["srv-db01", "srv-db02"]),
        ("невідомий параметр і хибні значення викликають помилки",
         errors == ["TypeError", "ValueError", "ValueError"]),
        ("порожній виклик не падає", empty["summary"]["accepted"] == 0),
        ("int не змінюється, append видно, перез'язування не видно",
         scopes["int_unchanged"] and scopes["append_visible"]
         and scopes["rebind_invisible"]),
        ("LEGB, global і nonlocal працюють як очікувано",
         scopes["legb"] and scopes["global_nonlocal"]),
        ("виявлено UnboundLocalError", scopes["unbound"]),
        ("*args - tuple, **kwargs - dict", scopes["varargs_types"]),
        ("lambda: ім'я <lambda>, без операторів, пізнє зв'язування",
         scopes["lambda_name"] and scopes["lambda_no_statements"]
         and scopes["late_binding"] and scopes["early_binding"]),
    ]
    for text, ok in checks:
        print(f"[{'  OK' if ok else 'FAIL'}] {text}")
    print()
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    print(f"Час виконання функціонального конвеєра: {elapsed_ms:.3f} мс")
    return all(ok for _, ok in checks)


if __name__ == "__main__":
    # Гарантуємо UTF-8 у консолі (важливо для Windows).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
