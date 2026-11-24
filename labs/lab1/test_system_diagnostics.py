# -*- coding: utf-8 -*-
"""
Модульні тести для system_diagnostics.py (ЛБ № 1, варіант 2).

Запуск:  python -m unittest -v
"""

import json
import platform
import subprocess
import sys
import unittest
from pathlib import Path

import system_diagnostics as sd


class DecodeHexversionTests(unittest.TestCase):
    """Перевірка розшифровки sys.hexversion на відомих значеннях (формат 0xMMmmPPLS)."""

    def test_python_3_10_0_final(self):
        d = sd.decode_hexversion(0x030A00F0)
        self.assertEqual((d["major"], d["minor"], d["micro"]), (3, 10, 0))
        self.assertEqual((d["releaselevel"], d["serial"]), ("final", 0))

    def test_python_3_10_14_final(self):
        d = sd.decode_hexversion(0x030A0EF0)
        self.assertEqual((d["major"], d["minor"], d["micro"]), (3, 10, 14))
        self.assertEqual(d["releaselevel"], "final")

    def test_prerelease_levels(self):
        self.assertEqual(sd.decode_hexversion(0x030B00A3)["releaselevel"], "alpha")
        self.assertEqual(sd.decode_hexversion(0x030B00B2)["releaselevel"], "beta")
        self.assertEqual(sd.decode_hexversion(0x030B00C1)["releaselevel"], "candidate")
        self.assertEqual(sd.decode_hexversion(0x030B00B2)["serial"], 2)

    def test_unknown_level(self):
        self.assertEqual(sd.decode_hexversion(0x030A0010)["releaselevel"], "unknown")

    def test_hex_string_format(self):
        self.assertEqual(sd.decode_hexversion(0x030A00F0)["hex"], "0x030a00f0")


class RealInterpreterTests(unittest.TestCase):
    """Перевірки, що порівнюють результати модуля зі стандартною бібліотекою."""

    def test_decoded_matches_version_info(self):
        d = sd.decode_hexversion(sys.hexversion)
        vi = sys.version_info
        self.assertEqual((d["major"], d["minor"], d["micro"]), (vi.major, vi.minor, vi.micro))
        self.assertEqual(d["releaselevel"], vi.releaselevel)
        self.assertEqual(d["serial"], vi.serial)

    def test_inspect_version_all_checks_pass(self):
        result = sd.inspect_version()
        failed = [name for name, ok in result["checks"].items() if not ok]
        self.assertEqual(failed, [], f"Не пройдено перевірки: {failed}")
        self.assertTrue(result["all_checks_passed"])

    def test_micro_in_report_matches_sys(self):
        result = sd.inspect_version()
        self.assertEqual(result["version_info"]["micro"], sys.version_info.micro)
        self.assertEqual(result["micro_analysis"]["micro"], sys.version_info.micro)
        self.assertEqual(result["hexversion"]["micro"], sys.version_info.micro)

    def test_python_build_matches_platform(self):
        build_no, build_date = platform.python_build()
        result = sd.inspect_version()["python_build"]
        self.assertEqual(result["build_number"], build_no)
        self.assertEqual(result["build_date"], build_date)

    def test_required_version(self):
        self.assertGreaterEqual(sys.version_info[:2], sd.REQUIRED_VERSION)


class BuildDateTests(unittest.TestCase):
    def test_parse_normal(self):
        self.assertEqual(sd.parse_build_date("Jul 18 2026 17:02:35"), (2026, 7, 18, "17:02:35"))

    def test_parse_padded_day(self):
        self.assertEqual(sd.parse_build_date("Jun  4 2024 11:12:09"), (2024, 6, 4, "11:12:09"))

    def test_parse_garbage_returns_none(self):
        self.assertIsNone(sd.parse_build_date("невідомо"))
        self.assertIsNone(sd.parse_build_date(""))


class ClassifyMicroTests(unittest.TestCase):
    @staticmethod
    def _vi(micro, level="final", serial=0):
        return type("VI", (), {"micro": micro, "releaselevel": level, "serial": serial})()

    def test_first_release(self):
        self.assertIn("x.y.0", sd.classify_micro(self._vi(0)))

    def test_maintenance_release(self):
        self.assertIn("14", sd.classify_micro(self._vi(14)))

    def test_prerelease(self):
        self.assertIn("beta", sd.classify_micro(self._vi(0, "beta", 2)))


class MemoryAndCacheTests(unittest.TestCase):
    def test_memory_table_values(self):
        mem = sd.calculate_memory_footprint()
        self.assertEqual(mem["int (1)"], 28)          # однакове для CPython 3.10+
        self.assertGreaterEqual(mem["int (0)"], 24)
        self.assertGreater(mem["int (2**64)"], mem["int (1)"])
        self.assertEqual(mem["None"], 16)
        self.assertEqual(mem["str (20 ASCII)"] - mem["str (порожній)"], 20)

    def test_small_int_cache(self):
        for row in sd.verify_integer_cache():
            low, high = sd.SMALL_INT_CACHE_RANGE
            expected = low <= row["value"] <= high
            self.assertEqual(row["same_object"], expected, f"значення {row['value']}")


class CommandLineTests(unittest.TestCase):
    SCRIPT = str(Path(__file__).with_name("system_diagnostics.py"))

    def test_text_report_runs(self):
        proc = subprocess.run([sys.executable, self.SCRIPT], capture_output=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ІНСПЕКЦІЯ ВЕРСІЙ СЕРЕДОВИЩА", proc.stdout)

    def test_json_report_is_valid(self):
        proc = subprocess.run([sys.executable, self.SCRIPT, "--json"], capture_output=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["version_inspection"]["version_info"]["micro"], sys.version_info.micro)


if __name__ == "__main__":
    unittest.main(verbosity=2)
