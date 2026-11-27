import os
import fitz  # PyMuPDF
from datetime import datetime
from typing import List, Dict, Any, Optional

def number_to_vietnamese_words(n: int) -> str:
    """Chuyen so tien thanh chu tieng Viet co ban"""
    if n == 0:
        return "Không đồng"
    
    units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    
    def read_three_digits(num: int, has_higher: bool) -> str:
        h = num // 100
        t = (num % 100) // 10
        u = num % 10
        res = []
        if h > 0 or has_higher:
            res.append(f"{units[h]} trăm")
        if t > 1:
            res.append(f"{units[t]} mươi")
        elif t == 1:
            res.append("mười")
        elif t == 0 and u > 0 and (h > 0 or has_higher):
            res.append("lẻ")
        
        if t > 1 and u == 1:
            res.append("mốt")
        elif t > 0 and u == 5:
            res.append("lăm")
        elif u > 0:
            res.append(units[u])
        return " ".join(res)

    scales = ["", "nghìn", "triệu", "tỷ"]
    parts = []
    scale_idx = 0
    temp = n
    while temp > 0:
        chunk = temp % 1000
        if chunk > 0:
            chunk_str = read_three_digits(chunk, temp >= 1000)
            scale_str = scales[scale_idx]
            parts.append(f"{chunk_str} {scale_str}".strip())
        temp //= 1000
        scale_idx += 1
    
    words = " ".join(reversed(parts)).strip()
    return words.capitalize() + " đồng"

def generate_receipt_pdf(
    requester_name: str,
    requester_type: str,
    department_or_grade: str,
    jobs: List[Dict[str, Any]],
    output_pdf_path: str,
    school_name: str = "TRƯỜNG THPT BẮC ĐÔNG QUAN"
) -> str:
    """
    Tao file PDF Phieu thu tien / Bien nhan in an chuan dep theo phong cach van ban hanh chinh truong hoc.
    """
    doc = fitz.open()
    # Kho giay A4 doc (595 x 842 points)
    page = doc.new_page(width=595, height=842)

    # 1. Header co quan ban hanh
    page.insert_text(fitz.Point(50, 50), "SỞ GIÁO DỤC VÀ ĐÀO TẠO", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
    page.insert_text(fitz.Point(50, 65), school_name.upper(), fontsize=11, fontname="helv", color=(0.1, 0.3, 0.7))
    page.draw_line(fitz.Point(50, 72), fitz.Point(230, 72), color=(0.1, 0.3, 0.7), width=1)

    page.insert_text(fitz.Point(340, 50), "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
    page.insert_text(fitz.Point(375, 65), "Độc lập - Tự do - Hạnh phúc", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
    page.draw_line(fitz.Point(365, 72), fitz.Point(525, 72), color=(0.4, 0.4, 0.4), width=1)

    # 2. Tieu de phieu
    page.insert_text(fitz.Point(120, 115), "BẢNG KÊ & PHIẾU XÁC NHẬN THANH TOÁN IN ẤN", fontsize=14, fontname="helv", color=(0.1, 0.2, 0.6))
    now_str = datetime.now().strftime("Ngày %d tháng %m năm %Y - %H:%M")
    page.insert_text(fitz.Point(210, 133), f"({now_str})", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # 3. Thong tin doi tuong
    y = 160
    type_vn = "Giáo viên" if requester_type == "teacher" else ("Lớp" if requester_type == "class" else "Khác")
    page.insert_text(fitz.Point(50, y), f"Đối tượng thanh toán: {requester_name} ({type_vn})", fontsize=11, fontname="helv")
    if department_or_grade:
        page.insert_text(fitz.Point(350, y), f"Tổ / Khối: {department_or_grade}", fontsize=11, fontname="helv")
    
    y += 20
    page.insert_text(fitz.Point(50, y), "Bộ phận thực hiện: Văn phòng In ấn - Thiết bị nhà trường", fontsize=10, fontname="helv", color=(0.3, 0.3, 0.3))

    # 4. Bang danh sach cac luot in
    y += 25
    headers = ["STT", "Thời gian", "Tên tài liệu / Đề thi", "Trang", "Bản", "Số tờ", "Thành tiền"]
    col_x = [50, 75, 175, 360, 400, 440, 490, 545]

    # Ve header bang
    page.draw_rect(fitz.Rect(col_x[0], y, col_x[-1], y + 22), color=(0.2, 0.4, 0.8), fill=(0.92, 0.95, 0.99))
    for i, h in enumerate(headers):
        page.insert_text(fitz.Point(col_x[i] + 4, y + 15), h, fontsize=9, fontname="helv", color=(0.1, 0.2, 0.5))

    y += 22
    total_sheets = 0
    total_amount = 0.0

    max_rows = min(len(jobs), 22) # Gioi han trang 1
    for idx in range(max_rows):
        job = jobs[idx]
        dt_str = str(job.get("created_at", ""))[:16]
        title = str(job.get("title", ""))[:28]
        pages = job.get("pages", 1)
        copies = job.get("copies", 1)
        sheets = job.get("sheets", 1)
        amount = float(job.get("amount", 0.0))

        total_sheets += sheets
        total_amount += amount

        bg_color = (0.98, 0.98, 0.99) if idx % 2 == 1 else (1.0, 1.0, 1.0)
        page.draw_rect(fitz.Rect(col_x[0], y, col_x[-1], y + 18), color=(0.85, 0.85, 0.85), fill=bg_color)

        page.insert_text(fitz.Point(col_x[0] + 5, y + 13), str(idx + 1), fontsize=8, fontname="helv")
        page.insert_text(fitz.Point(col_x[1] + 3, y + 13), dt_str, fontsize=8, fontname="helv")
        page.insert_text(fitz.Point(col_x[2] + 4, y + 13), title, fontsize=8, fontname="helv")
        page.insert_text(fitz.Point(col_x[3] + 8, y + 13), str(pages), fontsize=8, fontname="helv")
        page.insert_text(fitz.Point(col_x[4] + 8, y + 13), str(copies), fontsize=8, fontname="helv")
        page.insert_text(fitz.Point(col_x[5] + 8, y + 13), str(sheets), fontsize=8, fontname="helv")
        page.insert_text(fitz.Point(col_x[6] + 4, y + 13), f"{amount:,.0f} đ", fontsize=8, fontname="helv", color=(0.1, 0.1, 0.1))

        y += 18

    # Dong tong cong
    page.draw_rect(fitz.Rect(col_x[0], y, col_x[-1], y + 22), color=(0.2, 0.4, 0.8), fill=(0.94, 0.97, 1.0))
    page.insert_text(fitz.Point(col_x[0] + 10, y + 15), "TỔNG CỘNG:", fontsize=9, fontname="helv", color=(0.1, 0.2, 0.6))
    page.insert_text(fitz.Point(col_x[5] + 4, y + 15), f"{total_sheets}", fontsize=9, fontname="helv", color=(0.1, 0.2, 0.6))
    page.insert_text(fitz.Point(col_x[6] + 2, y + 15), f"{total_amount:,.0f} VNĐ", fontsize=10, fontname="helv", color=(0.8, 0.1, 0.1))

    # So tien bang chu
    y += 35
    words = number_to_vietnamese_words(int(total_amount))
    page.insert_text(fitz.Point(50, y), f"Số tiền viết bằng chữ: {words}", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))

    # 5. Khung ky ten
    y += 45
    page.insert_text(fitz.Point(75, y), "NGƯỜI NỘP TIỀN", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
    page.insert_text(fitz.Point(70, y + 14), "(Ký và ghi rõ họ tên)", fontsize=8, fontname="helv", color=(0.5, 0.5, 0.5))

    page.insert_text(fitz.Point(235, y), "NGƯỜI LẬP PHIẾU", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
    page.insert_text(fitz.Point(230, y + 14), "(Ký và ghi rõ họ tên)", fontsize=8, fontname="helv", color=(0.5, 0.5, 0.5))

    page.insert_text(fitz.Point(395, y), "PHỤ TRÁCH THỦ QUỸ / IN ẤN", fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
    page.insert_text(fitz.Point(420, y + 14), "(Xác nhận đã thu)", fontsize=8, fontname="helv", color=(0.5, 0.5, 0.5))

    doc.save(output_pdf_path)
    doc.close()
    return output_pdf_path
