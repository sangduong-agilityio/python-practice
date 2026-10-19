import pptx
from pptx.dml.color import RGBColor
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import sys

sys.stdout.reconfigure(encoding='utf-8')

pptx_path = r"C:\Users\sangd\Downloads\_SangDuong__Database_Training_-_2026__4__updated.pptx"
prs = pptx.Presentation(pptx_path)

# Palette
C_WHITE = RGBColor(255, 255, 255)
C_SLATE_100 = RGBColor(241, 245, 249)
C_SLATE_200 = RGBColor(226, 232, 240)
C_SLATE_300 = RGBColor(203, 213, 225)
C_SLATE_400 = RGBColor(148, 163, 184)
C_SLATE_700 = RGBColor(51, 65, 85)
C_SLATE_800 = RGBColor(30, 41, 59)
C_NAVY_DARK = RGBColor(11, 18, 32)
C_TERMINAL_BG = RGBColor(15, 23, 42)

C_CYAN = RGBColor(56, 189, 248) # #38BDF8
C_CYAN_DARK = RGBColor(2, 132, 199)
C_YELLOW_CODE = RGBColor(253, 224, 71) # #FDE047
C_CORAL_RED = RGBColor(248, 113, 113) # #F87171
C_MINT_GREEN = RGBColor(52, 211, 153) # #34D399
C_GREEN_CELL = RGBColor(8, 38, 30)
C_GREEN_HEADER = RGBColor(6, 78, 59)
C_GREEN_TEXT = RGBColor(167, 243, 208)

# Check if slide already exists or create new slide
# Insert after Slide 12 (0-indexed 11) -> new slide index 12
blank_slide_layout = prs.slide_layouts[6] # blank layout
new_slide = prs.slides.add_slide(blank_slide_layout)

# Move new_slide to position after Slide 12 (index 12)
slide_id_list = prs.slides._sldIdLst
new_slide_elem = slide_id_list[-1]
slide_id_list.insert(12, new_slide_elem)

# Set Dark Background for new slide
background = new_slide.background
fill = background.fill
fill.solid()
fill.fore_color.rgb = C_NAVY_DARK

# 1. Slide Title & Subtitle
title_box = new_slide.shapes.add_textbox(365760, 210000, 8412480, 400000)
tf = title_box.text_frame
tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
p = tf.paragraphs[0]
r = p.add_run()
r.text = "FastAPI & SQLAlchemy — Transaction Implementation"
r.font.bold = True
r.font.size = Pt(18)
r.font.color.rgb = C_WHITE

sub_box = new_slide.shapes.add_textbox(365760, 580000, 8412480, 220000)
tf = sub_box.text_frame
tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
p = tf.paragraphs[0]
r = p.add_run()
r.text = "HOW POSTGRESQL TRANSACTIONS ARE MANAGED IN MODERN PYTHON BACKEND APIS"
r.font.bold = True
r.font.size = Pt(9.5)
r.font.color.rgb = C_CYAN

# Layout: 2 Columns (Left: Per-Request Pattern, Right: Explicit & Nested Savepoints)
col_width = 4050000
col_gap = 312480
left_col = 365760
right_col = left_col + col_width + col_gap
top_base = 880000

# ==============================================================================
# LEFT COLUMN: Pattern 1 - Per-Request Dependency (Enterprise Standard)
# ==============================================================================
left_card_h = 3280000
c1 = new_slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_col, top_base, col_width, left_card_h)
c1.fill.solid()
c1.fill.fore_color.rgb = C_TERMINAL_BG
c1.line.color.rgb = C_MINT_GREEN
c1.line.width = Pt(1.5)
tf1 = c1.text_frame
tf1.margin_left = Pt(10)
tf1.margin_top = Pt(8)
tf1.margin_right = Pt(10)

# Header
p = tf1.paragraphs[0]
r = p.add_run()
r.text = "1. Per-Request Transaction (Depends(get_db))\n"
r.font.bold = True
r.font.size = Pt(10)
r.font.color.rgb = C_MINT_GREEN

p_desc = tf1.add_paragraph()
r_desc = p_desc.add_run()
r_desc.text = "• Enterprise Pattern: Each API request gets an isolated transaction.\n• Auto COMMIT on 2xx OK · Auto ROLLBACK on Exception / 500 error.\n"
r_desc.font.size = Pt(8)
r_desc.font.color.rgb = C_SLATE_300

# Python Code
p_code = tf1.add_paragraph()
lines = [
    ("# database.py (Session Generator)", C_SLATE_400, False),
    ("async def ", C_CYAN, True), ("get_db", C_YELLOW_CODE, True), ("():\n", C_WHITE, False),
    ("    async with ", C_CYAN, True), ("AsyncSessionLocal() ", C_WHITE, False), ("as ", C_CYAN, True), ("session:\n", C_WHITE, False),
    ("        try:\n", C_CYAN, True),
    ("            yield ", C_CYAN, True), ("session\n", C_WHITE, False),
    ("            await ", C_CYAN, True), ("session.commit()    ", C_MINT_GREEN, True), ("# Auto COMMIT\n", C_SLATE_400, False),
    ("        except ", C_CYAN, True), ("Exception:\n", C_CORAL_RED, True),
    ("            await ", C_CYAN, True), ("session.rollback()  ", C_CORAL_RED, True), ("# Auto ROLLBACK\n", C_SLATE_400, False),
    ("            raise\n", C_CORAL_RED, True),
    ("        finally:\n", C_CYAN, True),
    ("            await ", C_CYAN, True), ("session.close()\n\n", C_WHITE, False),
    ("# router.py (Endpoint Injection)", C_SLATE_400, False),
    ("@router.post(", C_CYAN, True), ("\"/tasks/{id}/assign\"", C_YELLOW_CODE, False), (")\n", C_WHITE, False),
    ("async def ", C_CYAN, True), ("assign_task", C_YELLOW_CODE, True), ("(db: AsyncSession = ", C_WHITE, False), ("Depends", C_CYAN, True), ("(get_db)):\n", C_WHITE, False),
    ("    await ", C_CYAN, True), ("task_service.assign(db, task_id, user_id)", C_SLATE_200, False)
]

for item in lines:
    txt, col, bold = item[0], item[1], item[2]
    r = p_code.add_run()
    r.text = txt
    r.font.size = Pt(7.8)
    r.font.color.rgb = col
    r.font.bold = bold


# ==============================================================================
# RIGHT COLUMN - TOP: Pattern 2 - Explicit Context Manager (session.begin())
# ==============================================================================
right_card_h1 = 1580000
c2 = new_slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_col, top_base, col_width, right_card_h1)
c2.fill.solid()
c2.fill.fore_color.rgb = C_TERMINAL_BG
c2.line.color.rgb = C_CYAN
c2.line.width = Pt(1.2)
tf2 = c2.text_frame
tf2.margin_left = Pt(10)
tf2.margin_top = Pt(7)
tf2.margin_right = Pt(10)

p = tf2.paragraphs[0]
r = p.add_run()
r.text = "2. Explicit Scope (async with session.begin():)\n"
r.font.bold = True
r.font.size = Pt(9.5)
r.font.color.rgb = C_CYAN

p_code2 = tf2.add_paragraph()
lines2 = [
    ("# Multi-table write inside Service layer\n", C_SLATE_400, False),
    ("async with ", C_CYAN, True), ("session.begin():  ", C_CYAN, True), ("# Starts TX\n", C_SLATE_400, False),
    ("    session.add(TaskAssignee(task_id, user_id))\n", C_SLATE_200, False),
    ("    session.add(ActivityLog(task_id, 'assigned'))\n", C_SLATE_200, False),
    ("    session.add(Notification(user_id, 'assigned'))\n", C_SLATE_200, False),
    ("    # ✔ Auto COMMIT on block exit | ✖ Auto ROLLBACK on error", C_MINT_GREEN, True)
]
for txt, col, bold in lines2:
    r = p_code2.add_run()
    r.text = txt
    r.font.size = Pt(7.6)
    r.font.color.rgb = col
    r.font.bold = bold

# ==============================================================================
# RIGHT COLUMN - BOTTOM: Pattern 3 - Nested Transactions (Savepoints)
# ==============================================================================
top_right2 = top_base + right_card_h1 + 120000
right_card_h2 = 1580000
c3 = new_slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_col, top_right2, col_width, right_card_h2)
c3.fill.solid()
c3.fill.fore_color.rgb = C_TERMINAL_BG
c3.line.color.rgb = C_YELLOW_CODE
c3.line.width = Pt(1.2)
tf3 = c3.text_frame
tf3.margin_left = Pt(10)
tf3.margin_top = Pt(7)
tf3.margin_right = Pt(10)

p = tf3.paragraphs[0]
r = p.add_run()
r.text = "3. Nested Transactions / Savepoints (begin_nested())\n"
r.font.bold = True
r.font.size = Pt(9.5)
r.font.color.rgb = C_YELLOW_CODE

p_code3 = tf3.add_paragraph()
lines3 = [
    ("async with ", C_CYAN, True), ("session.begin():  ", C_CYAN, True), ("# Main Transaction\n", C_SLATE_400, False),
    ("    session.add(new_task)      ", C_SLATE_200, False), ("# Core business entity\n", C_SLATE_400, False),
    ("    try:\n", C_CYAN, True),
    ("        async with ", C_CYAN, True), ("session.begin_nested(): ", C_YELLOW_CODE, True), ("# SQL SAVEPOINT\n", C_SLATE_400, False),
    ("            session.add(notification)   ", C_SLATE_200, False), ("# Non-critical\n", C_SLATE_400, False),
    ("    except Exception: pass ", C_CORAL_RED, True), ("# Notification fail != Task lost", C_SLATE_300, False)
]
for txt, col, bold in lines3:
    r = p_code3.add_run()
    r.text = txt
    r.font.size = Pt(7.6)
    r.font.color.rgb = col
    r.font.bold = bold


# ==============================================================================
# BOTTOM BANNER (Key Takeaway)
# ==============================================================================
banner_top = top_base + left_card_h + 140000
banner_h = 420000
banner_w = 8412480

b_box = new_slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_col, banner_top, banner_w, banner_h)
b_box.fill.solid()
b_box.fill.fore_color.rgb = C_GREEN_HEADER
b_box.line.color.rgb = C_MINT_GREEN
b_box.line.width = Pt(1.5)
tf_b = b_box.text_frame
tf_b.margin_top = Pt(3)
tf_b.margin_bottom = Pt(2)
p = tf_b.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "⚡ Key Takeaway: "
r.font.bold = True
r.font.size = Pt(9.5)
r.font.color.rgb = C_GREEN_TEXT

r2 = p.add_run()
r2.text = "FastAPI & SQLAlchemy eliminate manual SQL BEGIN/COMMIT while guaranteeing 100% ACID compliance across all REST API endpoints."
r2.font.size = Pt(8.5)
r2.font.color.rgb = C_WHITE

# Update Slide Numbers across all slides
total_slides = len(prs.slides)
print(f"Total slides now: {total_slides}")

for s_idx, slide in enumerate(prs.slides):
    num_txt = f"{s_idx+1} / {total_slides}"
    # Search for slide number shape
    found_num = False
    for shape in slide.shapes:
        if shape.has_text_frame:
            t = shape.text_frame.text.strip()
            if "/" in t and len(t) <= 8 and any(c.isdigit() for c in t):
                shape.text_frame.text = num_txt
                for p in shape.text_frame.paragraphs:
                    p.alignment = PP_ALIGN.RIGHT
                    for r in p.runs:
                        r.font.size = Pt(10)
                        r.font.color.rgb = C_SLATE_500
                found_num = True
                break
    if not found_num and s_idx == 12: # Add to new slide
        num_box = slide.shapes.add_textbox(8046720, 4800600, 914400, 183000)
        tf = num_box.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run()
        r.text = num_txt
        r.font.size = Pt(10)
        r.font.color.rgb = C_SLATE_500

prs.save(pptx_path)
print(f"Successfully added FastAPI Transaction Slide and updated: {pptx_path}")
