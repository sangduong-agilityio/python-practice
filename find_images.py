import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

dirs = [
    r"C:\Users\sangd\.gemini\antigravity\brain\27db37f5-881f-470b-8a71-e704d78d7f86",
    r"C:\Users\sangd\Downloads"
]

for d in dirs:
    print(f"\nScanning {d}:")
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                full_p = os.path.join(d, f)
                mtime = os.path.getmtime(full_p)
                size = os.path.getsize(full_p)
                print(f"  {f} (size={size}, mtime={mtime})")
