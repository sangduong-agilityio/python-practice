import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

downloads = r"C:\Users\sangd\Downloads"
for f in sorted(os.listdir(downloads)):
    if "SangDuong" in f or "note" in f.lower() or "demo" in f.lower():
        full_p = os.path.join(downloads, f)
        print(f"{f} (size={os.path.getsize(full_p)}, mtime={os.path.getmtime(full_p)})")
