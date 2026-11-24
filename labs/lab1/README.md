# Лабораторна робота №1. Розгортання інфраструктури розробки: Miniconda, VS Code, Git/GitHub та базові режими виконання Python

**Дисципліна:** Програмування мовою Python
**Студент:** Афанасьєв Сергій, група КІ-24-1
**Варіант:** 2
**Університет:** Кременчуцький національний університет імені Михайла Остроградського

## Параметри варіанта 2

| Параметр | Значення |
|---|---|
| Назва | Інспекція версій середовища |
| Параметри | `sys.version_info`, `platform.python_build()`, `sys.hexversion` |
| Очікуваний результат | Аналіз мікроверсії інтерпретатора CPython |

Індивідуальне завдання виконано в модулі `system_diagnostics.py` (функція `inspect_version`):
виведено поля `sys.version_info`, номер і дату збірки з `platform.python_build()`,
розшифровано `sys.hexversion` (формат `0xMMmmPPLS`) побітовими операціями, класифіковано
мікроверсію (`micro`) та виконано перехресні перевірки узгодженості всіх джерел версії.
Еталонна частина звіту містить метадані платформи, розміри об'єктів (`sys.getsizeof`) та
перевірку кешу малих цілих `[-5, 256]`.

## Структура

```
lab1/
├── .vscode/
│   ├── launch.json                # Конфігурація запуску налагоджувача для ЛБ №1
│   └── settings.json              # Налаштування менеджера середовищ VS Code (conda)
├── .gitignore                     # Правила виключення тимчасових файлів
├── environment.yml                # Опис Conda-середовища ce_lab_env (Python 3.10)
├── system_diagnostics.py          # Діагностичний модуль, індивідуальне завдання варіанта 2
├── test_system_diagnostics.py     # Модульні тести (unittest)
├── exploration_notebook.ipynb     # Ноутбук: шлях ядра, π за рядом Лейбніца, варіант 2
└── README.md                      # Короткий звіт з описом параметрів варіанта
```

## Запуск

```bash
conda env create -f environment.yml
conda activate ce_lab_env
python system_diagnostics.py
python system_diagnostics.py --json
python -m unittest -v
```
