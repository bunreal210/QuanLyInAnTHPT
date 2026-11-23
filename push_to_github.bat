@echo off
chcp 65001 > nul
echo ======================================================================
echo    ĐANG CHUẨN BỊ TẠO REPO GITHUB VÀ ĐẨY BẢN EXE LÊN MỤC RELEASE...
echo ======================================================================
python scripts/push_to_github.py
pause
