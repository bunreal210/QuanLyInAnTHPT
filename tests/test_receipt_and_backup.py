import os
import unittest
import tempfile
import sqlite3
from app.services.receipt import generate_receipt_pdf, number_to_vietnamese_words
from app.services.backup import create_database_backup, restore_database_from_backup
from app.db.connection import get_database_path, init_db

class TestReceiptAndBackup(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_number_to_vietnamese_words(self):
        self.assertEqual(number_to_vietnamese_words(0), "Không đồng")
        self.assertIn("năm mươi nghìn", number_to_vietnamese_words(50000).lower())
        self.assertIn("triệu", number_to_vietnamese_words(1500000).lower())

    def test_generate_receipt_pdf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = os.path.join(tmpdir, "test_receipt.pdf")
            sample_jobs = [
                {
                    "created_at": "2026-11-23 08:30:00",
                    "title": "Đề kiểm tra Toán 10",
                    "pages": 4,
                    "copies": 45,
                    "sheets": 45,
                    "amount": 31500.0
                },
                {
                    "created_at": "2026-11-23 10:15:00",
                    "title": "Phiếu bài tập Hóa học",
                    "pages": 2,
                    "copies": 45,
                    "sheets": 23,
                    "amount": 16100.0
                }
            ]
            pdf_path = generate_receipt_pdf(
                requester_name="Nguyễn Văn A",
                requester_type="teacher",
                department_or_grade="Toán - Tin",
                jobs=sample_jobs,
                output_pdf_path=out_pdf
            )
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 1000)

    def test_database_backup_and_restore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Create backup
            ok, backup_path = create_database_backup(destination_dir=tmpdir)
            self.assertTrue(ok)
            self.assertTrue(os.path.exists(backup_path))
            self.assertGreater(os.path.getsize(backup_path), 1000)

            # 2. Restore backup
            restore_ok, msg = restore_database_from_backup(backup_path)
            self.assertTrue(restore_ok)
            self.assertIn("Đã khôi phục thành công", msg)

if __name__ == "__main__":
    unittest.main()
