import os
import math
import logging
import pymupdf  # PyMuPDF

logger = logging.getLogger("print_manager.booklet")

def create_booklet_pdf(input_pdf_path: str, output_pdf_path: str, target_paper: str = "A4") -> str:
    """
    Bien doi file PDF bat ky thanh file PDF dang Booklet (in kieu sach / tap gap doi).
    
    Quy tac:
    - So trang phai la boi so cua 4 (neu thieu thi bo sung trang trang vao cuoi).
    - Moi to giay se chua 4 trang goc (2 trang o mat truoc, 2 trang o mat sau).
    - Sau khi in 2 mat (lat canh ngan - duplex short), gap doi to giay lai se thanh quyen sach theo dung thu tu 1, 2, 3...
    
    Vi du tap 8 trang:
    - To 1 Mat truoc: [Trang 8] [Trang 1]
    - To 1 Mat sau:   [Trang 2] [Trang 7]
    - To 2 Mat truoc: [Trang 6] [Trang 3]
    - To 2 Mat sau:   [Trang 4] [Trang 5]
    """
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Khong tim thay file PDF: {input_pdf_path}")

    src_doc = pymupdf.open(input_pdf_path)
    src_page_count = len(src_doc)
    if src_page_count == 0:
        src_doc.close()
        raise ValueError("File PDF khong co trang nao!")

    # 1. Tinh so trang can bo sung de tong so trang la boi so cua 4
    total_pages = math.ceil(src_page_count / 4.0) * 4
    blank_pages_needed = total_pages - src_page_count

    # Kich thuoc to giay in booklet (A4 nam ngang hoac A3 nam ngang)
    # A4: 595 x 842 points -> A4 Landscape: 842 x 595 (moi trang con la A5: 421 x 595)
    # A3: 842 x 1191 points -> A3 Landscape: 1191 x 842 (moi trang con la A4: 595 x 842)
    if target_paper.upper() == "A3":
        sheet_w, sheet_h = 1191, 842
    else: # Mac dinh A4
        sheet_w, sheet_h = 842, 595

    half_w = sheet_w / 2.0
    rect_left = pymupdf.Rect(0, 0, half_w, sheet_h)
    rect_right = pymupdf.Rect(half_w, 0, sheet_w, sheet_h)

    out_doc = pymupdf.open()

    # So to giay booklet
    sheets_count = total_pages // 4

    for sheet_idx in range(sheets_count):
        # 1. Mat truoc (Front page)
        front_left_page_num = total_pages - (2 * sheet_idx)      # 8, 6, ...
        front_right_page_num = (2 * sheet_idx) + 1               # 1, 3, ...

        page_front = out_doc.new_page(width=sheet_w, height=sheet_h)
        _place_subpage(out_doc, page_front, src_doc, front_left_page_num, rect_left, src_page_count)
        _place_subpage(out_doc, page_front, src_doc, front_right_page_num, rect_right, src_page_count)

        # Duong ke gap o giua mat truoc (mo nhat de huong dan gap)
        page_front.draw_line(pymupdf.Point(half_w, 0), pymupdf.Point(half_w, sheet_h), color=(0.85, 0.85, 0.85), width=0.5)

        # 2. Mat sau (Back page)
        back_left_page_num = (2 * sheet_idx) + 2                 # 2, 4, ...
        back_right_page_num = total_pages - (2 * sheet_idx) - 1  # 7, 5, ...

        page_back = out_doc.new_page(width=sheet_w, height=sheet_h)
        _place_subpage(out_doc, page_back, src_doc, back_left_page_num, rect_left, src_page_count)
        _place_subpage(out_doc, page_back, src_doc, back_right_page_num, rect_right, src_page_count)

        # Duong ke gap o giua mat sau
        page_back.draw_line(pymupdf.Point(half_w, 0), pymupdf.Point(half_w, sheet_h), color=(0.85, 0.85, 0.85), width=0.5)

    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    out_doc.save(output_pdf_path)
    out_doc.close()
    src_doc.close()

    logger.info(f"Da tao thanh cong Booklet PDF {total_pages} trang ({sheets_count} to 2 mat): {output_pdf_path}")
    return output_pdf_path

def _place_subpage(out_doc, target_page, src_doc, page_num_1based, target_rect, src_max_pages):
    """Ve noi dung trang nguon vao nua to giay (neu trang thieu thi de trang)"""
    if 1 <= page_num_1based <= src_max_pages:
        src_page = src_doc[page_num_1based - 1]
        target_page.show_pdf_page(target_rect, src_doc, page_num_1based - 1)
    else:
        # Trang trang (blank padding)
        pass
