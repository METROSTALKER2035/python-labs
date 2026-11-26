"""Точка входу: python main.py --input data/tasks_demo.txt --algo both --quantum 2"""
import sys

from cpu_scheduler.cli import main

if __name__ == "__main__":  # захищена точка входу
    if hasattr(sys.stdout, "reconfigure"):  # UTF-8 у консолі Windows
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
