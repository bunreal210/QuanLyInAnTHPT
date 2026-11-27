import os
import sys
import sqlite3
import socket
import logging

logger = logging.getLogger("print_manager.db")

APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DATA_DIR = os.path.join(APP_DIR, "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "print_manager.db")

# Cache current DB path
_CURRENT_DB_PATH = None

def get_machine_name():
    """Lay ten may tinh Windows hien tai (ho tro phan biet 2 may)"""
    return socket.gethostname()

def get_database_path():
    """Lay duong dan database hien tai tu file config hoac mac dinh"""
    global _CURRENT_DB_PATH
    if _CURRENT_DB_PATH:
        return _CURRENT_DB_PATH

    # Kiem tra file config cuc bo local_settings.ini neu co
    config_file = os.path.join(APP_DIR, "local_config.txt")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                path = f.read().strip()
                if path and os.path.exists(os.path.dirname(path)):
                    _CURRENT_DB_PATH = path
                    return _CURRENT_DB_PATH
        except Exception as e:
            logger.warning(f"Loi doc local_config.txt: {e}")

    os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
    _CURRENT_DB_PATH = DEFAULT_DB_PATH
    return _CURRENT_DB_PATH

def set_database_path(new_path):
    """Luu duong dan database moi (khi nguoi dung tro sang thu muc mang dung chung 2 may)"""
    global _CURRENT_DB_PATH
    dir_name = os.path.dirname(new_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    _CURRENT_DB_PATH = new_path
    config_file = os.path.join(APP_DIR, "local_config.txt")
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(new_path)
    logger.info(f"Da chuyen duong dan database sang: {new_path}")
    init_db()

def get_connection():
    """Tao ket noi SQLite voi che do WAL, cache toi uu may yeu va Memory-Mapped I/O doc dia HDD sieu toc"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 10000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -16000;") # 16MB cache vua van khong chiem RAM may yeu
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA mmap_size = 33554432;") # 32MB Memory-Mapped I/O tang toc doc CSDL tren o dia HDD
    return conn

def init_db():
    """Khoi tao database theo schema va chen du lieu co dinh ban dau"""
    db_path = get_database_path()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Khong tim thay file schema: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        with conn:
            conn.executescript(schema_sql)
            # Migration: Dam bao cot student_count ton tai trong requesters
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(requesters)")
            cols = [col[1] for col in cur.fetchall()]
            if "student_count" not in cols:
                conn.execute("ALTER TABLE requesters ADD COLUMN student_count INTEGER DEFAULT 0;")
                logger.info("Da chay migration them cot student_count vao bang requesters.")

            # Indexes toi uu hieu nang cho Dashboard & Bao cao
            conn.execute("CREATE INDEX IF NOT EXISTS idx_print_jobs_dashboard ON print_jobs(status, paid_status, is_free);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_print_jobs_created_status ON print_jobs(created_at, status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_requesters_type_active ON requesters(type, active);")

            _seed_default_data(conn)
        logger.info(f"Khoi tao database thanh cong tai: {db_path}")
    finally:
        conn.close()

def _seed_default_data(conn):
    """Nap 42 lop co dinh, cai dat he thong va cac mau in mac dinh neu chua co"""
    cursor = conn.cursor()

    # 1. Kiem tra va nap 42 lop hoc: 10A1 -> 10A14, 11A1 -> 11A14, 12A1 -> 12A14
    cursor.execute("SELECT COUNT(*) FROM requesters WHERE type = 'class'")
    class_count = cursor.fetchone()[0]
    if class_count == 0:
        logger.info("Dang nap 42 lop hoc co dinh (Khoi 10, 11, 12)...")
        classes_data = []
        for grade in [10, 11, 12]:
            for num in range(1, 15):
                class_name = f"{grade}A{num}"
                classes_data.append((class_name, 'class', None, grade, f"Lop {class_name}"))
        cursor.executemany(
            "INSERT INTO requesters (name, type, department, grade, note) VALUES (?, ?, ?, ?, ?)",
            classes_data
        )

    # 2. Nap cai dat mac dinh vao bang settings
    default_settings = [
        ('storage_dir', 'D:\\DeDaIn'),
        ('excel_path', 'D:\\DeDaIn\\TongHopInAn.xlsx'),
        ('pricing_unit', 'sheet'), # 'sheet' (theo to giay) hoac 'page' (theo mat in)
        ('unaccent_folder_name', '0'), # 0: giu nguyen tieng Viet co dau, 1: bo dau
        ('save_converted_pdf', '1'), # 1: luu ca file PDF da chuyen doi, 0: chi luu file goc
        ('warn_high_pages_threshold', '100'), # Canh bao neu so trang vuot nguon
        ('warn_high_copies_threshold', '100'), # Canh bao neu so ban in qua lon
        ('sumatra_path', ''), # De trong de he thong tu dong nhan dien duong dan chinh xac theo runtime
        ('libreoffice_path', ''), # Tu do tim neu de trong
        ('backup_dir', os.path.join(APP_DIR, "backups")),
        ('auto_backup_days', '30')
    ]
    for key, val in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

    # Tu dong don dep sumatra_path neu dang tro vao duong dan temp _MEI cu hoac khong ton tai
    try:
        cursor.execute("SELECT value FROM settings WHERE key = 'sumatra_path'")
        row = cursor.fetchone()
        if row and row[0]:
            val = str(row[0])
            if "_MEI" in val or not os.path.exists(val):
                cursor.execute("UPDATE settings SET value = '' WHERE key = 'sumatra_path'")
    except Exception:
        pass

    # 3. Nap bang gia mac dinh (to hop chung: NULL cho printer_id nghia la ap dung moi may)
    cursor.execute("SELECT COUNT(*) FROM price_rules")
    if cursor.fetchone()[0] == 0:
        default_prices = [
            (None, 'A4', 0, 0, 250.0, 'sheet'), # A4 trang den 1 mat: 250d/to
            (None, 'A4', 0, 1, 350.0, 'sheet'), # A4 trang den 2 mat: 350d/to
            (None, 'A4', 1, 0, 1000.0, 'sheet'), # A4 mau 1 mat: 1000d/to
            (None, 'A4', 1, 1, 1500.0, 'sheet'), # A4 mau 2 mat: 1500d/to
            (None, 'A3', 0, 0, 500.0, 'sheet'), # A3 trang den 1 mat: 500d/to
            (None, 'A3', 0, 1, 700.0, 'sheet'), # A3 trang den 2 mat: 700d/to
            (None, 'A3', 1, 0, 2000.0, 'sheet'), # A3 mau 1 mat: 2000d/to
            (None, 'A3', 1, 1, 3000.0, 'sheet'), # A3 mau 2 mat: 3000d/to
        ]
        cursor.executemany(
            "INSERT INTO price_rules (printer_id, paper, color, duplex, price_per_unit, unit_type) VALUES (?, ?, ?, ?, ?, ?)",
            default_prices
        )

    # 4. Nap mau cau hinh in cai san (presets)
    cursor.execute("SELECT COUNT(*) FROM presets")
    if cursor.fetchone()[0] == 0:
        default_presets = [
            ("Đề kiểm tra chuẩn (A4, 2 mặt, Đen trắng)", None, 'A4', 1, 0, 'auto', "In đề thi / kiểm tra 2 mặt"),
            ("Phiếu học tập (A4, 1 mặt, Đen trắng)", None, 'A4', 0, 0, 'auto', "Phiếu học tập hoặc đề 1 trang"),
            ("Tài liệu A3 (A3, 2 mặt, Đen trắng)", None, 'A3', 1, 0, 'auto', "In giấy thi, tài liệu A3 gập đôi"),
            ("Bìa màu / Tài liệu màu (A4, 1 mặt, Màu)", None, 'A4', 0, 1, 'auto', "In trang bìa hoặc phụ lục ảnh màu")
        ]
        cursor.executemany(
            "INSERT INTO presets (name, printer_id, paper, duplex, color, orientation, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
            default_presets
        )
