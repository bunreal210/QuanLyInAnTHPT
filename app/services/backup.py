import os
import shutil
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Tuple
from app.db.connection import get_database_path, get_connection

logger = logging.getLogger("print_manager.backup")

def create_database_backup(destination_dir: str = None) -> Tuple[bool, str]:
    """
    Sao luu an toan CSDL SQLite bang API backup truc tiep cua SQLite,
    chong loi khi CSDL dang o che do WAL.
    """
    db_path = get_database_path()
    if not os.path.exists(db_path):
        return False, f"File CSDL khong ton tai tai: {db_path}"

    if not destination_dir:
        destination_dir = os.path.join(os.path.dirname(db_path), "backups")

    try:
        os.makedirs(destination_dir, exist_ok=True)
    except Exception as e:
        return False, f"Khong the tao thu muc sao luu: {e}"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"PrintManager_Backup_{timestamp}.bak"
    backup_path = os.path.join(destination_dir, backup_filename)

    try:
        source_conn = get_connection()
        dest_conn = sqlite3.connect(backup_path)
        with dest_conn:
            source_conn.backup(dest_conn)
        dest_conn.close()
        source_conn.close()

        file_size = os.path.getsize(backup_path)
        logger.info(f"Da tao ban sao luu thanh cong: {backup_path} ({file_size} bytes)")
        return True, backup_path
    except Exception as e:
        logger.error(f"Loi khi sao luu CSDL: {e}")
        return False, str(e)

def restore_database_from_backup(backup_path: str) -> Tuple[bool, str]:
    """
    Khoi phuc CSDL tu file sao luu .bak.
    Kiem tra tinh toan ven PRAGMA integrity_check truoc khi ghi de.
    """
    if not os.path.exists(backup_path):
        return False, f"File sao luu khong ton tai: {backup_path}"

    # 1. Kiem tra tinh toan ven cua file backup
    try:
        test_conn = sqlite3.connect(backup_path)
        cur = test_conn.cursor()
        cur.execute("PRAGMA integrity_check")
        res = cur.fetchone()
        test_conn.close()
        if not res or res[0] != "ok":
            return False, "File sao luu bi loi hoac khong phai file SQLite hop le!"
    except Exception as check_err:
        return False, f"Kiem tra file sao luu that bai: {check_err}"

    # 2. Thuc hien khoi phuc
    db_path = get_database_path()
    try:
        # Tao ban du phong an toan truoc khi ghi de
        if os.path.exists(db_path):
            safety_copy = db_path + ".pre_restore"
            shutil.copy2(db_path, safety_copy)

        dest_conn = get_connection()
        source_conn = sqlite3.connect(backup_path)
        with dest_conn:
            source_conn.backup(dest_conn)
        source_conn.close()
        dest_conn.close()

        logger.info(f"Da khoi phuc CSDL thanh cong tu: {backup_path}")
        return True, f"Đã khôi phục thành công cơ sở dữ liệu từ: {os.path.basename(backup_path)}"
    except Exception as restore_err:
        logger.error(f"Loi khoi phuc CSDL: {restore_err}")
        return False, str(restore_err)
