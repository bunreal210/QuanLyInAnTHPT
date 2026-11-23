import os
import sys
import urllib.request
import zipfile
import shutil

TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
os.makedirs(TOOLS_DIR, exist_ok=True)
SUMATRA_EXE = os.path.join(TOOLS_DIR, "SumatraPDF.exe")

def ensure_sumatra():
    if os.path.exists(SUMATRA_EXE):
        print(f"SumatraPDF already exists: {SUMATRA_EXE}")
        return True

    url = "https://www.sumatrapdfreader.org/dl/rel/3.5.2/SumatraPDF-3.5.2-64.zip"
    zip_path = os.path.join(TOOLS_DIR, "sumatra.zip")

    print(f"Downloading SumatraPDF portable from {url}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp, open(zip_path, 'wb') as out_file:
            shutil.copyfileobj(resp, out_file)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.lower().endswith("sumatrapdf.exe"):
                    with zip_ref.open(member) as source, open(SUMATRA_EXE, "wb") as target:
                        shutil.copyfileobj(source, target)
                    break
        if os.path.exists(zip_path):
            os.remove(zip_path)
        print(f"Successfully installed SumatraPDF to {SUMATRA_EXE}")
        return True
    except Exception as e:
        print(f"Failed to download SumatraPDF automatically: {e}")
        return False

if __name__ == "__main__":
    ensure_sumatra()
