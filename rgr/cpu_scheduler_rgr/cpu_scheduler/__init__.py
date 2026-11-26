"""Пакет cpu_scheduler: симуляція диспетчеризації задач процесора (FIFO, Round Robin)."""
from .exceptions import (CliArgumentError, DataFileFormatError, DuplicateTaskError,
                         EmptyTaskSetError, InvalidTaskError, PersistenceError,
                         QuantumError, SchedulerError, TaskFormatError, TaskValueError)
from .metrics import Segment, SimulationResult
from .parser import normalize_algorithm, parse_task_line, parse_tasks
from .schedulers import FifoScheduler, RoundRobinScheduler, Scheduler
from .storage import load_tasks, save_result_csv, save_result_json
from .task import Task

__version__ = "1.0.0"

__all__ = [
    "Task", "Scheduler", "FifoScheduler", "RoundRobinScheduler",
    "Segment", "SimulationResult",
    "parse_task_line", "parse_tasks", "normalize_algorithm",
    "load_tasks", "save_result_json", "save_result_csv",
    "SchedulerError", "InvalidTaskError", "TaskFormatError", "TaskValueError",
    "DuplicateTaskError", "QuantumError", "EmptyTaskSetError",
    "PersistenceError", "DataFileFormatError", "CliArgumentError",
]
