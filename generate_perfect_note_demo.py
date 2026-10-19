import docx
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import sys

sys.stdout.reconfigure(encoding='utf-8')

doc_path = r"C:\Users\sangd\Downloads\note demo (1).docx"
doc = docx.Document()

# Page Setup: Standard A4 / Letter with 0.8 inch margins
sections = doc.sections
for section in sections:
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Color Palette Constants
HEX_NAVY = "0F172A"       # Deep Navy
HEX_BLUE = "0284C7"       # Accent Cyan Blue
HEX_SLATE_BG = "F1F5F9"   # Light Slate Box
HEX_CODE_BG = "0F172A"    # Dark Code BG
HEX_GREEN = "059669"      # Emerald Green
HEX_RED = "DC2626"        # Coral Red
HEX_BORDER = "CBD5E1"     # Slate Border

COLOR_TITLE = RGBColor(15, 23, 42)
COLOR_SUBTITLE = RGBColor(100, 116, 139)
COLOR_HEADING = RGBColor(2, 132, 199)
COLOR_BODY = RGBColor(30, 41, 59)
COLOR_ACTION = RGBColor(180, 83, 9)     # Amber/Orange for Action
COLOR_QUOTE = RGBColor(15, 23, 42)
COLOR_MUTED = RGBColor(100, 116, 139)

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_header(title, subtitle, meta):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title)
    r.font.name = "Arial"
    r.font.size = Pt(20)
    r.font.bold = True
    r.font.color.rgb = COLOR_TITLE
    
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(2)
    r2 = p2.add_run(subtitle)
    r2.font.name = "Arial"
    r2.font.size = Pt(12)
    r2.font.bold = True
    r2.font.color.rgb = COLOR_HEADING
    
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.paragraph_format.space_after = Pt(16)
    r3 = p3.add_run(meta)
    r3.font.name = "Calibri"
    r3.font.size = Pt(10)
    r3.font.color.rgb = COLOR_SUBTITLE

def add_slide_section(slide_num, total_slides, slide_title, timing, screen_context="SLIDE"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.9)
    
    cell = table.cell(0, 0)
    set_cell_background(cell, "0F172A")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    
    r_badge = p.add_run(f" SLIDE {slide_num}/{total_slides} ")
    r_badge.font.name = "Arial"
    r_badge.font.size = Pt(11)
    r_badge.font.bold = True
    r_badge.font.color.rgb = RGBColor(56, 189, 248) # Cyan
    
    r_title = p.add_run(f"  ·  {slide_title}  ")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(12)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(255, 255, 255)
    
    r_time = p.add_run(f"[{timing}]  [{screen_context}]")
    r_time.font.name = "Calibri"
    r_time.font.size = Pt(10)
    r_time.font.color.rgb = RGBColor(148, 163, 184)

def add_speech(speech_text, bold_keywords=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.2
    
    r_label = p.add_run("🎙️ LỜI THOẠI TRÌNH BÀY:\n")
    r_label.font.name = "Arial"
    r_label.font.size = Pt(10)
    r_label.font.bold = True
    r_label.font.color.rgb = COLOR_HEADING
    
    r_quote = p.add_run(speech_text)
    r_quote.font.name = "Calibri"
    r_quote.font.size = Pt(11)
    r_quote.font.color.rgb = COLOR_BODY

def add_action_box(action_title, steps):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.9)
    
    cell = table.cell(0, 0)
    set_cell_background(cell, "FEF3C7") # Warm Light Yellow
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    
    r = p.add_run(f"👉 {action_title}\n")
    r.font.name = "Arial"
    r.font.size = Pt(10.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(180, 83, 9)
    
    for s in steps:
        p_step = cell.add_paragraph()
        p_step.paragraph_format.space_before = Pt(2)
        p_step.paragraph_format.space_after = Pt(2)
        r_step = p_step.add_run(s)
        r_step.font.name = "Calibri"
        r_step.font.size = Pt(10)
        r_step.font.color.rgb = RGBColor(69, 26, 3)

def add_note_box(note_title, points):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.9)
    
    cell = table.cell(0, 0)
    set_cell_background(cell, "F0FDF4") # Light Green
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    
    r = p.add_run(f"💡 {note_title}\n")
    r.font.name = "Arial"
    r.font.size = Pt(10.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(22, 101, 52)
    
    for pt_item in points:
        p_pt = cell.add_paragraph()
        p_pt.paragraph_format.space_before = Pt(2)
        p_pt.paragraph_format.space_after = Pt(2)
        r_pt = p_pt.add_run(pt_item)
        r_pt.font.name = "Calibri"
        r_pt.font.size = Pt(10)
        r_pt.font.color.rgb = RGBColor(20, 83, 45)

def add_divider():
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run("────────────────────────────────────────────────────────────────────────")
    r.font.name = "Calibri"
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(203, 213, 225)

# ==============================================================================
# DOCUMENT GENERATION
# ==============================================================================

add_header(
    "TASK MANAGEMENT SYSTEM — DATABASE DESIGN",
    "BẢN GHI CHÚ THUYẾT TRÌNH & HƯỚNG DẪN DEMO PGADMIN ĐỒNG BỘ 15 SLIDES",
    "Presenter: Sang Duong  ·  Mentor: Anh Nhân Đoàn  ·  Supporter: Anh Thiên Lê  ·  Thời lượng: 15 Phút"
)

# ------------------------------------------------------------------------------
# SLIDE 1
# ------------------------------------------------------------------------------
add_slide_section(1, 15, "Opening (Giới Thiệu Dự Án)", "~30s", "SLIDE")
add_speech(
    "\"Xin chào anh Nhân, anh Thiên và mọi người. Em là Sang Duong. "
    "Hôm nay em xin phép trình bày về kết quả bài thực hành Database Design cho hệ thống Task Management System.\n\n"
    "Hệ thống này được thiết kế với mục tiêu xây dựng một cơ sở dữ liệu quan hệ hoàn chỉnh gồm 13 bảng trên PostgreSQL, "
    "đảm bảo tính toàn vẹn 3NF, tối ưu hiệu năng truy vấn với Indexing và bảo vệ toàn vẹn giao dịch với ACID Transactions.\""
)
add_note_box("Mục Tiêu Slide 1", [
    "• Tạo ấn tượng ban đầu tự tin, phong thái chuyên nghiệp, giới thiệu đúng chủ đề và cấu trúc bài báo cáo."
])
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 2
# ------------------------------------------------------------------------------
add_slide_section(2, 15, "Agenda (Nội Dung Buổi Báo Cáo)", "~30s", "SLIDE")
add_speech(
    "\"Nội dung báo cáo hôm nay gồm 5 phần chính tương ứng với toàn bộ quy trình thiết kế CSDL:\n"
    "1. Requirement Analysis: Phân tích nghiệp vụ và xác định Scope.\n"
    "2. Logical Design: Phân tích 5 Domain Zones, sơ đồ ERD 13 bảng và 6 quyết định thiết kế then chốt.\n"
    "3. Normalization: Phân tích trực quan 1NF ➔ 2NF ➔ 3NF và demo xử lý 3 dị thường dữ liệu trên pgAdmin.\n"
    "4. Physical Optimization & Indexing: Đo lường hiệu năng EXPLAIN ANALYZE trước và sau khi đánh B-Tree Index.\n"
    "5. Transaction Design: Thiết kế giao dịch nguyên tử (ACID) và bài học kỹ thuật rút ra.\""
)
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 3
# ------------------------------------------------------------------------------
add_slide_section(3, 15, "Database Design Workflow (Quy Trình 5 Bước)", "~45s", "SLIDE")
add_speech(
    "\"Trên màn hình là toàn bộ quy trình 5 bước em đã triển khai:\n"
    "• Bước 1 — Phân tích yêu cầu: Trích xuất các thực thể và mối quan hệ nghiệp vụ.\n"
    "• Bước 2 — Thiết kế Logic (ERD): Định nghĩa khóa chính, khóa ngoại và 6 quyết định kiến trúc.\n"
    "• Bước 3 — Chuẩn hóa 3NF: Kiểm chứng loại bỏ hoàn toàn dữ liệu dư thừa và dị thường.\n"
    "• Bước 4 — Tối ưu hóa vật lý: Thiết lập ràng buộc Constraints và 8 B-Tree Indexes.\n"
    "• Bước 5 — Giao dịch Transaction: Thiết kế các luồng Atomic để bảo vệ tính nhất quán dữ liệu.\""
)
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 4
# ------------------------------------------------------------------------------
add_slide_section(4, 15, "Domain Analysis (5 Phân Vùng Nghiệp Vụ)", "~1m", "SLIDE")
add_speech(
    "\"Em chia 13 bảng của hệ thống thành 5 phân vùng rõ ràng:\n"
    "1. CORE (Xương sống): Gồm `users`, `projects`, `tasks` — đây là các thực thể nghiệp vụ trung tâm.\n"
    "2. BRIDGE (Bảng cầu nối): Gồm `project_members` và `task_assignees` — xử lý quan hệ Nhiều-Nhiều.\n"
    "3. SUPPORTING (Tương tác): Gồm `task_comments` và `task_attachments` phục vụ thảo luận và đính kèm file.\n"
    "4. LOOKUP (Tham chiếu): Gồm `task_statuses`, `task_priorities`, `categories`, `project_statuses` — dùng chung toàn hệ thống.\n"
    "5. AUDIT (Kiểm toán & Thông báo): Gồm `activity_logs` và `notifications` lưu vết lịch sử và gửi thông báo.\""
)
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 5
# ------------------------------------------------------------------------------
add_slide_section(5, 15, "ERD & Relationships (Sơ Đồ Thực Thể Quan Hệ)", "~1m", "SLIDE")
add_speech(
    "\"Đây là sơ đồ ERD hoàn chỉnh gồm 13 bảng được vẽ trên dbdiagram.io.\n"
    "• Mối quan hệ cốt lõi: 1 User có thể sở hữu nhiều Projects (1-N), 1 Project chứa nhiều Tasks (1-N).\n"
    "• Xử lý Nhiều-Nhiều: Bảng `project_members` kết nối Users và Projects; bảng `task_assignees` kết nối Tasks và Users.\n"
    "• Luồng tương tác & kiểm toán: Mọi thay đổi trên Task đều kích hoạt ghi log vào `activity_logs` và tạo thông báo ở `notifications`.\""
)
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 6
# ------------------------------------------------------------------------------
add_slide_section(6, 15, "Design Decisions (Quyết Định Kiến Trúc Then Chốt)", "~1m", "SLIDE")
add_speech(
    "\"Ngay tại bước thiết kế ERD, em đã đưa ra 6 quyết định kiến trúc then chốt:\n"
    "1. UUID Primary Keys: Dùng UUID cho thực thể chính để chống dò quét ID trên API và sẵn sàng phân tán.\n"
    "2. Soft Delete: Dùng cờ `is_deleted` cho tasks và projects để có thể khôi phục và bảo vệ Audit Trail.\n"
    "3. Lookup Tables vs ENUM: Dùng bảng tra cứu để thêm trạng thái mới chỉ bằng lệnh INSERT mà không cần migration ALTER TYPE gây lock bảng.\n"
    "4. Timestamps: Mọi bảng đều có `created_at` và `updated_at` (TIMESTAMPTZ UTC) hỗ trợ Cache Invalidation.\n"
    "5. Member Role: Dùng cột `role VARCHAR` đơn giản trong `project_members` tránh over-engineering.\n"
    "6. Assigned_by: Lưu UUID người gán việc để truy vết rõ ràng trong Activity Logs.\""
)
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 7
# ------------------------------------------------------------------------------
add_slide_section(7, 15, "Normalization — What & Why (Lý Thuyết Trực Quan)", "~45s", "SLIDE")
add_speech(
    "\"Để chứng minh vì sao cần chuẩn hóa, trên slide này em trực quan hóa 3 chuẩn dữ liệu:\n"
    "• 1NF: Loại bỏ ô chứa danh sách gộp email ➔ Tách thành bảng `task_assignees` (mỗi ô 1 giá trị nguyên tử).\n"
    "• 2NF: Loại bỏ phụ thuộc một phần khi có Composite PK ➔ Nhấc `project_name` sang bảng riêng `projects`.\n"
    "• 3NF: Loại bỏ phụ thuộc bắc cầu qua status_id ➔ Nhấc `status_name` sang bảng tra cứu `task_statuses`.\""
)
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 8
# ------------------------------------------------------------------------------
add_slide_section(8, 15, "Normalization: Bad Design ➔ 3NF Case Study", "~2m", "SLIDE ➔ PGADMIN")
add_speech(
    "\"Trong thực tế, một kỹ sư thường vẽ 3NF ngay từ đầu. Nhưng trong bài training này, em cố tình mô phỏng bảng phẳng `tasks_flat` để mổ xẻ 4 thảm họa dữ liệu:\n"
    "1. Dư thừa dữ liệu: Task 1 lặp lại 3 dòng cho 3 người nhận việc kéo theo tên dự án và owner bị lặp 3 lần.\n"
    "2. Update Anomaly: Sửa tên dự án ở dòng Khôi mà quên sửa ở Kiệt và Tuyền ➔ Dữ liệu bị lệch nhau.\n"
    "3. Insert Anomaly: Dự án mới chưa có Task không thể thêm vào bảng vì `task_id` cấm NULL.\n"
    "4. Delete Anomaly: Xóa task duy nhất của Beta Project làm mất luôn sự tồn tại của dự án và anh Nam.\n\n"
    "Sau đây, em xin chuyển sang màn hình pgAdmin để chứng minh bằng SQL thực tế!\""
)
add_action_box("THAO TÁC PGADMIN — LIVE DEMO NORMALIZATION", [
    "1. Mở tab 01_bad_design.sql ➔ Bấm F5 ➔ Chỉ chuột vào 3 dòng đầu của Task 1 (tên Alpha Project và sang@gmail.com lặp lại).",
    "2. Mở tab 02_update_anomaly.sql ➔ Bấm F5 ➔ Chỉ vào kết quả: Dòng 1 mang tên 'Alpha Project v2', dòng 2-3 vẫn mang tên cũ.",
    "3. Mở tab 03_apply_1nf.sql ➔ Bấm F5 ➔ Show bảng task_assignees đạt chuẩn 1NF nguyên tử.",
    "4. Mở tab 04_apply_2nf.sql ➔ Bấm F5 ➔ Show bảng tasks JOIN projects đạt chuẩn 2NF.",
    "5. Mở tab 05_apply_3nf.sql ➔ Bấm F5 ➔ Show bảng tasks JOIN task_statuses đạt chuẩn 3NF sạch hoàn toàn."
])
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 9
# ------------------------------------------------------------------------------
add_slide_section(9, 15, "Constraints & Indexing (5 Ràng Buộc & 8 Chỉ Mục)", "~45s", "SLIDE")
add_speech(
    "\"Trở lại slide, em thiết lập hệ thống phòng ngự dữ liệu gồm 5 loại Constraints và 8 B-Tree Indexes:\n"
    "• Constraints: PK, FK (Restrict cho Project, Cascade cho Comments), Unique (email, username), Composite PK (chặn gán trùng), và Check constraint giới hạn giá trị hợp lệ.\n"
    "• 8 Indexes: Đều được tạo trên các cột Foreign Key (`project_id`, `status_id`, `user_id`) để triệt tiêu chi phí phép JOIN và tăng tốc độ lọc WHERE.\""
)
add_note_box("Mentor Q&A Trigger", [
    "• Mentor hỏi: 'Postgres tự tạo index nào và cái nào mình phải tự tạo?'",
    "• Trả lời: Postgres TỰ ĐỘNG tạo index cho PRIMARY KEY và UNIQUE. Còn FOREIGN KEY và các cột WHERE/ORDER BY mình BẮT BUỘC PHẢI TỰ TẠO bằng lệnh CREATE INDEX."
])
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 10
# ------------------------------------------------------------------------------
add_slide_section(10, 15, "Indexing: Seq Scan vs Index Scan (Cơ Chế Đĩa)", "~45s", "SLIDE")
add_speech(
    "\"Trên sơ đồ kiến trúc của Crunchy Data này:\n"
    "• Bên trái — Sequential Scan: PostgreSQL phải quét tuần tự (Streaming I/O) qua toàn bộ các Table Pages trên đĩa cứng từ đầu đến cuối ➔ Tốn chi phí Cost 250 và đọc qua hàng trăm dòng rác.\n"
    "• Bên phải — Index Scan: PostgreSQL đi qua cấu trúc cây B-Tree Index, sau đó nhảy thẳng (Random Fetch) đến đúng các block đĩa chứa dòng dữ liệu cần tìm ➔ Chi phí giảm xuống 8.3 và không loại bỏ dòng rác nào.\""
)
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 11
# ------------------------------------------------------------------------------
add_slide_section(11, 15, "EXPLAIN ANALYZE — Before vs. After Index", "~1.5m", "SLIDE ➔ PGADMIN")
add_speech(
    "\"Để chứng minh sự khác biệt này, em sẽ chạy EXPLAIN ANALYZE trước và sau khi đánh index `idx_tasks_project_id` trên pgAdmin!\""
)
add_action_box("THAO TÁC PGADMIN — LIVE DEMO EXPLAIN ANALYZE", [
    "1. Mở tab 06_explain_before_index.sql ➔ Bấm F5.",
    "   • Điểm nhấn: Chỉ vào chữ 'Seq Scan on tasks' và dòng 'Rows Removed by Filter: 673' (quét qua 673 dòng rác).",
    "2. Mở tab 07_create_index.sql ➔ Bấm F5 ➔ Tạo index idx_tasks_project_id.",
    "3. Mở tab 08_explain_after_index.sql ➔ Bấm F5.",
    "   • Điểm nhấn: Chỉ vào chữ 'Bitmap Index Scan on idx_tasks_project_id', dòng 'Index Searches: 1', và biến mất hoàn toàn dòng Rows Removed by Filter!"
])
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 12
# ------------------------------------------------------------------------------
add_slide_section(12, 15, "Transaction Design (3 Luồng Giao Dịch Nguyên Tử)", "~45s", "SLIDE")
add_speech(
    "\"Về đường ghi, em thiết kế 3 chuỗi giao dịch nguyên tử:\n"
    "• Create Task: BEGIN ➔ INSERT tasks ➔ INSERT activity_logs ➔ COMMIT.\n"
    "• Assign Task (Trọng tâm Demo): BEGIN ➔ INSERT task_assignees ➔ INSERT activity_logs ➔ INSERT notifications ➔ COMMIT.\n"
    "• Change Status: BEGIN ➔ UPDATE tasks ➔ INSERT activity_logs ➔ INSERT notifications ➔ COMMIT.\n\n"
    "Tất cả đều tuân thủ nguyên lý ACID: Nếu bất kỳ bước nào thất bại, toàn bộ giao dịch sẽ ROLLBACK về trạng thái ban đầu.\""
)
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 13
# ------------------------------------------------------------------------------
add_slide_section(13, 15, "Why Do We Need Transactions? (Demo 3 Kịch Bản)", "~2m", "SLIDE ➔ PGADMIN")
add_speech(
    "\"Em xin phân tích 3 kịch bản cụ thể của hành động Assign Task:\n"
    "• Scenario A (Không dùng TX): Lệnh 2 gặp lỗi/sập server ➔ Lệnh 3 không chạy ➔ Dữ liệu bất nhất quán (Assignee có nhưng log/notif mất).\n"
    "• Scenario B (Có TX thành công): Cả 3 bảng cùng nhận dữ liệu đồng bộ khi COMMIT.\n"
    "• Scenario C (Có TX gặp lỗi Rollback): Bước tạo notification vi phạm Check constraint ➔ Database tự động ROLLBACK toàn bộ, bảo vệ tính toàn vẹn.\n\n"
    "Sau đây em xin demo trực tiếp 3 kịch bản này trên pgAdmin!\""
)
add_action_box("THAO TÁC PGADMIN — LIVE DEMO TRANSACTIONS", [
    "1. Mở tab 09_tx_check_initial.sql ➔ Bấm F5 ➔ Kiểm tra Task 3 ban đầu chưa có assignee.",
    "2. Mở tab 10_tx_success.sql ➔ Bấm F5 ➔ Chạy Scenario B thành công (COMMIT).",
    "3. Mở tab 11_tx_verify_and_cleanup.sql ➔ Bấm F5 ➔ Show cả 3 bảng đều có data, sau đó dọn dẹp data test.",
    "4. Mở tab 12_tx_fail_rollback.sql ➔ Bấm F5 ➔ Show lỗi đỏ CHECK constraint violation ở lệnh notification.",
    "5. Mở tab 13_tx_verify_rollback.sql ➔ Bấm F5 ➔ Nhấn mạnh kết quả 'Total rows: 0' — bảng sạch trơn, chứng minh tính chất Atomicity!"
])
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 14
# ------------------------------------------------------------------------------
add_slide_section(14, 15, "Issues & Challenges (4 Thách Thức Kỹ Thuật Đã Vượt Qua)", "~1m", "SLIDE")
add_speech(
    "\"Trong quá trình thực hành, em đã đúc kết được 4 bài học kỹ thuật quan trọng:\n"
    "1. Primary Key Type: Chấp nhận trade-off 16 bytes của UUID để đổi lấy tính bảo mật chống duyệt API và sẵn sàng phân tán.\n"
    "2. ENUM vs Lookup Tables: Dùng Lookup Tables để tránh việc phải chạy migration ALTER TYPE gây lock bảng khi thêm trạng thái mới.\n"
    "3. Fooled by Buffer Cache: Ở máy local, 1,000 dòng nằm trọn trong RAM nên thời gian chạy giữa Seq Scan và Index Scan đều < 0.1ms. Bài học rút ra là phải đánh giá dựa trên Plan Type và Rows Removed (985 ➔ 0) thay vì thời gian local.\n"
    "4. Soft Delete vs Hard Delete: Chọn Soft Delete với cờ `is_deleted` để bảo vệ dữ liệu lịch sử phục vụ Audit Trail thay vì xóa cứng CASCADE.\""
)
add_divider()

# ------------------------------------------------------------------------------
# SLIDE 15
# ------------------------------------------------------------------------------
add_slide_section(15, 15, "Q & A (Tổng Kết & Thảo Luận)", "~1m", "SLIDE")
add_speech(
    "\"Đó là toàn bộ nội dung bài thực hành Database Design của em từ phân tích yêu cầu, chuẩn hóa 3NF, đánh Index cho đến bảo vệ giao dịch Transaction.\n\n"
    "Em xin chân thành cảm ơn anh Nhân và anh Thiên đã lắng nghe và hướng dẫn em trong suốt buổi training. Em rất mong nhận được những câu hỏi và ý kiến đóng góp từ các anh ạ!\""
)
add_note_box("TOP 3 CÂU HỎI MENTOR HAY HỎI NHẤT & CÂU TRẢ LỜI NHANH", [
    "1. Q: 'Trong thực tế dự án có ai làm Bad Design rồi sửa từng bước 1NF-2NF-3NF không?'\n   ➔ A: Dạ không, thực tế senior sẽ vẽ 3NF trực tiếp. Trong bài training này em cố tình làm bad design để mổ xẻ 3 dị thường và chứng minh bản chất bằng SQL.",
    "2. Q: 'PostgreSQL tự tạo index nào và cái nào mình phải tự tạo?'\n   ➔ A: Postgres TỰ ĐỘNG tạo index cho PRIMARY KEY và UNIQUE. Còn FOREIGN KEY và các cột WHERE/ORDER BY mình BẮT BUỘC PHẢI TỰ TẠO bằng lệnh CREATE INDEX.",
    "3. Q: 'FastAPI hỗ trợ những loại transaction nào?'\n   ➔ A: Có 3 loại chính: Per-Request qua Depends(get_db), Explicit qua session.begin(), và Nested Savepoints qua session.begin_nested()."
])

doc.save(doc_path)
print(f"Successfully generated and formatted: {doc_path}")

# Also save to note demo.docx as backup
backup_path = r"C:\Users\sangd\Downloads\note demo.docx"
doc.save(backup_path)
print(f"Successfully saved backup to: {backup_path}")
