-- Schema for School Print Manager (Quan ly in an de truong THPT)
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 10000;
PRAGMA foreign_keys = ON;

-- Requesters (Giao vien, Lop, Khac)
CREATE TABLE IF NOT EXISTS requesters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('teacher', 'class', 'other')),
    department TEXT, -- To chuyen mon (doi voi giao vien)
    grade INTEGER,   -- Khoi 10, 11, 12 (doi voi lop)
    student_count INTEGER DEFAULT 0, -- Si so hoc sinh cua lop
    note TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Printers (Cau hinh may in duoc luu lai)
CREATE TABLE IF NOT EXISTS printers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    windows_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    color_supported INTEGER NOT NULL DEFAULT 0,
    duplex_supported INTEGER NOT NULL DEFAULT 1,
    papers TEXT NOT NULL DEFAULT 'A4,A3', -- danh sach kho giay cach nhau boi dau phay
    note TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Price Rules (Bang gia theo to hop)
CREATE TABLE IF NOT EXISTS price_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER, -- NULL neu ap dung chung cho tat ca may in
    paper TEXT NOT NULL DEFAULT 'A4', -- A4, A3, ...
    color INTEGER NOT NULL DEFAULT 0, -- 0: den trang, 1: mau
    duplex INTEGER NOT NULL DEFAULT 1, -- 0: 1 mat, 1: 2 mat
    price_per_unit REAL NOT NULL DEFAULT 250.0,
    unit_type TEXT NOT NULL DEFAULT 'sheet' CHECK(unit_type IN ('sheet', 'page')), -- 'sheet' (to) hoac 'page' (mat in)
    effective_from DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE SET NULL
);

-- Presets (Mau cau hinh in cai san)
CREATE TABLE IF NOT EXISTS presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    printer_id INTEGER,
    paper TEXT NOT NULL DEFAULT 'A4',
    duplex INTEGER NOT NULL DEFAULT 1,
    color INTEGER NOT NULL DEFAULT 0,
    orientation TEXT NOT NULL DEFAULT 'auto', -- auto, portrait, landscape
    note TEXT,
    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE SET NULL
);

-- Print Jobs (Nhat ky in)
CREATE TABLE IF NOT EXISTS print_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    machine_name TEXT, -- Ten may tinh Windows thuc hien in (ho tro 2 may)
    requester_id INTEGER,
    payer_id INTEGER, -- Nguoi chiu phi (neu khac requester_id)
    related_classes TEXT, -- Chuoi danh sach lop lien quan (vd: '10A1, 10A2')
    title TEXT NOT NULL, -- Ten de / file
    file_type TEXT NOT NULL, -- docx, xlsx, pptx, pdf, jpg...
    original_file_path TEXT,
    pages INTEGER NOT NULL DEFAULT 1,
    page_range TEXT, -- vd: '1-3, 5, 8-10'
    copies INTEGER NOT NULL DEFAULT 1,
    sheets INTEGER NOT NULL DEFAULT 1, -- Tong so to giay thuc te su dung
    printer_id INTEGER,
    printer_name TEXT, -- Luu ten thuc te luc in phong khi sua danh muc
    paper TEXT NOT NULL DEFAULT 'A4',
    duplex INTEGER NOT NULL DEFAULT 1,
    color INTEGER NOT NULL DEFAULT 0,
    unit_price REAL NOT NULL DEFAULT 0,
    amount REAL NOT NULL DEFAULT 0,
    amount_override REAL, -- Neu co sua tay thanh tien
    is_free INTEGER NOT NULL DEFAULT 0, -- 1 neu mien phi
    override_reason TEXT, -- Ly do sua gia hoac mien phi
    saved_path TEXT, -- Duong dan ban sao file goc
    pdf_path TEXT, -- Duong dan ban sao PDF
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'printed', 'error', 'cancelled')),
    error_message TEXT,
    paid_status TEXT NOT NULL DEFAULT 'unpaid' CHECK(paid_status IN ('unpaid', 'paid')),
    paid_at DATETIME,
    note TEXT,
    FOREIGN KEY (requester_id) REFERENCES requesters(id) ON DELETE SET NULL,
    FOREIGN KEY (payer_id) REFERENCES requesters(id) ON DELETE SET NULL,
    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE SET NULL
);

-- Related classes linking table (Quan he nhieu lop)
CREATE TABLE IF NOT EXISTS job_classes (
    job_id INTEGER NOT NULL,
    class_requester_id INTEGER NOT NULL,
    PRIMARY KEY (job_id, class_requester_id),
    FOREIGN KEY (job_id) REFERENCES print_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (class_requester_id) REFERENCES requesters(id) ON DELETE CASCADE
);

-- Excel sync queue (Hang doi dong bo khi file Excel bi khoa / dang mo)
CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    operation TEXT NOT NULL DEFAULT 'insert', -- insert, update
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'synced', 'failed')),
    retries INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    synced_at DATETIME,
    FOREIGN KEY (job_id) REFERENCES print_jobs(id) ON DELETE CASCADE
);

-- Settings (Key-Value)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes de tim kiem nhanh
CREATE INDEX IF NOT EXISTS idx_print_jobs_created_at ON print_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_print_jobs_requester ON print_jobs(requester_id);
CREATE INDEX IF NOT EXISTS idx_print_jobs_status ON print_jobs(status);
CREATE INDEX IF NOT EXISTS idx_print_jobs_paid_status ON print_jobs(paid_status);
CREATE INDEX IF NOT EXISTS idx_requesters_name ON requesters(name);
