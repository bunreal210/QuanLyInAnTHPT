import os
import sys

# Dam bao thu muc goc luon nam trong sys.path ca khi chay file .py hoac exe dong goi
if getattr(sys, 'frozen', False):
    # Khi chay tu PyInstaller exe
    BASE_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
    if EXE_DIR not in sys.path:
        sys.path.insert(0, EXE_DIR)
else:
    # Khi chay bang python binh thuong
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

from app.main import main

if __name__ == "__main__":
    main()
