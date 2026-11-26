import unittest

from cpu_scheduler import (EmptyTaskSetError, FifoScheduler, QuantumError,
                           RoundRobinScheduler, Scheduler, Segment, Task)
from cpu_scheduler.benchmark import generate_tasks


def demo():
    return [Task("P1", 0, 5), Task("P2", 1, 3), Task("P3", 2, 8),
            Task("P4", 3, 2), Task("P5", 4, 4)]


def rows(result):
    return {row["pid"]: row for row in result.per_task()}


class FifoTests(unittest.TestCase):
    def test_hand_computed_values(self):
        res = FifoScheduler().run(demo())
        self.assertEqual([r["finish"] for r in res.per_task()], [5, 8, 16, 18, 22])
        self.assertEqual([r["waiting"] for r in res.per_task()], [0, 4, 6, 13, 14])
        self.assertAlmostEqual(res.avg_waiting, 7.4)
        self.assertAlmostEqual(res.avg_turnaround, 11.8)
        self.assertEqual(res.context_switches, 4)
        self.assertEqual(res.makespan, 22)

    def test_order_independent_of_input_order(self):
        shuffled = list(reversed(demo()))
        self.assertEqual(FifoScheduler().run(shuffled).summary(),
                         FifoScheduler().run(demo()).summary())

    def test_idle_interval(self):
        res = FifoScheduler().run([Task("A", 0, 3), Task("B", 10, 2)])
        self.assertEqual(res.segments[1], Segment("IDLE", 3, 10))
        self.assertEqual(res.makespan, 12)
        self.assertAlmostEqual(res.cpu_utilization, 100 * 5 / 12)

    def test_input_tasks_not_mutated(self):
        tasks = demo()
        FifoScheduler().run(tasks)
        self.assertTrue(all(t.remaining == t.burst and t.finish is None for t in tasks))


class RoundRobinTests(unittest.TestCase):
    def test_hand_computed_gantt_q2(self):
        res = RoundRobinScheduler(2).run(demo())
        expected = [("P1", 0, 2), ("P2", 2, 4), ("P3", 4, 6), ("P1", 6, 8), ("P4", 8, 10),
                    ("P5", 10, 12), ("P2", 12, 13), ("P3", 13, 15), ("P1", 15, 16),
                    ("P5", 16, 18), ("P3", 18, 22)]
        self.assertEqual([(s.pid, s.start, s.end) for s in res.segments], expected)
        self.assertEqual([r["finish"] for r in res.per_task()], [16, 13, 22, 10, 18])
        self.assertAlmostEqual(res.avg_waiting, 9.4)
        self.assertAlmostEqual(res.avg_turnaround, 13.8)
        self.assertAlmostEqual(res.avg_response, 2.8)
        self.assertEqual(res.context_switches, 10)

    def test_large_quantum_equals_fifo(self):
        fifo = FifoScheduler().run(demo())
        rr = RoundRobinScheduler(100).run(demo())
        self.assertEqual(rows(fifo).keys(), rows(rr).keys())
        for pid, row in rows(fifo).items():
            self.assertEqual(row["finish"], rows(rr)[pid]["finish"])

    def test_quantum_one_total_time_and_idle(self):
        res = RoundRobinScheduler(1).run([Task("A", 0, 2), Task("B", 5, 1)])
        self.assertEqual([(s.pid, s.start, s.end) for s in res.segments],
                         [("A", 0, 2), ("IDLE", 2, 5), ("B", 5, 6)])

    def test_invalid_quantum(self):
        for bad in (0, -3, 1.5, "2", True):
            with self.assertRaises(QuantumError):
                RoundRobinScheduler(bad)

    def test_properties_hold_on_random_sets(self):
        for seed in range(5):
            tasks = generate_tasks(60, seed=seed)
            for sch in (FifoScheduler(), RoundRobinScheduler(3)):
                res = sch.run(tasks)
                self.assertEqual(res.busy_time, sum(tasks))  # весь обсяг роботи виконано
                for row in res.per_task():
                    self.assertGreaterEqual(row["waiting"], 0)
                    self.assertEqual(row["turnaround"], row["waiting"] + row["burst"])
                    self.assertGreaterEqual(row["start"], row["arrival"])


class BaseTests(unittest.TestCase):
    def test_empty_set(self):
        with self.assertRaises(EmptyTaskSetError):
            FifoScheduler().run([])

    def test_abstract_and_polymorphism(self):
        with self.assertRaises(TypeError):
            Scheduler("x")
        names = [type(s).__name__ for s in (FifoScheduler(), RoundRobinScheduler(2))]
        self.assertEqual(names, ["FifoScheduler", "RoundRobinScheduler"])

    def test_results_comparison(self):
        fifo, rr = FifoScheduler().run(demo()), RoundRobinScheduler(2).run(demo())
        self.assertTrue(fifo < rr)
        self.assertEqual(min(fifo, rr), fifo)


if __name__ == "__main__":
    unittest.main()
