import logging
import datetime
from typing import Dict, Any, List
from app.db.connection import get_connection

logger = logging.getLogger("print_manager.reports")

def get_dashboard_summary() -> Dict[str, Any]:
    """Lay so lieu tong quan cho bang dieu khien: Hom nay & Cong no"""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        cur = conn.cursor()
        # 1. Hom nay
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(sheets), 0), COALESCE(SUM(amount), 0)
            FROM print_jobs
            WHERE date(created_at) = date('now', 'localtime') AND status != 'cancelled'
        """)
        today_row = cur.fetchone()

        # 2. Tong no chua thu (toan bo)
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0), COUNT(*)
            FROM print_jobs
            WHERE paid_status = 'unpaid' AND is_free = 0 AND status != 'cancelled'
        """)
        unpaid_row = cur.fetchone()

        # 3. Tong da thu
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM print_jobs
            WHERE paid_status = 'paid' AND status != 'cancelled'
        """)
        paid_row = cur.fetchone()

        return {
            "today_jobs": today_row[0],
            "today_sheets": today_row[1],
            "today_amount": today_row[2],
            "unpaid_amount": unpaid_row[0],
            "unpaid_jobs": unpaid_row[1],
            "paid_amount": paid_row[0]
        }
    finally:
        conn.close()

def get_report_by_requesters(time_range: str = "month") -> List[Dict[str, Any]]:
    """Tong hop theo giao vien & nguoi yeu cau trong khoang thoi gian"""
    where_time = ""
    if time_range == "today":
        where_time = " AND date(j.created_at) = date('now', 'localtime')"
    elif time_range == "week":
        where_time = " AND j.created_at >= date('now', '-7 days', 'localtime')"
    elif time_range == "month":
        where_time = " AND j.created_at >= date('now', 'start of month', 'localtime')"

    conn = get_connection()
    try:
        cur = conn.cursor()
        query = f"""
            SELECT r.id, r.name, r.type, r.department,
                   COUNT(j.id) as job_count,
                   COALESCE(SUM(j.sheets), 0) as total_sheets,
                   COALESCE(SUM(j.amount), 0) as total_amount,
                   COALESCE(SUM(CASE WHEN j.paid_status = 'paid' THEN j.amount ELSE 0 END), 0) as paid_amount,
                   COALESCE(SUM(CASE WHEN j.paid_status = 'unpaid' AND j.is_free = 0 THEN j.amount ELSE 0 END), 0) as debt_amount
            FROM requesters r
            LEFT JOIN print_jobs j ON j.requester_id = r.id AND j.status != 'cancelled' {where_time}
            WHERE r.active = 1
            GROUP BY r.id
            HAVING job_count > 0 OR debt_amount > 0
            ORDER BY total_amount DESC, r.name ASC
        """
        cur.execute(query)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def mark_jobs_as_paid(job_ids: List[int] = None, requester_id: int = None):
    """Danh dau da thu tien cho danh sach job hoac tat ca job cua mot nguoi"""
    conn = get_connection()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with conn:
            cur = conn.cursor()
            if job_ids:
                placeholders = ",".join(["?"] * len(job_ids))
                cur.execute(
                    f"UPDATE print_jobs SET paid_status = 'paid', paid_at = ? WHERE id IN ({placeholders})",
                    [now_str] + job_ids
                )
            elif requester_id:
                cur.execute(
                    "UPDATE print_jobs SET paid_status = 'paid', paid_at = ? WHERE requester_id = ? AND paid_status = 'unpaid'",
                    (now_str, requester_id)
                )
    finally:
        conn.close()
