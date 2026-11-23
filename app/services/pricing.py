import math
import logging
from typing import Dict, Any, List
from app.db.models import get_price, get_setting

logger = logging.getLogger("print_manager.pricing")

def calculate_print_cost(
    pages_count: int,
    copies: int = 1,
    printer_id: int = None,
    paper: str = "A4",
    duplex: int = 1, # 0: 1 mat, 1: 2 mat lat dai, 2: 2 mat lat ngan, 3: booklet
    color: int = 0,  # 0: den trang, 1: mau
    is_booklet: bool = False
) -> Dict[str, Any]:
    """
    Tinh so to giay va thanh tien theo dung quy tac Muc 5.3:
    - In 1 mat: so_to_moi_ban = so_trang
    - In 2 mat: so_to_moi_ban = ceil(so_trang / 2)
    - In Booklet: 1 to chua 4 trang -> so_to_moi_ban = ceil(so_trang / 4)
    - Tong so to = so_to_moi_ban * so_ban
    - Thanh tien = tong_so_to * don_gia (hoac tong_so_mat * don_gia tuy cai dat)
    """
    if pages_count <= 0:
        pages_count = 1
    if copies <= 0:
        copies = 1

    unit_type = get_setting("pricing_unit", "sheet") # 'sheet' (to) hoac 'page' (mat in)

    # 1. Tinh so to cho 1 ban
    if is_booklet or duplex == 3:
        sheets_per_copy = math.ceil(pages_count / 4.0)
        duplex_for_price = 1 # Booklet luon in 2 mat
    elif duplex in (1, 2):
        sheets_per_copy = math.ceil(pages_count / 2.0)
        duplex_for_price = 1
    else:
        sheets_per_copy = pages_count
        duplex_for_price = 0

    total_sheets = sheets_per_copy * copies
    total_pages = pages_count * copies

    # 2. Lay don gia tu DB
    unit_price = get_price(printer_id=printer_id, paper=paper, color=color, duplex=duplex_for_price)

    # 3. Tinh thanh tien
    if unit_type == "page":
        # Tinh theo mat in: 1 mat = 1 trang, in 2 mat van la tinh so trang
        amount = total_pages * unit_price
    else:
        # Tinh theo to giay thuc te su dung (pho bien nhat)
        amount = total_sheets * unit_price

    return {
        "pages_per_copy": pages_count,
        "copies": copies,
        "sheets_per_copy": sheets_per_copy,
        "total_sheets": total_sheets,
        "total_pages": total_pages,
        "unit_price": unit_price,
        "amount": amount,
        "unit_type": unit_type
    }
