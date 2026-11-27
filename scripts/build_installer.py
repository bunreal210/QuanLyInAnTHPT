import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

def find_iscc():
    """Tim duong dan toi Inno Setup Compiler (ISCC.exe)"""
    # 1. Kiem tra trong PATH
    which_iscc = shutil.which("iscc")
    if which_iscc:
        return which_iscc
    
    # 2. Kiem tra cac duong dan pho bien tren Windows
    localappdata = os.environ.get("LOCALAPPDATA", "")
    programfiles = os.environ.get("ProgramFiles", r"C:\Program Files")
    programfiles_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

    candidates = [
        os.path.join(localappdata, "Programs", "Inno Setup 6", "ISCC.exe"),
        os.path.join(programfiles, "Inno Setup 6", "ISCC.exe"),
        os.path.join(programfiles_x86, "Inno Setup 6", "ISCC.exe"),
        os.path.join(localappdata, "Programs", "Inno Setup 7", "ISCC.exe"),
        os.path.join(programfiles, "Inno Setup 7", "ISCC.exe"),
        os.path.join(programfiles_x86, "Inno Setup 7", "ISCC.exe"),
    ]

    for p in candidates:
        if os.path.isfile(p):
            return p
    return None

def build_installer():
    print("=" * 60)
    print("BAT DAU BIEN DICH TRINH CAI DAT UNG DUNG: QUAN LY IN AN")
    print("=" * 60)

    # 1. Kiem tra thu muc dist/QuanLyInAn
    dist_dir = os.path.join(BASE_DIR, "dist", "QuanLyInAn")
    exe_file = os.path.join(dist_dir, "QuanLyInAn.exe")
    if not os.path.isdir(dist_dir) or not os.path.isfile(exe_file):
        print(f"[LOI] Khong tim thay thu muc ban build: {dist_dir}")
        print("Vui long chay scripts/build_exe.py truoc de tao ban build onedir.")
        return False

    # 2. Tim ISCC.exe
    iscc = find_iscc()
    if not iscc:
        print("[LOI] Khong tim thay Inno Setup Compiler (ISCC.exe) tren he thong!")
        print("Huong dan cai dat Inno Setup qua winget:")
        print("    winget install --id JRSoftware.InnoSetup -e")
        return False

    print(f"[THONG TIN] Su dung trinh bien dich: {iscc}")

    # 3. Kiem tra file script installer.iss
    iss_file = os.path.join(BASE_DIR, "installer.iss")
    if not os.path.isfile(iss_file):
        print(f"[LOI] Khong tim thay file script: {iss_file}")
        return False

    # 4. Chay ISCC de tao bo cai
    release_dir = os.path.join(BASE_DIR, "release")
    os.makedirs(release_dir, exist_ok=True)

    print("\nDang dong goi va nen bo cai dat (LZMA2 Ultra Compression)...")
    cmd = [iscc, iss_file]
    res = subprocess.run(cmd)

    if res.returncode != 0:
        print("\n[LOI] Bien dich trinh cai dat that bai!")
        return False

    installer_file = os.path.join(release_dir, "QuanLyInAn_Setup_v1.0.0.exe")
    if os.path.isfile(installer_file):
        size_mb = os.path.getsize(installer_file) / (1024 * 1024)
        print("\n" + "=" * 60)
        print("HOAN TAT TAO TRINH CAI DAT THANH CONG!")
        print(f"File cai dat: {installer_file}")
        print(f"Dung luong: {size_mb:.2f} MB")
        print("=" * 60)
        return True
    else:
        print("\n[LOI] Khong tim thay file ket qua sau khi bien dich!")
        return False

if __name__ == "__main__":
    success = build_installer()
    if not success:
        sys.exit(1)
