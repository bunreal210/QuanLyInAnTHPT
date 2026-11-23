import os
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox,
    QPushButton, QCheckBox, QGroupBox, QTextEdit, QMessageBox, QSpinBox,
    QFileDialog, QFrame, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QColor

from app.services.printer import (
    list_windows_printers, build_sumatra_print_settings,
    execute_sumatra_print, create_sample_test_pdf
)
from app.db.models import (
    get_setting, save_or_update_printer, get_printer_by_windows_name
)

class PrintWorker(QThread):
    finished_signal = Signal(dict)

    def __init__(self, sumatra_exe, printer_name, pdf_path, settings_str):
        super().__init__()
        self.sumatra_exe = sumatra_exe
        self.printer_name = printer_name
        self.pdf_path = pdf_path
        self.settings_str = settings_str

    def run(self):
        result = execute_sumatra_print(
            self.sumatra_exe, self.printer_name, self.pdf_path, self.settings_str
        )
        self.finished_signal.emit(result)


class PrinterTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Công cụ kiểm tra máy in & Xác nhận cấu hình in - Giai đoạn 1")
        self.resize(850, 680)
        self.test_pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools", "sample_test.pdf")
        self.init_ui()
        self.load_printers()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 1. Header Banner
        header = QLabel("KIỂM TRA TƯƠNG THÍCH MÁY IN TRƯỜNG HỌC (RICOH / KONICA MINOLTA / CANON)")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header.setFont(header_font)
        header.setStyleSheet("color: #1a56db; margin-bottom: 5px;")
        main_layout.addWidget(header)

        sub_desc = QLabel(
            "Màn hình này dùng để in thử 1 tờ giấy (2 mặt, có màu/đen trắng) trên từng máy in thật của trường, "
            "nhằm xác nhận driver có nhận đúng lệnh in 2 mặt và màu qua ứng dụng hay không."
        )
        sub_desc.setWordWrap(True)
        sub_desc.setStyleSheet("color: #4b5563; font-size: 11pt;")
        main_layout.addWidget(sub_desc)

        # 2. Khung Chọn máy in & Cấu hình máy
        printer_box = QGroupBox("1. Danh sách máy in đã cài đặt trên Windows")
        printer_layout = QGridLayout(printer_box)

        printer_layout.addWidget(QLabel("Chọn máy in:"), 0, 0)
        self.cb_printers = QComboBox()
        self.cb_printers.currentIndexChanged.connect(self.on_printer_selected)
        printer_layout.addWidget(self.cb_printers, 0, 1, 1, 2)

        self.btn_refresh_printers = QPushButton("Làm mới danh sách")
        self.btn_refresh_printers.clicked.connect(self.load_printers)
        printer_layout.addWidget(self.btn_refresh_printers, 0, 3)

        printer_layout.addWidget(QLabel("Tên gợi nhớ thân thiện:"), 1, 0)
        self.txt_display_name = QTextEdit()
        self.txt_display_name.setMaximumHeight(32)
        printer_layout.addWidget(self.txt_display_name, 1, 1, 1, 2)

        self.btn_save_printer_info = QPushButton("Lưu cấu hình máy này vào CSDL")
        self.btn_save_printer_info.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px;")
        self.btn_save_printer_info.clicked.connect(self.save_printer_capabilities)
        printer_layout.addWidget(self.btn_save_printer_info, 1, 3)

        # Checkboxes tính năng phần cứng máy in
        hw_layout = QHBoxLayout()
        self.chk_hw_duplex = QCheckBox("Máy này hỗ trợ in 2 mặt tự động (Duplex)")
        self.chk_hw_duplex.setChecked(True)
        self.chk_hw_color = QCheckBox("Máy này hỗ trợ in màu (Color)")
        self.chk_hw_a3 = QCheckBox("Hỗ trợ khổ A3")
        self.chk_hw_a3.setChecked(True)
        hw_layout.addWidget(self.chk_hw_duplex)
        hw_layout.addWidget(self.chk_hw_color)
        hw_layout.addWidget(self.chk_hw_a3)
        hw_layout.addStretch()
        printer_layout.addLayout(hw_layout, 2, 1, 1, 3)

        main_layout.addWidget(printer_box)

        # 3. Khung Thiết lập lệnh in thử
        test_box = QGroupBox("2. Thiết lập thông số in thử (Lệnh sẽ gửi qua SumatraPDF)")
        test_layout = QGridLayout(test_box)

        # Khổ giấy
        test_layout.addWidget(QLabel("Khổ giấy:"), 0, 0)
        self.cb_test_paper = QComboBox()
        self.cb_test_paper.addItems(["A4", "A3"])
        test_layout.addWidget(self.cb_test_paper, 0, 1)

        # Chế độ mặt in
        test_layout.addWidget(QLabel("Số mặt in:"), 0, 2)
        self.cb_test_duplex = QComboBox()
        self.cb_test_duplex.addItem("2 mặt - Lật cạnh dài (Duplex Long - Đề chuẩn)", 1)
        self.cb_test_duplex.addItem("2 mặt - Lật cạnh ngắn (Duplex Short - Giấy thi ngang)", 2)
        self.cb_test_duplex.addItem("1 mặt (Simplex)", 0)
        test_layout.addWidget(self.cb_test_duplex, 0, 3)

        # Chế độ màu
        test_layout.addWidget(QLabel("Màu sắc:"), 1, 0)
        self.cb_test_color = QComboBox()
        self.cb_test_color.addItem("Đen trắng (Monochrome)", 0)
        self.cb_test_color.addItem("In màu (Color)", 1)
        test_layout.addWidget(self.cb_test_color, 1, 1)

        # Số bản
        test_layout.addWidget(QLabel("Số bản in:"), 1, 2)
        self.sp_copies = QSpinBox()
        self.sp_copies.setRange(1, 5)
        self.sp_copies.setValue(1)
        test_layout.addWidget(self.sp_copies, 1, 3)

        main_layout.addWidget(test_box)

        # 4. Hàng nút hành động
        action_layout = QHBoxLayout()
        self.btn_preview_pdf = QPushButton("1. Xem / Mở file PDF in thử (2 trang)")
        self.btn_preview_pdf.setFixedHeight(38)
        self.btn_preview_pdf.clicked.connect(self.preview_sample_pdf)
        action_layout.addWidget(self.btn_preview_pdf)

        self.btn_send_print = QPushButton("2. GỬI LỆNH IN THỬ TỚI MÁY ĐÃ CHỌN")
        self.btn_send_print.setFixedHeight(38)
        self.btn_send_print.setStyleSheet("background-color: #059669; color: white; font-weight: bold; font-size: 11pt;")
        self.btn_send_print.clicked.connect(self.send_test_print)
        action_layout.addWidget(self.btn_send_print)

        main_layout.addLayout(action_layout)

        # 5. Khung Log chi tiết
        log_box = QGroupBox("3. Nhật ký lệnh in và kết quả phản hồi từ hệ thống")
        log_layout = QVBoxLayout(log_box)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; font-size: 10pt;")
        log_layout.addWidget(self.txt_log)

        main_layout.addWidget(log_box)

        # Tự động tạo sample test pdf nếu chưa có
        self.ensure_sample_pdf()

    def log(self, message: str):
        self.txt_log.append(message)

    def ensure_sample_pdf(self):
        if not os.path.exists(self.test_pdf_path):
            try:
                create_sample_test_pdf(self.test_pdf_path, "KIỂM TRA CẤU HÌNH IN")
                self.log(f"[HỆ THỐNG] Đã tạo file PDF in thử tiêu chuẩn tại: {self.test_pdf_path}")
            except Exception as e:
                self.log(f"[LỖI] Không thể tạo file PDF in thử: {e}")

    def load_printers(self):
        self.cb_printers.clear()
        printers = list_windows_printers()
        if not printers:
            self.log("[CẢNH BÁO] Không tìm thấy máy in nào trên hệ điều hành Windows!")
            return

        self.log(f"[HỆ THỐNG] Tìm thấy {len(printers)} máy in trên Windows.")
        default_index = 0
        for idx, p in enumerate(printers):
            win_name = p['windows_name']
            self.cb_printers.addItem(win_name, p)
            if p.get('is_default'):
                default_index = idx

        self.cb_printers.setCurrentIndex(default_index)
        self.on_printer_selected(default_index)

    def on_printer_selected(self, index):
        if index < 0 or index >= self.cb_printers.count():
            return
        printer_data = self.cb_printers.itemData(index)
        if not printer_data:
            return

        win_name = printer_data['windows_name']
        self.txt_display_name.setPlainText(win_name)

        # Kiểm tra xem máy này đã được lưu trong DB chưa
        saved = get_printer_by_windows_name(win_name)
        if saved:
            self.txt_display_name.setPlainText(saved['display_name'])
            self.chk_hw_color.setChecked(bool(saved['color_supported']))
            self.chk_hw_duplex.setChecked(bool(saved['duplex_supported']))
            papers = saved.get('papers', 'A4,A3')
            self.chk_hw_a3.setChecked('A3' in papers)
            self.log(f"[DB] Đã tải cấu hình lưu trước đó cho máy: {saved['display_name']}")
        else:
            # Gợi ý tự động dựa trên tên máy in
            is_color = ("color" in win_name.lower()) or ("c554" in win_name.lower()) or ("ix6700" in win_name.lower())
            self.chk_hw_color.setChecked(is_color)
            is_duplex = not ("ix6700" in win_name.lower()) # Canon ix6700 thuong la may in phun 1 mat thu cong
            self.chk_hw_duplex.setChecked(is_duplex)
            self.log(f"[MÁY IN] Đã chọn: {win_name}")

    def save_printer_capabilities(self):
        win_name = self.cb_printers.currentText()
        if not win_name:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn máy in trước.")
            return

        display_name = self.txt_display_name.toPlainText().strip() or win_name
        color = 1 if self.chk_hw_color.isChecked() else 0
        duplex = 1 if self.chk_hw_duplex.isChecked() else 0
        papers = "A4,A3" if self.chk_hw_a3.isChecked() else "A4"

        try:
            save_or_update_printer(
                windows_name=win_name,
                display_name=display_name,
                color_supported=color,
                duplex_supported=duplex,
                papers=papers,
                note="Đã xác nhận trong màn hình kiểm tra"
            )
            self.log(f"[LƯU THÀNH CÔNG] Đã lưu thông số máy in: '{display_name}' (Màu: {color}, 2 mặt: {duplex}, Khổ: {papers})")
            QMessageBox.information(self, "Thành công", f"Đã lưu cấu hình máy in '{display_name}' vào cơ sở dữ liệu.")
        except Exception as e:
            self.log(f"[LỖI] Không thể lưu cấu hình máy in: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {e}")

    def preview_sample_pdf(self):
        self.ensure_sample_pdf()
        if os.path.exists(self.test_pdf_path):
            try:
                os.startfile(self.test_pdf_path)
                self.log(f"[XEM TRƯỚC] Đã mở file PDF kiểm tra: {self.test_pdf_path}")
            except Exception as e:
                self.log(f"[LỖI] Không thể mở file PDF: {e}")
        else:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file mẫu PDF kiểm tra.")

    def send_test_print(self):
        win_name = self.cb_printers.currentText()
        if not win_name:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn máy in cần test.")
            return

        self.ensure_sample_pdf()
        from app.services.printer import find_or_extract_sumatra
        sumatra_exe = find_or_extract_sumatra(get_setting("sumatra_path"))

        paper = self.cb_test_paper.currentText()
        duplex = self.cb_test_duplex.currentData()
        color = self.cb_test_color.currentData()
        copies = self.sp_copies.value()

        settings_str = build_sumatra_print_settings(
            copies=copies,
            duplex=duplex,
            color=color,
            paper=paper,
            collate=True
        )

        duplex_label = self.cb_test_duplex.currentText()
        color_label = self.cb_test_color.currentText()

        self.log("\n------------------------------------------------------------")
        self.log(f"[BẮT ĐẦU IN THỬ] Máy in: {win_name}")
        self.log(f"[THÔNG SỐ] Khổ: {paper} | Chế độ mặt: {duplex_label} | Màu: {color_label} | Số bản: {copies}")
        self.log(f"[CÂU LỆNH SUMATRA] -print-settings \"{settings_str}\"")
        self.btn_send_print.setEnabled(False)
        self.btn_send_print.setText("Đang gửi lệnh in...")

        # Chạy trong luồng phụ để không đơ UI
        self.worker = PrintWorker(sumatra_exe, win_name, self.test_pdf_path, settings_str)
        self.worker.finished_signal.connect(self.on_print_finished)
        self.worker.start()

    def on_print_finished(self, result: dict):
        self.btn_send_print.setEnabled(True)
        self.btn_send_print.setText("2. GỬI LỆNH IN THỬ TỚI MÁY ĐÃ CHỌN")

        if result.get("success"):
            self.log(f"[KẾT QUẢ] THÀNH CÔNG! {result.get('message')}")
            self.log("[HƯỚNG DẪN KIỂM TRA GIẤY]:")
            self.log(" -> Vui lòng đến máy in lấy tờ giấy ra xem:")
            self.log("    1. Trang 2 có nằm ở mặt sau không (in 2 mặt)?")
            self.log("    2. Dải màu có ra đúng màu (nếu chọn Màu) hay thành sắc xám (nếu chọn Đen trắng)?")
            self.log(" -> Nếu giấy in đúng như mong muốn, hãy bấm nút 'Lưu cấu hình máy này vào CSDL' phía trên.")
            QMessageBox.information(
                self, "Lệnh in đã gửi",
                "Đã gửi lệnh in thử thành công tới máy in!\n\n"
                "Vui lòng kiểm tra tờ giấy in ra thực tế để xác nhận:\n"
                "- Chế độ 2 mặt có lật đúng chiều không\n"
                "- Chế độ màu / đen trắng có chuẩn không."
            )
        else:
            self.log(f"[KẾT QUẢ] THẤT BẠI! Lỗi: {result.get('error')}")
            QMessageBox.critical(self, "Lỗi in ấn", f"Không thể gửi lệnh in:\n{result.get('error')}")
