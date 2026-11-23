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

    app = QApplication(sys.argv)
    app.setApplicationName("Quản lý in ấn đề - THPT")

    # Font chu he thong dep cho tieng Viet tren Windows
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Khoi dong giao dien chinh
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
