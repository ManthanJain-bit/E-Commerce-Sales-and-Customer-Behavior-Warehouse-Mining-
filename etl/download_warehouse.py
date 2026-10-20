import os
import sys
import zipfile
import urllib.request
import time

RELEASE_URL = "https://github.com/ManthanJain-bit/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/releases/download/v1.0.0/warehouse_data.zip"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
WAREHOUSE_DIR = os.path.join(DATA_DIR, "warehouse")
ZIP_PATH = os.path.join(DATA_DIR, "warehouse_data.zip")


def download_and_extract():
    os.makedirs(DATA_DIR, exist_ok=True)
    duckdb_path = os.path.join(WAREHOUSE_DIR, "dwm.duckdb")

    if os.path.exists(duckdb_path) and os.path.getsize(duckdb_path) > 100 * 1024 * 1024:
        print(f"[SKIP] Warehouse database already exists: {duckdb_path} ({os.path.getsize(duckdb_path) / (1024*1024):.2f} MB)")
        print("You can run the dashboard immediately: streamlit run dashboard/app.py")
        return

    # Check if zip already exists locally
    if not (os.path.exists(ZIP_PATH) and os.path.getsize(ZIP_PATH) > 100 * 1024 * 1024):
        print(f"Downloading pre-built warehouse from GitHub Release v1.0.0...")
        print(f"Source URL: {RELEASE_URL}")
        print(f"Destination: {ZIP_PATH}\n")

        t0 = time.time()

        def progress_hook(blocks, block_size, total_size):
            downloaded = blocks * block_size
            pct = min(100.0, (downloaded / total_size) * 100) if total_size > 0 else 0
            mb_done = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            sys.stdout.write(f"\r  Progress: {pct:5.1f}% [{mb_done:6.1f} MB / {mb_total:6.1f} MB]")
            sys.stdout.flush()

        urllib.request.urlretrieve(RELEASE_URL, ZIP_PATH, reporthook=progress_hook)
        duration = time.time() - t0
        print(f"\n\nDownload completed in {duration:.1f}s!")

    print(f"\nExtracting {ZIP_PATH} into {DATA_DIR}...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        zf.extractall(DATA_DIR)

    print(f"Extraction complete! Warehouse files ready in: {WAREHOUSE_DIR}")
    print("\nYou can now launch the dashboard immediately:")
    print("  streamlit run dashboard/app.py\n")


if __name__ == "__main__":
    download_and_extract()
