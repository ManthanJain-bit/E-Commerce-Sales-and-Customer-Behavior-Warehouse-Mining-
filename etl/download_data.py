import os
import sys
import urllib.request
import time

FILES = [
    "aisles.csv",
    "departments.csv",
    "products.csv",
    "orders.csv",
    "order_products__train.csv",
    "order_products__prior.csv",
]

BASE_URL = "https://huggingface.co/datasets/attik/Instacart-Market-Basket-Analysis/resolve/main/"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")


def download_file(filename: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    target_path = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        print(f"[SKIP] {filename} already exists ({os.path.getsize(target_path) / (1024*1024):.2f} MB)")
        return

    url = BASE_URL + filename
    print(f"\n[DOWNLOADING] {filename} from {url}...")

    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urllib.request.urlopen(req) as resp, open(target_path, "wb") as out_f:
        total_size = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                pct = downloaded / total_size * 100
                mb_down = downloaded / (1024 * 1024)
                mb_tot = total_size / (1024 * 1024)
                sys.stdout.write(f"\r  -> {mb_down:.1f}MB / {mb_tot:.1f}MB ({pct:.1f}%)")
            else:
                mb_down = downloaded / (1024 * 1024)
                sys.stdout.write(f"\r  -> {mb_down:.1f}MB downloaded")
            sys.stdout.flush()

    duration = time.time() - t0
    size_mb = os.path.getsize(target_path) / (1024 * 1024)
    speed = size_mb / duration if duration > 0 else 0
    print(f"\n[DONE] Saved {filename} ({size_mb:.2f} MB) in {duration:.1f}s ({speed:.2f} MB/s)")


def main():
    print(f"Target directory: {OUTPUT_DIR}")
    for fname in FILES:
        download_file(fname)
    print("\nAll raw dataset files verified and ready.")


if __name__ == "__main__":
    main()
