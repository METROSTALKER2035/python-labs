import unittest

from cpu_scheduler import (CliArgumentError, DuplicateTaskError, EmptyTaskSetError,
                           TaskFormatError, TaskValueError, normalize_algorithm,
                           parse_task_line, parse_tasks)


class ParserTests(unittest.TestCase):
    def test_separators(self):
        for line in ("p1;0;5", "P1,0,5", "P1 0 5", "  p1 ;  0 ; 5  # коментар"):
            task = parse_task_line(line)
            self.assertEqual((task.pid, task.arrival, task.burst), ("P1", 0, 5))

    def test_skipped_lines(self):
        for line in ("", "   ", "# коментар", "pid,arrival,burst"):
            self.assertIsNone(parse_task_line(line))

    def test_bad_format(self):
        for line in ("P1;0", "P1;a;5", "1P;0;5", "P1;0;5;7", "P1;-1;5"):
            with self.assertRaises(TaskFormatError):
                parse_task_line(line, 3)

    def test_error_carries_line_number(self):
        with self.assertRaises(TaskFormatError) as ctx:
            parse_tasks(["P1;0;5", "oops"])
        self.assertEqual(ctx.exception.line_no, 2)
        self.assertIn("Рядок 2", str(ctx.exception))

    def test_zero_burst_rejected_by_model(self):
        with self.assertRaises(TaskValueError):
            parse_task_line("P1;0;0")

    def test_duplicates_and_empty(self):
        with self.assertRaises(DuplicateTaskError):
            parse_tasks(["P1;0;5", "p1;1;2"])
        with self.assertRaises(EmptyTaskSetError):
            parse_tasks(["# нічого", ""])

    def test_normalize_algorithm(self):
        self.assertEqual(normalize_algorithm(" FCFS "), "fifo")
        self.assertEqual(normalize_algorithm("Round-Robin"), "rr")
        self.assertEqual(normalize_algorithm("round_robin"), "rr")
        self.assertEqual(normalize_algorithm("ALL"), "both")
        with self.assertRaises(CliArgumentError):
            normalize_algorithm("sjf")


if __name__ == "__main__":
    unittest.main()
