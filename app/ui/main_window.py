import os
import sys
import datetime
import subprocess
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QCheckBox, QGroupBox, QTextEdit,
    QMessageBox, QSpinBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QSplitter, QFrame, QScrollArea, QAbstractItemView,
    QProgressBar, QDialog, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor, QImage, QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
import fitz

from app.services.converter import (
    convert_to_pdf, count_pages, render_page_thumbnail, render_page_pixmap_data,
    parse_page_ranges, extract_pages_to_new_pdf,
    WordBatchConverter, ExcelBatchConverter
)
from app.services.booklet import create_booklet_pdf
from app.services.printer import (
    list_windows_printers, build_sumatra_print_settings, execute_sumatra_print,
    open_windows_print_dialog, open_printer_preferences_dialog, open_printer_device_settings_dialog
)
from app.services.storage import organize_and_save_files
from app.services.pricing import calculate_print_cost
from app.services.excel_sync import export_full_excel, append_job_to_excel, append_job_to_excel_async
from app.services.cloud_sync import (
    get_cloud_sync_folder, set_cloud_sync_folder, sync_both_ways
)
from app.services.reports import (
    get_dashboard_summary, get_report_by_requesters, mark_jobs_as_paid,
    get_jobs_for_requester
)
from app.services.receipt import generate_receipt_pdf
from app.services.backup import create_database_backup, restore_database_from_backup
from app.db.connection import get_machine_name, get_connection
from app.db.models import (
    get_requesters, search_requesters, get_recent_requester_ids, get_cached_requesters,
    get_printers, get_presets, get_setting, set_setting,
    create_print_job, update_print_job_status, add_requester,
    get_all_price_rules, update_price_rule_amount, add_price_rule,
    delete_price_rule, reset_default_prices,
    import_classes_from_excel, create_classes_template_excel,
    import_teachers_from_excel, create_teachers_template_excel
)

def play_alert_sound():
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

MODERN_STYLE = """
/* Modern Clean Light Theme for QuanLyInAnTHPT */
QMainWindow {
    background-color: #f8fafc;
}
QWidget#centralWidget {
    background-color: #f8fafc;
}
QScrollArea {
    background-color: #f8fafc;
    border: none;
}
QScrollArea > QWidget {
    background-color: #f8fafc;
}
QScrollArea > QWidget > QWidget {
    background-color: #f8fafc;
}
QWidget {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #1e293b;
    font-size: 10pt;
}
QTabWidget::pane {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    background-color: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background-color: #f1f5f9;
    color: #475569;
    font-weight: 600;
    font-size: 10.5pt;
    padding: 10px 18px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #cbd5e1;
    border-bottom: none;
}
QTabBar::tab:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}
QTabBar::tab:selected {
    background-color: #1d4ed8;
    color: #ffffff;
    border-color: #1d4ed8;
}
QGroupBox {
    font-weight: bold;
    font-size: 10pt;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 20px;
    padding-left: 14px;
    padding-right: 14px;
    padding-bottom: 14px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 3px 12px;
    background-color: #2563eb;
    color: #ffffff;
    border-radius: 4px;
    font-weight: bold;
    font-size: 9.5pt;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 10pt;
    color: #0f172a;
    min-height: 22px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 2px solid #2563eb;
    background-color: #ffffff;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #dbeafe;
    selection-color: #1e3a8a;
    border: 1px solid #cbd5e1;
}
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    gridline-color: #e2e8f0;
    selection-background-color: #dbeafe;
    selection-color: #1e3a8a;
    color: #0f172a;
}
QTableCornerButton::section {
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
}
QHeaderView::section {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: bold;
    border: none;
    border-right: 1px solid #e2e8f0;
    border-bottom: 2px solid #cbd5e1;
    padding: 8px;
    height: 28px;
}
QProgressBar {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    text-align: center;
    background-color: #f1f5f9;
    height: 20px;
    font-size: 9pt;
    font-weight: bold;
    color: #0f172a;
}
QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 5px;
}
QSplitter::handle {
    background-color: #cbd5e1;
}
QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #cbd5e1;
    color: #475569;
}
"""

class FullscreenPreviewDialog(QDialog):
    """Cửa sổ xem trước trang in chất lượng cao, phóng to toàn màn hình"""
    def __init__(self, pdf_path: str, initial_page: int = 1, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Xem trước chất lượng cao - {os.path.basename(pdf_path)}")
        self.resize(1100, 850)
        self.pdf_path = pdf_path
        self.current_page = initial_page
        self.total_pages = count_pages(pdf_path)
        self.zoom = 1.8
        self.init_ui()
        self.render_page()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        top_bar = QHBoxLayout()
        self.lbl_info = QLabel(f"📄 {os.path.basename(self.pdf_path)}")
        self.lbl_info.setStyleSheet("font-weight: bold; font-size: 11pt; color: #1e3a8a;")
        top_bar.addWidget(self.lbl_info)
        top_bar.addStretch()

        self.btn_prev = QPushButton("◀ Trang trước")
        self.btn_prev.clicked.connect(self.prev_page)
        top_bar.addWidget(self.btn_prev)

        self.lbl_page = QLabel(f"Trang {self.current_page} / {self.total_pages}")
        self.lbl_page.setStyleSheet("font-weight: bold; font-size: 11pt; margin: 0 8px;")
        top_bar.addWidget(self.lbl_page)

        self.btn_next = QPushButton("Trang sau ▶")
        self.btn_next.clicked.connect(self.next_page)
        top_bar.addWidget(self.btn_next)

        top_bar.addSpacing(16)
        self.btn_zoom_in = QPushButton("🔍 +")
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        top_bar.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton("🔍 -")
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        top_bar.addWidget(self.btn_zoom_out)

        self.btn_close = QPushButton("✕ Đóng")
        self.btn_close.clicked.connect(self.accept)
        top_bar.addWidget(self.btn_close)

        layout.addLayout(top_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #334155; border-radius: 8px;")

        self.lbl_image = QLabel()
        self.lbl_image.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.lbl_image)

        layout.addWidget(self.scroll_area)

    def render_page(self):
        dpi = int(120 * self.zoom)
        data = render_page_pixmap_data(self.pdf_path, self.current_page, dpi=dpi)
        if data:
            samples, w, h, s, a = data
            fmt = QImage.Format_RGBA8888 if a else QImage.Format_RGB888
            qimg = QImage(samples, w, h, s, fmt).copy()
            pixmap = QPixmap.fromImage(qimg)
            self.lbl_image.setPixmap(pixmap)
            self.lbl_page.setText(f"Trang {self.current_page} / {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_page()

    def zoom_in(self):
        self.zoom = min(self.zoom * 1.25, 3.5)
        self.render_page()

    def zoom_out(self):
        self.zoom = max(self.zoom * 0.8, 0.8)
        self.render_page()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.prev_page()
        elif event.key() == Qt.Key_Right:
            self.next_page()
        elif event.key() == Qt.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)


class FileConvertWorker(QThread):
    """Tiến trình chuyển đổi tài liệu ngầm, tối ưu tốc độ bằng session COM dùng chung"""
    file_converted_signal = Signal(dict)
    progress_signal = Signal(int, int)
    all_done_signal = Signal()

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        total = len(self.file_paths)
        has_word = any(os.path.splitext(p)[1].lower() in [".doc", ".docx"] for p in self.file_paths)
        has_excel = any(os.path.splitext(p)[1].lower() in [".xls", ".xlsx"] for p in self.file_paths)

        word_converter = WordBatchConverter() if has_word else None
        excel_converter = ExcelBatchConverter() if has_excel else None

        try:
            if word_converter:
                word_converter.__enter__()
            if excel_converter:
                excel_converter.__enter__()

            for idx, p in enumerate(self.file_paths):
                ext = os.path.splitext(p)[1].lower()
                base_name = os.path.basename(p)
                try:
                    if ext in [".doc", ".docx"] and word_converter and word_converter.word:
                        from app.services.converter import TEMP_PDF_DIR
                        out_pdf = os.path.join(TEMP_PDF_DIR, f"{os.path.splitext(base_name)[0]}_{abs(hash(p)) % 1000000}.pdf")
                        ok = word_converter.convert(p, out_pdf)
                        pdf_path = out_pdf if ok else ""
                        err = "" if ok else "Không thể chuyển đổi Word sang PDF."
                    elif ext in [".xls", ".xlsx"] and excel_converter and excel_converter.excel:
                        from app.services.converter import TEMP_PDF_DIR
                        out_pdf = os.path.join(TEMP_PDF_DIR, f"{os.path.splitext(base_name)[0]}_{abs(hash(p)) % 1000000}.pdf")
                        ok = excel_converter.convert(p, out_pdf)
                        pdf_path = out_pdf if ok else ""
                        err = "" if ok else "Không thể chuyển đổi Excel sang PDF."
                    else:
                        ok, pdf_path, err = convert_to_pdf(p)

                    pages = count_pages(pdf_path) if ok else 1
                except Exception as e:
                    ok, pdf_path, err, pages = False, "", str(e), 1

                item = {
                    "original_path": p,
                    "pdf_path": pdf_path if ok else "",
                    "file_name": base_name,
                    "ext": ext,
                    "pages": pages,
                    "convert_ok": ok,
                    "convert_error": err
                }
                self.file_converted_signal.emit(item)
                self.progress_signal.emit(idx + 1, total)
        finally:
            if word_converter:
                word_converter.__exit__(None, None, None)
            if excel_converter:
                excel_converter.__exit__(None, None, None)

        self.all_done_signal.emit()


class BatchPrintWorker(QThread):
    """Tiến trình in liên tục toàn bộ hàng đợi file với báo cáo tiến độ chi tiết"""
    progress_signal = Signal(int, int, str)
    item_status_signal = Signal(int, str, str)
    finished_signal = Signal(dict)

    def __init__(self, queue_items_with_indices, job_configs, sumatra_exe):
        super().__init__()
        self.items_with_indices = queue_items_with_indices
        self.job_configs = job_configs
        self.sumatra_exe = sumatra_exe
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        total = len(self.items_with_indices)
        success_count = 0
        failed_count = 0
        total_sheets = 0
        total_amount = 0.0

        for seq, (queue_idx, item) in enumerate(self.items_with_indices):
            if self._cancelled:
                break

            fname = item.get("file_name", f"File #{seq+1}")
            self.progress_signal.emit(seq + 1, total, fname)
            self.item_status_signal.emit(queue_idx, "🔵 Đang in...", "#0284c7")

            try:
                req_data = self.job_configs['req_data']
                duplex_val = self.job_configs['duplex_val']
                paper = self.job_configs['paper']
                color = self.job_configs['color']
                copies = self.job_configs['copies']
                is_booklet = (duplex_val == 3)
                printer_name = self.job_configs['printer_name']

                src_pdf = item['pdf_path']
                ready_pdf = src_pdf
                duplex_for_printer = duplex_val

                if is_booklet:
                    booklet_pdf = os.path.splitext(ready_pdf)[0] + "_booklet.pdf"
                    create_booklet_pdf(ready_pdf, booklet_pdf, target_paper=paper)
                    ready_pdf = booklet_pdf
                    duplex_for_printer = 2

                cost_info = calculate_print_cost(
                    pages_count=item.get("pages", 1),
                    copies=copies,
                    paper=paper,
                    duplex=duplex_val,
                    color=color,
                    is_booklet=is_booklet
                )

                saved_orig, saved_pdf = organize_and_save_files(
                    original_file_path=item['original_path'],
                    converted_pdf_path=ready_pdf,
                    requester_type=req_data['type'],
                    requester_name=req_data['name'],
                    copies=copies,
                    title=item['file_name']
                )

                job_data = {
                    "requester_id": req_data['id'],
                    "related_classes": self.job_configs.get('related_classes', ''),
                    "title": item['file_name'],
                    "file_type": item['ext'].replace(".", ""),
                    "original_file_path": item['original_path'],
                    "pages": item.get("pages", 1),
                    "page_range": "",
                    "copies": copies,
                    "sheets": cost_info['total_sheets'],
                    "printer_name": printer_name,
                    "paper": paper,
                    "duplex": duplex_val,
                    "color": color,
                    "unit_price": cost_info['unit_price'],
                    "amount": cost_info['amount'],
                    "amount_override": None,
                    "is_free": 0,
                    "override_reason": "",
                    "saved_path": saved_orig,
                    "pdf_path": saved_pdf,
                    "status": "pending",
                    "paid_status": "unpaid",
                    "note": self.job_configs.get('note', ''),
                    "print_file_path": ready_pdf
                }
                job_id = create_print_job(job_data)

                settings_str = build_sumatra_print_settings(
                    copies=copies,
                    duplex=duplex_for_printer,
                    color=color,
                    paper=paper,
                    collate=True
                )
                res = execute_sumatra_print(
                    self.sumatra_exe,
                    printer_name,
                    ready_pdf,
                    settings_str
                )

                if res.get("success"):
                    update_print_job_status(job_id, "printed")
                    success_count += 1
                    total_sheets += cost_info['total_sheets']
                    total_amount += cost_info['amount']
                    self.item_status_signal.emit(queue_idx, "✔️ Đã in", "#16a34a")
                else:
                    update_print_job_status(job_id, "error", res.get("error"))
                    failed_count += 1
                    self.item_status_signal.emit(queue_idx, "❌ Lỗi in", "#dc2626")

            except Exception as e:
                failed_count += 1
                self.item_status_signal.emit(queue_idx, f"❌ Lỗi: {e}", "#dc2626")

        # Đồng bộ Excel 1 lần duy nhất cho toàn bộ lô in thay vì ghi đè liên tục
        if success_count > 0:
            try:
                export_full_excel()
            except Exception as ex_err:
                pass

        self.finished_signal.emit({
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "total_sheets": total_sheets,
            "total_amount": total_amount
        })


class FileDropListWidget(QTableWidget):
    """Bảng danh sách hàng đợi file hỗ trợ kéo thả trực tiếp từ Windows Explorer"""
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Tên file", "Định dạng", "Số trang", "Trạng thái", "Đường dẫn"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.setColumnHidden(4, True) # Ẩn cột đường dẫn gốc
        self.verticalHeader().setDefaultSectionSize(32)
        self.setAlternatingRowColors(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        file_paths = []
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                file_paths.append(path)
        if file_paths:
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()


class BackgroundPrintWorker(QThread):
    finished_signal = Signal(dict)

    def __init__(self, job_data, sumatra_exe, settings_str, print_mode="silent"):
        super().__init__()
        self.job_data = job_data
        self.sumatra_exe = sumatra_exe
        self.settings_str = settings_str
        self.print_mode = print_mode

    def run(self):
        if self.print_mode == "dialog":
            res = open_windows_print_dialog(
                file_path=self.job_data.get('original_file_path'),
                pdf_path=self.job_data.get('print_file_path'),
                printer_name=self.job_data.get('printer_name'),
                prefer_original_app=False,
                settings_str=self.settings_str
            )
        else:
            # 1. Gui lenh in toi SumatraPDF (in ngam)
            res = execute_sumatra_print(
                self.sumatra_exe,
                self.job_data['printer_name'],
                self.job_data['print_file_path'],
                self.settings_str
            )
        self.finished_signal.emit({
            "job_id": self.job_data.get('job_id'),
            "result": res,
            "mode": self.print_mode
        })


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Quản lý in ấn - Trường THPT Bắc Đông Quan [{get_machine_name()}]")
        self.resize(1300, 820)

        # Dat icon cua so va taskbar
        from app.main import get_app_icon_path
        icon_path = get_app_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        self.current_queue = [] # Danh sach cac file trong hang doi
        self.selected_file_index = -1
        self.current_preview_page = 1
        self.total_preview_pages = 1
        self.current_pdf_for_preview = None
        self.preview_cache = {} # Cache thumbnail: (pdf_path, page, zoom) -> QPixmap
        self.zoom_factor = 1.0

        # Co che Lazy Tab Loading de may yeu khoi dong sieu toc
        self._loaded_tabs = set()
        self._dirty_history = False
        self._dirty_reports = False

        self.setStyleSheet(MODERN_STYLE)
        self.init_ui()
        self.load_initial_data()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Thanh Tabs chính
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { font-size: 11pt; font-weight: bold; padding: 10px 20px; }
            QTabBar::tab:selected { background-color: #1a56db; color: white; }
        """)

        # Tab 1: In ấn & Hàng đợi
        self.tab_print = QWidget()
        self.init_tab_print()
        self.tabs.addTab(self.tab_print, "🖨️ In ấn & Hàng đợi")

        # Tab 2: Lịch sử in
        self.tab_history = QWidget()
        self.init_tab_history()
        self.tabs.addTab(self.tab_history, "📜 Lịch sử in")

        # Tab 3: Báo cáo & Thu tiền
        self.tab_reports = QWidget()
        self.init_tab_reports()
        self.tabs.addTab(self.tab_reports, "💰 Báo cáo & Thu tiền")

        # Tab 4: Cấu hình Bảng giá tiền
        self.tab_pricing = QWidget()
        self.init_tab_pricing()
        self.tabs.addTab(self.tab_pricing, "💲 Cấu hình Bảng giá")

        # Tab 5: Đồng bộ 2 máy (Cloud Sync)
        self.tab_sync = QWidget()
        self.init_tab_sync()
        self.tabs.addTab(self.tab_sync, "☁️ Đồng bộ 2 máy ở xa")

        # Tab 6: Cài đặt & Danh mục
        self.tab_settings = QWidget()
        self.init_tab_settings()
        self.tabs.addTab(self.tab_settings, "⚙️ Cài đặt & Danh mục")

        self.tabs.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tabs)

        # Status Bar dưới cùng
        self.status_bar_label = QLabel(f"Quản lý in ấn | Tác giả: Phạm Công Vinh (THPT Bắc Đông Quan) | Máy tính: {get_machine_name()}")
        self.statusBar().addWidget(self.status_bar_label)

    # ==================== TAB 1: IN ẤN & HÀNG ĐỢI ====================
    def init_tab_print(self):
        layout = QHBoxLayout(self.tab_print)
        splitter = QSplitter(Qt.Horizontal)

        # --- KHỐI TRÁI: HÀNG ĐỢI FILE KÉO THẢ ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        lbl_queue = QLabel("1. HÀNG ĐỢI FILE CẦN IN (Kéo thả file vào đây)")
        lbl_queue.setStyleSheet("font-weight: bold; color: #1e3a8a; font-size: 11pt;")
        left_layout.addWidget(lbl_queue)

        self.progress_queue = QProgressBar()
        self.progress_queue.setVisible(False)
        left_layout.addWidget(self.progress_queue)

        self.table_queue = FileDropListWidget()
        self.table_queue.setMinimumHeight(220)
        self.table_queue.files_dropped.connect(self.add_files_to_queue)
        self.table_queue.itemSelectionChanged.connect(self.on_queue_selection_changed)
        left_layout.addWidget(self.table_queue)

        btn_box = QHBoxLayout()
        self.btn_add_files = QPushButton("➕ Chọn thêm file...")
        self.btn_add_files.clicked.connect(self.choose_files_dialog)
        self.btn_remove_file = QPushButton("❌ Xóa file đã chọn")
        self.btn_remove_file.clicked.connect(self.remove_selected_file)
        self.btn_clear_queue = QPushButton("🗑️ Xóa toàn bộ")
        self.btn_clear_queue.clicked.connect(self.clear_queue)
        btn_box.addWidget(self.btn_add_files)
        btn_box.addWidget(self.btn_remove_file)
        btn_box.addWidget(self.btn_clear_queue)
        left_layout.addLayout(btn_box)

        # Preset nhanh
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Mẫu cấu hình:"))
        self.cb_presets = QComboBox()
        self.cb_presets.currentIndexChanged.connect(self.apply_preset)
        preset_layout.addWidget(self.cb_presets, 1)
        left_layout.addLayout(preset_layout)

        # Áp dụng cho tất cả
        self.btn_apply_all = QPushButton("📋 Áp dụng cấu hình này cho TẤT CẢ file")
        self.btn_apply_all.setStyleSheet("background-color: #f1f5f9; color: #1f2937; padding: 6px; font-weight: bold;")
        self.btn_apply_all.clicked.connect(self.apply_config_to_all)
        left_layout.addWidget(self.btn_apply_all)

        # Nút in toàn bộ hàng đợi
        self.btn_batch_print_all = QPushButton("🚀 IN TẤT CẢ FILE TRONG HÀNG ĐỢI (BATCH)")
        self.btn_batch_print_all.setFixedHeight(40)
        self.btn_batch_print_all.setStyleSheet("""
            QPushButton { background-color: #ea580c; color: white; font-weight: bold; font-size: 11pt; border-radius: 6px; }
            QPushButton:hover { background-color: #c2410c; }
        """)
        self.btn_batch_print_all.clicked.connect(self.execute_batch_print_all)
        left_layout.addWidget(self.btn_batch_print_all)

        splitter.addWidget(left_widget)

        # --- KHỐI GIỮA: BIỂU MẪU CẤU HÌNH IN ---
        mid_scroll = QScrollArea()
        mid_scroll.setWidgetResizable(True)
        mid_widget = QWidget()
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(10, 0, 10, 0)

        lbl_config = QLabel("2. CẤU HÌNH CHI TIẾT LƯỢT IN")
        lbl_config.setStyleSheet("font-weight: bold; color: #1e3a8a; font-size: 11pt;")
        mid_layout.addWidget(lbl_config)

        # Group 1: Người yêu cầu
        grp_req = QGroupBox("Người yêu cầu & Lớp liên quan")
        req_grid = QGridLayout(grp_req)

        req_grid.addWidget(QLabel("Tìm người yêu cầu:"), 0, 0)
        self.txt_search_req = QLineEdit()
        self.txt_search_req.setPlaceholderText("Gõ tên không dấu (vd: 'lan', '10a1')...")
        self.txt_search_req.textChanged.connect(self.on_search_requester_changed)
        req_grid.addWidget(self.txt_search_req, 0, 1)

        req_grid.addWidget(QLabel("Chọn người yêu cầu:"), 1, 0)
        self.cb_requesters = QComboBox()
        self.cb_requesters.currentIndexChanged.connect(self.on_requester_changed)
        req_grid.addWidget(self.cb_requesters, 1, 1)

        req_grid.addWidget(QLabel("Lớp liên quan (tuỳ chọn):"), 2, 0)
        self.txt_related_classes = QLineEdit()
        self.txt_related_classes.setPlaceholderText("Vd: 10A1, 10A2, 10A3...")
        req_grid.addWidget(self.txt_related_classes, 2, 1)

        # Gần đây
        recent_box = QHBoxLayout()
        recent_box.addWidget(QLabel("Gần đây:"))
        self.btn_recent_1 = QPushButton("-")
        self.btn_recent_2 = QPushButton("-")
        self.btn_recent_3 = QPushButton("-")
        for b in [self.btn_recent_1, self.btn_recent_2, self.btn_recent_3]:
            b.setStyleSheet("background-color: #e5e7eb; border-radius: 4px; padding: 2px 8px;")
            b.clicked.connect(self.on_recent_clicked)
            recent_box.addWidget(b)
        recent_box.addStretch()
        req_grid.addLayout(recent_box, 3, 0, 1, 2)

        mid_layout.addWidget(grp_req)

        # Group 2: Thiết lập máy in & Giấy
        grp_print = QGroupBox("Cấu hình in ấn")
        print_grid = QGridLayout(grp_print)

        print_grid.addWidget(QLabel("Máy in:"), 0, 0)
        printer_h_layout = QHBoxLayout()
        self.cb_printers = QComboBox()
        self.cb_printers.currentIndexChanged.connect(self.recalculate_cost)
        printer_h_layout.addWidget(self.cb_printers, 1)

        self.btn_printer_properties = QPushButton("⚙️ Cấu hình máy in (Properties)...")
        self.btn_printer_properties.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.btn_printer_properties.setToolTip("Mở bảng tùy chọn driver máy in (Printing Preferences) để cấu hình sâu: Bộ dập ghim (Stapler), đục lỗ, khay giấy dày...")

        # Menu tùy chọn cấu hình in sâu
        prop_menu = QMenu(self)
        act_preferences = prop_menu.addAction("📑 Tùy chọn in (Dập ghim, Khay giấy, Chế độ in)...")
        act_preferences.triggered.connect(lambda: self.open_selected_printer_properties(mode="preferences"))
        act_properties = prop_menu.addAction("🛠️ Thuộc tính thiết bị (Cấu hình phần cứng Finisher)...")
        act_properties.triggered.connect(lambda: self.open_selected_printer_properties(mode="properties"))
        prop_menu.addSeparator()
        act_refresh_printers = prop_menu.addAction("🔄 Làm mới danh sách máy in")
        act_refresh_printers.triggered.connect(self.refresh_printers_dropdown)
        self.btn_printer_properties.setMenu(prop_menu)

        printer_h_layout.addWidget(self.btn_printer_properties)
        print_grid.addLayout(printer_h_layout, 0, 1)

        print_grid.addWidget(QLabel("Khổ giấy:"), 1, 0)
        self.cb_paper = QComboBox()
        self.cb_paper.addItems(["A4", "A3", "A5"])
        self.cb_paper.currentIndexChanged.connect(self.recalculate_cost)
        print_grid.addWidget(self.cb_paper, 1, 1)

        print_grid.addWidget(QLabel("Chế độ in:"), 2, 0)
        self.cb_duplex = QComboBox()
        self.cb_duplex.addItem("2 mặt - Lật cạnh dài (Chuẩn)", 1)
        self.cb_duplex.addItem("1 mặt (Đơn)", 0)
        self.cb_duplex.addItem("2 mặt - Lật cạnh ngắn (Ngang)", 2)
        self.cb_duplex.addItem("📖 In Booklet (Sách gập đôi ghim giữa)", 3)
        self.cb_duplex.currentIndexChanged.connect(self.recalculate_cost)
        print_grid.addWidget(self.cb_duplex, 2, 1)

        print_grid.addWidget(QLabel("Màu sắc:"), 3, 0)
        self.cb_color = QComboBox()
        self.cb_color.addItem("Đen trắng (Monochrome)", 0)
        self.cb_color.addItem("In màu (Color)", 1)
        self.cb_color.currentIndexChanged.connect(self.recalculate_cost)
        print_grid.addWidget(self.cb_color, 3, 1)

        print_grid.addWidget(QLabel("Số bản in (Copies):"), 4, 0)
        self.sp_copies = QSpinBox()
        self.sp_copies.setRange(1, 1000)
        self.sp_copies.setValue(1)
        self.sp_copies.valueChanged.connect(self.recalculate_cost)
        print_grid.addWidget(self.sp_copies, 4, 1)

        print_grid.addWidget(QLabel("Khoảng trang cần in:"), 5, 0)
        self.txt_page_range = QLineEdit()
        self.txt_page_range.setPlaceholderText("Để trống = in hết (vd: 1-3, 5, 8-10)")
        self.txt_page_range.textChanged.connect(self.recalculate_cost)
        print_grid.addWidget(self.txt_page_range, 5, 1)

        print_grid.addWidget(QLabel("Ghi chú lượt in:"), 6, 0)
        self.txt_job_note = QLineEdit()
        self.txt_job_note.setPlaceholderText("Vd: Đề thi khảo sát chung, Phiếu bài tập...")
        print_grid.addWidget(self.txt_job_note, 6, 1)

        lbl_finisher_tip = QLabel("💡 <i>Máy có bộ dập ghim Finisher: bấm <b>'⚙️ Cấu hình máy in (Properties)'</b> ở trên để chọn dập 1 ghim, 2 ghim hoặc dập ghim giữa Booklet (Saddle Stitch).</i>")
        lbl_finisher_tip.setStyleSheet("color: #0284c7; font-size: 9pt;")
        lbl_finisher_tip.setWordWrap(True)
        print_grid.addWidget(lbl_finisher_tip, 7, 0, 1, 2)

        mid_layout.addWidget(grp_print)

        # Group 3: Tiền và Miễn phí
        grp_cost = QGroupBox("Thành tiền & Điều chỉnh")
        cost_grid = QGridLayout(grp_cost)

        cost_grid.addWidget(QLabel("Đơn giá:"), 0, 0)
        self.lbl_unit_price = QLabel("0 đ / tờ")
        self.lbl_unit_price.setStyleSheet("font-weight: bold;")
        cost_grid.addWidget(self.lbl_unit_price, 0, 1)

        cost_grid.addWidget(QLabel("Số tờ thực tế:"), 1, 0)
        self.lbl_sheets_calc = QLabel("0 tờ")
        self.lbl_sheets_calc.setStyleSheet("font-weight: bold; color: #1e3a8a;")
        cost_grid.addWidget(self.lbl_sheets_calc, 1, 1)

        cost_grid.addWidget(QLabel("Thành tiền tính toán:"), 2, 0)
        self.lbl_calc_amount = QLabel("0 đ")
        self.lbl_calc_amount.setStyleSheet("font-size: 13pt; font-weight: bold; color: #047857;")
        cost_grid.addWidget(self.lbl_calc_amount, 2, 1)

        self.chk_override_amount = QCheckBox("Sửa tay số tiền:")
        self.chk_override_amount.toggled.connect(self.on_override_toggled)
        cost_grid.addWidget(self.chk_override_amount, 3, 0)

        self.sp_override_amount = QSpinBox()
        self.sp_override_amount.setRange(0, 10000000)
        self.sp_override_amount.setSingleStep(1000)
        self.sp_override_amount.setEnabled(False)
        cost_grid.addWidget(self.sp_override_amount, 3, 1)

        self.chk_free = QCheckBox("Miễn phí (In việc chung của trường)")
        self.chk_free.toggled.connect(self.on_free_toggled)
        cost_grid.addWidget(self.chk_free, 4, 0)

        self.txt_free_reason = QLineEdit()
        self.txt_free_reason.setPlaceholderText("Nhập lý do miễn phí hoặc sửa giá...")
        cost_grid.addWidget(self.txt_free_reason, 4, 1)

        mid_layout.addWidget(grp_cost)
        mid_layout.addStretch()

        mid_scroll.setWidget(mid_widget)
        splitter.addWidget(mid_scroll)

        # --- KHỐI PHẢI: XEM TRƯỚC VÀ NÚT HÀNH ĐỘNG ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        lbl_preview = QLabel("3. XEM TRƯỚC TRANG ĐỀ")
        lbl_preview.setStyleSheet("font-weight: bold; color: #1e3a8a; font-size: 11pt;")
        right_layout.addWidget(lbl_preview)

        # Khung ảnh xem trước
        self.lbl_preview_img = QLabel("Kéo file vào để xem trước")
        self.lbl_preview_img.setAlignment(Qt.AlignCenter)
        self.lbl_preview_img.setStyleSheet("background-color: #f9fafb; border: 1px solid #d1d5db; min-height: 340px;")
        right_layout.addWidget(self.lbl_preview_img, 1)

        # Nút chuyển trang preview
        nav_box = QHBoxLayout()
        self.btn_prev_page = QPushButton("◀ Trang trước")
        self.btn_prev_page.clicked.connect(self.prev_preview_page)
        self.lbl_page_indicator = QLabel("Trang 0 / 0")
        self.lbl_page_indicator.setAlignment(Qt.AlignCenter)
        self.btn_next_page = QPushButton("Trang sau ▶")
        self.btn_next_page.clicked.connect(self.next_preview_page)
        nav_box.addWidget(self.btn_prev_page)
        nav_box.addWidget(self.lbl_page_indicator)
        nav_box.addWidget(self.btn_next_page)
        right_layout.addLayout(nav_box)

        # Thanh phóng to / thu nhỏ & xem toàn màn hình
        zoom_box = QHBoxLayout()
        self.btn_zoom_out = QPushButton("🔍 -")
        self.btn_zoom_out.setFixedWidth(50)
        self.btn_zoom_out.clicked.connect(self.zoom_out_preview)

        self.btn_zoom_reset = QPushButton("100%")
        self.btn_zoom_reset.setFixedWidth(60)
        self.btn_zoom_reset.clicked.connect(self.zoom_reset_preview)

        self.btn_zoom_in = QPushButton("🔍 +")
        self.btn_zoom_in.setFixedWidth(50)
        self.btn_zoom_in.clicked.connect(self.zoom_in_preview)

        self.btn_fullscreen_preview = QPushButton("⛶ Xem lớn")
        self.btn_fullscreen_preview.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold;")
        self.btn_fullscreen_preview.clicked.connect(self.open_fullscreen_preview)

        zoom_box.addWidget(self.btn_zoom_out)
        zoom_box.addWidget(self.btn_zoom_reset)
        zoom_box.addWidget(self.btn_zoom_in)
        zoom_box.addWidget(self.btn_fullscreen_preview)
        right_layout.addLayout(zoom_box)

        # Nút hành động lớn
        self.btn_print_now = QPushButton("🖨️ IN NHANH TỰ ĐỘNG (SILENT)")
        self.btn_print_now.setFixedHeight(46)
        self.btn_print_now.setStyleSheet("""
            QPushButton { background-color: #059669; color: white; font-size: 12pt; font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background-color: #047857; }
        """)
        self.btn_print_now.clicked.connect(self.execute_current_print)
        right_layout.addWidget(self.btn_print_now)

        self.btn_print_windows = QPushButton("🖥️ MỞ CỬA SỔ IN WINDOWS (PRINT DIALOG)")
        self.btn_print_windows.setFixedHeight(42)
        self.btn_print_windows.setStyleSheet("""
            QPushButton { background-color: #4f46e5; color: white; font-size: 11pt; font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background-color: #4338ca; }
        """)
        self.btn_print_windows.clicked.connect(self.execute_windows_dialog_print)
        right_layout.addWidget(self.btn_print_windows)

        self.btn_save_only = QPushButton("💾 LƯU KHÔNG IN (GHI SỔ THỦ CÔNG)")
        self.btn_save_only.setFixedHeight(34)
        self.btn_save_only.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_save_only.clicked.connect(self.execute_save_only)
        right_layout.addWidget(self.btn_save_only)

        splitter.addWidget(right_widget)
        splitter.setSizes([320, 520, 380])
        layout.addWidget(splitter)

    # ==================== TAB 2: LỊCH SỬ IN ====================
    def init_tab_history(self):
        layout = QVBoxLayout(self.tab_history)

        # Bộ lọc
        filter_box = QHBoxLayout()
        filter_box.addWidget(QLabel("Tìm kiếm nhanh:"))
        self.txt_history_search = QLineEdit()
        self.txt_history_search.setPlaceholderText("Tên người, tên đề, máy in...")
        self.txt_history_search.textChanged.connect(self.load_history_data)
        filter_box.addWidget(self.txt_history_search, 1)

        filter_box.addWidget(QLabel("Thời gian:"))
        self.cb_history_filter = QComboBox()
        self.cb_history_filter.addItems(["Hôm nay", "7 ngày gần nhất", "Tháng này", "Toàn bộ"])
        self.cb_history_filter.currentIndexChanged.connect(self.load_history_data)
        filter_box.addWidget(self.cb_history_filter)

        self.btn_refresh_history = QPushButton("🔄 Tải lại")
        self.btn_refresh_history.clicked.connect(self.load_history_data)
        filter_box.addWidget(self.btn_refresh_history)

        layout.addLayout(filter_box)

        # Bảng dữ liệu
        self.table_history = QTableWidget()
        self.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_history.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_history.setColumnCount(12)
        self.table_history.setMinimumHeight(260)
        self.table_history.verticalHeader().setDefaultSectionSize(32)
        self.table_history.setAlternatingRowColors(True)
        self.table_history.setHorizontalHeaderLabels([
            "Mã", "Ngày giờ", "Máy tính", "Người in", "Lớp", "Tên tài liệu",
            "Trang", "Bản", "Tờ", "Thành tiền", "Trạng thái", "Thanh toán"
        ])
        self.table_history.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        layout.addWidget(self.table_history)

        # Nút thao tác dưới lịch sử
        act_box = QHBoxLayout()
        self.btn_open_file = QPushButton("📂 Mở file đã lưu")
        self.btn_open_file.clicked.connect(self.open_history_file)
        self.btn_open_folder = QPushButton("📁 Mở thư mục chứa")
        self.btn_open_folder.clicked.connect(self.open_history_folder)
        self.btn_reprint = QPushButton("🔁 In lại lượt này")
        self.btn_reprint.clicked.connect(self.reprint_history_job)
        self.btn_cancel_job = QPushButton("❌ Hủy lượt in này")
        self.btn_cancel_job.clicked.connect(self.cancel_history_job)

        act_box.addWidget(self.btn_open_file)
        act_box.addWidget(self.btn_open_folder)
        act_box.addWidget(self.btn_reprint)
        act_box.addWidget(self.btn_cancel_job)
        act_box.addStretch()
        layout.addLayout(act_box)

    # ==================== TAB 3: BÁO CÁO & THU TIỀN ====================
    def init_tab_reports(self):
        layout = QVBoxLayout(self.tab_reports)

        # Dashboard thống kê nhanh
        dash_box = QHBoxLayout()
        self.lbl_dash_today = QLabel("Hôm nay: 0 lượt | 0 tờ | 0 đ")
        self.lbl_dash_today.setStyleSheet("background-color: #ecfdf5; color: #065f46; font-size: 11pt; font-weight: bold; padding: 12px; border-radius: 6px; border: 1px solid #a7f3d0;")
        self.lbl_dash_debt = QLabel("Tổng nợ chưa thu: 0 đ")
        self.lbl_dash_debt.setStyleSheet("background-color: #fef2f2; color: #991b1b; font-size: 11pt; font-weight: bold; padding: 12px; border-radius: 6px; border: 1px solid #fecaca;")
        dash_box.addWidget(self.lbl_dash_today)
        dash_box.addWidget(self.lbl_dash_debt)
        layout.addLayout(dash_box)

        # Bộ lọc báo cáo
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Khoảng thời gian báo cáo:"))
        self.cb_report_time = QComboBox()
        self.cb_report_time.addItem("Tháng này", "month")
        self.cb_report_time.addItem("Hôm nay", "today")
        self.cb_report_time.addItem("7 ngày gần đây", "week")
        self.cb_report_time.currentIndexChanged.connect(self.load_report_data)
        filter_layout.addWidget(self.cb_report_time)

        self.btn_refresh_report = QPushButton("🔄 Tải lại số liệu")
        self.btn_refresh_report.clicked.connect(self.load_report_data)
        filter_layout.addWidget(self.btn_refresh_report)

        self.btn_export_excel_report = QPushButton("📊 Xuất file Excel tổng hợp ngay")
        self.btn_export_excel_report.setStyleSheet("background-color: #107c41; color: white; font-weight: bold;")
        self.btn_export_excel_report.clicked.connect(self.export_excel_now)
        filter_layout.addWidget(self.btn_export_excel_report)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Bảng tổng hợp theo giáo viên & lớp
        self.table_report = QTableWidget()
        self.table_report.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_report.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_report.setColumnCount(8)
        self.table_report.setMinimumHeight(260)
        self.table_report.verticalHeader().setDefaultSectionSize(32)
        self.table_report.setAlternatingRowColors(True)
        self.table_report.setHorizontalHeaderLabels([
            "Mã", "Họ và tên / Lớp", "Loại", "Tổ / Khối", "Số lượt in",
            "Tổng số tờ", "Tổng tiền", "Còn nợ (đ)"
        ])
        self.table_report.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table_report)

        # Nút thu tiền & In phiếu thu
        action_layout = QHBoxLayout()
        self.btn_mark_paid = QPushButton("✅ ĐÁNH DẤU ĐÃ THU TIỀN CHO NGƯỜI ĐANG CHỌN")
        self.btn_mark_paid.setFixedHeight(38)
        self.btn_mark_paid.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; font-size: 11pt;")
        self.btn_mark_paid.clicked.connect(self.mark_selected_requester_paid)
        action_layout.addWidget(self.btn_mark_paid)

        self.btn_print_receipt = QPushButton("🧾 XUẤT / IN PHIẾU THU TIỀN")
        self.btn_print_receipt.setFixedHeight(38)
        self.btn_print_receipt.setStyleSheet("background-color: #059669; color: white; font-weight: bold; font-size: 11pt;")
        self.btn_print_receipt.clicked.connect(self.generate_receipt_for_selected)
        action_layout.addWidget(self.btn_print_receipt)

        action_layout.addStretch()
        layout.addLayout(action_layout)

    # ==================== TAB 4: CẤU HÌNH TIỀN & BẢNG GIÁ ====================
    def init_tab_pricing(self):
        layout = QVBoxLayout(self.tab_pricing)
        layout.setSpacing(10)

        # 1. Header Banner & Chọn cách tính tiền
        top_box = QGroupBox("1. Quy ước tính tiền in ấn")
        top_lay = QHBoxLayout(top_box)

        top_lay.addWidget(QLabel("Cách tính tiền:"))
        self.cb_pricing_unit = QComboBox()
        self.cb_pricing_unit.addItem("Tính theo Tờ giấy thực tế (sheet - Mặc định)", "sheet")
        self.cb_pricing_unit.addItem("Tính theo Mặt in (page - Trang)", "page")
        if get_setting("pricing_unit", "sheet") == "page":
            self.cb_pricing_unit.setCurrentIndex(1)
        top_lay.addWidget(self.cb_pricing_unit, 1)

        self.btn_save_unit = QPushButton("💾 Lưu cách tính")
        self.btn_save_unit.clicked.connect(self.save_pricing_unit_setting)
        top_lay.addWidget(self.btn_save_unit)
        top_lay.addStretch()

        layout.addWidget(top_box)

        # 2. Bảng giá in chi tiết
        price_box = QGroupBox("2. Bảng đơn giá in ấn chi tiết theo Khổ giấy, Mặt in, Màu sắc (Áp dụng tự động)")
        price_lay = QVBoxLayout(price_box)

        self.table_prices = QTableWidget()
        self.table_prices.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_prices.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_prices.setColumnCount(7)
        self.table_prices.setMinimumHeight(240)
        self.table_prices.verticalHeader().setDefaultSectionSize(32)
        self.table_prices.setAlternatingRowColors(True)
        self.table_prices.setHorizontalHeaderLabels([
            "Mã", "Khổ giấy", "Màu sắc", "Chế độ mặt", "Máy in áp dụng", "Đơn giá hiện tại (đ)", "Đơn vị"
        ])
        self.table_prices.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_prices.itemSelectionChanged.connect(self.on_price_table_selected)
        price_lay.addWidget(self.table_prices)

        # Dòng sửa nhanh đơn giá
        edit_row = QHBoxLayout()
        edit_row.addWidget(QLabel("<b>Sửa đơn giá cho dòng đang chọn:</b>"))
        self.sp_edit_price = QSpinBox()
        self.sp_edit_price.setRange(50, 100000)
        self.sp_edit_price.setSingleStep(50)
        self.sp_edit_price.setValue(350)
        edit_row.addWidget(self.sp_edit_price)

        self.btn_save_price_amount = QPushButton("💾 CẬP NHẬT ĐƠN GIÁ NÀY")
        self.btn_save_price_amount.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 6px 12px;")
        self.btn_save_price_amount.clicked.connect(self.save_selected_price_amount)
        edit_row.addWidget(self.btn_save_price_amount)
        edit_row.addStretch()

        self.btn_reset_prices = QPushButton("↺ Khôi phục bảng giá chuẩn")
        self.btn_reset_prices.clicked.connect(self.reset_prices_to_default)
        edit_row.addWidget(self.btn_reset_prices)

        price_lay.addLayout(edit_row)

        # Dòng thêm quy tắc mới
        add_box = QGroupBox("Thêm quy tắc giá mới")
        add_grid = QGridLayout(add_box)

        add_grid.addWidget(QLabel("Khổ giấy:"), 0, 0)
        self.cb_new_price_paper = QComboBox()
        self.cb_new_price_paper.addItems(["A4", "A3", "A5"])
        add_grid.addWidget(self.cb_new_price_paper, 0, 1)

        add_grid.addWidget(QLabel("Màu sắc:"), 0, 2)
        self.cb_new_price_color = QComboBox()
        self.cb_new_price_color.addItem("Đen trắng", 0)
        self.cb_new_price_color.addItem("In màu", 1)
        add_grid.addWidget(self.cb_new_price_color, 0, 3)

        add_grid.addWidget(QLabel("Mặt in:"), 0, 4)
        self.cb_new_price_duplex = QComboBox()
        self.cb_new_price_duplex.addItem("1 mặt", 0)
        self.cb_new_price_duplex.addItem("2 mặt", 1)
        add_grid.addWidget(self.cb_new_price_duplex, 0, 5)

        add_grid.addWidget(QLabel("Đơn giá (đ):"), 0, 6)
        self.sp_new_price_val = QSpinBox()
        self.sp_new_price_val.setRange(50, 100000)
        self.sp_new_price_val.setSingleStep(50)
        self.sp_new_price_val.setValue(350)
        add_grid.addWidget(self.sp_new_price_val, 0, 7)

        self.btn_add_price_rule = QPushButton("➕ Thêm quy tắc giá")
        self.btn_add_price_rule.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold;")
        self.btn_add_price_rule.clicked.connect(self.add_new_price_rule_from_ui)
        add_grid.addWidget(self.btn_add_price_rule, 0, 8)

        price_lay.addWidget(add_box)

        layout.addWidget(price_box)

    # ==================== TAB 5: ĐỒNG BỘ 2 MÁY (CLOUD SYNC) ====================
    def init_tab_sync(self):
        layout = QVBoxLayout(self.tab_sync)
        layout.setSpacing(12)

        info_box = QGroupBox("Cấu hình Đồng bộ giữa 2 máy ở xa (không cùng mạng LAN)")
        info_layout = QGridLayout(info_box)

        info_layout.addWidget(QLabel("Tên máy tính này:"), 0, 0)
        lbl_my_machine = QLabel(f"<b>{get_machine_name()}</b> (tự động nhận diện)")
        info_layout.addWidget(lbl_my_machine, 0, 1)

        info_layout.addWidget(QLabel("Thư mục đồng bộ đám mây:"), 1, 0)
        self.txt_cloud_folder = QLineEdit()
        self.txt_cloud_folder.setText(get_cloud_sync_folder())
        self.txt_cloud_folder.setPlaceholderText("Trỏ tới thư mục Google Drive hoặc OneDrive (vd: D:\\GoogleDrive\\InAn_DongBo)...")
        info_layout.addWidget(self.txt_cloud_folder, 1, 1)

        self.btn_browse_cloud = QPushButton("Chọn thư mục...")
        self.btn_browse_cloud.clicked.connect(self.browse_cloud_folder)
        info_layout.addWidget(self.btn_browse_cloud, 1, 2)

        self.btn_save_cloud_cfg = QPushButton("Lưu cấu hình thư mục")
        self.btn_save_cloud_cfg.clicked.connect(self.save_cloud_folder_setting)
        info_layout.addWidget(self.btn_save_cloud_cfg, 2, 1)

        layout.addWidget(info_box)

        # Nút hành động đồng bộ
        sync_act_box = QHBoxLayout()
        self.btn_do_sync = QPushButton("🔄 ĐỒNG BỘ 2 CHIỀU NGAY BÂY GIỜ")
        self.btn_do_sync.setFixedHeight(45)
        self.btn_do_sync.setStyleSheet("background-color: #0284c7; color: white; font-size: 12pt; font-weight: bold;")
        self.btn_do_sync.clicked.connect(self.execute_cloud_sync)
        sync_act_box.addWidget(self.btn_do_sync)
        layout.addLayout(sync_act_box)

        # Log đồng bộ
        log_box = QGroupBox("Nhật ký đồng bộ đám mây")
        log_lay = QVBoxLayout(log_box)
        self.txt_sync_log = QTextEdit()
        self.txt_sync_log.setReadOnly(True)
        self.txt_sync_log.setStyleSheet("background-color: #1e1e1e; color: #a3e635; font-family: Consolas; font-size: 10pt;")
        log_lay.addWidget(self.txt_sync_log)
        layout.addWidget(log_box)

    # ==================== TAB 6: CÀI ĐẶT & QUẢN LÝ DANH MỤC ====================
    def init_tab_settings(self):
        layout = QVBoxLayout(self.tab_settings)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("settingsScroll")
        container = QWidget()
        container.setObjectName("settingsContainer")
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.setSpacing(18)

        # --- PHẦN 1: CẤU HÌNH HỆ THỐNG ---
        grp_sys = QGroupBox("1. Thư mục lưu trữ & File Excel tổng hợp")
        sys_grid = QGridLayout(grp_sys)
        sys_grid.setContentsMargins(16, 22, 16, 16)
        sys_grid.setSpacing(12)

        sys_grid.addWidget(QLabel("Thư mục lưu trữ bản sao đề in (DeDaIn):"), 0, 0)
        self.txt_cfg_storage = QLineEdit(get_setting("storage_dir", "D:\\DeDaIn"))
        sys_grid.addWidget(self.txt_cfg_storage, 0, 1)

        sys_grid.addWidget(QLabel("Đường dẫn file Excel tổng hợp:"), 1, 0)
        self.txt_cfg_excel = QLineEdit(get_setting("excel_path", "D:\\DeDaIn\\TongHopInAn.xlsx"))
        sys_grid.addWidget(self.txt_cfg_excel, 1, 1)

        self.btn_save_sys_cfg = QPushButton("💾 Lưu đường dẫn hệ thống")
        self.btn_save_sys_cfg.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px;")
        self.btn_save_sys_cfg.clicked.connect(self.save_general_settings)
        sys_grid.addWidget(self.btn_save_sys_cfg, 2, 1)

        vbox.addWidget(grp_sys)

        # --- PHẦN 2: DANH MỤC LỚP & SĨ SỐ ---
        grp_class = QGroupBox("2. Quản lý Danh mục Lớp học & Sĩ số (Hỗ trợ Nhập từ Excel)")
        class_vbox = QVBoxLayout(grp_class)
        class_vbox.setContentsMargins(16, 22, 16, 16)
        class_vbox.setSpacing(12)

        # Nút thao tác lớp
        class_btn_box = QHBoxLayout()
        self.btn_import_classes_excel = QPushButton("📥 NHẬP DANH SÁCH LỚP TỪ FILE EXCEL (.xlsx)")
        self.btn_import_classes_excel.setStyleSheet("background-color: #107c41; color: white; font-weight: bold; padding: 8px 12px;")
        self.btn_import_classes_excel.clicked.connect(self.import_classes_excel_dialog)
        class_btn_box.addWidget(self.btn_import_classes_excel)

        self.btn_download_class_template = QPushButton("📄 Tải file Excel mẫu danh sách Lớp")
        self.btn_download_class_template.clicked.connect(self.download_classes_template_dialog)
        class_btn_box.addWidget(self.btn_download_class_template)
        class_btn_box.addStretch()
        class_vbox.addLayout(class_btn_box)

        # Bảng hiển thị danh mục lớp
        self.table_classes = QTableWidget()
        self.table_classes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_classes.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_classes.setColumnCount(5)
        self.table_classes.setHorizontalHeaderLabels(["ID", "Khối", "Tên lớp", "Sĩ số học sinh", "Ghi chú"])
        self.table_classes.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_classes.setMinimumHeight(200)
        self.table_classes.setMaximumHeight(260)
        self.table_classes.verticalHeader().setDefaultSectionSize(32)
        self.table_classes.setAlternatingRowColors(True)
        self.table_classes.itemSelectionChanged.connect(self.on_class_table_selected)
        class_vbox.addWidget(self.table_classes)

        # Sửa nhanh sĩ số lớp
        edit_class_box = QHBoxLayout()
        edit_class_box.addWidget(QLabel("<b>Sửa sĩ số cho lớp đang chọn:</b>"))
        self.sp_edit_student_count = QSpinBox()
        self.sp_edit_student_count.setRange(0, 100)
        self.sp_edit_student_count.setValue(45)
        edit_class_box.addWidget(self.sp_edit_student_count)

        self.btn_save_student_count = QPushButton("💾 Cập nhật sĩ số")
        self.btn_save_student_count.clicked.connect(self.save_class_student_count)
        edit_class_box.addWidget(self.btn_save_student_count)
        edit_class_box.addStretch()
        class_vbox.addLayout(edit_class_box)

        vbox.addWidget(grp_class)

        # --- PHẦN 3: DANH MỤC GIÁO VIÊN ---
        grp_teacher = QGroupBox("3. Quản lý Danh mục Giáo viên (Hỗ trợ Nhập từ Excel)")
        teacher_vbox = QVBoxLayout(grp_teacher)
        teacher_vbox.setContentsMargins(16, 22, 16, 16)
        teacher_vbox.setSpacing(12)

        # Nút thao tác giáo viên
        teacher_btn_box = QHBoxLayout()
        self.btn_import_teachers_excel = QPushButton("📥 NHẬP DANH SÁCH GIÁO VIÊN TỪ FILE EXCEL (.xlsx)")
        self.btn_import_teachers_excel.setStyleSheet("background-color: #107c41; color: white; font-weight: bold; padding: 8px 12px;")
        self.btn_import_teachers_excel.clicked.connect(self.import_teachers_excel_dialog)
        teacher_btn_box.addWidget(self.btn_import_teachers_excel)

        self.btn_download_teacher_template = QPushButton("📄 Tải file Excel mẫu danh sách Giáo viên")
        self.btn_download_teacher_template.clicked.connect(self.download_teachers_template_dialog)
        teacher_btn_box.addWidget(self.btn_download_teacher_template)
        teacher_btn_box.addStretch()
        teacher_vbox.addLayout(teacher_btn_box)

        # Bảng hiển thị giáo viên
        self.table_teachers = QTableWidget()
        self.table_teachers.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_teachers.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_teachers.setColumnCount(4)
        self.table_teachers.setHorizontalHeaderLabels(["ID", "Họ và tên giáo viên", "Tổ chuyên môn", "Ghi chú"])
        self.table_teachers.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_teachers.setMinimumHeight(200)
        self.table_teachers.setMaximumHeight(260)
        self.table_teachers.verticalHeader().setDefaultSectionSize(32)
        self.table_teachers.setAlternatingRowColors(True)
        teacher_vbox.addWidget(self.table_teachers)

        # Thêm thủ công 1 giáo viên
        add_gv_box = QHBoxLayout()
        self.txt_new_gv_name = QLineEdit()
        self.txt_new_gv_name.setPlaceholderText("Họ và tên giáo viên...")
        self.txt_new_gv_dept = QLineEdit()
        self.txt_new_gv_dept.setPlaceholderText("Tổ chuyên môn...")
        self.btn_add_gv = QPushButton("➕ Thêm giáo viên")
        self.btn_add_gv.clicked.connect(self.add_new_teacher)
        add_gv_box.addWidget(self.txt_new_gv_name, 2)
        add_gv_box.addWidget(self.txt_new_gv_dept, 1)
        add_gv_box.addWidget(self.btn_add_gv)
        teacher_vbox.addLayout(add_gv_box)

        vbox.addWidget(grp_teacher)

        # --- PHẦN 4: SAO LƯU & KHÔI PHỤC DỮ LIỆU ---
        grp_backup = QGroupBox("4. An toàn dữ liệu: Sao lưu & Khôi phục CSDL")
        backup_vbox = QVBoxLayout(grp_backup)
        backup_vbox.setContentsMargins(16, 22, 16, 16)
        backup_vbox.setSpacing(12)
        backup_btn_box = QHBoxLayout()
        self.btn_backup_now = QPushButton("💾 Sao lưu dữ liệu CSDL ngay (.bak)")
        self.btn_backup_now.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 8px 14px;")
        self.btn_backup_now.clicked.connect(self.backup_database_now)
        backup_btn_box.addWidget(self.btn_backup_now)

        self.btn_restore_now = QPushButton("📂 Khôi phục CSDL từ file sao lưu...")
        self.btn_restore_now.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 8px 14px;")
        self.btn_restore_now.clicked.connect(self.restore_database_dialog)
        backup_btn_box.addWidget(self.btn_restore_now)
        backup_btn_box.addStretch()
        backup_vbox.addLayout(backup_btn_box)

        lbl_backup_info = QLabel("Khuyên dùng: Nên bấm sao lưu định kỳ hoặc trước khi cài lại Windows / chuyển máy.")
        lbl_backup_info.setStyleSheet("color: #64748b; font-style: italic;")
        backup_vbox.addWidget(lbl_backup_info)

        vbox.addWidget(grp_backup)

        # --- PHẦN 5: BẢN QUYỀN & THÔNG TIN TÁC GIẢ ---
        grp_about = QGroupBox("5. Bản quyền phần mềm & Thông tin tác giả")
        about_vbox = QVBoxLayout(grp_about)
        about_vbox.setContentsMargins(16, 20, 16, 16)
        about_vbox.setSpacing(8)

        lbl_app_title = QLabel("🖨️ PHẦN MỀM QUẢN LÝ IN ẤN")
        lbl_app_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1e40af;")
        about_vbox.addWidget(lbl_app_title)

        lbl_author = QLabel("• <b>Tác giả:</b> Phạm Công Vinh")
        lbl_author.setStyleSheet("font-size: 11pt; color: #1e293b;")
        about_vbox.addWidget(lbl_author)

        lbl_role = QLabel("• <b>Chức vụ:</b> Bí thư chi đoàn 11A5, Chủ tịch CLB Nghiên cứu Khoa học, STEM và Robotics")
        lbl_role.setStyleSheet("font-size: 11pt; color: #1e293b;")
        about_vbox.addWidget(lbl_role)

        lbl_unit = QLabel("• <b>Đơn vị:</b> Trường THPT Bắc Đông Quan")
        lbl_unit.setStyleSheet("font-size: 11pt; color: #1e293b;")
        about_vbox.addWidget(lbl_unit)

        lbl_version = QLabel("• <b>Phiên bản:</b> v1.0.0 (Bản chính thức)")
        lbl_version.setStyleSheet("font-size: 10.5pt; color: #475569;")
        about_vbox.addWidget(lbl_version)

        lbl_copyright = QLabel("• <b>Bản quyền:</b> © 2026 Phạm Công Vinh - Trường THPT Bắc Đông Quan. All rights reserved.")
        lbl_copyright.setStyleSheet("font-size: 10pt; color: #64748b; font-style: italic;")
        about_vbox.addWidget(lbl_copyright)

        vbox.addWidget(grp_about)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    # ==================== DATA LOADING & LOGIC ====================
    def on_tab_changed(self, index):
        """Lazy loading: Chi nap du lieu tab khi nguoi dung nhap vao, giup may yeu mo app duoi 0.3 giay"""
        if index == 1 and (1 not in self._loaded_tabs or self._dirty_history):
            self.load_history_data()
            self._loaded_tabs.add(1)
            self._dirty_history = False
        elif index == 2 and (2 not in self._loaded_tabs or self._dirty_reports):
            self.load_report_data()
            self._loaded_tabs.add(2)
            self._dirty_reports = False
        elif index == 3 and 3 not in self._loaded_tabs:
            self.load_prices_table()
            self._loaded_tabs.add(3)
        elif index == 5 and 5 not in self._loaded_tabs:
            self.load_classes_table()
            self.load_teachers_table()
            self._loaded_tabs.add(5)

    def mark_history_and_reports_dirty(self):
        """Danh dau can lam moi Lich su & Bao cao khi nguoi dung thuc hien in hoac doi trang thai"""
        self._dirty_history = True
        self._dirty_reports = True
        current_idx = self.tabs.currentIndex()
        if current_idx == 1:
            self.load_history_data()
            self._dirty_history = False
        elif current_idx == 2:
            self.load_report_data()
            self._dirty_reports = False

    def load_initial_data(self):
        # 1. Load danh sách máy in (được cache)
        self.cb_printers.clear()
        printers = list_windows_printers()
        default_idx = 0
        for idx, p in enumerate(printers):
            self.cb_printers.addItem(p['display_name'], p)
            if p.get('is_default'):
                default_idx = idx
        if printers:
            self.cb_printers.setCurrentIndex(default_idx)

        # 2. Load presets
        self.cb_presets.clear()
        self.cb_presets.addItem("-- Chọn mẫu cài sẵn --", None)
        presets = get_presets()
        for pr in presets:
            self.cb_presets.addItem(pr['name'], pr)

        # 3. Load Requesters từ RAM cache
        self.load_requesters_dropdown()

        # 4. Load 3 người gần đây
        self.update_recent_requester_buttons()

        # Đánh dấu Tab 0 đã sẵn sàng; các tab khác chỉ nạp khi người dùng bấm vào
        self._loaded_tabs.add(0)

    def get_selected_printer_name(self) -> str:
        """Lay ten may in Windows thuc te dang duoc chon"""
        printer_item = self.cb_printers.currentData()
        if printer_item and isinstance(printer_item, dict):
            return printer_item.get("windows_name", self.cb_printers.currentText())
        return self.cb_printers.currentText()

    def open_selected_printer_properties(self, mode="preferences"):
        """Mo hop thoai Driver Properties de nguoi dung cau hinh dap ghim (Finisher), khay giay, duc lo..."""
        pname = self.get_selected_printer_name()
        if not pname:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một máy in trước!")
            return

        if mode == "properties":
            ok = open_printer_device_settings_dialog(pname)
            desc = "Thuộc tính thiết bị (Printer Properties)"
        else:
            ok = open_printer_preferences_dialog(pname)
            desc = "Tùy chọn in (Printing Preferences - Dập ghim, khay giấy)"

        if ok:
            self.status_bar_label.setText(f"💡 Đang mở {desc} của máy in: {pname}")
        else:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở cửa sổ cấu hình máy in cho '{pname}'.")

    def refresh_printers_dropdown(self):
        """Quet lai danh sach may in tren Windows"""
        printers = list_windows_printers(force_refresh=True)
        self.cb_printers.clear()
        default_idx = 0
        for idx, p in enumerate(printers):
            self.cb_printers.addItem(p['display_name'], p)
            if p.get('is_default'):
                default_idx = idx
        if printers:
            self.cb_printers.setCurrentIndex(default_idx)
        self.status_bar_label.setText(f"Đã làm mới danh sách máy in: tìm thấy {len(printers)} máy in.")

    def load_requesters_dropdown(self, keyword=""):
        self.cb_requesters.blockSignals(True)
        self.cb_requesters.clear()
        reqs = search_requesters(keyword, limit=50)
        for r in reqs:
            dept = f" ({r['department']})" if r.get('department') else ""
            if r['type'] == 'class':
                st_count = r.get('student_count', 0)
                st_info = f" (Sĩ số: {st_count} hs)" if st_count > 0 else ""
                display = f"[Lớp] {r['name']}{st_info}"
            elif r['type'] == 'teacher':
                display = f"[GV] {r['name']}{dept}"
            else:
                display = f"[Khác] {r['name']}"
            self.cb_requesters.addItem(display, r)
        self.cb_requesters.blockSignals(False)

    def on_search_requester_changed(self, text):
        self.load_requesters_dropdown(text.strip())

    def update_recent_requester_buttons(self):
        recent_ids = get_recent_requester_ids(limit=3)
        all_reqs = {r['id']: r for r in get_cached_requesters(active_only=False)}
        buttons = [self.btn_recent_1, self.btn_recent_2, self.btn_recent_3]
        for i, b in enumerate(buttons):
            if i < len(recent_ids) and recent_ids[i] in all_reqs:
                r = all_reqs[recent_ids[i]]
                b.setText(r['name'])
                b.setProperty("req_data", r)
                b.setVisible(True)
            else:
                b.setVisible(False)

    def on_recent_clicked(self):
        sender = self.sender()
        r_data = sender.property("req_data")
        if r_data:
            # Chọn trên dropdown
            for i in range(self.cb_requesters.count()):
                item_r = self.cb_requesters.itemData(i)
                if item_r and item_r['id'] == r_data['id']:
                    self.cb_requesters.setCurrentIndex(i)
                    break

    def on_requester_changed(self, index):
        r_data = self.cb_requesters.itemData(index)
        if r_data and r_data['type'] == 'class':
            # Tự động điền vào lớp liên quan nếu chọn lớp
            if not self.txt_related_classes.text():
                self.txt_related_classes.setText(r_data['name'])
            # Tự động điền số bản in = Sĩ số lớp nếu có
            st_count = r_data.get('student_count', 0)
            if st_count and st_count > 0:
                self.sp_copies.setValue(st_count)
                self.status_bar_label.setText(f"💡 Đã tự động đặt số bản in = {st_count} (theo sĩ số lớp {r_data['name']})")

    # ==================== LOGIC BẢNG GIÁ ====================
    def load_prices_table(self):
        prices = get_all_price_rules()
        self.table_prices.setUpdatesEnabled(False)
        self.table_prices.clearContents()
        self.table_prices.setRowCount(len(prices))
        color_map = {0: "Đen trắng", 1: "In màu"}
        duplex_map = {0: "1 mặt", 1: "2 mặt"}
        unit_map = {"sheet": "đ / tờ", "page": "đ / mặt"}

        for idx, p in enumerate(prices):
            self.table_prices.setItem(idx, 0, QTableWidgetItem(str(p['id'])))
            self.table_prices.setItem(idx, 1, QTableWidgetItem(str(p['paper'])))
            self.table_prices.setItem(idx, 2, QTableWidgetItem(color_map.get(p['color'], "Đen trắng")))
            self.table_prices.setItem(idx, 3, QTableWidgetItem(duplex_map.get(p['duplex'], "1 mặt")))
            self.table_prices.setItem(idx, 4, QTableWidgetItem(str(p.get('printer_name') or "Tất cả máy in")))
            self.table_prices.setItem(idx, 5, QTableWidgetItem(f"{p['price_per_unit']:,.0f}"))
            self.table_prices.setItem(idx, 6, QTableWidgetItem(unit_map.get(p['unit_type'], "đ / tờ")))
        self.table_prices.setUpdatesEnabled(True)

    def on_price_table_selected(self):
        selected = self.table_prices.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        val_str = self.table_prices.item(row, 5).text().replace(",", "").replace(".", "").strip()
        try:
            val = int(val_str)
            self.sp_edit_price.setValue(val)
        except ValueError:
            pass

    def save_selected_price_amount(self):
        selected = self.table_prices.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một dòng quy tắc giá trong bảng!")
            return
        row = selected[0].row()
        rule_id = int(self.table_prices.item(row, 0).text())
        new_price = float(self.sp_edit_price.value())

        update_price_rule_amount(rule_id, new_price)
        QMessageBox.information(self, "Thành công", f"Đã cập nhật đơn giá thành {new_price:,.0f} đ!")
        self.load_prices_table()
        self.recalculate_cost()

    def add_new_price_rule_from_ui(self):
        paper = self.cb_new_price_paper.currentText()
        color = self.cb_new_price_color.currentData()
        duplex = self.cb_new_price_duplex.currentData()
        price = float(self.sp_new_price_val.value())
        unit_type = self.cb_pricing_unit.currentData()

        add_price_rule(paper=paper, color=color, duplex=duplex, price=price, unit_type=unit_type)
        QMessageBox.information(self, "Thành công", f"Đã thêm quy tắc giá mới: {paper} | {price:,.0f} đ")
        self.load_prices_table()
        self.recalculate_cost()

    def reset_prices_to_default(self):
        reply = QMessageBox.question(
            self, "Khôi phục", "Khôi phục toàn bộ bảng giá về mức chuẩn ban đầu (250đ/350đ/1.000đ)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            reset_default_prices()
            QMessageBox.information(self, "Thành công", "Đã khôi phục bảng giá chuẩn!")
            self.load_prices_table()
            self.recalculate_cost()

    def save_pricing_unit_setting(self):
        unit = self.cb_pricing_unit.currentData()
        set_setting("pricing_unit", unit)
        QMessageBox.information(self, "Thành công", f"Đã lưu cách tính tiền: {'Tính theo Tờ giấy' if unit == 'sheet' else 'Tính theo Mặt in'}")
        self.recalculate_cost()

    # ==================== LOGIC LỚP & SĨ SỐ ====================
    def load_classes_table(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, grade, name, student_count, note FROM requesters WHERE type = 'class' ORDER BY grade ASC, name ASC")
            classes = cur.fetchall()
            self.table_classes.setUpdatesEnabled(False)
            self.table_classes.clearContents()
            self.table_classes.setRowCount(len(classes))
            for idx, c in enumerate(classes):
                self.table_classes.setItem(idx, 0, QTableWidgetItem(str(c[0])))
                self.table_classes.setItem(idx, 1, QTableWidgetItem(f"Khối {c[1]}" if c[1] else ""))
                self.table_classes.setItem(idx, 2, QTableWidgetItem(str(c[2])))
                self.table_classes.setItem(idx, 3, QTableWidgetItem(f"{c[3]} học sinh" if c[3] else "Chưa có"))
                self.table_classes.setItem(idx, 4, QTableWidgetItem(str(c[4] or "")))
            self.table_classes.setUpdatesEnabled(True)
        finally:
            conn.close()

    def on_class_table_selected(self):
        selected = self.table_classes.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        count_text = self.table_classes.item(row, 3).text().replace("học sinh", "").strip()
        try:
            cnt = int(count_text)
            self.sp_edit_student_count.setValue(cnt)
        except ValueError:
            self.sp_edit_student_count.setValue(45)

    def save_class_student_count(self):
        selected = self.table_classes.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một lớp trong bảng!")
            return
        row = selected[0].row()
        class_id = int(self.table_classes.item(row, 0).text())
        class_name = self.table_classes.item(row, 2).text()
        count = self.sp_edit_student_count.value()

        conn = get_connection()
        try:
            with conn:
                conn.execute("UPDATE requesters SET student_count = ? WHERE id = ?", (count, class_id))
            QMessageBox.information(self, "Thành công", f"Đã cập nhật sĩ số lớp {class_name} thành {count} học sinh!")
            self.load_classes_table()
            self.load_requesters_dropdown()
        finally:
            conn.close()

    def import_classes_excel_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Excel danh sách Lớp có Sĩ số", "", "File Excel (*.xlsx *.xls)"
        )
        if path:
            count, msg = import_classes_from_excel(path)
            if count > 0:
                QMessageBox.information(self, "Nhập Excel thành công", msg)
                self.load_classes_table()
                self.load_requesters_dropdown()
            else:
                QMessageBox.critical(self, "Lỗi nhập Excel", msg)

    def download_classes_template_dialog(self):
        dest, _ = QFileDialog.getSaveFileName(
            self, "Lưu file Excel mẫu danh sách Lớp", "Mau_Danh_Sach_Lop.xlsx", "File Excel (*.xlsx)"
        )
        if dest:
            try:
                create_classes_template_excel(dest)
                QMessageBox.information(self, "Thành công", f"Đã tạo file Excel mẫu tại:\n{dest}\n\nBạn có thể mở file này để điền danh sách lớp và sĩ số rồi bấm 'Nhập danh sách Lớp từ file Excel'.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể tạo file mẫu: {e}")

    # ==================== LOGIC GIÁO VIÊN ====================
    def load_teachers_table(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, department, note FROM requesters WHERE type = 'teacher' AND active = 1 ORDER BY name ASC")
            teachers = cur.fetchall()
            self.table_teachers.setUpdatesEnabled(False)
            self.table_teachers.clearContents()
            self.table_teachers.setRowCount(len(teachers))
            for idx, t in enumerate(teachers):
                self.table_teachers.setItem(idx, 0, QTableWidgetItem(str(t[0])))
                self.table_teachers.setItem(idx, 1, QTableWidgetItem(str(t[1])))
                self.table_teachers.setItem(idx, 2, QTableWidgetItem(str(t[2] or "")))
                self.table_teachers.setItem(idx, 3, QTableWidgetItem(str(t[3] or "")))
            self.table_teachers.setUpdatesEnabled(True)
        finally:
            conn.close()

    def import_teachers_excel_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Excel danh sách Giáo viên", "", "File Excel (*.xlsx *.xls)"
        )
        if path:
            count, msg = import_teachers_from_excel(path)
            if count > 0:
                QMessageBox.information(self, "Nhập Excel thành công", msg)
                self.load_teachers_table()
                self.load_requesters_dropdown()
            else:
                QMessageBox.critical(self, "Lỗi nhập Excel", msg)

    def download_teachers_template_dialog(self):
        dest, _ = QFileDialog.getSaveFileName(
            self, "Lưu file Excel mẫu danh sách Giáo viên", "Mau_Danh_Sach_Giao_Vien.xlsx", "File Excel (*.xlsx)"
        )
        if dest:
            try:
                create_teachers_template_excel(dest)
                QMessageBox.information(self, "Thành công", f"Đã tạo file Excel mẫu tại:\n{dest}\n\nBạn có thể mở file này để điền danh sách giáo viên rồi bấm 'Nhập danh sách Giáo viên từ file Excel'.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể tạo file mẫu: {e}")

    def apply_preset(self, index):
        preset = self.cb_presets.itemData(index)
        if not preset:
            return
        # Set paper
        paper_idx = self.cb_paper.findText(preset.get('paper', 'A4'))
        if paper_idx >= 0:
            self.cb_paper.setCurrentIndex(paper_idx)
        # Set duplex
        duplex_val = preset.get('duplex', 1)
        for i in range(self.cb_duplex.count()):
            if self.cb_duplex.itemData(i) == duplex_val:
                self.cb_duplex.setCurrentIndex(i)
                break
        # Set color
        color_val = preset.get('color', 0)
        for i in range(self.cb_color.count()):
            if self.cb_color.itemData(i) == color_val:
                self.cb_color.setCurrentIndex(i)
                break
        self.recalculate_cost()

    # ==================== QUEUE MANAGEMENT ====================
    def choose_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn file cần in", "",
            "Tất cả tài liệu hỗ trợ (*.docx *.doc *.xlsx *.xls *.pptx *.ppt *.pdf *.jpg *.png *.jpeg);;Word (*.docx *.doc);;Excel (*.xlsx *.xls);;PowerPoint (*.pptx *.ppt);;PDF (*.pdf);;Ảnh (*.jpg *.png *.jpeg)"
        )
        if files:
            self.add_files_to_queue(files)

    def add_files_to_queue(self, file_paths):
        if not file_paths:
            return

        self.progress_queue.setVisible(True)
        self.progress_queue.setMaximum(len(file_paths))
        self.progress_queue.setValue(0)
        self.status_bar_label.setText(f"Đang xử lý {len(file_paths)} file...")

        self.convert_worker = FileConvertWorker(file_paths)
        self.convert_worker.file_converted_signal.connect(self.on_file_converted)
        self.convert_worker.progress_signal.connect(self.on_convert_progress)
        self.convert_worker.all_done_signal.connect(self.on_convert_all_done)
        self.convert_worker.start()

    def on_file_converted(self, item):
        self.current_queue.append(item)
        row = self.table_queue.rowCount()
        self.table_queue.insertRow(row)
        self.table_queue.setItem(row, 0, QTableWidgetItem(item['file_name']))
        self.table_queue.setItem(row, 1, QTableWidgetItem(item['ext'].upper().replace(".", "")))
        self.table_queue.setItem(row, 2, QTableWidgetItem(str(item['pages'])))

        status_item = QTableWidgetItem()
        if item['convert_ok']:
            status_item.setText("🟢 Sẵn sàng")
            status_item.setForeground(QColor("#16a34a"))
        else:
            status_item.setText("❌ Lỗi đổi")
            status_item.setForeground(QColor("#dc2626"))
        self.table_queue.setItem(row, 3, status_item)
        self.table_queue.setItem(row, 4, QTableWidgetItem(item['original_path']))

        if self.selected_file_index == -1:
            self.table_queue.selectRow(0)

    def on_convert_progress(self, current, total):
        self.progress_queue.setValue(current)
        self.status_bar_label.setText(f"Đang xử lý file {current}/{total}...")

    def on_convert_all_done(self):
        self.progress_queue.setVisible(False)
        self.status_bar_label.setText(f"Hàng đợi: {len(self.current_queue)} file sẵn sàng.")
        self.recalculate_cost()

    def on_queue_selection_changed(self):
        selected_rows = self.table_queue.selectionModel().selectedRows()
        if not selected_rows:
            self.selected_file_index = -1
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self.current_queue):
            self.selected_file_index = row
            item = self.current_queue[row]
            self.current_pdf_for_preview = item.get('pdf_path')
            self.total_preview_pages = item.get('pages', 1)
            self.current_preview_page = 1
            self.update_preview()
            self.recalculate_cost()

    def remove_selected_file(self):
        if self.selected_file_index >= 0 and self.selected_file_index < len(self.current_queue):
            self.current_queue.pop(self.selected_file_index)
            self.table_queue.removeRow(self.selected_file_index)
            self.selected_file_index = -1
            self.lbl_preview_img.setText("Đã xóa file khỏi hàng đợi.")
            self.recalculate_cost()

    def clear_queue(self):
        self.current_queue.clear()
        self.table_queue.setRowCount(0)
        self.selected_file_index = -1
        self.lbl_preview_img.setText("Hàng đợi trống.")
        self.recalculate_cost()

    def apply_config_to_all(self):
        if not self.current_queue:
            QMessageBox.warning(self, "Thông báo", "Hàng đợi đang trống!")
            return
        QMessageBox.information(
            self, "Thành công",
            f"Đã lưu và áp dụng cấu hình in hiện tại cho toàn bộ {len(self.current_queue)} file trong hàng đợi!"
        )

    # ==================== PREVIEW & PRICING ====================
    def update_preview(self):
        if not self.current_pdf_for_preview or not os.path.exists(self.current_pdf_for_preview):
            self.lbl_preview_img.setText("Kéo file vào để xem trước")
            self.lbl_page_indicator.setText("Trang 0 / 0")
            return

        cache_key = (self.current_pdf_for_preview, self.current_preview_page, round(self.zoom_factor, 2))
        if cache_key in self.preview_cache:
            pixmap = self.preview_cache[cache_key]
        else:
            # 75 DPI la do phan giai toi uu cho o preview (~350px), tiet kiem 70% CPU va RAM cho may yeu
            dpi = int(75 * self.zoom_factor)
            data = render_page_pixmap_data(self.current_pdf_for_preview, self.current_preview_page, dpi=dpi)
            if data:
                samples, w, h, s, a = data
                fmt = QImage.Format_RGBA8888 if a else QImage.Format_RGB888
                qimg = QImage(samples, w, h, s, fmt).copy()
                pixmap = QPixmap.fromImage(qimg)
                # Giu toi da 15 trang cache de khong tran RAM may yeu (chiem duoi 20MB)
                if len(self.preview_cache) > 15:
                    self.preview_cache.pop(next(iter(self.preview_cache)))
                self.preview_cache[cache_key] = pixmap
            else:
                pixmap = None

        if pixmap and not pixmap.isNull():
            transform_mode = Qt.FastTransformation if self.zoom_factor <= 1.0 else Qt.SmoothTransformation
            self.lbl_preview_img.setPixmap(
                pixmap.scaled(self.lbl_preview_img.width() - 10, self.lbl_preview_img.height() - 10, Qt.KeepAspectRatio, transform_mode)
            )
            self.lbl_page_indicator.setText(f"Trang {self.current_preview_page} / {self.total_preview_pages}")
            self.btn_zoom_reset.setText(f"{int(self.zoom_factor * 100)}%")

    def prev_preview_page(self):
        if self.current_preview_page > 1:
            self.current_preview_page -= 1
            self.update_preview()

    def next_preview_page(self):
        if self.current_preview_page < self.total_preview_pages:
            self.current_preview_page += 1
            self.update_preview()

    def zoom_in_preview(self):
        self.zoom_factor = min(self.zoom_factor * 1.25, 3.0)
        self.update_preview()

    def zoom_out_preview(self):
        self.zoom_factor = max(self.zoom_factor * 0.8, 0.4)
        self.update_preview()

    def zoom_reset_preview(self):
        self.zoom_factor = 1.0
        self.update_preview()

    def open_fullscreen_preview(self):
        if not self.current_pdf_for_preview or not os.path.exists(self.current_pdf_for_preview):
            QMessageBox.information(self, "Thông báo", "Chưa có file PDF nào để xem toàn màn hình.")
            return
        dlg = FullscreenPreviewDialog(self.current_pdf_for_preview, self.current_preview_page, self)
        dlg.exec()

    def recalculate_cost(self):
        if self.selected_file_index < 0 or self.selected_file_index >= len(self.current_queue):
            self.lbl_sheets_calc.setText("0 tờ")
            self.lbl_calc_amount.setText("0 đ")
            return

        item = self.current_queue[self.selected_file_index]
        total_p = item.get('pages', 1)

        # Khoảng trang
        range_str = self.txt_page_range.text().strip()
        selected_pages = parse_page_ranges(range_str, total_p)
        actual_pages = len(selected_pages)

        copies = self.sp_copies.value()
        paper = self.cb_paper.currentText()
        duplex = self.cb_duplex.currentData()
        color = self.cb_color.currentData()

        is_booklet = (duplex == 3)

        cost_info = calculate_print_cost(
            pages_count=actual_pages,
            copies=copies,
            paper=paper,
            duplex=duplex,
            color=color,
            is_booklet=is_booklet
        )

        self.lbl_unit_price.setText(f"{cost_info['unit_price']:,.0f} đ / {cost_info['unit_type']}")
        self.lbl_sheets_calc.setText(f"{cost_info['total_sheets']:,} tờ ({actual_pages} trang x {copies} bản)")

        if self.chk_free.isChecked():
            self.lbl_calc_amount.setText("0 đ (Miễn phí)")
        elif self.chk_override_amount.isChecked():
            self.lbl_calc_amount.setText(f"{self.sp_override_amount.value():,.0f} đ (Sửa tay)")
        else:
            self.lbl_calc_amount.setText(f"{cost_info['amount']:,.0f} đ")

    def on_override_toggled(self, checked):
        self.sp_override_amount.setEnabled(checked)
        self.recalculate_cost()

    def on_free_toggled(self, checked):
        self.recalculate_cost()

    # ==================== EXECUTE PRINT & SAVE ====================
    def execute_current_print(self):
        self._process_job(mode="silent")

    def execute_windows_dialog_print(self):
        """
        Mo hop thoai in goc cua Windows.
        Sau khi nguoi dung bam IN tren cua so Windows:
        1. Tu dong lay toan bo thuoc tinh in thuc te: May in, So ban in, Che do 2 mat, Mau sac, Kho giay, Khoang trang.
        2. Cap nhat nguoc lai toan bo cac truong cau hinh tren giao dien chinh cua App de dong bo.
        3. Tinh toan lai so to va thanh tien tu dong theo bang gia.
        4. Thuc hien in qua may in, ghi so nhat ky SQLite va dong bo ngay lap tuc vao file Excel.
        """
        if self.selected_file_index < 0 or self.selected_file_index >= len(self.current_queue):
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn một file trong hàng đợi trước!")
            return

        item = self.current_queue[self.selected_file_index]
        if not item.get('convert_ok') or not item.get('pdf_path'):
            QMessageBox.critical(self, "Lỗi chuyển đổi", f"File này chưa được chuyển đổi thành công:\n{item.get('convert_error')}")
            return

        req_data = self.cb_requesters.currentData()
        if not req_data:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn Người yêu cầu (giáo viên hoặc lớp)!")
            return

        src_pdf = item.get('pdf_path')
        total_pages = item.get('pages', 1)

        # 1. Mo cua so in goc cua Windows (PrintDlgW)
        from app.services.printer import show_native_windows_print_dialog, find_or_extract_sumatra, execute_sumatra_print, build_sumatra_print_settings
        current_printer = self.get_selected_printer_name()
        current_copies = self.sp_copies.value()
        current_duplex = self.cb_duplex.currentData()
        current_color = self.cb_color.currentData()
        current_paper = self.cb_paper.currentText()

        dlg_result = show_native_windows_print_dialog(
            parent_hwnd=int(self.winId()),
            current_printer=current_printer,
            current_copies=current_copies,
            current_duplex=current_duplex,
            current_color=current_color,
            current_paper=current_paper,
            total_pages=total_pages
        )

        # Neu nguoi dung bam Cancel hoac dong cua so Windows -> Huy an toan
        if dlg_result is None:
            self.status_bar_label.setText("ℹ️ Người dùng đã hủy hoặc đóng cửa sổ in Windows.")
            return

        # 2. TRÍCH XUẤT CÁC THÔNG SỐ VỪA ĐƯỢC CHỌN TỪ WINDOWS
        chosen_printer = dlg_result.get('printer_name') or current_printer
        chosen_copies = max(1, dlg_result.get('copies', 1))
        final_duplex = dlg_result.get('duplex', current_duplex)
        final_color = dlg_result.get('color', current_color)
        final_paper = dlg_result.get('paper', current_paper)
        final_range = dlg_result.get('page_range', '')
        is_booklet = (final_duplex == 3)

        # 3. TỰ ĐỘNG ĐỒNG BỘ CẤU HÌNH NGƯỢC LẠI GIAO DIỆN CỦA APP
        # Cap nhat May in
        idx_pr = self.cb_printers.findText(chosen_printer)
        if idx_pr >= 0:
            self.cb_printers.setCurrentIndex(idx_pr)
        else:
            self.cb_printers.addItem(chosen_printer)
            self.cb_printers.setCurrentText(chosen_printer)

        # Cap nhat So ban in
        self.sp_copies.setValue(chosen_copies)

        # Cap nhat Kho giay
        idx_paper = self.cb_paper.findText(final_paper)
        if idx_paper >= 0:
            self.cb_paper.setCurrentIndex(idx_paper)

        # Cap nhat Che do in (Duplex)
        idx_dup = self.cb_duplex.findData(final_duplex)
        if idx_dup >= 0:
            self.cb_duplex.setCurrentIndex(idx_dup)

        # Cap nhat Mau sac
        idx_col = self.cb_color.findData(final_color)
        if idx_col >= 0:
            self.cb_color.setCurrentIndex(idx_col)

        # Cap nhat Khoang trang
        self.txt_page_range.setText(final_range)

        # 4. TÍNH TOÁN LẠI SỐ TRANG, SỐ TỜ VÀ THÀNH TIỀN TỰ ĐỘNG
        if final_range:
            selected_pages = parse_page_ranges(final_range, total_pages)
            actual_pages_printed = len(selected_pages)
        else:
            selected_pages = list(range(1, total_pages + 1))
            actual_pages_printed = total_pages

        cost_info = calculate_print_cost(
            pages_count=actual_pages_printed,
            copies=chosen_copies,
            paper=final_paper,
            duplex=final_duplex,
            color=final_color,
            is_booklet=is_booklet
        )

        final_amount = cost_info['amount']
        is_free = 1 if self.chk_free.isChecked() else 0
        override_reason = self.txt_free_reason.text().strip()
        amount_override = None

        if is_free:
            final_amount = 0.0
        elif self.chk_override_amount.isChecked():
            amount_override = float(self.sp_override_amount.value())
            final_amount = amount_override

        # Cap nhat tong ket thanh tien len giao dien
        self.lbl_cost_summary.setText(f"Tổng: {cost_info['total_sheets']} tờ | {final_amount:,.0f} đ")
        self.lbl_sheets_calc.setText(f"{cost_info['total_sheets']:,} tờ ({actual_pages_printed} trang x {chosen_copies} bản)")
        self.lbl_calc_amount.setText(f"{final_amount:,.0f} đ")

        # 5. XỬ LÝ FILE PDF CẦN IN (Cắt khoảng trang / Booklet nếu có)
        ready_pdf = src_pdf
        if final_range and len(selected_pages) < total_pages:
            custom_range_pdf = os.path.splitext(src_pdf)[0] + "_range.pdf"
            extract_pages_to_new_pdf(src_pdf, custom_range_pdf, selected_pages)
            ready_pdf = custom_range_pdf

        if is_booklet:
            booklet_pdf = os.path.splitext(ready_pdf)[0] + "_booklet.pdf"
            try:
                create_booklet_pdf(ready_pdf, booklet_pdf, target_paper=final_paper)
                ready_pdf = booklet_pdf
                duplex_for_printer = 2
            except Exception as b_err:
                QMessageBox.critical(self, "Lỗi tạo Booklet", f"Không thể dàn trang Booklet: {b_err}")
                return
        else:
            duplex_for_printer = final_duplex

        # 6. LƯU BẢN SAO THEO MỤC 5.4
        saved_orig, saved_pdf = organize_and_save_files(
            original_file_path=item['original_path'],
            converted_pdf_path=ready_pdf,
            requester_type=req_data['type'],
            requester_name=req_data['name'],
            copies=chosen_copies,
            title=item['file_name']
        )

        # 7. GHI NHẬT KÝ VÀO SQLITE & ĐỒNG BỘ VÀO EXCEL
        job_data = {
            "requester_id": req_data['id'],
            "related_classes": self.txt_related_classes.text().strip(),
            "title": item['file_name'],
            "file_type": item['ext'].replace(".", ""),
            "original_file_path": item['original_path'],
            "pages": actual_pages_printed,
            "page_range": final_range if final_range else "Toàn bộ",
            "copies": chosen_copies,
            "sheets": cost_info['total_sheets'],
            "printer_name": chosen_printer,
            "paper": final_paper,
            "duplex": final_duplex,
            "color": final_color,
            "unit_price": cost_info['unit_price'],
            "amount": final_amount,
            "amount_override": amount_override,
            "is_free": is_free,
            "override_reason": override_reason,
            "saved_path": saved_orig,
            "pdf_path": saved_pdf,
            "status": "printed",
            "paid_status": "unpaid" if not is_free else "paid",
            "note": self.txt_job_note.text().strip(),
            "print_file_path": ready_pdf
        }

        job_id = create_print_job(job_data)
        append_job_to_excel_async(job_id)
        self.mark_history_and_reports_dirty()
        self.update_recent_requester_buttons()

        # 8. GỬI LỆNH IN QUA SUMATRAPDF (VỚI CÁC THIẾT LẬP THỰC TẾ TỪ WINDOWS)
        sumatra_exe = find_or_extract_sumatra(get_setting("sumatra_path"))
        settings_str = build_sumatra_print_settings(
            copies=chosen_copies,
            duplex=duplex_for_printer,
            color=final_color,
            paper=final_paper,
            collate=True
        )

        self.status_bar_label.setText(f"⏳ Đang gửi file in tới máy in [{chosen_printer}]...")
        QApplication.processEvents()

        execute_sumatra_print(
            sumatra_exe,
            chosen_printer,
            ready_pdf,
            settings_str
        )

        # 9. THÔNG BÁO TỔNG KẾT
        duplex_names = {0: "1 mặt", 1: "2 mặt (Lật cạnh dài)", 2: "2 mặt (Lật cạnh ngắn)", 3: "📖 In Booklet"}
        color_name = "In màu" if final_color == 1 else "Đen trắng"

        msg = (
            f"🎉 ĐÃ IN THÀNH CÔNG VỚI THIẾT LẬP TỪ WINDOWS (Lượt #{job_id})!\n\n"
            f"📋 THUỘC TÍNH IN THỰC TẾ TỪ CỬA SỔ WINDOWS:\n"
            f"• Máy in đã chọn: {chosen_printer}\n"
            f"• Số bản in (Copies): {chosen_copies} bản\n"
            f"• Khổ giấy & Chế độ: {final_paper} | {duplex_names.get(final_duplex, '1 mặt')} | {color_name}\n"
            f"• Số trang: {actual_pages_printed} trang ({final_range if final_range else 'Toàn bộ'})\n\n"
            f"💰 KẾT QUẢ TÍNH TIỀN TỰ ĐỘNG:\n"
            f"• Tổng số tờ giấy thực tế: {cost_info['total_sheets']} tờ\n"
            f"• Đơn giá áp dụng: {cost_info['unit_price']:,.0f} đ\n"
            f"• THÀNH TIỀN: {final_amount:,.0f} đ\n\n"
            f"📁 Đã cập nhật cấu hình giao diện, ghi sổ nhật ký và đồng bộ vào file Excel!"
        )
        QMessageBox.information(self, "In thành công & Đã tính tiền", msg)

    def execute_save_only(self):
        self._process_job(mode="save_only")

    def _process_job(self, mode="silent"):
        if self.selected_file_index < 0 or self.selected_file_index >= len(self.current_queue):
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn một file trong hàng đợi trước!")
            return

        item = self.current_queue[self.selected_file_index]
        if mode != "dialog" and (not item.get('convert_ok') or not item.get('pdf_path')):
            QMessageBox.critical(self, "Lỗi chuyển đổi", f"File này chưa được chuyển đổi thành công:\n{item.get('convert_error')}")
            return

        req_data = self.cb_requesters.currentData()
        if not req_data:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn Người yêu cầu (giáo viên hoặc lớp)!")
            return

        # Cảnh báo an toàn nếu số bản lớn
        copies = self.sp_copies.value()
        warn_threshold = int(get_setting("warn_high_copies_threshold", "100"))
        if copies >= warn_threshold:
            reply = QMessageBox.question(
                self, "Xác nhận số lượng lớn",
                f"Bạn đang đặt in {copies} bản. Thao tác này sẽ in số lượng giấy rất lớn.\nBạn có chắc chắn muốn in không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # 1. Trích xuất khoảng trang nếu có
        src_pdf = item.get('pdf_path')
        range_str = self.txt_page_range.text().strip()
        item_pages = item.get('pages', 1)
        selected_pages = parse_page_ranges(range_str, item_pages) if item_pages else [1]

        ready_pdf = src_pdf
        if src_pdf and os.path.exists(src_pdf):
            if len(selected_pages) < item_pages:
                custom_range_pdf = os.path.splitext(src_pdf)[0] + "_range.pdf"
                extract_pages_to_new_pdf(src_pdf, custom_range_pdf, selected_pages)
                ready_pdf = custom_range_pdf

        # 2. Xử lý in Booklet nếu người dùng chọn
        duplex_val = self.cb_duplex.currentData()
        paper = self.cb_paper.currentText()
        color = self.cb_color.currentData()
        is_booklet = (duplex_val == 3)

        if is_booklet:
            if ready_pdf and os.path.exists(ready_pdf):
                booklet_pdf = os.path.splitext(ready_pdf)[0] + "_booklet.pdf"
                try:
                    create_booklet_pdf(ready_pdf, booklet_pdf, target_paper=paper)
                    ready_pdf = booklet_pdf
                    # In booklet luon la 2 mat lat canh ngan (duplexshort)
                    duplex_for_printer = 2
                except Exception as b_err:
                    QMessageBox.critical(self, "Lỗi tạo Booklet", f"Không thể dàn trang Booklet: {b_err}")
                    return
            else:
                QMessageBox.critical(self, "Lỗi", "In Booklet yêu cầu file cần được chuyển đổi qua PDF để dàn trang.")
                return
        else:
            duplex_for_printer = duplex_val

        # 3. Tính toán tiền và số tờ
        cost_info = calculate_print_cost(
            pages_count=len(selected_pages),
            copies=copies,
            paper=paper,
            duplex=duplex_val,
            color=color,
            is_booklet=is_booklet
        )

        final_amount = cost_info['amount']
        is_free = 1 if self.chk_free.isChecked() else 0
        override_reason = self.txt_free_reason.text().strip()
        amount_override = None

        if is_free:
            final_amount = 0.0
        elif self.chk_override_amount.isChecked():
            amount_override = float(self.sp_override_amount.value())
            final_amount = amount_override

        # 4. Lưu bản sao theo Mục 5.4
        saved_orig, saved_pdf = organize_and_save_files(
            original_file_path=item['original_path'],
            converted_pdf_path=ready_pdf,
            requester_type=req_data['type'],
            requester_name=req_data['name'],
            copies=copies,
            title=item['file_name']
        )

        # 5. Ghi nhật ký vào SQLite trước
        printer_name = self.get_selected_printer_name()

        job_data = {
            "requester_id": req_data['id'],
            "related_classes": self.txt_related_classes.text().strip(),
            "title": item['file_name'],
            "file_type": item['ext'].replace(".", ""),
            "original_file_path": item['original_path'],
            "pages": len(selected_pages),
            "page_range": range_str,
            "copies": copies,
            "sheets": cost_info['total_sheets'],
            "printer_name": printer_name,
            "paper": paper,
            "duplex": duplex_val,
            "color": color,
            "unit_price": cost_info['unit_price'],
            "amount": final_amount,
            "amount_override": amount_override,
            "is_free": is_free,
            "override_reason": override_reason,
            "saved_path": saved_orig,
            "pdf_path": saved_pdf,
            "status": "pending" if mode != "save_only" else "printed",
            "paid_status": "unpaid" if not is_free else "paid",
            "note": self.txt_job_note.text().strip(),
            "print_file_path": ready_pdf
        }

        job_id = create_print_job(job_data)
        job_data['job_id'] = job_id

        # 6. Nếu chỉ ghi sổ (không in qua máy)
        if mode == "save_only":
            update_print_job_status(job_id, "printed")
            append_job_to_excel_async(job_id)
            QMessageBox.information(self, "Thành công", f"Đã ghi sổ thủ công lượt in #{job_id} thành công!\nSố tờ: {cost_info['total_sheets']} | Thành tiền: {final_amount:,.0f} đ")
            self.mark_history_and_reports_dirty()
            return

        # 7. Gửi lệnh in (ngầm qua SumatraPDF hoặc mở cửa sổ Windows)
        from app.services.printer import find_or_extract_sumatra
        sumatra_exe = find_or_extract_sumatra(get_setting("sumatra_path"))

        settings_str = build_sumatra_print_settings(
            copies=copies,
            duplex=duplex_for_printer,
            color=color,
            paper=paper,
            collate=True
        )

        self.btn_print_now.setEnabled(False)
        self.btn_print_windows.setEnabled(False)
        if mode == "dialog":
            self.btn_print_windows.setText("Đang mở cửa sổ in Windows...")
        else:
            self.btn_print_now.setText("Đang gửi lệnh in tới máy in...")

        self.worker = BackgroundPrintWorker(job_data, sumatra_exe, settings_str, print_mode=mode)
        self.worker.finished_signal.connect(self.on_print_job_finished)
        self.worker.start()

    def on_print_job_finished(self, data):
        self.btn_print_now.setEnabled(True)
        self.btn_print_now.setText("🖨️ IN NHANH TỰ ĐỘNG (SILENT)")
        self.btn_print_windows.setEnabled(True)
        self.btn_print_windows.setText("🖥️ MỞ CỬA SỔ IN WINDOWS (PRINT DIALOG)")
        job_id = data.get("job_id")
        res = data.get("result", {})
        mode = data.get("mode", "silent")

        if res.get("success"):
            update_print_job_status(job_id, "printed")
            append_job_to_excel_async(job_id)
            if mode == "dialog":
                QMessageBox.information(
                    self, "Hoàn thành",
                    f"Đã xử lý in qua cửa sổ Windows cho lượt #{job_id}!\n"
                    f"- Bản sao file đã lưu vào thư mục có tổ chức\n"
                    f"- Đã ghi nhật ký và đồng bộ Excel."
                )
            else:
                QMessageBox.information(
                    self, "In thành công",
                    f"Đã gửi lệnh in #{job_id} tới máy in thành công!\n"
                    f"- Bản sao file đã lưu vào thư mục có tổ chức\n"
                    f"- Đã ghi nhật ký và đồng bộ Excel."
                )
        else:
            if res.get("cancelled"):
                update_print_job_status(job_id, "cancelled", res.get("error"))
                QMessageBox.information(self, "Thông báo", "Bạn đã đóng hoặc hủy thao tác trong cửa sổ in.")
            else:
                update_print_job_status(job_id, "error", res.get("error"))
                QMessageBox.critical(self, "Lỗi in", f"Lỗi gửi lệnh in #{job_id}:\n{res.get('error')}\n(Bản ghi vẫn được lưu trong lịch sử để bạn thử lại)")

        self.mark_history_and_reports_dirty()
        self.update_recent_requester_buttons()

    def execute_batch_print_all(self):
        """In toàn bộ các file trong hàng đợi có convert_ok = True"""
        if not self.current_queue:
            QMessageBox.warning(self, "Thông báo", "Hàng đợi đang trống! Hãy kéo thả file vào trước.")
            return

        valid_items = [(idx, item) for idx, item in enumerate(self.current_queue) if item.get('convert_ok')]
        if not valid_items:
            QMessageBox.warning(self, "Thông báo", "Không có file nào trong hàng đợi sẵn sàng để in.")
            return

        req_data = self.cb_requesters.currentData()
        if not req_data:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn Người yêu cầu (giáo viên hoặc lớp) trước khi in!")
            return

        copies = self.sp_copies.value()
        paper = self.cb_paper.currentText()
        duplex_val = self.cb_duplex.currentData()
        color = self.cb_color.currentData()
        is_booklet = (duplex_val == 3)
        printer_name = self.get_selected_printer_name()

        est_sheets = 0
        est_amount = 0.0
        for _, item in valid_items:
            c = calculate_print_cost(
                pages_count=item.get('pages', 1),
                copies=copies,
                paper=paper,
                duplex=duplex_val,
                color=color,
                is_booklet=is_booklet
            )
            est_sheets += c['total_sheets']
            est_amount += c['amount']

        confirm = QMessageBox.question(
            self, "Xác nhận in toàn bộ hàng đợi",
            f"Bạn có chắc chắn muốn in liên tiếp {len(valid_items)} file trong hàng đợi?\n\n"
            f"- Người yêu cầu: {req_data['name']}\n"
            f"- Máy in: {printer_name}\n"
            f"- Số bản in mỗi file: {copies}\n"
            f"- Ước tính tổng số tờ: {est_sheets:,} tờ\n"
            f"- Ước tính thành tiền: {est_amount:,.0f} đ\n\n"
            f"Hệ thống sẽ gửi lệnh in tự động lần lượt từng file.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        self.btn_batch_print_all.setEnabled(False)
        self.btn_batch_print_all.setText("Đang in hàng loạt...")
        self.btn_print_now.setEnabled(False)
        self.btn_print_windows.setEnabled(False)

        self.progress_queue.setVisible(True)
        self.progress_queue.setMaximum(len(valid_items))
        self.progress_queue.setValue(0)

        sumatra_exe = find_or_extract_sumatra(get_setting("sumatra_path"))
        job_configs = {
            "req_data": req_data,
            "related_classes": self.txt_related_classes.text().strip(),
            "duplex_val": duplex_val,
            "paper": paper,
            "color": color,
            "copies": copies,
            "printer_name": printer_name,
            "note": self.txt_job_note.text().strip()
        }

        self.batch_worker = BatchPrintWorker(valid_items, job_configs, sumatra_exe)
        self.batch_worker.progress_signal.connect(self.on_batch_progress)
        self.batch_worker.item_status_signal.connect(self.on_batch_item_status)
        self.batch_worker.finished_signal.connect(self.on_batch_finished)
        self.batch_worker.start()

    def on_batch_progress(self, current, total, filename):
        self.progress_queue.setValue(current)
        self.status_bar_label.setText(f"Đang in hàng loạt: {current}/{total} - {filename}")

    def on_batch_item_status(self, queue_idx, status_text, color_code):
        if 0 <= queue_idx < self.table_queue.rowCount():
            item = self.table_queue.item(queue_idx, 3)
            if not item:
                item = QTableWidgetItem()
                self.table_queue.setItem(queue_idx, 3, item)
            item.setText(status_text)
            item.setForeground(QColor(color_code))

    def on_batch_finished(self, summary):
        self.btn_batch_print_all.setEnabled(True)
        self.btn_batch_print_all.setText("🚀 IN TẤT CẢ FILE TRONG HÀNG ĐỢI (BATCH)")
        self.btn_print_now.setEnabled(True)
        self.btn_print_windows.setEnabled(True)
        self.progress_queue.setVisible(False)
        self.status_bar_label.setText(f"Hoàn thành in hàng loạt {summary['success']}/{summary['total']} file.")

        play_alert_sound()

        self.mark_history_and_reports_dirty()
        self.update_recent_requester_buttons()

        QMessageBox.information(
            self, "Hoàn tất in hàng loạt",
            f"Đã hoàn thành in hàng loạt!\n\n"
            f"- Tổng số file: {summary['total']}\n"
            f"- Thành công: {summary['success']} file\n"
            f"- Thất bại: {summary['failed']} file\n"
            f"- Tổng số tờ giấy đã in: {summary['total_sheets']:,} tờ\n"
            f"- Tổng số tiền: {summary['total_amount']:,.0f} đ\n\n"
            f"Toàn bộ bản ghi đã được ghi sổ CSDL và đồng bộ Excel."
        )

    def generate_receipt_for_selected(self):
        """Xuất phiếu thu tiền in ấn đẹp theo quy chuẩn văn bản THPT"""
        selected_rows = self.table_report.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn một người trong bảng báo cáo để xuất phiếu thu!")
            return

        row = selected_rows[0].row()
        req_id = int(self.table_report.item(row, 0).text())
        req_name = self.table_report.item(row, 1).text()
        req_type = self.table_report.item(row, 2).text()
        dept = self.table_report.item(row, 3).text()

        jobs = get_jobs_for_requester(req_id, unpaid_only=False, limit=30)
        if not jobs:
            QMessageBox.information(self, "Thông báo", f"Không tìm thấy lượt in nào của {req_name}.")
            return

        storage_dir = get_setting("storage_dir", "D:\\DeDaIn")
        receipt_dir = os.path.join(storage_dir, "PhieuThu")
        os.makedirs(receipt_dir, exist_ok=True)
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in req_name if c.isalnum() or c in " _-").strip()
        receipt_path = os.path.join(receipt_dir, f"PhieuThu_{safe_name}_{date_str}.pdf")

        try:
            generate_receipt_pdf(
                requester_name=req_name,
                requester_type="teacher" if "giáo viên" in req_type.lower() else "class",
                department_or_grade=dept,
                jobs=jobs,
                output_pdf_path=receipt_path
            )

            reply = QMessageBox.question(
                self, "Xuất phiếu thu thành công",
                f"Đã tạo Phiếu xác nhận thanh toán in ấn cho:\n{req_name}\n\nĐường dẫn: {receipt_path}\n\nBạn có muốn mở xem và in ngay phiếu này không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                os.startfile(receipt_path)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo phiếu thu: {e}")

    def backup_database_now(self):
        """Sao lưu CSDL SQLite 1 chạm an toàn"""
        backup_dir = get_setting("backup_dir", os.path.join(get_setting("storage_dir", "D:\\DeDaIn"), "backups"))
        ok, res = create_database_backup(backup_dir)
        if ok:
            QMessageBox.information(
                self, "Sao lưu thành công",
                f"Đã sao lưu toàn bộ dữ liệu CSDL an toàn tới:\n{res}\n\nFile này lưu toàn bộ danh mục giáo viên, 42 lớp, bảng giá và toàn bộ lịch sử in ấn."
            )
        else:
            QMessageBox.critical(self, "Lỗi sao lưu", f"Không thể sao lưu CSDL:\n{res}")

    def restore_database_dialog(self):
        """Khôi phục CSDL từ file sao lưu .bak"""
        backup_file, _ = QFileDialog.getOpenFileName(
            self, "Chọn file sao lưu CSDL cần khôi phục", "", "File sao lưu SQLite (*.bak *.db);;Tất cả file (*.*)"
        )
        if not backup_file:
            return

        confirm = QMessageBox.question(
            self, "Xác nhận khôi phục",
            f"CẢNH BÁO: Thao tác này sẽ ghi đè dữ liệu hiện tại bằng dữ liệu từ file sao lưu:\n{backup_file}\n\nBạn có chắc chắn muốn khôi phục không?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        ok, msg = restore_database_from_backup(backup_file)
        if ok:
            QMessageBox.information(self, "Khôi phục thành công", msg)
            self.load_initial_data()
            self.load_history_data()
            self.load_report_data()
        else:
            QMessageBox.critical(self, "Lỗi khôi phục", msg)

    # ==================== HISTORY & REPORTS ====================
    def load_history_data(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            kw = self.txt_history_search.text().strip()
            time_filter = self.cb_history_filter.currentText()

            query = """
                SELECT j.id, j.created_at, j.machine_name, r.name, j.related_classes,
                       j.title, j.pages, j.copies, j.sheets, j.amount, j.status, j.paid_status,
                       j.saved_path
                FROM print_jobs j
                LEFT JOIN requesters r ON j.requester_id = r.id
                WHERE 1=1
            """
            params = []
            if time_filter == "Hôm nay":
                query += " AND date(j.created_at) = date('now', 'localtime')"
            elif time_filter == "7 ngày gần nhất":
                query += " AND j.created_at >= date('now', '-7 days', 'localtime')"
            elif time_filter == "Tháng này":
                query += " AND j.created_at >= date('now', 'start of month', 'localtime')"

            if kw:
                query += " AND (j.title LIKE ? OR r.name LIKE ? OR j.printer_name LIKE ?)"
                params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])

            query += " ORDER BY j.id DESC LIMIT 200"
            cur.execute(query, params)
            rows = cur.fetchall()

            self.table_history.setUpdatesEnabled(False)
            self.table_history.clearContents()
            self.table_history.setRowCount(len(rows))
            status_vn = {"printed": "Đã gửi in", "pending": "Chờ", "error": "Lỗi", "cancelled": "Đã hủy"}
            paid_vn = {"unpaid": "Chưa thu", "paid": "Đã thu"}

            for row_idx, r in enumerate(rows):
                self.table_history.setItem(row_idx, 0, QTableWidgetItem(str(r[0])))
                self.table_history.setItem(row_idx, 1, QTableWidgetItem(str(r[1])))
                self.table_history.setItem(row_idx, 2, QTableWidgetItem(str(r[2] or "")))
                self.table_history.setItem(row_idx, 3, QTableWidgetItem(str(r[3] or "Khác")))
                self.table_history.setItem(row_idx, 4, QTableWidgetItem(str(r[4] or "")))
                self.table_history.setItem(row_idx, 5, QTableWidgetItem(str(r[5])))
                self.table_history.setItem(row_idx, 6, QTableWidgetItem(str(r[6])))
                self.table_history.setItem(row_idx, 7, QTableWidgetItem(str(r[7])))
                self.table_history.setItem(row_idx, 8, QTableWidgetItem(str(r[8])))
                self.table_history.setItem(row_idx, 9, QTableWidgetItem(f"{r[9]:,.0f} đ"))
                self.table_history.setItem(row_idx, 10, QTableWidgetItem(status_vn.get(r[10], r[10])))
                self.table_history.setItem(row_idx, 11, QTableWidgetItem(paid_vn.get(r[11], r[11])))
                # Lưu saved_path vào item data
                item_0 = self.table_history.item(row_idx, 0)
                if item_0:
                    item_0.setData(Qt.UserRole, r[12])
            self.table_history.setUpdatesEnabled(True)
        finally:
            conn.close()

    def open_history_file(self):
        selected = self.table_history.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        path = self.table_history.item(row, 0).data(Qt.UserRole)
        if path and os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.warning(self, "Thông báo", f"Không tìm thấy file: {path}")

    def open_history_folder(self):
        selected = self.table_history.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        path = self.table_history.item(row, 0).data(Qt.UserRole)
        if path:
            folder = os.path.dirname(path)
            if os.path.exists(folder):
                os.startfile(folder)
            else:
                QMessageBox.warning(self, "Thông báo", f"Thư mục không tồn tại: {folder}")

    def reprint_history_job(self):
        selected = self.table_history.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        job_id = int(self.table_history.item(row, 0).text())
        reply = QMessageBox.question(self, "In lại", f"Bạn có muốn in lại lượt in #{job_id} không?")
        if reply == QMessageBox.Yes:
            # Load path va in lai
            path = self.table_history.item(row, 0).data(Qt.UserRole)
            if path and os.path.exists(path):
                self.add_files_to_queue([path])
                self.tabs.setCurrentIndex(0)

    def cancel_history_job(self):
        selected = self.table_history.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        job_id = int(self.table_history.item(row, 0).text())
        reply = QMessageBox.question(self, "Hủy lượt in", f"Hủy lượt in #{job_id} (giữ lại bản ghi đối chiếu)?")
        if reply == QMessageBox.Yes:
            update_print_job_status(job_id, "cancelled")
            self.load_history_data()
            self.load_report_data()

    def load_report_data(self):
        # 1. Dashboard summary
        summary = get_dashboard_summary()
        self.lbl_dash_today.setText(
            f"Hôm nay: {summary['today_jobs']} lượt | {summary['today_sheets']:,} tờ | {summary['today_amount']:,.0f} đ"
        )
        self.lbl_dash_debt.setText(
            f"Tổng nợ chưa thu: {summary['unpaid_amount']:,.0f} đ ({summary['unpaid_jobs']} lượt chưa thu)"
        )

        # 2. Table report
        time_range = self.cb_report_time.currentData()
        req_reports = get_report_by_requesters(time_range)

        self.table_report.setUpdatesEnabled(False)
        self.table_report.clearContents()
        self.table_report.setRowCount(len(req_reports))
        type_vn = {"teacher": "Giáo viên", "class": "Lớp", "other": "Khác"}

        for idx, r in enumerate(req_reports):
            self.table_report.setItem(idx, 0, QTableWidgetItem(str(r['id'])))
            self.table_report.setItem(idx, 1, QTableWidgetItem(r['name']))
            self.table_report.setItem(idx, 2, QTableWidgetItem(type_vn.get(r['type'], r['type'])))
            self.table_report.setItem(idx, 3, QTableWidgetItem(r.get('department') or ""))
            self.table_report.setItem(idx, 4, QTableWidgetItem(str(r['job_count'])))
            self.table_report.setItem(idx, 5, QTableWidgetItem(f"{r['total_sheets']:,}"))
            self.table_report.setItem(idx, 6, QTableWidgetItem(f"{r['total_amount']:,.0f} đ"))

            debt_item = QTableWidgetItem(f"{r['debt_amount']:,.0f} đ")
            if r['debt_amount'] > 0:
                debt_item.setForeground(QColor("#dc2626"))
                debt_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_report.setItem(idx, 7, debt_item)
        self.table_report.setUpdatesEnabled(True)

    def mark_selected_requester_paid(self):
        selected = self.table_report.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một người trong bảng!")
            return
        row = selected[0].row()
        req_id = int(self.table_report.item(row, 0).text())
        name = self.table_report.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Xác nhận thu tiền",
            f"Bạn có chắc muốn đánh dấu ĐÃ THU TIỀN cho toàn bộ các lượt in chưa thu của '{name}' không?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            mark_jobs_as_paid(requester_id=req_id)
            QMessageBox.information(self, "Thành công", f"Đã đánh dấu thu tiền thành công cho '{name}'.")
            self.load_report_data()
            self.load_history_data()

    def export_excel_now(self):
        ok, msg = export_full_excel()
        if ok:
            QMessageBox.information(self, "Xuất Excel", msg)
        else:
            QMessageBox.critical(self, "Lỗi xuất Excel", msg)

    # ==================== CLOUD SYNC & SETTINGS ====================
    def browse_cloud_folder(self):
        f = QFileDialog.getExistingDirectory(self, "Chọn thư mục Google Drive / OneDrive đồng bộ 2 máy")
        if f:
            self.txt_cloud_folder.setText(f)

    def save_cloud_folder_setting(self):
        f = self.txt_cloud_folder.text().strip()
        set_cloud_sync_folder(f)
        QMessageBox.information(self, "Thành công", "Đã lưu đường dẫn thư mục đồng bộ đám mây!")

    def execute_cloud_sync(self):
        f = self.txt_cloud_folder.text().strip()
        self.txt_sync_log.append(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Bắt đầu đồng bộ 2 chiều...")
        ok, msg = sync_both_ways(f)
        self.txt_sync_log.append(msg)
        if ok:
            QMessageBox.information(self, "Đồng bộ đám mây", "Đồng bộ 2 chiều thành công!")
            self.load_history_data()
            self.load_report_data()
        else:
            QMessageBox.warning(self, "Đồng bộ", msg)

    def save_general_settings(self):
        set_setting("storage_dir", self.txt_cfg_storage.text().strip())
        set_setting("excel_path", self.txt_cfg_excel.text().strip())
        set_setting("pricing_unit", self.cb_cfg_unit.currentData())
        QMessageBox.information(self, "Thành công", "Đã lưu cài đặt hệ thống!")

    def add_new_teacher(self):
        name = self.txt_new_gv_name.text().strip()
        dept = self.txt_new_gv_dept.text().strip()
        if not name:
            QMessageBox.warning(self, "Thông báo", "Vui lòng nhập họ tên giáo viên!")
            return
        add_requester(name=name, req_type="teacher", department=dept)
        QMessageBox.information(self, "Thành công", f"Đã thêm giáo viên '{name}' vào danh mục!")
        self.txt_new_gv_name.clear()
        self.txt_new_gv_dept.clear()
        self.load_requesters_dropdown()
