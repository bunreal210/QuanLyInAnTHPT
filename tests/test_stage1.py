import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.printer import build_sumatra_print_settings, create_sample_test_pdf, list_windows_printers
from app.db.connection import init_db, get_connection
from app.db.models import (
    get_requesters, get_presets, get_price, save_or_update_printer,
    get_printer_by_windows_name
)

class Stage1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_sumatra_settings_string(self):
        settings = build_sumatra_print_settings(
            copies=3, duplex=1, color=0, paper="A4", collate=True
        )
        self.assertEqual(settings, "3x,duplexlong,monochrome,paper=A4,collate")

        settings_color = build_sumatra_print_settings(
            copies=1, duplex=0, color=1, paper="A3", collate=False
        )
        self.assertEqual(settings_color, "1x,simplex,color,paper=A3,nocolla")

    def test_create_sample_pdf(self):
        test_pdf = os.path.join(BASE_DIR, "tools", "unit_test_sample.pdf")
        if os.path.exists(test_pdf):
            os.remove(test_pdf)
        out = create_sample_test_pdf(test_pdf, "UNIT TEST SAMPLE")
        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 1000)
        # Clean up
        if os.path.exists(test_pdf):
            os.remove(test_pdf)

    def test_list_printers(self):
        printers = list_windows_printers()
        self.assertIsInstance(printers, list)
        self.assertGreater(len(printers), 0)
        print(f"\n[TEST INFO] Tim thay {len(printers)} may in: {[p['windows_name'] for p in printers]}")

    def test_db_seeded_data(self):
        classes = get_requesters(requester_type='class')
        self.assertEqual(len(classes), 42)
        presets = get_presets()
        self.assertGreaterEqual(len(presets), 4)

    def test_printer_save_to_db(self):
        save_or_update_printer(
            windows_name="TEST_VIRTUAL_PRINTER",
            display_name="Máy in ảo Test",
            color_supported=1,
            duplex_supported=1,
            papers="A4,A3",
            note="Test Unit"
        )
        p = get_printer_by_windows_name("TEST_VIRTUAL_PRINTER")
        self.assertIsNotNone(p)
        self.assertEqual(p['display_name'], "Máy in ảo Test")
        self.assertEqual(p['color_supported'], 1)

if __name__ == "__main__":
    unittest.main()
