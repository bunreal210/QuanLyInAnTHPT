@echo off
chcp 65001 > nul
echo Đang tiến hành đóng gói phần mềm Quản lý in ấn THPT sang file .exe...
python build_exe.py
pause
