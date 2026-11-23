import os
import sys
import subprocess
import shutil
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
RELEASE_DIR = os.path.join(BASE_DIR, "release")

def ensure_tools():
    """Dam bao SumatraPDF co san trong tools/"""
    sumatra_path = os.path.join(BASE_DIR, "tools", "SumatraPDF.exe")
    if not os.path.exists(sumatra_path):
        print("Tools/SumatraPDF.exe chua co. Dang tu dong tai...")
        import scripts.download_sumatra as dl
        dl.ensure_sumatra()

def build():
    print("=== TIẾN HÀNH ĐÓNG GÓI PHẦN MỀM QUẢN LÝ IN THPT (WINDOWS) ===")
    ensure_tools()

    # 1. Cài đặt PyInstaller nếu thiếu
    try:
        import PyInstaller
    except ImportError:
        print("Cài đặt PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Dọn dẹp thư mục dist và build cũ
    for d in [DIST_DIR, BUILD_DIR, RELEASE_DIR]:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
            except Exception as e:
                print(f"Cảnh báo dọn dẹp {d}: {e}")
    os.makedirs(RELEASE_DIR, exist_ok=True)

    # 3. Đóng gói bản Portable (Folder onedir) - Mở nhanh, siêu ổn định
    print("\n[1/3] Đang đóng gói bản Portable Onedir...")
    cmd_onedir = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "QuanLyInAnTHPT",
        "--add-data", f"{os.path.join(BASE_DIR, 'tools')};tools",
        "--add-data", f"{os.path.join(BASE_DIR, 'app', 'db', 'schema.sql')};app/db",
        os.path.join(BASE_DIR, "run.py")
    ]
    res_onedir = subprocess.run(cmd_onedir)
    if res_onedir.returncode != 0:
        print(f"Lỗi đóng gói Onedir: {res_onedir.returncode}")
        return False

    app_folder = os.path.join(DIST_DIR, "QuanLyInAnTHPT")

    # 4. Tạo file Zip Portable đặt vào thư mục release/
    print("\n[2/3] Đang nén file Zip Release để chia sẻ sang máy khác...")
    zip_release_path = os.path.join(RELEASE_DIR, "QuanLyInAnTHPT_v1.0.0_Windows_Portable.zip")
    with zipfile.ZipFile(zip_release_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(app_folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, DIST_DIR)
                zipf.write(full_path, rel_path)
    print(f" -> Đã tạo file Zip Release: {zip_release_path} ({os.path.getsize(zip_release_path) / (1024*1024):.1f} MB)")

    # 5. Đóng gói bản 1 File Exe duy nhất (--onefile)
    print("\n[3/3] Đang đóng gói bản 1 File Exe độc lập (Standalone Single File)...")
    cmd_onefile = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "QuanLyInAnTHPT_SingleFile",
        "--distpath", RELEASE_DIR,
        "--add-data", f"{os.path.join(BASE_DIR, 'tools')};tools",
        "--add-data", f"{os.path.join(BASE_DIR, 'app', 'db', 'schema.sql')};app/db",
        os.path.join(BASE_DIR, "run.py")
    ]
    res_onefile = subprocess.run(cmd_onefile)
    
    single_exe_path = os.path.join(RELEASE_DIR, "QuanLyInAnTHPT_SingleFile.exe")

    print("\n" + "="*70)
    print("🎉 ĐÓNG GÓI HOÀN TẤT THÀNH CÔNG!")
    print(f"📁 Thư mục Release: {RELEASE_DIR}")
    if os.path.exists(single_exe_path):
        print(f" 1. File EXE độc lập duy nhất (OneFile): {single_exe_path}")
    print(f" 2. File ZIP trọn gói (Portable, mở tức thì): {zip_release_path}")
    print("="*70)
    return True

if __name__ == "__main__":
    build()
