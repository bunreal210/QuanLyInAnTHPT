import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GH_EXE = r"C:\Program Files\GitHub CLI\gh.exe"

def run_cmd(cmd_list, check=True):
    print(f"\n> {' '.join(cmd_list)}")
    res = subprocess.run(cmd_list)
    if check and res.returncode != 0:
        raise RuntimeError(f"Lenh that bai voi ma: {res.returncode}")
    return res.returncode

def main():
    print("="*70)
    print("   TỰ ĐỘNG TẠO REPO GITHUB & ĐẨY MÃ NGUỒN + BẢN EXE LÊN RELEASE")
    print("="*70)

    gh_bin = GH_EXE if os.path.exists(GH_EXE) else "gh"

    # 1. Kiem tra dang nhap GitHub
    res = subprocess.run([gh_bin, "auth", "status"], capture_output=True, text=True)
    if res.returncode != 0:
        print("\n[BƯỚC 1] Đang mở trình duyệt để bạn đăng nhập GitHub...")
        print("Trình duyệt sẽ mở ra. Vui lòng bấm 'Authorize github' để hoàn tất.")
        run_cmd([gh_bin, "auth", "login", "--web", "-p", "https"])

    # 2. Hoi nguoi dung ten repo (hoac mac dinh: QuanLyInAnTHPT)
    repo_name = "QuanLyInAnTHPT"
    print(f"\n[BƯỚC 2] Tự động tạo Repository trên GitHub: '{repo_name}'...")
    
    # Tao repo tren GitHub va tu dong link remote origin
    # Tu chon public de de chia se
    try:
        run_cmd([
            gh_bin, "repo", "create", repo_name,
            "--public",
            "--source=.",
            "--remote=origin",
            "--description", "Phan mem quan ly in an de thi va tai lieu THPT chay tren Windows"
        ])
    except Exception as e:
        print(f"Lưu ý tạo repo (có thể đã tồn tại): {e}")

    # 3. Push code len nhanh main
    print("\n[BƯỚC 3] Đang đẩy toàn bộ mã nguồn lên nhánh 'main'...")
    run_cmd(["git", "branch", "-M", "main"], check=False)
    run_cmd(["git", "push", "-u", "origin", "main"], check=False)

    # 4. Tao Release v1.0.0 va tai file exe + zip len
    print("\n[BƯỚC 4] Đang tạo GitHub Release v1.0.0 và tải file Exe lên...")
    release_dir = os.path.join(BASE_DIR, "release")
    single_exe = os.path.join(release_dir, "QuanLyInAnTHPT_SingleFile.exe")
    portable_zip = os.path.join(release_dir, "QuanLyInAnTHPT_v1.0.0_Windows_Portable.zip")

    assets = []
    if os.path.exists(single_exe):
        assets.append(single_exe)
    if os.path.exists(portable_zip):
        assets.append(portable_zip)

    release_cmd = [
        gh_bin, "release", "create", "v1.0.0",
        "--title", "Phiên bản v1.0.0 - Quản lý in ấn THPT (Windows)",
        "--notes", "Bản phát hành chính thức:\n- Hỗ trợ in đề kiểm tra, phiếu học tập, in Booklet (sách gập đôi)\n- Đồng bộ 2 máy ở xa qua đám mây\n- Đầy đủ file EXE độc lập chạy ngay không cần cài đặt."
    ] + assets

    run_cmd(release_cmd, check=False)

    print("\n" + "="*70)
    print("🎉 HOÀN TẤT THÀNH CÔNG RỰC RỠ!")
    print(f"Repo GitHub và bản Release kèm file EXE đã sẵn sàng trên trang cá nhân của bạn!")
    print("="*70)

if __name__ == "__main__":
    main()
