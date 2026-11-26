import csv
import json
import os
import tempfile
import unittest

from cpu_scheduler import (DataFileFormatError, FifoScheduler, PersistenceError,
                           RoundRobinScheduler, load_tasks, save_result_csv,
                           save_result_json)

DEMO_LINES = "P1;0;5\nP2;1;3\n"


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.dir, name)

    def write(self, name, text):
        with open(self.path(name), "w", encoding="utf-8") as handle:
            handle.write(text)
        return self.path(name)

    def test_load_txt_csv_json(self):
        txt = self.write("a.txt", DEMO_LINES)
        csv_path = self.write("a.csv", "pid,arrival,burst\nP1,0,5\nP2,1,3\n")
        js = self.write("a.json", json.dumps({"tasks": [
            {"pid": "P1", "arrival": 0, "burst": 5}, {"pid": "P2", "arrival": 1, "burst": 3}]}))
        loaded = [load_tasks(p) for p in (txt, csv_path, js)]
        self.assertEqual(loaded[0], loaded[1])
        self.assertEqual(loaded[0], loaded[2])

    def test_errors(self):
        with self.assertRaises(PersistenceError):
            load_tasks(self.path("missing.txt"))
        with self.assertRaises(DataFileFormatError):
            load_tasks(self.write("a.xml", "<x/>"))
        with self.assertRaises(DataFileFormatError):
            load_tasks(self.write("bad.json", "{oops"))
        with self.assertRaises(DataFileFormatError):
            load_tasks(self.write("shape.json", json.dumps([1, 2])))
        with self.assertRaises(DataFileFormatError):
            load_tasks(self.write("keys.json", json.dumps({"tasks": [{"pid": "P1"}]})))

    def test_save_json_and_csv(self):
        tasks = load_tasks(self.write("a.txt", DEMO_LINES))
        results = [FifoScheduler().run(tasks), RoundRobinScheduler(2).run(tasks)]
        json_path, csv_path = self.path("r.json"), self.path("r.csv")
        save_result_json(json_path, results)
        save_result_csv(csv_path, results)
        with open(json_path, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["results"][0]["summary"]["algorithm"], "FIFO")
        with open(csv_path, encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["algorithm"], "FIFO")
        self.assertEqual(rows[1]["finish"], "8")

    def test_save_to_missing_directory(self):
        tasks = load_tasks(self.write("a.txt", DEMO_LINES))
        with self.assertRaises(PersistenceError):
            save_result_json(os.path.join(self.dir, "no", "r.json"),
                             [FifoScheduler().run(tasks)])


if __name__ == "__main__":
    unittest.main()
