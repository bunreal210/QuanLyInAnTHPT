import os
import sys
import logging

# Xu ly sys.path de chay duoc ca khi chay ma nguon truc tiep va khi dong goi exe bang PyInstaller
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    EXE_DIR = os.path.dirname(sys.executable)
    for p in [BUNDLE_DIR, EXE_DIR]:
        if p not in sys.path:
            sys.path.insert(0, p)
    # Phong truong hop PyInstaller dong goi dat thang noi dung 'app' o root
    if "app" not in sys.modules:
        try:
            import db
            import services
            import ui
            import types
            app_mod = types.ModuleType("app")
            app_mod.db = db
            app_mod.services = services
            app_mod.ui = ui
            sys.modules["app"] = app_mod
            sys.modules["app.db"] = db
            sys.modules["app.db.connection"] = getattr(db, 'connection', None)
            sys.modules["app.db.models"] = getattr(db, 'models', None)
            sys.modules["app.services"] = services
            sys.modules["app.ui"] = ui
        except Exception:
            pass
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app.db.connection import init_db
from app.ui.main_window import MainWindow

def get_app_icon_path() -> str:
    """Lay duong dan file icon ung dung ho tro ca khi chay truc tiep va khi dong goi exe"""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.ico"),
        os.path.join(getattr(sys, '_MEIPASS', ''), "app", "resources", "icon.ico"),
        os.path.join(getattr(sys, '_MEIPASS', ''), "resources", "icon.ico"),
        os.path.join(os.path.dirname(sys.executable), "app", "resources", "icon.ico"),
        os.path.join(os.path.dirname(sys.executable), "resources", "icon.ico"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "resources", "icon.ico"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return ""

def setup_logging():
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(log_dir, "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger("print_manager")
    logger.info("Khoi dong ung dung Quan ly in an de truong THPT...")

    # Khoi tao CSDL SQLite
    try:
        init_db()
    except Exception as e:
        logger.error(f"Khong the khoi tao database: {e}", exc_info=True)

    # Don dep ngam cac file rac temp cu ma khong lam cham khoi dong
    try:
        import threading
        from app.services.converter import clean_old_temp_files
        threading.Thread(target=clean_old_temp_files, daemon=True).start()
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Quản lý in ấn")
    app.setApplicationDisplayName("Quản lý in ấn - Trường THPT Bắc Đông Quan")
    app.setOrganizationName("Trường THPT Bắc Đông Quan")
    app.setOrganizationDomain("thptbacdongquan.edu.vn")

    icon_path = get_app_icon_path()
    if icon_path:
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(icon_path))

    # Ép kiểu giao diện Fusion và bảng màu Light Theme nhất quán, bất chấp Windows Dark Mode
    app.setStyle("Fusion")
    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f8fafc"))
    palette.setColor(QPalette.WindowText, QColor("#0f172a"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f1f5f9"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#0f172a"))
    palette.setColor(QPalette.Text, QColor("#0f172a"))
    palette.setColor(QPalette.Button, QColor("#f8fafc"))
    palette.setColor(QPalette.ButtonText, QColor("#0f172a"))
    palette.setColor(QPalette.BrightText, QColor("#dc2626"))
    palette.setColor(QPalette.Link, QColor("#2563eb"))
    palette.setColor(QPalette.Highlight, QColor("#2563eb"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # Font chu he thong dep cho tieng Viet tren Windows
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Khoi dong giao dien chinh
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
