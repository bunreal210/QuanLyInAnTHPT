import os
import sys
import subprocess
import logging
from typing import Tuple, List, Optional
from PIL import Image
import pymupdf  # PyMuPDF

logger = logging.getLogger("print_manager.converter")

APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP_PDF_DIR = os.path.join(APP_DIR, "data", "temp_pdf")
os.makedirs(TEMP_PDF_DIR, exist_ok=True)

# Tim kiem duong dan LibreOffice neu co tren may
def find_libreoffice_path() -> Optional[str]:
    possible_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def convert_word_to_pdf_com(input_path: str, output_pdf_path: str) -> bool:
    """Chuyen doi Word (.doc, .docx) sang PDF bang Microsoft Office COM"""
    import win32com.client
    import pythoncom

    pythoncom.CoInitialize()
    word = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        # Vo hieu hoa macro tu file la (bao ve khoi ma doc USB)
        # msoAutomationSecurityForceDisable = 3
        try:
            word.AutomationSecurity = 3
        except Exception:
            pass

        doc = word.Documents.Open(os.path.abspath(input_path), ReadOnly=True)
        # wdExportFormatPDF = 17
        doc.ExportAsFixedFormat(
            OutputFileName=os.path.abspath(output_pdf_path),
            ExportFormat=17,
            OpenAfterExport=False,
            OptimizeFor=0  # wdExportOptimizeForPrint = 0
        )
        doc.Close(SaveChanges=False)
        return True
    except Exception as e:
        logger.error(f"Loi chuyen Word qua COM: {e}")
        return False
    finally:
        if word:
            try:
                word.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()

def convert_excel_to_pdf_com(input_path: str, output_pdf_path: str) -> bool:
    """Chuyen doi Excel (.xls, .xlsx) sang PDF bang Microsoft Office COM"""
    import win32com.client
    import pythoncom

    pythoncom.CoInitialize()
    excel = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        try:
            excel.AutomationSecurity = 3
        except Exception:
            pass

        wb = excel.Workbooks.Open(os.path.abspath(input_path), ReadOnly=True)
        # xlTypePDF = 0
        wb.ExportAsFixedFormat(0, os.path.abspath(output_pdf_path))
        wb.Close(SaveChanges=False)
        return True
    except Exception as e:
        logger.error(f"Loi chuyen Excel qua COM: {e}")
        return False
    finally:
        if excel:
            try:
                excel.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()

def convert_powerpoint_to_pdf_com(input_path: str, output_pdf_path: str) -> bool:
    """Chuyen doi PowerPoint (.ppt, .pptx) sang PDF bang Microsoft Office COM"""
    import win32com.client
    import pythoncom

    pythoncom.CoInitialize()
    powerpoint = None
    try:
        powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
        # With PowerPoint, setting AutomationSecurity must be done carefully
        presentation = powerpoint.Presentations.Open(
            os.path.abspath(input_path),
            ReadOnly=True,
            Untitled=False,
            WithWindow=False
        )
        # ppFixedFormatTypePDF = 2
        presentation.ExportAsFixedFormat(
            Path=os.path.abspath(output_pdf_path),
            FixedFormatType=2,
            PrintRange=None
        )
        presentation.Close()
        return True
    except Exception as e:
        logger.error(f"Loi chuyen PowerPoint qua COM: {e}")
        return False
    finally:
        if powerpoint:
            try:
                powerpoint.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()

def convert_office_via_libreoffice(input_path: str, output_pdf_path: str, soffice_path: str = None) -> bool:
    """Phuong an du phong: Chuyen doi Office sang PDF qua LibreOffice Headless"""
    if not soffice_path:
        soffice_path = find_libreoffice_path()

    if not soffice_path or not os.path.exists(soffice_path):
        return False

    out_dir = os.path.dirname(output_pdf_path)
    cmd = [
        soffice_path,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", out_dir,
        os.path.abspath(input_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=60)
        # Libreoffice se dat ten file giong file goc nhung duoi .pdf
        base_name = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
        generated_pdf = os.path.join(out_dir, base_name)
        if os.path.exists(generated_pdf):
            if generated_pdf != output_pdf_path:
                if os.path.exists(output_pdf_path):
                    os.remove(output_pdf_path)
                os.rename(generated_pdf, output_pdf_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Loi chuyen LibreOffice: {e}")
        return False

def convert_image_to_pdf(input_path: str, output_pdf_path: str, paper: str = "A4") -> bool:
    """Chuyen doi anh (.jpg, .png, .bmp, .tiff) sang PDF chuan A4"""
    try:
        # A4 kich thuoc chuan: 595 x 842 points
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)

        # Lay kich thuoc anh goc
        with Image.open(input_path) as img:
            img_w, img_h = img.size

        # Tinh toan ty le de anh vua van trang A4 voi le 20pt
        margin = 20
        max_w = 595 - (2 * margin)
        max_h = 842 - (2 * margin)

        ratio = min(max_w / img_w, max_h / img_h)
        target_w = img_w * ratio
        target_h = img_h * ratio

        # Can giua trang
        x0 = margin + (max_w - target_w) / 2
        y0 = margin + (max_h - target_h) / 2
        rect = pymupdf.Rect(x0, y0, x0 + target_w, y0 + target_h)

        page.insert_image(rect, filename=input_path)
        doc.save(output_pdf_path)
        doc.close()
        return True
    except Exception as e:
        logger.error(f"Loi chuyen anh sang PDF: {e}")
        return False

def convert_to_pdf(input_path: str, custom_output_path: str = None) -> Tuple[bool, str, str]:
    """
    Ham tong hop chuyen doi bat ky dinh dang nao sang PDF.
    Tra ve: (ThanhCong, DuongDanPDF, ThongBaoLoi)
    """
    if not os.path.exists(input_path):
        return False, "", "File không tồn tại hoặc đã bị xóa."

    ext = os.path.splitext(input_path)[1].lower()
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    if not custom_output_path:
        out_pdf = os.path.join(TEMP_PDF_DIR, f"{base_name}_{abs(hash(input_path)) % 1000000}.pdf")
    else:
        out_pdf = custom_output_path

    # Neu da la file PDF
    if ext == ".pdf":
        return True, input_path, ""

    # Dinh dang anh
    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"]:
        success = convert_image_to_pdf(input_path, out_pdf)
        if success:
            return True, out_pdf, ""
        return False, "", "Không thể chuyển đổi file ảnh sang PDF."

    # Dinh dang Word
    if ext in [".doc", ".docx"]:
        success = convert_word_to_pdf_com(input_path, out_pdf)
        if not success:
            logger.info("Chuyen thu sang LibreOffice...")
            success = convert_office_via_libreoffice(input_path, out_pdf)
        if success:
            return True, out_pdf, ""
        return False, "", "Không thể chuyển file Word sang PDF. Vui lòng kiểm tra xem máy có cài Microsoft Office hoặc LibreOffice không."

    # Dinh dang Excel
    if ext in [".xls", ".xlsx"]:
        success = convert_excel_to_pdf_com(input_path, out_pdf)
        if not success:
            success = convert_office_via_libreoffice(input_path, out_pdf)
        if success:
            return True, out_pdf, ""
        return False, "", "Không thể chuyển file Excel sang PDF."

    # Dinh dang PowerPoint
    if ext in [".ppt", ".pptx"]:
        success = convert_powerpoint_to_pdf_com(input_path, out_pdf)
        if not success:
            success = convert_office_via_libreoffice(input_path, out_pdf)
        if success:
            return True, out_pdf, ""
        return False, "", "Không thể chuyển file PowerPoint sang PDF."

    return False, "", f"Định dạng file '{ext}' chưa được hỗ trợ."

def count_pages(pdf_path: str) -> int:
    """Dem tong so trang cua file PDF"""
    try:
        doc = pymupdf.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except Exception as e:
        logger.error(f"Loi dem trang PDF: {e}")
        return 1

def render_page_thumbnail(pdf_path: str, page_number_1based: int = 1, output_png_path: str = None) -> Optional[str]:
    """Render 1 trang PDF thanh anh PNG de hien thi xem truoc tren giao dien"""
    try:
        doc = pymupdf.open(pdf_path)
        if page_number_1based < 1 or page_number_1based > len(doc):
            page_number_1based = 1
        page = doc[page_number_1based - 1]
        pix = page.get_pixmap(dpi=120)

        if not output_png_path:
            output_png_path = os.path.join(TEMP_PDF_DIR, f"preview_{page_number_1based}_{abs(hash(pdf_path)) % 1000000}.png")

        pix.save(output_png_path)
        doc.close()
        return output_png_path
    except Exception as e:
        logger.error(f"Loi render preview PDF: {e}")
        return None

def parse_page_ranges(range_str: str, total_pages: int) -> List[int]:
    """
    Phan tich cu phap khoang trang in (vd: '1-3, 5, 8-10') thanh danh sach so trang 1-based hop le.
    Neu de trong, tra ve tat ca cac trang tu 1 den total_pages.
    """
    if not range_str or not range_str.strip():
        return list(range(1, total_pages + 1))

    selected_pages = set()
    parts = range_str.replace(";", ",").split(",")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            sub = part.split("-")
            if len(sub) == 2:
                try:
                    start = int(sub[0].strip())
                    end = int(sub[1].strip())
                    if start <= end:
                        for p in range(start, end + 1):
                            if 1 <= p <= total_pages:
                                selected_pages.add(p)
                except ValueError:
                    continue
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    selected_pages.add(p)
            except ValueError:
                continue

    result = sorted(list(selected_pages))
    return result if result else list(range(1, total_pages + 1))

def extract_pages_to_new_pdf(src_pdf: str, target_pdf: str, pages_1based: List[int]) -> str:
    """Tach chi cac trang duoc chon ra file PDF moi de in"""
    src_doc = pymupdf.open(src_pdf)
    out_doc = pymupdf.open()
    for p in pages_1based:
        if 1 <= p <= len(src_doc):
            out_doc.insert_pdf(src_doc, from_page=p-1, to_page=p-1)
    out_doc.save(target_pdf)
    out_doc.close()
    src_doc.close()
    return target_pdf
