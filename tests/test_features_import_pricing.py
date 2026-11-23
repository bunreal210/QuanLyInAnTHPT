import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db.connection import init_db, get_connection
from app.db.models import (
    create_classes_template_excel, import_classes_from_excel,
    create_teachers_template_excel, import_teachers_from_excel,
    get_all_price_rules, update_price_rule_amount, get_price,
    get_requesters, search_requesters
)

class ImportAndPricingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_class_template_and_import(self):
        tmpl_path = os.path.join(BASE_DIR, "data", "test_mau_lop.xlsx")
        if os.path.exists(tmpl_path):
            os.remove(tmpl_path)
        
        # 1. Tao file mau
        create_classes_template_excel(tmpl_path)
        self.assertTrue(os.path.exists(tmpl_path))
        
        # 2. Import tu file mau (mau co 10A1 si so 45, 10A2 si so 44)
        count, msg = import_classes_from_excel(tmpl_path)
        self.assertGreaterEqual(count, 4)
        
        # 3. Kiem tra si so trong CSDL
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT student_count FROM requesters WHERE type = 'class' AND name = '10A1'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 45)
        conn.close()

    def test_teacher_template_and_import(self):
        tmpl_path = os.path.join(BASE_DIR, "data", "test_mau_gv.xlsx")
        if os.path.exists(tmpl_path):
            os.remove(tmpl_path)
            
        create_teachers_template_excel(tmpl_path)
        self.assertTrue(os.path.exists(tmpl_path))
        
        count, msg = import_teachers_from_excel(tmpl_path)
        self.assertGreaterEqual(count, 4)
        
        teachers = get_requesters(requester_type='teacher')
        teacher_names = [t['name'] for t in teachers]
        self.assertIn("Nguyễn Thị Lan", teacher_names)

    def test_pricing_configuration(self):
        rules = get_all_price_rules()
        self.assertGreater(len(rules), 0)
        
        # Tim rule A4 2 mat den trang
        target_rule = None
        for r in rules:
            if r['paper'] == 'A4' and r['color'] == 0 and r['duplex'] == 1 and r['printer_id'] is None:
                target_rule = r
                break
        self.assertIsNotNone(target_rule)
        
        # Cap nhat don gia len 400d
        update_price_rule_amount(target_rule['id'], 400.0)
        p = get_price(paper='A4', color=0, duplex=1)
        self.assertEqual(p, 400.0)

if __name__ == "__main__":
    unittest.main()
