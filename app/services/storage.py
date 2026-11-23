import os
import re
import shutil
import datetime
import logging
from typing import Tuple, Optional
from app.db.models import remove_accents, get_setting

logger = logging.getLogger("print_manager.storage")

INVALID_CHARS_REGEX = re.compile(r'[\\/*?:"<>|]')

def sanitize_filename(filename: str, unaccent: bool = False, max_len: int = 80) -> str:
    """Loai bo ky tu cam cua Windows va cat do dai tranh vuot 260 ky tu"""
    if not filename:
        return "TaiLieu"
    # Loai bo ky tu cam
    clean = INVALID_CHARS_REGEX.sub("_", filename).strip()
    if unaccent:
        clean = remove_accents(clean)
    # Cat bot do dai
    name, ext = os.path.splitext(clean)
    if len(name) > max_len:
        name = name[:max_len]
    return f"{name}{ext}"

def get_storage_base_dir() -> str:
    """Lay thu muc goc luu tru tu settings"""
    base = get_setting("storage_dir", "D:\\DeDaIn")
    # Neu o dia D khong ton tai thi fallback sang o C hoac thu muc du an
    drive = os.path.splitdrive(base)[0]
    if drive and not os.path.exists(drive + "\\"):
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base = os.path.join(app_dir, "DeDaIn")
    os.makedirs(base, exist_ok=True)
    return base

def organize_and_save_files(
    original_file_path: str,
    converted_pdf_path: str,
    requester_type: str,     # 'teacher', 'class', 'other'
    requester_name: str,     # vd: 'Nguyen Thi Lan' hoac '10A1'
    copies: int = 1,
    title: str = ""
) -> Tuple[str, str]:
    """
    To chuc va luu tru ban sao file goc va file PDF theo chuan Muc 5.4:
    DeDaIn/<Loai>/<TenNguoi>/<YYYY-MM-DD>/<HHMM>_<TenDe>_<SoBan>ban.<ext>
    
    Tra ve: (saved_original_path, saved_pdf_path)
    """
    base_dir = get_storage_base_dir()
    unaccent = (get_setting("unaccent_folder_name", "0") == "1")
    save_pdf = (get_setting("save_converted_pdf", "1") == "1")

    # 1. Thu muc cap 1: Loai nguoi yeu cau
    type_map = {
        "teacher": "GiaoVien",
        "class": "Lop",
        "other": "Khac"
    }
    type_folder = type_map.get(requester_type, "Khac")

    # 2. Thu muc cap 2: Ten nguoi yeu cau
    clean_req_name = sanitize_filename(requester_name or "Chung", unaccent=unaccent, max_len=50)

    # 3. Thu muc cap 3: Ngay in (YYYY-MM-DD)
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_prefix = now.strftime("%H%M")

    target_dir = os.path.join(base_dir, type_folder, clean_req_name, date_str)
    os.makedirs(target_dir, exist_ok=True)

    # 4. Dat ten file: <HHMM>_<TenDe>_<SoBan>ban.<ext>
    file_title = title if title else os.path.splitext(os.path.basename(original_file_path))[0]
    clean_title = sanitize_filename(file_title, unaccent=unaccent, max_len=60)
    orig_ext = os.path.splitext(original_file_path)[1].lower()

    base_file_name = f"{time_prefix}_{clean_title}_{copies}ban"

    # Xu ly trung ten (them _2, _3)
    target_orig = os.path.join(target_dir, f"{base_file_name}{orig_ext}")
    counter = 2
    while os.path.exists(target_orig):
        target_orig = os.path.join(target_dir, f"{base_file_name}_{counter}{orig_ext}")
        counter += 1

    # Luu ban sao file goc
    try:
        shutil.copy2(original_file_path, target_orig)
        logger.info(f"Da luu ban sao file goc tai: {target_orig}")
    except Exception as e:
        logger.error(f"Khong the copy file goc: {e}")
        target_orig = original_file_path

    # Luu ban sao PDF (neu co va neu bat luu PDF)
    target_pdf = ""
    if save_pdf and converted_pdf_path and os.path.exists(converted_pdf_path):
        target_pdf = os.path.splitext(target_orig)[0] + ".pdf"
        try:
            if os.path.abspath(converted_pdf_path) != os.path.abspath(target_pdf):
                shutil.copy2(converted_pdf_path, target_pdf)
            logger.info(f"Da luu ban sao PDF tai: {target_pdf}")
        except Exception as e:
            logger.error(f"Khong the copy file PDF: {e}")
            target_pdf = converted_pdf_path

    return target_orig, target_pdf
