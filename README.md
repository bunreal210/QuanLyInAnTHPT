# PHẦN MỀM QUẢN LÝ IN ẤN ĐỀ THI & TÀI LIỆU (THPT)

Phần mềm chuyên dụng cho trường học giúp đơn giản hóa quy trình in ấn: Kéo thả file -> Tự động chuyển đổi & đếm trang -> Chọn người in -> Gửi lệnh in -> Lưu trữ thư mục tự động -> Ghi sổ nhật ký & xuất Excel.

---

## 🚀 1. Cách khởi động phần mềm

Mở terminal hoặc Command Prompt tại thư mục dự án và chạy:

```bash
python run.py
```

---

## 🌟 2. Các chức năng mới cập nhật

### 💲 Cấu hình Bảng giá tiền in
- **Giao diện trực quan tại Tab "💲 Cấu hình Bảng giá":**
  - Hiển thị đầy đủ bảng đơn giá theo từng tổ hợp: Khổ giấy (A4, A3), Chế độ mặt (1 mặt, 2 mặt), Màu sắc (Đen trắng, Màu), Máy in áp dụng.
  - **Sửa đơn giá dễ dàng:** Chọn dòng cần sửa trong bảng, nhập đơn giá mới và bấm **"Cập nhật đơn giá này"**.
  - **Thêm quy tắc giá mới:** Thêm giá riêng cho từng máy in hoặc khổ giấy đặc biệt.
  - **Nút "Khôi phục bảng giá chuẩn":** Trở về bảng giá mặc định ban đầu bất cứ lúc nào.
  - **Lựa chọn cách tính tiền:** Chọn tính theo *"Tờ giấy thực tế (sheet)"* hoặc theo *"Mặt in (page)"*.

### 📥 Nhập Danh sách Lớp bằng file Excel (kèm Sĩ số lớp)
- **Quản lý sĩ số lớp tại Tab "⚙️ Cài đặt & Danh mục":**
  - Nút **"📥 NHẬP DANH SÁCH LỚP TỪ FILE EXCEL (.xlsx)"**: Tự động nhận diện các cột *Khối, Lớp, Sĩ số học sinh, Ghi chú*.
  - Nút **"📄 Tải file Excel mẫu danh sách Lớp"**: Xuất file `Mau_Danh_Sach_Lop.xlsx` chuẩn để thầy/cô điền sĩ số và nhập vào.
  - Bảng danh sách 42 lớp hiển thị rõ sĩ số từng lớp. Cho phép bấm vào lớp và sửa nhanh sĩ số.
- **TÍNH NĂNG THÔNG MINH:** Khi in đề tại Tab 1, nếu thầy/cô chọn người in là một Lớp (ví dụ: *10A1 có 45 học sinh*), phần mềm sẽ **TỰ ĐỘNG ĐIỀN SỐ BẢN IN = SĨ SỐ LỚP (45 bản)**!

### 📥 Nhập Danh sách Giáo viên bằng file Excel
- **Quản lý giáo viên tại Tab "⚙️ Cài đặt & Danh mục":**
  - Nút **"📥 NHẬP DANH SÁCH GIÁO VIÊN TỪ FILE EXCEL (.xlsx)"**: Nhập nhanh toàn bộ danh sách 83 giáo viên của trường từ file Excel (tự nhận diện cột *Họ tên, Tổ chuyên môn, Ghi chú*).
  - Nút **"📄 Tải file Excel mẫu danh sách Giáo viên"**: Xuất file `Mau_Danh_Sach_Giao_Vien.xlsx` chuẩn.
  - Tìm kiếm giáo viên không dấu mượt mà ngay tại ô chọn in.

---

## 📖 3. Các tính năng cốt lõi khác
- **In Booklet (Sách gập đôi ghim giữa):** Tự động dàn trang PDF, chèn trang trắng bội số của 4, in 2 mặt lật cạnh ngắn.
- **Đồng bộ 2 máy ở xa (Không cùng mạng LAN):** Đồng bộ 2 chiều qua thư mục chia sẻ Google Drive / OneDrive.
- **Lưu trữ thư mục tự động theo chuẩn:** `DeDaIn/GiaoVien/.../YYYY-MM-DD/...`
- **Tự động xuất và đồng bộ file Excel:** `TongHopInAn.xlsx` gồm 3 sheet có công thức `SUMIFS`.

---

## 📦 4. Đóng gói file `.exe` cho Windows
Nhấp đúp vào file [build_exe.bat](file:///d:/New%20folder%20(3)/build_exe.bat) hoặc chạy:

```bash
python build_exe.py
```
File `.exe` sẽ được tạo tại `dist\QuanLyInAnTHPT\QuanLyInAnTHPT.exe`.
