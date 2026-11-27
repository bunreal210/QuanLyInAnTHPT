import os
import sys
import shutil
import zipfile
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

def build():
    print("=" * 60)
    print("BAT DAU DONG GOI UNG DUNG: QUAN LY IN AN")
    print("Tac gia: Pham Cong Vinh")
    print("Chuc vu: Bi thu chi doan 11A5, Chu tich CLB Nghien cuu Khoa hoc, STEM va Robotics")
    print("Don vi: Truong THPT Bac Dong Quan")
    print("=" * 60)

    icon_path = os.path.join(BASE_DIR, "app", "resources", "icon.ico")
    version_file = os.path.join(BASE_DIR, "version_info.txt")
    schema_file = os.path.join(BASE_DIR, "app", "db", "schema.sql")
    tools_dir = os.path.join(BASE_DIR, "tools")
    resources_dir = os.path.join(BASE_DIR, "app", "resources")
    release_dir = os.path.join(BASE_DIR, "release")
    os.makedirs(release_dir, exist_ok=True)

    # 1. Dong goi ban SingleFile (.exe 1 file duy nhat co nhung Icon va Version info)
    print("\n[1/3] Dang build ban Single File: QuanLyInAn_SingleFile.exe...")
    cmd_single = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onefile",
        f"--name=QuanLyInAn_SingleFile",
        f"--icon={icon_path}",
        f"--version-file={version_file}",
        f"--add-data={schema_file};app/db",
        f"--add-data={resources_dir};app/resources",
        f"--add-data={tools_dir};tools",
        "--hidden-import=fitz",
        "--hidden-import=pymupdf",
        "--hidden-import=win32com.client",
        "--hidden-import=openpyxl",
        "--hidden-import=PIL",
        os.path.join(BASE_DIR, "run.py")
    ]
    res1 = subprocess.run(cmd_single)
    if res1.returncode != 0:
        print("[LOI] Build Single File that bai!")
        return False

    built_single = os.path.join(BASE_DIR, "dist", "QuanLyInAn_SingleFile.exe")
    target_single = os.path.join(release_dir, "QuanLyInAn_SingleFile.exe")
    if os.path.exists(built_single):
        shutil.copy2(built_single, target_single)
        print(f"[THANH CONG] Da tao file: {target_single}")

    # 2. Dong goi ban Portable Folder (Sieu toc duoi 1s, khong lo bao dong gia AV)
    print("\n[2/3] Dang build ban Portable Folder: QuanLyInAn_Portable...")
    cmd_dir = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--onedir",
        f"--name=QuanLyInAn",
        f"--icon={icon_path}",
        f"--version-file={version_file}",
        f"--add-data={schema_file};app/db",
        f"--add-data={resources_dir};app/resources",
        f"--add-data={tools_dir};tools",
        "--hidden-import=fitz",
        "--hidden-import=pymupdf",
        "--hidden-import=win32com.client",
        "--hidden-import=openpyxl",
        "--hidden-import=PIL",
        os.path.join(BASE_DIR, "run.py")
    ]
    res2 = subprocess.run(cmd_dir)
    if res2.returncode != 0:
        print("[LOI] Build Portable Folder that bai!")
        return False

    built_dir = os.path.join(BASE_DIR, "dist", "QuanLyInAn")
    target_zip = os.path.join(release_dir, "QuanLyInAn_Windows_Portable.zip")

    # 3. Nen thanh file zip Portable
    print("\n[3/4] Dang dong goi file zip Portable...")
    if os.path.exists(target_zip):
        os.remove(target_zip)

    with zipfile.ZipFile(target_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(built_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.join("QuanLyInAn", os.path.relpath(full_path, built_dir))
                zf.write(full_path, rel_path)

    print(f"[THANH CONG] Da tao file zip Portable: {target_zip}")

    # 4. Tao trinh cai dat Setup Wizard (Inno Setup)
    print("\n[4/4] Dang dong goi Trinh cai dat Setup Wizard...")
    try:
        from scripts.build_installer import build_installer
        build_installer()
    except Exception as e:
        print(f"[CANH BAO] Khong the tu dong tao trinh cai dat: {e}")

    installer_file = os.path.join(release_dir, "QuanLyInAn_Setup_v1.0.0.exe")

    print("\n" + "=" * 60)
    print("HOAN TAT DONG GOI TOAN BO UNG DUNG!")
    print(f"1. Trinh cai dat Setup (Khuyen dung cho nguoi dung): {installer_file if os.path.exists(installer_file) else 'Chua build'}")
    print(f"2. File chay ngay (Single File): {target_single}")
    print(f"3. File nen Portable (Mo sieu toc < 1s): {target_zip}")
    print("Tat ca da duoc nhung truc tiep Icon va Thong tin Ban quyen Pham Cong Vinh - THPT Bac Dong Quan.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    build()
