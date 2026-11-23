import os
import json
import logging
import datetime
from typing import Dict, Any, List, Tuple
from app.db.connection import get_connection, get_machine_name
from app.db.models import get_setting, set_setting

logger = logging.getLogger("print_manager.cloud_sync")

def get_cloud_sync_folder() -> str:
    """Lay thu muc dong bo dam may (Google Drive, OneDrive...) tu cai dat"""
    return get_setting("cloud_sync_folder", "")

def set_cloud_sync_folder(folder_path: str):
    """Thiet lap thu muc dong bo dam may"""
    if folder_path and os.path.exists(folder_path):
        set_setting("cloud_sync_folder", folder_path)
        logger.info(f"Da dat thu muc dong bo dam may: {folder_path}")

def export_sync_package(cloud_dir: str = None) -> Tuple[bool, str]:
    """
    Xuat tat ca cac ban ghi print_jobs, requesters, price_rules cua may nay
    thanh file JSON trong thu muc dam may de may kia nap vao.
    Ten file: sync_<machine_name>.json
    """
    if not cloud_dir:
        cloud_dir = get_cloud_sync_folder()

    if not cloud_dir or not os.path.exists(cloud_dir):
        return False, "Chưa cấu hình thư mục đồng bộ đám mây (Google Drive/OneDrive) hoặc thư mục không tồn tại."

    machine = get_machine_name()
    sync_file = os.path.join(cloud_dir, f"sync_{machine}.json")

    conn = get_connection()
    try:
        cur = conn.cursor()
        # 1. Lay danh sach print_jobs cua may nay
        cur.execute("SELECT * FROM print_jobs WHERE machine_name = ?", (machine,))
        jobs = [dict(r) for r in cur.fetchall()]

        # 2. Lay danh sach requesters
        cur.execute("SELECT id, name, type, department, grade, note, active FROM requesters")
        requesters = [dict(r) for r in cur.fetchall()]

        data = {
            "version": "1.0",
            "machine_name": machine,
            "exported_at": datetime.datetime.now().isoformat(),
            "requesters": requesters,
            "jobs": jobs
        }

        # Ghi tam ra file tmp truoc khi doi ten de tranh xung dot dong bo
        tmp_file = sync_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if os.path.exists(sync_file):
            try:
                os.remove(sync_file)
            except Exception:
                pass
        os.rename(tmp_file, sync_file)

        msg = f"Đã xuất {len(jobs)} bản ghi in từ máy [{machine}] sang đám mây."
        logger.info(msg)
        return True, msg
    except Exception as e:
        logger.error(f"Loi xuat goi dong bo: {e}")
        return False, f"Lỗi xuất đồng bộ: {str(e)}"
    finally:
        conn.close()

def import_sync_packages(cloud_dir: str = None) -> Tuple[bool, str]:
    """
    Quet thu muc dam may, tim file sync cua CAC MAY KHAC va nap vao CSDL cua may nay.
    """
    if not cloud_dir:
        cloud_dir = get_cloud_sync_folder()

    if not cloud_dir or not os.path.exists(cloud_dir):
        return False, "Chưa cấu hình hoặc không tìm thấy thư mục đám mây."

    my_machine = get_machine_name()
    conn = get_connection()
    total_imported_jobs = 0
    total_imported_reqs = 0

    try:
        for fname in os.listdir(cloud_dir):
            if fname.startswith("sync_") and fname.endswith(".json") and not fname.startswith(f"sync_{my_machine}"):
                file_path = os.path.join(cloud_dir, fname)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as read_err:
                    logger.warning(f"Chua the doc file {fname} (co the dang dong bo): {read_err}")
                    continue

                source_machine = data.get("machine_name", "UNKNOWN")
                jobs = data.get("jobs", [])
                requesters = data.get("requesters", [])

                with conn:
                    cur = conn.cursor()
                    # 1. Dong bo Requesters (Giao vien, Lop)
                    for r in requesters:
                        cur.execute(
                            "INSERT INTO requesters (name, type, department, grade, note, active) "
                            "VALUES (?, ?, ?, ?, ?, ?) "
                            "ON CONFLICT(id) DO UPDATE SET "
                            "name = excluded.name, department = excluded.department, "
                            "grade = excluded.grade, note = excluded.note, active = excluded.active",
                            (r['name'], r['type'], r.get('department'), r.get('grade'), r.get('note', ''), r.get('active', 1))
                        )
                        total_imported_reqs += 1

                    # 2. Dong bo Print Jobs (Kiem tra trung theo machine_name va id tren may do hoac title+created_at)
                    for j in jobs:
                        cur.execute(
                            "SELECT id FROM print_jobs WHERE machine_name = ? AND title = ? AND created_at = ?",
                            (source_machine, j.get('title'), j.get('created_at'))
                        )
                        if not cur.fetchone():
                            cur.execute(
                                "INSERT INTO print_jobs (machine_name, requester_id, payer_id, related_classes, "
                                "title, file_type, original_file_path, pages, page_range, copies, sheets, "
                                "printer_name, paper, duplex, color, unit_price, amount, amount_override, "
                                "is_free, override_reason, saved_path, pdf_path, status, paid_status, paid_at, note, created_at) "
                                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (
                                    source_machine, j.get('requester_id'), j.get('payer_id'), j.get('related_classes'),
                                    j.get('title'), j.get('file_type', 'pdf'), j.get('original_file_path'), j.get('pages', 1),
                                    j.get('page_range'), j.get('copies', 1), j.get('sheets', 1), j.get('printer_name'),
                                    j.get('paper', 'A4'), j.get('duplex', 1), j.get('color', 0), j.get('unit_price', 0),
                                    j.get('amount', 0), j.get('amount_override'), j.get('is_free', 0), j.get('override_reason'),
                                    j.get('saved_path'), j.get('pdf_path'), j.get('status', 'printed'), j.get('paid_status', 'unpaid'),
                                    j.get('paid_at'), j.get('note'), j.get('created_at')
                                )
                            )
                            total_imported_jobs += 1

        msg = f"Đồng bộ thành công! Đã nạp {total_imported_jobs} lượt in mới từ các máy ở xa."
        logger.info(msg)
        return True, msg
    except Exception as e:
        logger.error(f"Loi nap goi dong bo: {e}")
        return False, f"Lỗi đồng bộ: {str(e)}"
    finally:
        conn.close()

def sync_both_ways(cloud_dir: str = None) -> Tuple[bool, str]:
    """Thuc hien dong bo 2 chieu: Nhap du lieu moi ve truoc, sau do Xuat du lieu cua minh len"""
    ok_in, msg_in = import_sync_packages(cloud_dir)
    ok_out, msg_out = export_sync_package(cloud_dir)
    if ok_in or ok_out:
        return True, f"{msg_in}\n{msg_out}"
    return False, f"{msg_in} | {msg_out}"
