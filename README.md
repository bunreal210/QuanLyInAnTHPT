# 🖨️ PHẦN MỀM QUẢN LÝ IN ẤN ĐỀ THI & TÀI LIỆU (THPT)

> **Giải pháp tối ưu hóa quy trình in ấn tại trường học:** Chỉ với 1 thao tác kéo thả file và bấm in, hệ thống tự động lưu bản sao khoa học, tính tiền, ghi nhật ký và đồng bộ vào file Excel tổng hợp phục vụ đối soát, thu tiền cuối kỳ.

[![GitHub release](https://img.shields.io/github/v/release/bunreal210/QuanLyInAnTHPT?color=blue&label=B%E1%BA%A3n%20ph%C3%A1t%20h%C3%A0nh)](https://github.com/bunreal210/QuanLyInAnTHPT/releases/tag/v1.0.0)
[![Platform](https://img.shields.io/badge/N%E1%BB%81n%20t%E1%BA%A3ng-Windows%2010%20%2F%2011-0078D6?logo=windows)](https://github.com/bunreal210/QuanLyInAnTHPT)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://python.org)

---

## 🎯 Bối cảnh & Mục tiêu

Tại các trường THPT, giáo viên kiêm phụ trách in ấn mỗi ngày nhận hàng chục đến hàng trăm file đề thi, tài liệu từ đồng nghiệp và học sinh gửi qua Zalo hoặc USB. Việc ghi sổ tay hoặc nhập thủ công vào Google Sheets cuối ngày rất dễ gây nhầm lẫn, mất file hoặc thất thoát chi phí in ấn.

**Ứng dụng ra đời để giải quyết bài toán trên theo quy trình 1 chạm:**
1. **Kéo thả file** vào ứng dụng $\rightarrow$ Tự động chuyển đổi sang PDF và đếm số trang chuẩn xác.
2. **Chọn người in** (gõ tên tìm kiếm không dấu hoặc chọn lớp) $\rightarrow$ Tự động gợi ý số bản in bằng đúng **sĩ số học sinh** của lớp.
3. **Cấu hình in:** Khổ giấy (A4, A3), số bản, 1 mặt, 2 mặt hoặc **in Booklet (sách gập đôi)**, màu hoặc đen trắng.
4. **Bấm IN:** Ứng dụng đồng thời:
   - 🖨️ Gửi lệnh in ngầm tới máy in (hỗ trợ driver RICOH, Konica Minolta, Canon...).
   - 📁 Lưu trữ bản sao file gốc và PDF vào thư mục tổ chức theo tên giáo viên/lớp và ngày in.
   - 📝 Ghi sổ nhật ký vào CSDL SQLite và cập nhật file Excel tổng hợp có công thức `SUMIFS`.
   - 💰 Cuối kỳ mở báo cáo là có ngay bảng công nợ từng giáo viên và 42 lớp để thu tiền.

---

## 🚀 Tải về và Dùng ngay (Không cần cài đặt)

Người dùng không rành công nghệ chỉ cần tải bản chạy sẵn:

👉 **[Tải file chạy ứng dụng tại mục GitHub Releases (v1.0.0)](https://github.com/bunreal210/QuanLyInAnTHPT/releases/tag/v1.0.0)**

- **`QuanLyInAnTHPT_SingleFile.exe`**: Đúng 1 file duy nhất, tải về nhấp đúp là chạy ngay lập tức.
- **`QuanLyInAnTHPT_v1.0.0_Windows_Portable.zip`**: Bản nén Portable trọn gói, giải nén ra nhấp đúp file chạy để mở siêu tốc dưới 1 giây.

---

## ✨ Các chức năng chính

### 1. 🖨️ Hàng đợi in ấn & Kéo thả đa file
- Kéo thả nhiều file cùng lúc: Word (`.docx`, `.doc`), Excel (`.xlsx`, `.xls`), PowerPoint (`.pptx`, `.ppt`), PDF, Ảnh (`.jpg`, `.png`, `.bmp`...).
- Khung xem trước trực quan từng trang trước khi in.
- Tìm kiếm người yêu cầu thông minh không dấu (*ví dụ gõ `lan` sẽ tìm thấy `Nguyễn Thị Lan`*).
- Ghi nhớ 3 người in gần nhất để chọn nhanh bằng 1 click.
- Tự động tính số tờ thực tế và thành tiền; hỗ trợ sửa tay hoặc tích chọn *"Miễn phí (Việc chung trường)"*.
- Nút **"Lưu không in (Ghi sổ thủ công)"** khi bản in đã thực hiện bằng cách khác.

### 2. 📖 Hai chế độ in linh hoạt & In Booklet (Sách gập đôi)
- **Chế độ 1 - In nhanh tự động (`🖨️ IN NHANH TỰ ĐỘNG`):** In ngầm 1 chạm không cần mở cửa sổ phụ, tự động áp dụng cấu hình phần mềm (số bản, 2 mặt, màu/đen trắng, khổ giấy) và trừ tiền vào sổ Excel tức thì.
- **Chế độ 2 - Mở cửa sổ in Windows (`🖥️ MỞ CỬA SỔ IN WINDOWS`):** Mở trực tiếp hộp thoại in gốc quen thuộc của Windows / Microsoft Word / Excel. Người dùng có thể bấm vào *Properties/Preferences* để vào thẳng driver máy in (Ricoh, Canon, HP...) chọn khay giấy, giấy dày, tùy chọn máy in nâng cao như bình thường.
- **Chức năng In Booklet chuẩn:** Tự bù trang trắng để chia hết cho 4, tự ghép trang theo thuật toán Saddle-Stitch Imposition (ghép 2 trang A4 lên 1 mặt A3 hoặc 2 trang A5 lên 1 mặt A4). Lệnh in gửi ra ở chế độ **2 mặt lật cạnh ngắn (Duplex Short)**, in xong chỉ cần gập đôi tờ giấy ở giữa là thành tập sách/đề thi chuẩn đẹp.
- Tự động tính toán số tờ: 1 tờ giấy in được 4 trang tài liệu.

### 3. 🏫 Quản lý 42 Lớp & Tự động điền Sĩ số
- **Nhập từ file Excel:** Nút nhập danh sách lớp từ file `.xlsx` tự động nhận diện *Khối, Tên lớp, Sĩ số, Ghi chú*.
- **Tải file mẫu Excel:** Có nút xuất file `Mau_Danh_Sach_Lop.xlsx` chuẩn.
- **Tính năng thông minh:** Khi chọn người in là một Lớp (ví dụ *10A1 có 45 học sinh*), phần mềm **tự động điền số bản in = 45 bản**.

### 4. 👨‍🏫 Quản lý Danh mục 83 Giáo viên
- Nhập nhanh toàn bộ danh sách giáo viên của trường từ file Excel.
- Phân loại theo tổ chuyên môn, hỗ trợ thêm/sửa/ẩn nhanh.

### 5. 💲 Cấu hình Bảng giá tiền in ấn
- Màn hình cấu hình bảng giá trực quan: Đơn giá theo Khổ giấy (A4, A3), Mặt in (1 mặt, 2 mặt), Màu sắc, Máy in áp dụng.
- Nhấp chọn dòng để sửa đơn giá trực tiếp; có nút khôi phục bảng giá chuẩn.
- Tùy chọn cách tính tiền linh hoạt: Theo *"Tờ giấy thực tế (sheet)"* hoặc theo *"Mặt in (page)"*.

### 6. 📁 Lưu trữ bản sao khoa học (Mục 5.4)
Tự động lưu trữ theo cấu trúc:
```
D:\DeDaIn\
  ├── GiaoVien\
  │   └── Nguyen Thi Lan\
  │       └── 2026-11-23\
  │           ├── 0815_De kiem tra Sinh 10_45ban.docx
  │           └── 0815_De kiem tra Sinh 10_45ban.pdf
  └── Lop\
      └── 10A2\
          └── 2026-11-23\
              └── 0930_Phieu hoc tap_44ban.pdf
```
- Tự động chuẩn hóa tên file bỏ ký tự cấm, chống trùng lặp, chống lỗi đường dẫn quá 260 ký tự.

### 7. 📊 Báo cáo, Thu tiền, Xuất Phiếu thu & Cập nhật Excel
- Dashboard thống kê nhanh hôm nay (số lượt, số tờ, tổng tiền) và tổng nợ chưa thu.
- Bảng công nợ theo từng giáo viên và 42 lớp; nút **"Đánh dấu đã thu tiền cho người này"**.
- **🧾 Xuất / In Phiếu thu tiền in ấn chuẩn THPT:** Tự động tạo file PDF Phiếu thu có quốc hiệu tiêu ngữ, chi tiết số tờ, thành tiền, số tiền viết bằng chữ tiếng Việt và khung ký tên 3 bên (Người nộp, Người lập, Thủ quỹ/Phụ trách in).
- Tự động tạo và cập nhật file Excel `TongHopInAn.xlsx` gồm 3 sheet có công thức `SUMIFS` đối chiếu.
- Cơ chế chống khóa file: Nếu file Excel đang mở, phần mềm tự đưa vào hàng đợi đồng bộ khi đóng file.

### 8. ⚡ Tối ưu hiệu năng, In hàng loạt & Xem trước nâng cao
- **🚀 In toàn bộ hàng đợi (Batch Print):** Nút in tự động liên tiếp tất cả file trong hàng đợi, tự động lưu trữ, tính tiền và đồng bộ Excel với thanh tiến trình % và âm thanh thông báo khi hoàn thành.
- **⚡ Bộ đệm hình ảnh xem trước (Preview Cache):** Lưu trữ trang trong RAM giúp chuyển trang tức thì (0ms), không độ trễ.
- **🔍 Phóng to / Thu nhỏ & Xem lớn (Fullscreen Preview):** Dễ dàng phóng to kiểm tra công thức toán, hình vẽ, sơ đồ trước khi gửi in.
- **💾 Sao lưu & Khôi phục CSDL 1 chạm:** Sao lưu toàn bộ dữ liệu ra file `.bak` an toàn hoặc khôi phục khi chuyển máy.

### 9. ☁️ Đồng bộ 2 máy tính ở xa (Không cần mạng LAN)
- Thầy/cô có thể dùng 1 máy ở trường và 1 máy ở nhà.
- Chỉ cần trỏ chung vào một thư mục trên **Google Drive** hoặc **OneDrive**, bấm nút **"Đồng bộ 2 chiều ngay"** là toàn bộ nhật ký in ấn giữa 2 máy sẽ tự động gộp lại mà không sợ xung đột file.

---

## 💻 Dành cho Lập trình viên & Chạy từ mã nguồn

### Yêu cầu môi trường
- Hệ điều hành: Windows 10 / 11
- Python: 3.11 trở lên

### Cài đặt & Khởi động
```bash
# 1. Clone repository
git clone https://github.com/bunreal210/QuanLyInAnTHPT.git
cd QuanLyInAnTHPT

# 2. Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# 3. Khởi chạy ứng dụng
python run.py
```

### Chạy kiểm thử tự động
```bash
python tests/test_full_workflow.py
```

---

## 📂 Cấu trúc thư mục dự án

```
QuanLyInAnTHPT/
  ├── app/
  │   ├── main.py              # Điểm vào ứng dụng
  │   ├── db/                  # Kết nối SQLite WAL, models & schema.sql
  │   ├── services/
  │   │   ├── booklet.py       # Thuật toán dàn trang in Booklet
  │   │   ├── converter.py     # Chuyển Word, Excel, PPT, Ảnh sang PDF
  │   │   ├── printer.py       # Quét máy in, gửi lệnh in ngầm SumatraPDF
  │   │   ├── pricing.py       # Logic tính số tờ và thành tiền
  │   │   ├── storage.py       # Quản lý lưu trữ bản sao thư mục
  │   │   ├── excel_sync.py    # Ghi và cập nhật file Excel tổng hợp
  │   │   ├── cloud_sync.py    # Đồng bộ 2 máy qua Google Drive/OneDrive
  │   │   └── reports.py       # Báo cáo thống kê và thu nợ
  │   └── ui/
  │       ├── main_window.py   # Toàn bộ giao diện chính PySide6
  │       └── test_printer_window.py # Màn hình in thử nghiệm
  ├── data/                    # Nơi lưu database cục bộ SQLite
  ├── tools/                   # Chứa SumatraPDF.exe portable
  ├── tests/                   # Bộ kiểm thử tự động
  ├── run.py                   # Script khởi động chuẩn
  ├── requirements.txt         # Danh sách thư viện Python
  └── README.md                # Tài liệu hướng dẫn sử dụng
```

---

## 📝 Giấy phép
Phần mềm phát triển phục vụ công tác in ấn trong ngành giáo dục. Mọi cá nhân, nhà trường đều có thể sử dụng và đóng góp phát triển miễn phí!
