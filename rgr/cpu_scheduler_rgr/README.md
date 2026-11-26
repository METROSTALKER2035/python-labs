# РГР. Симуляція диспетчеризації черги задач процесора (FIFO та Round Robin)

Розрахунково-графічна робота з освітнього компонента «Програмування на Python. Базовий рівень».

- **Студент:** Афанасьєв Сергій Олександрович, група КІ-24-1
- **Керівник:** викладач кафедри комп'ютерної інженерії Вадурін Кирило Олегович
- **Тема (варіант 2):** Система симуляції диспетчеризації черги задач центрального процесора на базі алгоритмів FIFO та Round Robin
- **Мова:** Python 3.10+, лише стандартна бібліотека

## Параметри варіанта

| Параметр | Значення |
|---|---|
| Алгоритми | FIFO (FCFS), Round Robin з квантом часу q |
| Вхідні дані | TXT / CSV / JSON: ідентифікатор, момент надходження, тривалість |
| Показники | час очікування, оборот, відгук, завантаження CPU, пропускна здатність, перемикання контексту |
| Збереження | JSON та CSV через `with` |
| Інтерфейс | командний рядок (`sys.argv`) |

## Структура проєкту

```text
cpu_scheduler_rgr/
├── main.py                 # точка входу (if __name__ == '__main__')
├── README.md               # цей файл
├── .gitignore              # службові файли, які не потрапляють до Git
├── .vscode/
│   └── launch.json         # конфігурації запуску та налагодження у VS Code
├── cpu_scheduler/          # пакет з публічним API через __all__
│   ├── __init__.py         # експорт імен пакета
│   ├── exceptions.py       # ієрархія власних винятків
│   ├── task.py             # клас Task: @property, dunder-методи
│   ├── parser.py           # регулярні вирази: розбір і нормалізація даних
│   ├── schedulers.py       # Scheduler (ABC), FifoScheduler, RoundRobinScheduler
│   ├── metrics.py          # Segment, SimulationResult, показники
│   ├── storage.py          # збереження та завантаження JSON/CSV/TXT
│   ├── reporting.py        # текстові звіти для консолі
│   ├── benchmark.py        # time.perf_counter(), генерація наборів задач
│   └── cli.py              # розбір sys.argv, коди завершення
├── tests/                  # модульні тести unittest
│   ├── test_task.py
│   ├── test_parser.py
│   ├── test_schedulers.py
│   ├── test_storage.py
│   └── test_cli.py
└── data/                   # вхідні набори задач
    ├── tasks_demo.txt      # демонстраційний набір (5 задач)
    ├── tasks_demo.csv      # той самий набір у CSV
    ├── tasks_demo.json     # той самий набір у JSON
    ├── tasks_idle.txt      # набір із простоєм процесора
    ├── tasks_convoy.txt    # ефект конвою (довга задача попереду коротких)
    ├── tasks_bad.txt       # некоректний рядок (аварійний режим)
    └── tasks_dup.txt       # дубльований ідентифікатор
```

## Запуск

Усі команди однакові для PowerShell, cmd та bash; виконуються з кореня проєкту.

```text
python main.py --help
python main.py --input data/tasks_demo.txt --algo both --quantum 2 --gantt
python main.py --input data/tasks_demo.csv --algo rr --quantum 3
python main.py --input data/tasks_demo.json --json result.json --csv result.csv
python main.py --bench 5000
```

Аварійні режими (демонстрація винятків):

```text
python main.py --input data/tasks_bad.txt
python main.py --input data/tasks_dup.txt
python main.py --input data/nofile.txt
python main.py --input data/tasks_demo.txt --algo rr --quantum 0
```

## Тестування

```text
python -m unittest discover -s tests -t . -v
```

## Коди завершення

| Код | Значення |
|---|---|
| 0 | успішне виконання |
| 1 | помилка аргументів командного рядка (включно з некоректним квантом) |
| 2 | помилка даних (формат рядка, дублікат, порожній набір, структура JSON/CSV) |
| 3 | помилка файлової системи (файл не знайдено, неможливо записати) |

## Формат вхідних даних

Один рядок — одна задача: `PID;arrival;burst`. Роздільником може бути `;`, `,` або пробіл. Ідентифікатор — латинська літера та до 7 літер, цифр чи `_`; нормалізується до верхнього регістру. Рядки, що починаються з `#`, порожні рядки та заголовок `pid,arrival,burst` ігноруються.
