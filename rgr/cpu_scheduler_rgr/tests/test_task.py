import unittest

from cpu_scheduler import Task, TaskValueError


class TaskTests(unittest.TestCase):
    def test_properties_and_normalization(self):
        task = Task(" p1 ", 2, 5)
        self.assertEqual((task.pid, task.arrival, task.burst, task.remaining), ("P1", 2, 5, 5))

    def test_setter_validation(self):
        task = Task("P1", 0, 1)
        for bad in (-1, 1.5, "3", True):
            with self.assertRaises(TaskValueError):
                task.arrival = bad
        with self.assertRaises(TaskValueError):
            task.burst = 0
        with self.assertRaises(TaskValueError):
            task.pid = "  "

    def test_str_repr_eq_hash(self):
        a, b = Task("P1", 0, 5), Task("p1", 0, 5)
        self.assertEqual(str(a), "P1(arrival=0, burst=5)")
        self.assertEqual(repr(a), "Task(pid='P1', arrival=0, burst=5)")
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertNotEqual(a, Task("P1", 0, 6))
        self.assertNotEqual(a, "P1")

    def test_ordering_and_arithmetic(self):
        a, b, c = Task("B", 1, 4), Task("A", 1, 2), Task("C", 0, 7)
        self.assertEqual(sorted([a, b, c]), [c, b, a])
        self.assertTrue(c < a)
        self.assertEqual(a + b, 6)
        self.assertEqual(a + 3, 7)
        self.assertEqual(sum([a, b, c]), 13)
        self.assertEqual(a - c, 1)
        with self.assertRaises(TypeError):
            _ = a < 5

    def test_run_state(self):
        task = Task("P1", 0, 5)
        self.assertEqual(task.run(2, 3), 2)
        self.assertEqual(task.first_start, 2)
        self.assertFalse(task.is_done)
        task.run(7, 2)
        self.assertTrue(task.is_done)
        self.assertEqual(task.finish, 9)
        with self.assertRaises(TaskValueError):
            task.run(9, 1)
        task.reset()
        self.assertEqual((task.remaining, task.first_start, task.finish), (5, None, None))


if __name__ == "__main__":
    unittest.main()
