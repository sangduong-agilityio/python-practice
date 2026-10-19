import pptx
import sys

sys.stdout.reconfigure(encoding='utf-8')

pptx_path = r"C:\Users\sangd\Downloads\_SangDuong__Database_Training_-_2026__4__updated.pptx"
prs = pptx.Presentation(pptx_path)

print(f"Total layouts: {len(prs.slide_layouts)}")
for i, l in enumerate(prs.slide_layouts):
    print(f"Layout {i}: {l.name}")
