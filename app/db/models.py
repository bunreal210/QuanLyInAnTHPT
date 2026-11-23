import os
import re
import unicodedata
from datetime import datetime
from app.db.connection import get_connection, get_machine_name

def remove_accents(input_str: str) -> str:
    """Chuyen chuoi co dau thanh khong dau de tim kiem nhanh (vd: 'Nguyễn Thị Lan' -> 'nguyen thi lan')"""
    if not input_str:
        return ""
    nfkd = unicodedata.normalize('NFKD', input_str)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Thay the d, D dac thu tieng Viet
    no_accent = no_accent.replace('đ', 'd').replace('Đ', 'D')
    return no_accent.lower().strip()

# ==================== SETTINGS ====================
def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else default
    finally:
        conn.close()

def set_setting(key: str, value: str):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                (key, str(value))
            )
    finally:
        conn.close()

def get_all_settings() -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings")
        return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        conn.close()

# ==================== REQUESTERS ====================
def get_requesters(requester_type: str = None, active_only: bool = True) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = "SELECT * FROM requesters WHERE 1=1"
        params = []
        if requester_type:
            query += " AND type = ?"
            params.append(requester_type)
        if active_only:
            query += " AND active = 1"
        query += " ORDER BY type ASC, grade ASC, name ASC"
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def search_requesters(keyword: str, limit: int = 15) -> list:
    """Tim kiem nguoi yeu cau khong dau (vd: 'lan' tim thay 'Nguyễn Thị Lan')"""
    if not keyword:
        return get_requesters(active_only=True)[:limit]

    kw_clean = remove_accents(keyword)
    all_reqs = get_requesters(active_only=True)
    matches = []
    for r in all_reqs:
        name_clean = remove_accents(r['name'])
        dept_clean = remove_accents(r.get('department') or '')
        if kw_clean in name_clean or kw_clean in dept_clean:
            matches.append(r)
            if len(matches) >= limit:
                break
    return matches

def get_recent_requester_ids(limit: int = 5) -> list:
    """Lay danh sach 5 nguoi yeu cau gan day nhat de chon nhanh tren giao dien"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT requester_id, MAX(created_at) as last_time FROM print_jobs "
            "WHERE requester_id IS NOT NULL "
            "GROUP BY requester_id ORDER BY last_time DESC LIMIT ?",
            (limit,)
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def add_requester(name: str, req_type: str, department: str = None, grade: int = None, note: str = "") -> int:
    conn = get_connection()
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO requesters (name, type, department, grade, note) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), req_type, department.strip() if department else None, grade, note)
            )
            return cur.lastrowid
    finally:
        conn.close()

def update_requester(req_id: int, name: str, department: str = None, grade: int = None, note: str = "", active: int = 1):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE requesters SET name = ?, department = ?, grade = ?, note = ?, active = ? WHERE id = ?",
                (name.strip(), department.strip() if department else None, grade, note, active, req_id)
            )
    finally:
        conn.close()

# ==================== PRINTERS ====================
def get_printers(active_only: bool = True) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = "SELECT * FROM printers WHERE 1=1"
        if active_only:
            query += " AND active = 1"
        query += " ORDER BY display_name ASC"
        cur.execute(query)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_printer_by_windows_name(win_name: str) -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM printers WHERE windows_name = ?", (win_name,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def save_or_update_printer(windows_name: str, display_name: str, color_supported: int, duplex_supported: int, papers: str = "A4,A3", note: str = ""):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO printers (windows_name, display_name, color_supported, duplex_supported, papers, note) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(windows_name) DO UPDATE SET "
                "display_name = excluded.display_name, "
                "color_supported = excluded.color_supported, "
                "duplex_supported = excluded.duplex_supported, "
                "papers = excluded.papers, "
                "note = excluded.note",
                (windows_name, display_name, color_supported, duplex_supported, papers, note)
            )
    finally:
        conn.close()

def get_all_price_rules() -> list:
    """Lay toan bo bang gia gom ca ten may in lien ket neu co"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT pr.id, pr.printer_id, p.display_name as printer_name,
                   pr.paper, pr.color, pr.duplex, pr.price_per_unit, pr.unit_type
            FROM price_rules pr
            LEFT JOIN printers p ON pr.printer_id = p.id
            ORDER BY pr.paper ASC, pr.color ASC, pr.duplex ASC
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def update_price_rule_amount(rule_id: int, new_price: float):
    conn = get_connection()
    try:
        with conn:
            conn.execute("UPDATE price_rules SET price_per_unit = ? WHERE id = ?", (new_price, rule_id))
    finally:
        conn.close()

def add_price_rule(paper: str, color: int, duplex: int, price: float, printer_id: int = None, unit_type: str = "sheet"):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO price_rules (printer_id, paper, color, duplex, price_per_unit, unit_type) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (printer_id, paper, color, duplex, price, unit_type)
            )
    finally:
        conn.close()

def delete_price_rule(rule_id: int):
    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM price_rules WHERE id = ?", (rule_id,))
    finally:
        conn.close()

def reset_default_prices():
    """Khoi phuc bang gia chuan ban dau"""
    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM price_rules WHERE printer_id IS NULL")
            default_prices = [
                (None, 'A4', 0, 0, 250.0, 'sheet'),
                (None, 'A4', 0, 1, 350.0, 'sheet'),
                (None, 'A4', 1, 0, 1000.0, 'sheet'),
                (None, 'A4', 1, 1, 1500.0, 'sheet'),
                (None, 'A3', 0, 0, 500.0, 'sheet'),
                (None, 'A3', 0, 1, 700.0, 'sheet'),
                (None, 'A3', 1, 0, 2000.0, 'sheet'),
                (None, 'A3', 1, 1, 3000.0, 'sheet'),
            ]
            conn.executemany(
                "INSERT INTO price_rules (printer_id, paper, color, duplex, price_per_unit, unit_type) VALUES (?, ?, ?, ?, ?, ?)",
                default_prices
            )
    finally:
        conn.close()

# ==================== PRICING & PRESETS ====================
def get_price(printer_id: int = None, paper: str = "A4", color: int = 0, duplex: int = 1) -> float:
    """Tra ve don gia (dong/to hoac dong/mat in) phu hop nhat"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Tim quy tac gia cu the cho may in nay truoc
        if printer_id:
            cur.execute(
                "SELECT price_per_unit FROM price_rules "
                "WHERE printer_id = ? AND paper = ? AND color = ? AND duplex = ? "
                "ORDER BY effective_from DESC LIMIT 1",
                (printer_id, paper, color, duplex)
            )
            row = cur.fetchone()
            if row:
                return float(row[0])

        # Neu khong co, tim quy tac ap dung chung (printer_id IS NULL)
        cur.execute(
            "SELECT price_per_unit FROM price_rules "
            "WHERE printer_id IS NULL AND paper = ? AND color = ? AND duplex = ? "
            "ORDER BY effective_from DESC LIMIT 1",
            (paper, color, duplex)
        )
        row = cur.fetchone()
        if row:
            return float(row[0])

        # Gia du phong mac dinh neu chua cau hinh
        if paper == "A3":
            return 700.0 if duplex else 500.0
        return 350.0 if duplex else 250.0
    finally:
        conn.close()

def get_presets() -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM presets ORDER BY id ASC")
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

# ==================== PRINT JOBS ====================
def create_print_job(job_data: dict) -> int:
    """Tao mot ban ghi nhat ky in moi"""
    conn = get_connection()
    try:
        with conn:
            cur = conn.cursor()
            job_data['machine_name'] = get_machine_name()
            columns = [
                'machine_name', 'requester_id', 'payer_id', 'related_classes', 'title',
                'file_type', 'original_file_path', 'pages', 'page_range', 'copies',
                'sheets', 'printer_id', 'printer_name', 'paper', 'duplex', 'color',
                'unit_price', 'amount', 'amount_override', 'is_free', 'override_reason',
                'saved_path', 'pdf_path', 'status', 'error_message', 'paid_status', 'note'
            ]
            valid_cols = [c for c in columns if c in job_data]
            placeholders = ", ".join(["?"] * len(valid_cols))
            col_names = ", ".join(valid_cols)
            values = [job_data[c] for c in valid_cols]

            query = f"INSERT INTO print_jobs ({col_names}) VALUES ({placeholders})"
            cur.execute(query, values)
            job_id = cur.lastrowid

            # Cho vao hang doi dong bo Excel
            cur.execute("INSERT INTO sync_queue (job_id, operation, status) VALUES (?, 'insert', 'pending')", (job_id,))
            return job_id
    finally:
        conn.close()

def update_print_job_status(job_id: int, status: str, error_message: str = None):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE print_jobs SET status = ?, error_message = ? WHERE id = ?",
                (status, error_message, job_id)
            )
            # Cap nhat vao hang doi dong bo Excel
            conn.execute("INSERT INTO sync_queue (job_id, operation, status) VALUES (?, 'update', 'pending')", (job_id,))
    finally:
        conn.close()

# ==================== EXCEL IMPORT & TEMPLATES ====================
def import_classes_from_excel(file_path: str) -> tuple[int, str]:
    """
    Nhap danh sach lop tu file Excel.
    Nhan dien cac cot: Lop, Khoi, Si so (hoc sinh), Ghi chu.
    """
    import openpyxl
    if not os.path.exists(file_path):
        return 0, "File không tồn tại."

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active

    # Tim dong tieu de (quet 3 hang dau)
    header_row_idx = None
    col_map = {} # 'name': col_idx, 'grade': col_idx, 'count': col_idx, 'note': col_idx

    for row_idx in range(1, min(ws.max_row + 1, 5)):
        row_vals = [str(ws.cell(row_idx, c).value or '').strip().lower() for c in range(1, ws.max_column + 1)]
        row_clean = [remove_accents(v) for v in row_vals]

        # Kiem tra xem co cot lop hay khong
        has_class = any(k in v for v in row_clean for k in ['lop', 'ten lop', 'class'])
        if has_class:
            header_row_idx = row_idx
            for c_idx, val in enumerate(row_clean, start=1):
                if any(k in val for k in ['lop', 'ten lop', 'class']):
                    if 'name' not in col_map:
                        col_map['name'] = c_idx
                elif any(k in val for k in ['si so', 'so luong', 'so hoc sinh', 'hoc sinh', 'count', 'sl']):
                    col_map['count'] = c_idx
                elif any(k in val for k in ['khoi', 'grade']):
                    col_map['grade'] = c_idx
                elif any(k in val for k in ['ghi chu', 'note']):
                    col_map['note'] = c_idx
            break

    if not header_row_idx or 'name' not in col_map:
        return 0, "Không nhận diện được cột 'Lớp' trong file Excel. Vui lòng kiểm tra tiêu đề các cột."

    conn = get_connection()
    count_success = 0
    try:
        with conn:
            cur = conn.cursor()
            for r in range(header_row_idx + 1, ws.max_row + 1):
                class_name_raw = ws.cell(r, col_map['name']).value
                if not class_name_raw:
                    continue
                class_name = str(class_name_raw).strip()
                if not class_name:
                    continue

                # Si so
                student_count = 0
                if 'count' in col_map:
                    try:
                        val_count = ws.cell(r, col_map['count']).value
                        if val_count is not None:
                            student_count = int(float(str(val_count).strip()))
                    except (ValueError, TypeError):
                        student_count = 0

                # Khoi
                grade = None
                if 'grade' in col_map:
                    try:
                        val_grade = ws.cell(r, col_map['grade']).value
                        if val_grade is not None:
                            grade = int(float(str(val_grade).strip()))
                    except (ValueError, TypeError):
                        pass

                # Neu chua co khoi, do tim tu ten lop (vd 10A1 -> 10, 11A2 -> 11, 12A14 -> 12)
                if not grade:
                    match = re.match(r'^(\d+)', class_name)
                    if match:
                        grade = int(match.group(1))

                # Ghi chu
                note = ""
                if 'note' in col_map:
                    val_note = ws.cell(r, col_map['note']).value
                    if val_note:
                        note = str(val_note).strip()

                # Kiem tra xem lop da ton tai trong CSDL chua
                cur.execute("SELECT id FROM requesters WHERE type = 'class' AND name = ?", (class_name,))
                existing = cur.fetchone()
                if existing:
                    cur.execute(
                        "UPDATE requesters SET student_count = ?, grade = COALESCE(?, grade), note = CASE WHEN ? != '' THEN ? ELSE note END, active = 1 "
                        "WHERE id = ?",
                        (student_count, grade, note, note, existing[0])
                    )
                else:
                    cur.execute(
                        "INSERT INTO requesters (name, type, grade, student_count, note, active) "
                        "VALUES (?, 'class', ?, ?, ?, 1)",
                        (class_name, grade, student_count, note)
                    )
                count_success += 1

        return count_success, f"Đã nhập thành công {count_success} lớp vào hệ thống."
    except Exception as e:
        return 0, f"Lỗi đọc file Excel: {str(e)}"
    finally:
        conn.close()

def create_classes_template_excel(output_path: str) -> str:
    """Tao file Excel mau danh sach lop kem si so"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh sách lớp"

    headers = ["STT", "Khối", "Tên lớp", "Sĩ số học sinh", "Ghi chú"]
    ws.append(headers)

    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(1, col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Dien du lieu mau
    sample_data = [
        (1, 10, "10A1", 45, "Lớp chọn Toán"),
        (2, 10, "10A2", 44, "Lớp chọn Anh"),
        (3, 11, "11A1", 42, ""),
        (4, 12, "12A1", 40, "Khối 12"),
    ]
    for row in sample_data:
        ws.append(list(row))

    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 10
    ws.column_dimensions['C'].width = 16
    ws.column_dimensions['D'].width = 18
    ws.column_dimensions['E'].width = 25

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    wb.save(output_path)
    return output_path

def import_teachers_from_excel(file_path: str) -> tuple[int, str]:
    """
    Nhap danh sach giao vien tu file Excel.
    Nhan dien cac cot: Ho ten, To chuyen mon, Ghi chu.
    """
    import openpyxl
    if not os.path.exists(file_path):
        return 0, "File không tồn tại."

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active

    header_row_idx = None
    col_map = {}

    for row_idx in range(1, min(ws.max_row + 1, 5)):
        row_vals = [str(ws.cell(row_idx, c).value or '').strip().lower() for c in range(1, ws.max_column + 1)]
        row_clean = [remove_accents(v) for v in row_vals]

        has_name = any(k in v for v in row_clean for k in ['ho ten', 'ho va ten', 'giao vien', 'ten gv', 'name'])
        if has_name:
            header_row_idx = row_idx
            for c_idx, val in enumerate(row_clean, start=1):
                if any(k in val for k in ['ho ten', 'ho va ten', 'giao vien', 'ten gv', 'name']):
                    if 'name' not in col_map:
                        col_map['name'] = c_idx
                elif any(k in val for k in ['to chuyen mon', 'to', 'bo mon', 'department', 'chuyen mon']):
                    col_map['dept'] = c_idx
                elif any(k in val for k in ['ghi chu', 'note', 'chuc vu']):
                    col_map['note'] = c_idx
            break

    if not header_row_idx or 'name' not in col_map:
        return 0, "Không nhận diện được cột 'Họ và tên' giáo viên trong file Excel."

    conn = get_connection()
    count_success = 0
    try:
        with conn:
            cur = conn.cursor()
            for r in range(header_row_idx + 1, ws.max_row + 1):
                name_raw = ws.cell(r, col_map['name']).value
                if not name_raw:
                    continue
                teacher_name = str(name_raw).strip()
                if not teacher_name:
                    continue

                dept = ""
                if 'dept' in col_map:
                    val_dept = ws.cell(r, col_map['dept']).value
                    if val_dept:
                        dept = str(val_dept).strip()

                note = ""
                if 'note' in col_map:
                    val_note = ws.cell(r, col_map['note']).value
                    if val_note:
                        note = str(val_note).strip()

                cur.execute("SELECT id FROM requesters WHERE type = 'teacher' AND name = ?", (teacher_name,))
                existing = cur.fetchone()
                if existing:
                    cur.execute(
                        "UPDATE requesters SET department = CASE WHEN ? != '' THEN ? ELSE department END, "
                        "note = CASE WHEN ? != '' THEN ? ELSE note END, active = 1 WHERE id = ?",
                        (dept, dept, note, note, existing[0])
                    )
                else:
                    cur.execute(
                        "INSERT INTO requesters (name, type, department, note, active) VALUES (?, 'teacher', ?, ?, 1)",
                        (teacher_name, dept, note)
                    )
                count_success += 1

        return count_success, f"Đã nhập thành công {count_success} giáo viên vào hệ thống."
    except Exception as e:
        return 0, f"Lỗi đọc file Excel: {str(e)}"
    finally:
        conn.close()

def create_teachers_template_excel(output_path: str) -> str:
    """Tao file Excel mau danh sach giao vien"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh sách giáo viên"

    headers = ["STT", "Họ và tên giáo viên", "Tổ chuyên môn", "Ghi chú"]
    ws.append(headers)

    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(1, col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    sample_data = [
        (1, "Nguyễn Thị Lan", "Sinh học", "Nhóm trưởng môn Sinh"),
        (2, "Trần Văn Nam", "Toán", "GVCN 10A1"),
        (3, "Lê Thị Hồng", "Ngữ văn", ""),
        (4, "Phạm Quốc Tuấn", "Vật lý", ""),
    ]
    for row in sample_data:
        ws.append(list(row))

    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 30

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    wb.save(output_path)
    return output_path

