import os
import sys
import unittest
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db.connection import init_db, get_connection
from app.services.booklet import create_booklet_pdf
from app.services.printer import create_sample_test_pdf
from app.services.converter import count_pages, parse_page_ranges
from app.services.pricing import calculate_print_cost
from app.services.storage import organize_and_save_files
from app.services.excel_sync import export_full_excel
from app.services.cloud_sync import export_sync_package, import_sync_packages
from app.db.models import create_print_job, add_requester, get_requesters

class FullWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_booklet_generation(self):
        # Tao file test 3 trang
        test_pdf = os.path.join(BASE_DIR, "tools", "test_for_booklet.pdf")
        create_sample_test_pdf(test_pdf, "BOOKLET SOURCE")
        
        booklet_out = os.path.join(BASE_DIR, "tools", "test_booklet_out.pdf")
        if os.path.exists(booklet_out):
            os.remove(booklet_out)
            
        create_booklet_pdf(test_pdf, booklet_out, target_paper="A4")
        self.assertTrue(os.path.exists(booklet_out))
        
        # Tap 2 trang goc -> booklet se co 1 to giay (2 trang mat truoc va mat sau)
        pages_booklet = count_pages(booklet_out)
        self.assertGreaterEqual(pages_booklet, 1)

    def test_pricing_and_booklet_calculation(self):
        # 8 trang in booklet, 10 ban
        # Moi ban booklet 8 trang ton 2 to giay -> 10 ban = 20 to
        cost = calculate_print_cost(pages_count=8, copies=10, paper="A4", duplex=3, color=0, is_booklet=True)
        self.assertEqual(cost['sheets_per_copy'], 2)
        self.assertEqual(cost['total_sheets'], 20)
        self.assertEqual(cost['amount'], 20 * cost['unit_price'])

    def test_storage_organization(self):
        sample_file = os.path.join(BASE_DIR, "tools", "test_for_booklet.pdf")
        saved_orig, saved_pdf = organize_and_save_files(
            original_file_path=sample_file,
            converted_pdf_path=sample_file,
            requester_type="teacher",
            requester_name="Nguyễn Thị Lan",
            copies=45,
            title="Đề kiểm tra Sinh 10"
        )
        self.assertTrue(os.path.exists(saved_orig))
        self.assertIn("GiaoVien", saved_orig)
        self.assertIn("Sinh 10_45ban", saved_orig)

    def test_print_job_creation_and_excel(self):
        # Them 1 giao vien test
        req_id = add_requester(name="Trần Văn Nam", req_type="teacher", department="Toán", note="GVCN 10A1")
        
        job_id = create_print_job({
            "requester_id": req_id,
            "related_classes": "10A1",
            "title": "Đề thi thử Toán 10",
            "file_type": "pdf",
            "pages": 4,
            "copies": 40,
            "sheets": 80,
            "printer_name": "RICOH MP 7503",
            "paper": "A4",
            "duplex": 1,
            "color": 0,
            "unit_price": 350.0,
            "amount": 28000.0,
            "status": "printed",
            "paid_status": "unpaid"
        })
        self.assertGreater(job_id, 0)

        # Xuat file Excel
        test_excel = os.path.join(BASE_DIR, "data", "Test_TongHopInAn.xlsx")
        if os.path.exists(test_excel):
            os.remove(test_excel)
        ok, msg = export_full_excel(test_excel)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(test_excel))

    def test_cloud_sync_export_import(self):
        sync_dir = os.path.join(BASE_DIR, "data", "test_cloud_folder")
        os.makedirs(sync_dir, exist_ok=True)
        
        ok_exp, msg_exp = export_sync_package(sync_dir)
        self.assertTrue(ok_exp)
        
        ok_imp, msg_imp = import_sync_packages(sync_dir)
        self.assertTrue(ok_imp)

if __name__ == "__main__":
    unittest.main()
