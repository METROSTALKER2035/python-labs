"""Ієрархія користувацьких виняткових ситуацій комплексу диспетчеризації."""


class SchedulerError(Exception):
    """Базовий клас усіх помилок комплексу (корінь власної ієрархії)."""

    def __init__(self, message: str = "Помилка планувальника") -> None:
        super().__init__(message)  # передаємо текст батьківському класу
        self.message = message  # зберігаємо текст для доступу у обробниках

    def __str__(self) -> str:
        return self.message  # рядкове подання помилки = її текст


class InvalidTaskError(SchedulerError):
    """Некоректні дані окремої задачі."""


class TaskFormatError(InvalidTaskError):
    """Рядок вхідних даних не відповідає шаблону регулярного виразу."""

    def __init__(self, line_no: int, line: str) -> None:
        super().__init__(f"Рядок {line_no}: невірний формат '{line.strip()}'")
        self.line_no = line_no  # номер рядка у вхідному файлі
        self.line = line  # вихідний текст рядка


class TaskValueError(InvalidTaskError):
    """Значення атрибута задачі виходить за допустимі межі."""


class DuplicateTaskError(InvalidTaskError):
    """У наборі присутні задачі з однаковим ідентифікатором."""


class QuantumError(SchedulerError):
    """Некоректний квант часу для алгоритму Round Robin."""


class EmptyTaskSetError(SchedulerError):
    """Набір задач для моделювання порожній."""


class PersistenceError(SchedulerError):
    """Помилка збереження або завантаження даних."""


class DataFileFormatError(PersistenceError):
    """Файл JSON/CSV має невірну структуру або розширення."""


class CliArgumentError(SchedulerError):
    """Невірні аргументи командного рядка."""
