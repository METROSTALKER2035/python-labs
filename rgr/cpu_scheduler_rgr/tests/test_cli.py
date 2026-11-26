import contextlib
import io
import os
import tempfile
import unittest

from cpu_scheduler.cli import (EXIT_ARGS, EXIT_DATA, EXIT_IO, EXIT_OK, main,
                               parse_arguments)


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.demo = os.path.join(self.tmp.name, "demo.txt")
        with open(self.demo, "w", encoding="utf-8") as handle:
            handle.write("P1;0;5\nP2;1;3\nP3;2;8\nP4;3;2\nP5;4;4\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_arguments(self):
        opts = parse_arguments(["-i", "f.txt", "-a", "rr", "-q", "3", "-g"])
        self.assertEqual((opts["input"], opts["algo"], opts["quantum"], opts["gantt"]),
                         ("f.txt", "rr", 3, True))

    def test_help_and_success(self):
        code, out, _ = run_cli("--help")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Використання", out)
        code, out, _ = run_cli("--input", self.demo, "--quantum", "2")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("RR(q=2)", out)
        self.assertIn("7.40", out)
        self.assertIn("9.40", out)

    def test_exit_codes(self):
        self.assertEqual(run_cli("--bogus")[0], EXIT_ARGS)
        self.assertEqual(run_cli("--quantum")[0], EXIT_ARGS)
        self.assertEqual(run_cli("--quantum", "x")[0], EXIT_ARGS)
        self.assertEqual(run_cli("--input", self.demo, "--algo", "sjf")[0], EXIT_ARGS)
        self.assertEqual(run_cli("--input", self.demo, "--algo", "rr", "-q", "0")[0], EXIT_ARGS)
        self.assertEqual(run_cli()[0], EXIT_ARGS)
        self.assertEqual(run_cli("--input", os.path.join(self.tmp.name, "no.txt"))[0], EXIT_IO)
        bad = os.path.join(self.tmp.name, "bad.txt")
        with open(bad, "w", encoding="utf-8") as handle:
            handle.write("P1;0;abc\n")
        code, _, err = run_cli("--input", bad)
        self.assertEqual(code, EXIT_DATA)
        self.assertIn("Рядок 1", err)

    def test_save_files(self):
        js, cs = os.path.join(self.tmp.name, "r.json"), os.path.join(self.tmp.name, "r.csv")
        code, out, _ = run_cli("--input", self.demo, "--json", js, "--csv", cs)
        self.assertEqual(code, EXIT_OK)
        self.assertTrue(os.path.getsize(js) > 0 and os.path.getsize(cs) > 0)

    def test_bench(self):
        code, out, _ = run_cli("--bench", "100")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("FIFO, мс", out)


if __name__ == "__main__":
    unittest.main()
