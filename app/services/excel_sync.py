import os
import logging
from typing import Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.db.connection import get_connection
from app.db.models import get_setting, get_requesters, get_price

logger = logging.getLogger("print_manager.excel")

def get_excel_file_path() -> str:
    """Lay duong dan file Excel tong hop tu settings"""
    path = get_setting("excel_path", "D:\\DeDaIn\\TongHopInAn.xlsx")
    drive = os.path.splitdrive(path)[0]
    if drive and not os.path.exists(drive + "\\"):
        from app.services.storage import get_storage_base_dir
        path = os.path.join(get_storage_base_dir(), "TongHopInAn.xlsx")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        from app.db.connection import get_app_dir
        path = os.path.join(get_app_dir(), "DeDaIn", "TongHopInAn.xlsx")
        os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def is_file_locked(filepath: str) -> bool:
    """Kiem tra xem file Excel co dang bi chuong trinh khac (nhu Excel) mo khoa hay khong"""
    if not os.path.exists(filepath):
        return False
    try:
        # Thu mo file voi quyen ghi doc quyen
        with open(filepath, 'a+b') as f:
            pass
        return False
    except IOError:
        return True

def export_full_excel(output_path: str = None) -> Tuple[bool, str]:
    """
    Xuat hoan toan moi hoac lam moi toan bo file Excel tong hop tu SQLite.
    Bao gom:
    - Sheet 1: Nhat ky in
    - Sheet 2: Tong hop Giao vien (cong thuc SUMIFS)
    - Sheet 3: Tong hop Lop (cong thuc SUMIFS)
    - Sheet 4: Danh muc & Bang gia
    """
    if not output_path:
        output_path = get_excel_file_path()

    if is_file_locked(output_path):
        return False, "File Excel đang được mở bởi Microsoft Excel hoặc chương trình khác. Vui lòng đóng file rồi thử lại."

    wb = openpyxl.Workbook()
    # Xoa sheet default
    wb.remove(wb.active)

    # Dinh dang chung
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    sub_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    conn = get_connection()
    try:
        cur = conn.cursor()

        # ==================== SHEET 1: NHẬT KÝ IN ====================
        ws_log = wb.create_sheet(title="Nhật ký in")
        headers_log = [
            "Mã in", "Ngày giờ", "Máy tính", "Người yêu cầu", "Loại", "Lớp liên quan",
            "Tên đề / Tài liệu", "Định dạng", "Số trang", "Khoảng trang", "Số bản",
            "Tổng số tờ", "Máy in", "Khổ giấy", "Chế độ mặt", "Màu sắc", "Đơn giá (đ)",
            "Thành tiền (đ)", "Miễn phí", "Lý do", "Trạng thái", "Thanh toán", "Ghi chú", "Đường dẫn file"
        ]
        ws_log.append(headers_log)

        # Style header
        for col_idx, col_name in enumerate(headers_log, start=1):
            cell = ws_log.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Load print_jobs
        cur.execute("""
            SELECT j.id, j.created_at, j.machine_name, r.name, r.type, j.related_classes,
                   j.title, j.file_type, j.pages, j.page_range, j.copies, j.sheets,
                   j.printer_name, j.paper, j.duplex, j.color, j.unit_price, j.amount,
                   j.is_free, j.override_reason, j.status, j.paid_status, j.note, j.saved_path
            FROM print_jobs j
            LEFT JOIN requesters r ON j.requester_id = r.id
            ORDER BY j.id ASC
        """)
        jobs = cur.fetchall()

        type_vn = {"teacher": "Giáo viên", "class": "Lớp", "other": "Khác"}
        duplex_vn = {0: "1 mặt", 1: "2 mặt (dài)", 2: "2 mặt (ngắn)", 3: "Booklet"}
        paid_vn = {"unpaid": "Chưa thu", "paid": "Đã thu"}

        for row_idx, job in enumerate(jobs, start=2):
            req_type = type_vn.get(job[4], job[4] or "")
            dup_mode = duplex_vn.get(job[14], "1 mặt")
            color_mode = "Màu" if job[15] == 1 else "Đen trắng"
            paid_text = paid_vn.get(job[21], job[21] or "")

            row_data = [
                job[0], job[1], job[2], job[3] or "Khác", req_type, job[5] or "",
                job[6], job[7], job[8], job[9] or "Tất cả", job[10],
                job[11], job[12] or "", job[13], dup_mode, color_mode,
                job[16], job[17], "Có" if job[18] else "Không", job[19] or "",
                job[20], paid_text, job[22] or "", job[23] or ""
            ]
            ws_log.append(row_data)

            # Dinh dang so va border
            ws_log.cell(row=row_idx, column=17).number_format = '#,##0 "đ"'
            ws_log.cell(row=row_idx, column=18).number_format = '#,##0 "đ"'
            for c_idx in range(1, len(row_data) + 1):
                ws_log.cell(row=row_idx, column=c_idx).border = thin_border

        # Freeze header and add auto-filter
        ws_log.freeze_panes = "A2"
        ws_log.auto_filter.ref = f"A1:{get_column_letter(len(headers_log))}{max(len(jobs) + 1, 1)}"

        # ==================== SHEET 2: TỔNG HỢP GIÁO VIÊN ====================
        ws_teacher = wb.create_sheet(title="Tổng hợp Giáo viên")
        headers_teacher = ["Mã GV", "Họ và tên giáo viên", "Tổ chuyên môn", "Tổng lượt in", "Tổng số tờ in", "Thành tiền (đ)", "Ghi chú"]
        ws_teacher.append(headers_teacher)
        for col_idx in range(1, len(headers_teacher) + 1):
            cell = ws_teacher.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = sub_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        cur.execute("SELECT id, name, department, note FROM requesters WHERE type = 'teacher' ORDER BY name ASC")
        teachers = cur.fetchall()

        for idx, t in enumerate(teachers, start=2):
            t_name = t[1]
            # Dung cong thuc SUMIFS / COUNTIF tham chieu sang Sheet Nhat ky in
            formula_count = f'=COUNTIF(\'Nhật ký in\'!$D:$D, B{idx})'
            formula_sheets = f'=SUMIFS(\'Nhật ký in\'!$L:$L, \'Nhật ký in\'!$D:$D, B{idx})'
            formula_amount = f'=SUMIFS(\'Nhật ký in\'!$R:$R, \'Nhật ký in\'!$D:$D, B{idx})'

            ws_teacher.append([t[0], t_name, t[2] or "", formula_count, formula_sheets, formula_amount, t[3] or ""])
            ws_teacher.cell(row=idx, column=6).number_format = '#,##0 "đ"'
            for c_idx in range(1, len(headers_teacher) + 1):
                ws_teacher.cell(row=idx, column=c_idx).border = thin_border

        ws_teacher.freeze_panes = "A2"
        ws_teacher.auto_filter.ref = f"A1:G{max(len(teachers) + 1, 1)}"

        # ==================== SHEET 3: TỔNG HỢP 42 LỚP ====================
        ws_class = wb.create_sheet(title="Tổng hợp 42 Lớp")
        headers_class = ["Khối", "Lớp", "Tổng lượt in", "Tổng số tờ in", "Thành tiền (đ)"]
        ws_class.append(headers_class)
        for col_idx in range(1, len(headers_class) + 1):
            cell = ws_class.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = sub_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        cur.execute("SELECT id, name, grade FROM requesters WHERE type = 'class' ORDER BY grade ASC, name ASC")
        classes = cur.fetchall()

        for idx, c in enumerate(classes, start=2):
            c_name = c[1]
            # Dem hoac cong ca khi lop la nguoi yeu cau chinh hoac nam trong related_classes
            formula_sheets = f'=SUMIFS(\'Nhật ký in\'!$L:$L, \'Nhật ký in\'!$D:$D, B{idx}) + SUMIFS(\'Nhật ký in\'!$L:$L, \'Nhật ký in\'!$F:$F, "*" & B{idx} & "*")'
            formula_amount = f'=SUMIFS(\'Nhật ký in\'!$R:$R, \'Nhật ký in\'!$D:$D, B{idx}) + SUMIFS(\'Nhật ký in\'!$R:$R, \'Nhật ký in\'!$F:$F, "*" & B{idx} & "*")'
            formula_count = f'=COUNTIF(\'Nhật ký in\'!$D:$D, B{idx}) + COUNTIF(\'Nhật ký in\'!$F:$F, "*" & B{idx} & "*")'

            ws_class.append([f"Khối {c[2]}", c_name, formula_count, formula_sheets, formula_amount])
            ws_class.cell(row=idx, column=5).number_format = '#,##0 "đ"'
            for c_idx in range(1, len(headers_class) + 1):
                ws_class.cell(row=idx, column=c_idx).border = thin_border

        ws_class.freeze_panes = "A2"

        # Can chinh do rong cot co dinh toi uu toc do (tranh loop hang ngan cell gay cham ung dung)
        col_widths_log = [8, 19, 14, 22, 12, 14, 32, 10, 10, 14, 10, 12, 22, 10, 14, 12, 14, 16, 10, 16, 12, 12, 20, 30]
        for col_idx, width in enumerate(col_widths_log, start=1):
            ws_log.column_dimensions[get_column_letter(col_idx)].width = width

        col_widths_teacher = [10, 25, 20, 14, 15, 18, 25]
        for col_idx, width in enumerate(col_widths_teacher, start=1):
            ws_teacher.column_dimensions[get_column_letter(col_idx)].width = width

        col_widths_class = [12, 12, 14, 15, 18]
        for col_idx, width in enumerate(col_widths_class, start=1):
            ws_class.column_dimensions[get_column_letter(col_idx)].width = width

        wb.save(output_path)
        logger.info(f"Da xuat thanh cong file Excel tong hop tai: {output_path}")
        return True, f"Đã xuất thành công file Excel tại: {output_path}"
    except Exception as e:
        logger.error(f"Loi xuat file Excel: {e}")
        return False, f"Lỗi xuất file Excel: {str(e)}"
    finally:
        conn.close()

def append_job_to_excel(job_id: int) -> bool:
    """Them mot dong ban ghi moi vao file Excel hien tai (neu bi khoa thi dua vao hang doi)"""
    excel_path = get_excel_file_path()
    if not os.path.exists(excel_path):
        success, _ = export_full_excel(excel_path)
        return success

    if is_file_locked(excel_path):
        logger.warning("File Excel dang mo, se dong bo sau qua sync_queue.")
        return False

    # Neu khong bi khoa, xuat lai de cap nhat du lieu moi nhat
    success, _ = export_full_excel(excel_path)
    return success

import threading

def append_job_to_excel_async(job_id: int):
    """Ghi vao file Excel trong luong rieng (background thread) giup UI luon muot ma 100%"""
    t = threading.Thread(target=append_job_to_excel, args=(job_id,), daemon=True)
    t.start()
