import os
import sys
import time
import subprocess
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("print_manager.printer")

_CACHED_PRINTERS = None

def list_windows_printers(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Lay danh sach tat ca may in dang co tren Windows (co cache de may yeu khong bi do khi quet).
    Uu tien dung win32print, neu chua co se fallback qua PowerShell Get-Printer.
    """
    global _CACHED_PRINTERS
    if not force_refresh and _CACHED_PRINTERS is not None:
        return _CACHED_PRINTERS

    printers = []
    try:
        import win32print
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        printer_tuples = win32print.EnumPrinters(flags)
        default_printer = win32print.GetDefaultPrinter()

        for flags, desc, name, comment in printer_tuples:
            is_default = (name == default_printer)
            printers.append({
                "windows_name": name,
                "display_name": name,
                "is_default": is_default,
                "comment": comment or ""
            })
        _CACHED_PRINTERS = printers
        return printers
    except Exception as e:
        logger.warning(f"Loi doc win32print, chuyen sang PowerShell: {e}")

    # Fallback dung PowerShell
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "Get-Printer | Select-Object -Property Name, Type, Shared | ConvertTo-Json"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            import json
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                name = item.get("Name", "")
                if name:
                    printers.append({
                        "windows_name": name,
                        "display_name": name,
                        "is_default": False,
                        "comment": ""
                    })
    except Exception as ps_err:
        logger.error(f"Loi lay danh sach may in qua PowerShell: {ps_err}")

    _CACHED_PRINTERS = printers
    return printers

def build_sumatra_print_settings(
    copies: int = 1,
    duplex: int = 1, # 0: 1 mat (simplex), 1: 2 mat lat dai (duplexlong), 2: 2 mat lat ngan (duplexshort)
    color: int = 0,  # 0: den trang (monochrome), 1: mau (color)
    paper: str = "A4",
    collate: bool = True
) -> str:
    """
    Tao chuoi -print-settings cho SumatraPDF.
    Vi du: '1x,duplexlong,monochrome,paper=A4,collate'
    """
    parts = []
    # So ban in
    if copies > 1:
        parts.append(f"{copies}x")
    else:
        parts.append("1x")

    # In 2 mat
    if duplex == 1:
        parts.append("duplexlong")
    elif duplex == 2:
        parts.append("duplexshort")
    else:
        parts.append("simplex")

    # Mau / Den trang
    if color == 1:
        parts.append("color")
    else:
        parts.append("monochrome")

    # Kho giay
    if paper:
        parts.append(f"paper={paper}")

    # Chia tap (Collate)
    if collate:
        parts.append("collate")
    else:
        parts.append("nocolla")

    return ",".join(parts)

def apply_devmode_settings(printer_name: str, duplex: int = 1, color: int = 0, paper: str = "A4"):
    """
    Phuong an du phong cho driver Ricoh / Konica:
    Can thiep truc tiep vao DEVMODE cua Windows truoc khi in
    """
    try:
        import win32print
        import win32con
        
        # Open printer with admin/write permission if possible, else standard access
        hPrinter = win32print.OpenPrinter(printer_name, {"DesiredAccess": win32print.PRINTER_ACCESS_USE})
        try:
            properties = win32print.GetPrinter(hPrinter, 2)
            devmode = properties["pDevMode"]
            if devmode:
                # Duplex
                # DMDUP_SIMPLEX = 1, DMDUP_VERTICAL = 2 (long edge), DMDUP_HORIZONTAL = 3 (short edge)
                if duplex == 1:
                    devmode.Duplex = 2
                elif duplex == 2:
                    devmode.Duplex = 3
                else:
                    devmode.Duplex = 1
                devmode.Fields |= win32con.DM_DUPLEX

                # Color
                # DMCOLOR_MONOCHROME = 1, DMCOLOR_COLOR = 2
                if color == 1:
                    devmode.Color = 2
                else:
                    devmode.Color = 1
                devmode.Fields |= win32con.DM_COLOR

                # Paper size (DMPAPER_A4 = 9, DMPAPER_A3 = 8)
                if paper.upper() == "A3":
                    devmode.PaperSize = 8
                else:
                    devmode.PaperSize = 9
                devmode.Fields |= win32con.DM_PAPERSIZE

                # Tra ve doi tuong devmode da duoc cau hinh
                return devmode
        finally:
            win32print.ClosePrinter(hPrinter)
    except Exception as e:
        logger.warning(f"Khong the set DEVMODE cho {printer_name}: {e}")
    return None

_CACHED_SUMATRA_PATH = None

def find_or_extract_sumatra(custom_path: str = None) -> str:
    """
    Tim duong dan thuc te cua SumatraPDF.exe theo thu tu uu tien.
    Tu dong tim trong bundle PyInstaller, thu muc exe, thu muc tools hoac AppData.
    Neu hoan toan chua co, tu dong tai ve thu muc AppData de su dung ngay lap tuc.
    """
    global _CACHED_SUMATRA_PATH
    if not custom_path and _CACHED_SUMATRA_PATH and os.path.exists(_CACHED_SUMATRA_PATH):
        return _CACHED_SUMATRA_PATH

    candidates = []
    if custom_path and os.path.exists(custom_path) and os.path.getsize(custom_path) > 100000:
        _CACHED_SUMATRA_PATH = custom_path
        return custom_path

    # 1. Thu muc PyInstaller bundle
    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', '')
        if bundle_dir:
            candidates.append(os.path.join(bundle_dir, "tools", "SumatraPDF.exe"))
            candidates.append(os.path.join(bundle_dir, "_internal", "tools", "SumatraPDF.exe"))
            candidates.append(os.path.join(bundle_dir, "SumatraPDF.exe"))
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "tools", "SumatraPDF.exe"))
        candidates.append(os.path.join(exe_dir, "_internal", "tools", "SumatraPDF.exe"))
        candidates.append(os.path.join(exe_dir, "SumatraPDF.exe"))

    # 2. Thu muc du an goc
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidates.append(os.path.join(base_dir, "tools", "SumatraPDF.exe"))
    candidates.append(os.path.join(base_dir, "SumatraPDF.exe"))

    # 3. Thu muc AppData nguoi dung
    app_data_dir = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), "QuanLyInAnTHPT", "tools")
    try:
        os.makedirs(app_data_dir, exist_ok=True)
    except Exception:
        pass
    appdata_sumatra = os.path.join(app_data_dir, "SumatraPDF.exe")
    candidates.append(appdata_sumatra)

    # 4. Program Files he thong
    candidates.append(r"C:\Program Files\SumatraPDF\SumatraPDF.exe")
    candidates.append(r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe")

    for p in candidates:
        if p and os.path.exists(p) and os.path.getsize(p) > 100000:
            _CACHED_SUMATRA_PATH = p
            return p

    # Neu chua co bat cu dau, thu tu dong tai ve AppData
    try:
        import urllib.request, zipfile, io, shutil
        url = "https://www.sumatrapdfreader.org/dl/rel/3.5.2/SumatraPDF-3.5.2-64.zip"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            z = zipfile.ZipFile(io.BytesIO(resp.read()))
            for name in z.namelist():
                if name.lower().endswith(".exe"):
                    with z.open(name) as src, open(appdata_sumatra, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    return appdata_sumatra
    except Exception as e:
        logger.warning(f"Khong the tu dong tai SumatraPDF: {e}")

    return candidates[0] if candidates else ""

def execute_sumatra_print(
    sumatra_exe: str,
    printer_name: str,
    pdf_path: str,
    settings_str: str = ""
) -> Dict[str, Any]:
    """
    Goi SumatraPDF chay ngam de in ra may in chi dinh.
    Cau truc: SumatraPDF.exe -print-to "TEN_MAY_IN" -print-settings "settings" -silent "file.pdf"
    """
    if not sumatra_exe or not os.path.exists(sumatra_exe) or os.path.getsize(sumatra_exe) < 100000:
        sumatra_exe = find_or_extract_sumatra(sumatra_exe)

    if not os.path.exists(sumatra_exe):
        # Phuong an du phong cuoi cung: In qua Windows Shell (win32api ShellExecute)
        try:
            import win32api
            win32api.ShellExecute(0, "printto", os.path.abspath(pdf_path), f'"{printer_name}"', ".", 0)
            return {
                "success": True,
                "command": f"ShellExecute printto {printer_name}",
                "message": f"Da gui lenh in truc tiep qua Windows toi may in: {printer_name}"
            }
        except Exception as shell_err:
            return {
                "success": False,
                "error": f"Khong tim thay SumatraPDF.exe va loi goi Windows Shell: {shell_err}"
            }

    if not os.path.exists(pdf_path):
        return {
            "success": False,
            "error": f"Khong tim thay file PDF can in: {pdf_path}"
        }

    cmd = [sumatra_exe, "-print-to", printer_name]
    if settings_str:
        cmd.extend(["-print-settings", settings_str])
    cmd.extend(["-silent", pdf_path])

    logger.info(f"Thuc thi lenh in: {' '.join(cmd)}")

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        if process.returncode == 0:
            return {
                "success": True,
                "command": " ".join(cmd),
                "message": f"Da gui thanh cong lenh in toi may in: {printer_name}"
            }
        else:
            err = process.stderr.strip() or f"SumatraPDF thoat voi ma loi: {process.returncode}"
            return {
                "success": False,
                "command": " ".join(cmd),
                "error": err
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "command": " ".join(cmd),
            "error": "Qua thoi gian cho xu ly lenh in (Timeout 60s)"
        }
    except Exception as e:
        return {
            "success": False,
            "command": " ".join(cmd),
            "error": f"Loi he thong khi goi may in: {str(e)}"
        }

def open_windows_print_dialog(
    file_path: str,
    pdf_path: str = None,
    printer_name: str = None,
    prefer_original_app: bool = False,
    settings_str: str = ""
) -> Dict[str, Any]:
    """
    Mo hop thoai in (Print Dialog) cua Windows de nguoi dung tu chon may in,
    Preferences/Properties (khay giay, 2 mat, booklet, v.v.):
    - Su dung SumatraPDF voi tham so -print-dialog (tuyet doi KHONG kem -print-to vi se bi in ngam mat cua so)
    - Tu dong dua cua so Print Dialog len Foreground (phia truoc ung dung)
    """
    abs_orig = os.path.abspath(file_path) if file_path and os.path.exists(file_path) else None
    abs_pdf = os.path.abspath(pdf_path) if pdf_path and os.path.exists(pdf_path) else None
    ext = os.path.splitext(file_path)[1].lower() if file_path else ""

    target_pdf = abs_pdf or (abs_orig if ext == ".pdf" else None)
    if not target_pdf or not os.path.exists(target_pdf):
        return {
            "success": False,
            "error": "Không tìm thấy file PDF hợp lệ để mở cửa sổ in."
        }

    sumatra_exe = find_or_extract_sumatra()
    if not sumatra_exe or not os.path.exists(sumatra_exe):
        return {
            "success": False,
            "error": "Không tìm thấy công cụ SumatraPDF.exe để mở cửa sổ in."
        }

    # Luu y quan trong: Tuyet doi khong truyen -print-to vi SumatraPDF se in ngam truc tiep va bo qua cua so dialog!
    cmd = [sumatra_exe, "-print-dialog"]
    if settings_str:
        cmd.extend(["-print-settings", settings_str])
    cmd.append(target_pdf)

    try:
        logger.info(f"Mo hop thoai in Windows qua SumatraPDF: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd)

        # Cho 0.3 giay de cua so Print Dialog cua Windows xuat hien va dua len Foreground
        time.sleep(0.3)
        try:
            import win32gui
            import win32process
            import win32con

            def _bring_to_front(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid == proc.pid:
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.BringWindowToTop(hwnd)
                return True

            win32gui.EnumWindows(_bring_to_front, None)
        except Exception:
            pass

        ret = proc.wait(timeout=300)
        if ret == 0:
            return {
                "success": True,
                "command": " ".join(cmd),
                "message": "Đã gửi lệnh in từ cửa sổ Windows Print Dialog thành công."
            }
        else:
            return {
                "success": False,
                "cancelled": True,
                "error": "Người dùng đã đóng hoặc hủy in trong cửa sổ in Windows."
            }
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        return {
            "success": False,
            "cancelled": True,
            "error": "Hết thời gian chờ thao tác trên cửa sổ in Windows (quá 5 phút)."
        }
    except Exception as sum_err:
        logger.warning(f"Loi goi SumatraPDF -print-dialog: {sum_err}")
        return {
            "success": False,
            "error": f"Lỗi mở cửa sổ in Windows: {sum_err}"
        }

def create_sample_test_pdf(output_pdf_path: str, test_title: str = "BẢN IN THỬ NGHIỆM") -> str:
    """
    Tao mot file PDF 2 trang voi noi dung ro rang de in thu nghiem cac tinh nang:
    - Trang 1: Mau sac ruc ro + chu thich mat truoc
    - Trang 2: Noi dung mat sau de kiem tra 2 mat
    """
    import fitz  # PyMuPDF
    doc = fitz.open()

    # Trang 1: A4 (595 x 842 points)
    page1 = doc.new_page(width=595, height=842)
    rect1 = fitz.Rect(50, 50, 545, 792)

    # Khung vien trang 1
    page1.draw_rect(rect1, color=(0.1, 0.3, 0.7), width=2)
    # Tieu de
    page1.insert_text(fitz.Point(70, 100), "HE THONG QUAN LY IN AN TRUONG THPT", fontsize=18, fontname="helv", color=(0.1, 0.3, 0.7))
    page1.insert_text(fitz.Point(70, 130), f"TEST PAGE 1 (MAT TRUOC) - {test_title}", fontsize=14, fontname="helv", color=(0.8, 0.1, 0.1))
    page1.insert_text(fitz.Point(70, 170), "Muc tieu kiem tra:", fontsize=12, fontname="helv")
    page1.insert_text(fitz.Point(90, 200), "1. Kho giay (A4 / A3)", fontsize=11, fontname="helv")
    page1.insert_text(fitz.Point(90, 225), "2. In 2 mat tu dong (Neu in 2 mat, Trang 2 phai nam o mat sau)", fontsize=11, fontname="helv")
    page1.insert_text(fitz.Point(90, 250), "3. Mau sac (Neu chon 'Den trang', o vuong mau duoi day se thanh mau xam)", fontsize=11, fontname="helv")

    # Cac o mau kiem tra color vs monochrome
    colors = [
        ("RED", (0.9, 0.1, 0.1), 70),
        ("GREEN", (0.1, 0.7, 0.1), 160),
        ("BLUE", (0.1, 0.2, 0.8), 250),
        ("YELLOW", (0.9, 0.8, 0.1), 340),
        ("BLACK", (0.1, 0.1, 0.1), 430),
    ]
    for label, col, x in colors:
        page1.draw_rect(fitz.Rect(x, 280, x + 70, 340), color=col, fill=col)
        page1.insert_text(fitz.Point(x + 10, 360), label, fontsize=10, fontname="helv")

    page1.insert_text(fitz.Point(70, 420), "=== DAY LA TRANG SO 1 (FRONT PAGE) ===", fontsize=13, fontname="helv", color=(0.2, 0.2, 0.2))

    # Trang 2: Mat sau
    page2 = doc.new_page(width=595, height=842)
    rect2 = fitz.Rect(50, 50, 545, 792)
    page2.draw_rect(rect2, color=(0.7, 0.3, 0.1), width=2)
    page2.insert_text(fitz.Point(70, 100), "HE THONG QUAN LY IN AN TRUONG THPT", fontsize=18, fontname="helv", color=(0.7, 0.3, 0.1))
    page2.insert_text(fitz.Point(70, 130), "TEST PAGE 2 (MAT SAU - KIEM TRA DUPLEX)", fontsize=14, fontname="helv", color=(0.1, 0.5, 0.1))

    page2.insert_text(fitz.Point(70, 200), "Kiem tra huong lat giay:", fontsize=12, fontname="helv")
    page2.insert_text(fitz.Point(90, 230), "- Lat canh dai (duplexlong): Chieu chu trang 2 cung chieu trang 1 khi lat ngang.", fontsize=11, fontname="helv")
    page2.insert_text(fitz.Point(90, 260), "- Lat canh ngan (duplexshort): Dung cho tai lieu in ngang hoac giay thi.", fontsize=11, fontname="helv")

    page2.insert_text(fitz.Point(70, 350), "=== DAY LA TRANG SO 2 (BACK PAGE) ===", fontsize=13, fontname="helv", color=(0.2, 0.2, 0.2))

    doc.save(output_pdf_path)
    doc.close()
    return output_pdf_path

def open_printer_preferences_dialog(printer_name: str) -> bool:
    """
    Mo truc tiep bang tuy chon driver may in goc (Printing Preferences - rundll32 printui.dll,PrintUIEntry /e /n)
    Noi nguoi dung tuy chinh sau cac chuc nang phan cung cao cap:
    - Bo dap ghim (Finisher / Stapler): Dap 1 ghim, 2 ghim, ghim gap doi booklet saddle stitch
    - Bo duc lo (Punch): 2 lo, 3 lo, 4 lo
    - Khay giay ra (Finisher Shift Tray, Proof Tray)
    - Khay giay vao (Bypass tray, khay giay day Thick paper)
    """
    if not printer_name:
        return False
    try:
        cmd = ["rundll32.exe", "printui.dll,PrintUIEntry", "/e", "/n", printer_name]
        subprocess.Popen(cmd)
        logger.info(f"Da mo hop thoai Printing Preferences cho may in: {printer_name}")
        return True
    except Exception as e:
        logger.error(f"Loi goi PrintUIEntry cho {printer_name}: {e}")

    try:
        import win32print
        import win32con
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            win32print.DocumentProperties(0, hPrinter, printer_name, None, None, win32con.DM_IN_PROMPT)
            return True
        finally:
            win32print.ClosePrinter(hPrinter)
    except Exception as doc_err:
        logger.error(f"Loi mo DocumentProperties: {doc_err}")
        return False

def open_printer_device_settings_dialog(printer_name: str) -> bool:
    """
    Mo bang thuoc tinh may in (Printer Properties - rundll32 printui.dll,PrintUIEntry /p /n)
    Dung khi can kich hoat phan cung Bo dap ghim (Finisher) trong tab Device Settings neu may tinh chua nhan dien
    """
    if not printer_name:
        return False
    try:
        cmd = ["rundll32.exe", "printui.dll,PrintUIEntry", "/p", "/n", printer_name]
        subprocess.Popen(cmd)
        logger.info(f"Da mo hop thoai Printer Properties cho may in: {printer_name}")
        return True
    except Exception as e:
        logger.error(f"Loi goi PrintUIEntry /p cho {printer_name}: {e}")
        return False


# ==============================================================================
# NATIVE WINDOWS PRINT DIALOG (PrintDlgW)
# ==============================================================================
import ctypes
from ctypes import wintypes

class PRINTDLGW(ctypes.Structure):
    _fields_ = [
        ('lStructSize', wintypes.DWORD),
        ('hwndOwner', wintypes.HWND),
        ('hDevMode', wintypes.HGLOBAL),
        ('hDevNames', wintypes.HGLOBAL),
        ('hDC', wintypes.HDC),
        ('Flags', wintypes.DWORD),
        ('nFromPage', wintypes.WORD),
        ('nToPage', wintypes.WORD),
        ('nMinPage', wintypes.WORD),
        ('nMaxPage', wintypes.WORD),
        ('nCopies', wintypes.WORD),
        ('hInstance', wintypes.HINSTANCE),
        ('lCustData', wintypes.LPARAM),
        ('lpfnPrintHook', wintypes.LPVOID),
        ('lpfnSetupHook', wintypes.LPVOID),
        ('lpPrintTemplateName', wintypes.LPCWSTR),
        ('lpSetupTemplateName', wintypes.LPCWSTR),
        ('hPrintTemplate', wintypes.HGLOBAL),
        ('hSetupTemplate', wintypes.HGLOBAL),
    ]

class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ('dmDeviceName', wintypes.WCHAR * 32),
        ('dmSpecVersion', wintypes.WORD),
        ('dmDriverVersion', wintypes.WORD),
        ('dmSize', wintypes.WORD),
        ('dmDriverExtra', wintypes.WORD),
        ('dmFields', wintypes.DWORD),
        ('dmOrientation', ctypes.c_short),
        ('dmPaperSize', ctypes.c_short),
        ('dmPaperLength', ctypes.c_short),
        ('dmPaperWidth', ctypes.c_short),
        ('dmScale', ctypes.c_short),
        ('dmCopies', ctypes.c_short),
        ('dmDefaultSource', ctypes.c_short),
        ('dmPrintQuality', ctypes.c_short),
        ('dmColor', ctypes.c_short),
        ('dmDuplex', ctypes.c_short),
        ('dmYResolution', ctypes.c_short),
        ('dmTTOption', ctypes.c_short),
        ('dmCollate', ctypes.c_short),
        ('dmFormName', wintypes.WCHAR * 32),
        ('dmLogPixels', wintypes.WORD),
        ('dmBitsPerPel', wintypes.DWORD),
        ('dmPelsWidth', wintypes.DWORD),
        ('dmPelsHeight', wintypes.DWORD),
        ('dmDisplayFlags', wintypes.DWORD),
        ('dmDisplayFrequency', wintypes.DWORD),
        ('dmICMMethod', wintypes.DWORD),
        ('dmICMIntent', wintypes.DWORD),
        ('dmMediaType', wintypes.DWORD),
        ('dmDitherType', wintypes.DWORD),
        ('dmReserved1', wintypes.DWORD),
        ('dmReserved2', wintypes.DWORD),
        ('dmPanningWidth', wintypes.DWORD),
        ('dmPanningHeight', wintypes.DWORD),
    ]

class DEVNAMES(ctypes.Structure):
    _fields_ = [
        ('wDriverOffset', wintypes.WORD),
        ('wDeviceOffset', wintypes.WORD),
        ('wOutputOffset', wintypes.WORD),
        ('wDefault', wintypes.WORD),
    ]

def _make_native_devnames(device: str, driver: str = "winspool", output: str = ""):
    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

    hdr_size = ctypes.sizeof(DEVNAMES)
    w_hdr = hdr_size // 2
    w_drv = w_hdr
    w_dev = w_drv + len(driver) + 1
    w_out = w_dev + len(device) + 1
    total_chars = w_out + len(output) + 1

    size = total_chars * 2
    hMem = kernel32.GlobalAlloc(0x0002, size) # GMEM_MOVEABLE
    if not hMem:
        return 0
    p = kernel32.GlobalLock(hMem)
    if not p:
        return 0
    dn = DEVNAMES.from_address(p)
    dn.wDriverOffset = w_drv
    dn.wDeviceOffset = w_dev
    dn.wOutputOffset = w_out
    dn.wDefault = 0

    ptr_drv = p + w_drv * 2
    ptr_dev = p + w_dev * 2
    ptr_out = p + w_out * 2
    ctypes.memmove(ptr_drv, ctypes.c_wchar_p(driver), (len(driver) + 1) * 2)
    ctypes.memmove(ptr_dev, ctypes.c_wchar_p(device), (len(device) + 1) * 2)
    ctypes.memmove(ptr_out, ctypes.c_wchar_p(output), (len(output) + 1) * 2)
    kernel32.GlobalUnlock(hMem)
    return hMem

def _make_native_devmode(device: str, copies: int = 1, duplex: int = 1, color: int = 0, paper: str = "A4"):
    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

    hMem = kernel32.GlobalAlloc(0x0002, ctypes.sizeof(DEVMODEW))
    if not hMem:
        return 0
    p = kernel32.GlobalLock(hMem)
    if not p:
        return 0
    dm = DEVMODEW.from_address(p)
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    dm.dmDeviceName = str(device)[:31]
    dm.dmCopies = max(1, copies)
    dm.dmDuplex = 2 if duplex == 1 else (3 if duplex == 2 else 1)
    dm.dmColor = 2 if color == 1 else 1
    dm.dmPaperSize = 8 if paper.upper() == "A3" else (11 if paper.upper() == "A5" else 9)
    dm.dmFields = 0x00000100 | 0x00001000 | 0x00000800 | 0x00000002
    kernel32.GlobalUnlock(hMem)
    return hMem

def show_native_windows_print_dialog(
    parent_hwnd: int = 0,
    current_printer: str = None,
    current_copies: int = 1,
    current_duplex: int = 1,
    current_color: int = 0,
    current_paper: str = "A4",
    total_pages: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Mo hop thoai in goc (Native Windows Print Dialog) bang Windows API PrintDlgW:
    - Nguoi dung chon may in, so ban in, khoang trang va dac biet co the bam vao Preferences / Properties
      de tuy chon 2 mat (duplex), mau sac (color), kho giay (A4/A3/A5).
    - Sau khi nguoi dung bam nut "In" (Print) tren cua so Windows:
      Ham se doc toan bo DEVMODEW thuc te ma nguoi dung vua chon va tra ve dict thong so.
    - Neu nguoi dung bam "Huy" (Cancel) hoac dong hop thoai: Tra ve None.
    """
    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]

    comdlg32 = ctypes.windll.comdlg32

    pd = PRINTDLGW()
    pd.lStructSize = ctypes.sizeof(PRINTDLGW)
    pd.hwndOwner = parent_hwnd or 0
    # PD_ALLPAGES | PD_USEDEVMODECOPIESANDCOLLATE | PD_HIDEPRINTTOFILE | PD_NOSELECTION
    pd.Flags = 0x00000000 | 0x00040000 | 0x00100000 | 0x00000004
    pd.nMinPage = 1
    pd.nMaxPage = max(1, total_pages)
    pd.nFromPage = 1
    pd.nToPage = max(1, total_pages)
    pd.nCopies = max(1, current_copies)

    if current_printer:
        pd.hDevNames = _make_native_devnames(current_printer)
        pd.hDevMode = _make_native_devmode(current_printer, current_copies, current_duplex, current_color, current_paper)

    ret = comdlg32.PrintDlgW(ctypes.byref(pd))
    if not ret:
        if pd.hDevNames:
            kernel32.GlobalFree(pd.hDevNames)
        if pd.hDevMode:
            kernel32.GlobalFree(pd.hDevMode)
        return None

    result = {}
    chosen_printer = current_printer or ""
    if pd.hDevNames:
        pNames = kernel32.GlobalLock(pd.hDevNames)
        if pNames:
            dn = DEVNAMES.from_address(pNames)
            chosen_printer = ctypes.wstring_at(pNames + dn.wDeviceOffset * 2)
            kernel32.GlobalUnlock(pd.hDevNames)
    result['printer_name'] = chosen_printer

    chosen_copies = max(1, int(pd.nCopies or 1))
    final_duplex = current_duplex
    final_color = current_color
    final_paper = current_paper

    if pd.hDevMode:
        pMode = kernel32.GlobalLock(pd.hDevMode)
        if pMode:
            dm = DEVMODEW.from_address(pMode)
            if dm.dmCopies and dm.dmCopies > 0:
                chosen_copies = int(dm.dmCopies)

            # Duplex: 1 = simplex, 2 = vertical (lat dai), 3 = horizontal (lat ngan)
            if dm.dmDuplex == 2:
                final_duplex = 1 # 2 mat lat dai
            elif dm.dmDuplex == 3:
                final_duplex = 2 # 2 mat lat ngan
            elif dm.dmDuplex == 1:
                final_duplex = 0 # 1 mat

            # Color: 1 = monochrome, 2 = color
            if dm.dmColor == 2:
                final_color = 1 # In mau
            elif dm.dmColor == 1:
                final_color = 0 # Den trang

            # Paper: 8 = A3, 11 = A5, 9 = A4
            form_str = str(dm.dmFormName).upper()
            if dm.dmPaperSize == 8 or 'A3' in form_str:
                final_paper = 'A3'
            elif dm.dmPaperSize == 11 or 'A5' in form_str:
                final_paper = 'A5'
            elif dm.dmPaperSize == 9 or 'A4' in form_str:
                final_paper = 'A4'

            kernel32.GlobalUnlock(pd.hDevMode)

    result['copies'] = chosen_copies
    result['duplex'] = final_duplex
    result['color'] = final_color
    result['paper'] = final_paper

    # Khoang trang (Page range)
    if pd.Flags & 0x00000002: # PD_PAGENUMS
        from_p = max(1, int(pd.nFromPage))
        to_p = min(total_pages, int(pd.nToPage))
        result['page_range'] = f"{from_p}-{to_p}"
    else:
        result['page_range'] = ""

    if pd.hDevNames:
        kernel32.GlobalFree(pd.hDevNames)
    if pd.hDevMode:
        kernel32.GlobalFree(pd.hDevMode)

    return result

