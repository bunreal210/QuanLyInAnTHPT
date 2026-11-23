# Hướng dẫn đóng gói ứng dụng sang file `.exe` (PyInstaller)

## 1. Nguyên nhân lỗi `ModuleNotFoundError: No module named 'app.db.connection'`
Lỗi này xảy ra khi đóng gói trực tiếp file `app/main.py`. Khi đó PyInstaller hiểu thư mục `app/` là thư mục gốc, dẫn đến các lệnh `from app.db.connection` bị thiếu tiền tố package `app`.

## 2. Cách khắc phục chuẩn
Hệ thống đã được bổ sung:
- Các file `__init__.py` trong tất cả các thư mục con `app/`, `app/db/`, `app/services/`, `app/ui/`.
- File điểm vào chuẩn [run.py](file:///d:/New%20folder%20(3)/run.py) ở thư mục gốc.
- Script tự động [build_exe.py](file:///d:/New%20folder%20(3)/build_exe.py) và [build_exe.bat](file:///d:/New%20folder%20(3)/build_exe.bat).

## 3. Cách đóng gói cực kỳ đơn giản

### Cách 1 (Khuyên dùng - 1 cú nhấp chuột):
Chỉ cần nhấp đúp vào file **`build_exe.bat`** tại thư mục dự án.

### Cách 2 (Dùng lệnh dòng lệnh):
Mở PowerShell hoặc Command Prompt tại thư mục dự án và chạy:

```bash
python build_exe.py
```

Hoặc chạy trực tiếp PyInstaller:

```bash
pyinstaller --noconfirm --onedir --windowed `
  --name "QuanLyInAnTHPT" `
  --add-data "tools;tools" `
  --add-data "app/db/schema.sql;app/db" `
  run.py
```

## 4. Kết quả sau khi đóng gói
File `.exe` hoàn chỉnh sẽ nằm trong thư mục:
`dist\QuanLyInAnTHPT\QuanLyInAnTHPT.exe`

Bạn có thể copy nguyên thư mục `QuanLyInAnTHPT` này sang bất kỳ máy tính Windows nào khác (kể cả máy 2) để sử dụng mà không cần cài đặt Python!
