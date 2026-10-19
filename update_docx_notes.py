import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = docx.Document()

# Page Margins
sections = doc.sections
for section in sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Title
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("KỊCH BẢN THUYẾT TRÌNH 15 PHÚT (SPEAKER NOTES)")
run.font.name = "Calibri"
run.font.size = Pt(20)
run.font.bold = True
run.font.color.rgb = RGBColor(15, 23, 42)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_sub = sub.add_run("Báo Cáo Tiến Độ Training & Thiết Kế CSDL Task Management System\nPresenter: Sang Duong | Mentor: Anh Nhân Đoàn | Supporter: Anh Thiên Lê\n")
run_sub.font.name = "Calibri"
run_sub.font.size = Pt(11)
run_sub.font.italic = True
run_sub.font.color.rgb = RGBColor(100, 116, 139)

def add_slide_note(doc, slide_title, duration, speech):
    h = doc.add_paragraph()
    r = h.add_run(f"{slide_title} ({duration})")
    r.font.name = "Calibri"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = RGBColor(30, 58, 138)
    
    p = doc.add_paragraph()
    r_sp = p.add_run(f"🎙️ Kịch bản nói & Thao tác Demo:\n{speech}")
    r_sp.font.name = "Calibri"
    r_sp.font.size = Pt(10.5)
    r_sp.font.color.rgb = RGBColor(51, 65, 85)
    p.paragraph_format.space_after = Pt(12)

# Overview Table
doc.add_heading("⏱️ Phân Bổ Thời Gian 15 Phút Overview", level=2)
p_time = doc.add_paragraph()
p_time.add_run("• 00:00 – 01:30 (1.5 phút): Mở đầu & Báo cáo Tiến độ Lộ trình Học tập (Slide 1 – 2)\n"
               "• 01:30 – 04:00 (2.5 phút): Workflow, Phân tích Miền & Sơ đồ ERD (Slide 3 – 5)\n"
               "• 04:00 – 07:00 (3.0 phút): Chuẩn hóa 3NF & Live Demo Bad Design -> 3NF (Slide 6)\n"
               "• 07:00 – 10:30 (3.5 phút): Constraints, Indexes & Demo EXPLAIN ANALYZE (Slide 7 – 11)\n"
               "• 10:30 – 13:00 (2.5 phút): Transaction Design & Demo 3 Scenarios (Slide 12 – 14)\n"
               "• 13:00 – 14:30 (1.5 phút): Minh chứng Triển khai Backend REST API (Slide 15)\n"
               "• 14:30 – 15:00 (0.5 phút): Kết luận & Chuyển sang Q&A (Slide 16)\n")

doc.add_heading("🎙️ Chi Tiết Lời Thoại & Kịch Bản Cho Từng Slide", level=2)

slide6_content = (
    "\"Trước khi vào schema thực tế, em giải thích nhanh 3 Normal Forms là gì và tại sao cần chúng.\"\n"
    "\"1NF — mỗi cell chỉ chứa một giá trị duy nhất, không được gộp nhiều thứ vào một chỗ — ví dụ không được chứa 'tuyen@gmail.com, huy@gmail.com' trong cùng 1 cột. Trong schema của em: task_assignees tách ra mỗi row một assignee.\"\n"
    "\"2NF — mọi cột phải phụ thuộc vào TOÀN BỘ primary key, chỉ có vấn đề khi PK là composite key. Trong schema của em: project_name được tách khỏi tasks vì chỉ phụ thuộc project_id, chuyển sang bảng projects.\"\n"
    "\"3NF — không được có transitive dependency, mọi cột phải phụ thuộc trực tiếp vào primary key. Trong schema của em: status_name được tách khỏi tasks, chuyển sang task_statuses lookup table.\"\n\n"
    "\"Để minh họa lý do cần normalize, em show một thiết kế flat — tasks_flat gộp tất cả vào một bảng.\"\n"
    "\"4 vấn đề chính: Data Redundancy — project_name bị lặp lại cho mỗi assignee row. Update Anomaly — đổi tên project phải update N rows. Insert Anomaly — không thể tạo project mới nếu chưa có task. Delete Anomaly — xóa task cuối cùng làm mất luôn thông tin project.\"\n\n"
    "💻 DEMO TRÊN PGADMIN:\n"
    "Block 1 — Show Bad Design:\n"
    "SELECT * FROM tasks_flat ORDER BY task_id, assignee_email;\n"
    "Giải thích: 'Ở đây task_id = 1 xuất hiện 3 lần vì task có 3 assignees. Đồng thời project_name và owner_email cũng bị lặp lại trên cả 3 rows. Đây chính là data redundancy.'\n\n"
    "Block 2 — Update Anomaly:\n"
    "UPDATE tasks_flat SET project_name = 'Alpha Project v2' WHERE task_id = 1 AND assignee_email = 'tuyen@gmail.com';\n"
    "SELECT * FROM tasks_flat WHERE task_id = 1;\n"
    "Giải thích: 'Chỉ một row được update thành Alpha Project v2 trong khi các row còn lại vẫn là Alpha Project -> Update Anomaly.'\n"
    "(Sau đó chạy âm thầm 02b_reset_tasks_flat.sql để đưa dữ liệu về trạng thái sạch, không nói với mentor.)\n\n"
    "Apply 1NF -> 2NF -> 3NF:\n"
    "• 1NF (Atomic): SELECT t.title AS task, u.full_name AS assignee FROM task_assignees ta JOIN tasks t ON t.task_id = ta.task_id JOIN users u ON u.user_id = ta.user_id ORDER BY t.title, u.full_name;\n"
    "• 2NF (No partial dependency): SELECT t.title, p.project_name, u.full_name AS owner FROM tasks t JOIN projects p ON p.project_id = t.project_id JOIN users u ON u.user_id = p.owner_id WHERE t.is_deleted = false LIMIT 10;\n"
    "• 3NF (No transitive dependency): SELECT t.title, ts.name AS status, tp.name AS priority FROM tasks t JOIN task_statuses ts ON ts.status_id = t.status_id LEFT JOIN task_priorities tp ON tp.priority_id = t.priority_id WHERE t.is_deleted = false LIMIT 10;\n\n"
    "💡 Mentor Triggers:\n"
    "- 2NF vs 3NF: 2NF loại bỏ partial dependency (composite key), 3NF loại bỏ transitive dependency (A -> B -> C).\n"
    "- BCNF: Đạt BCNF vì không có overlapping candidate keys.\n"
    "- 4NF: Không cần 4NF vì many-to-many đã giải quyết bằng bridge tables."
)

slides_data = [
    ("Slide 1: Opening", "0.5 phút",
     "\"Xin chào mọi người, em là Sang Duong. Hôm nay em present về Database Design practice — thiết kế database cho một Task Management System. Và mentor của em là anh Nhân Đoàn và supporter là anh Thiên Lê.\""),
    ("Slide 2: Training Roadmap & Progress Status", "1.0 phút",
     "\"Trước khi đi vào kỹ thuật, em xin cập nhật nhanh tiến độ: Phase 1 Database Design và đọc sách System Design Interview của Alex Xu 16 chương đã hoàn thành 100%. Khóa Dometrain System Design đã xong 6/8 chương (xin gia hạn 2 ngày); khóa Python Interview Questions xin gia hạn 1 ngày. Toàn bộ kiến thức này đã được em áp dụng trực tiếp để xây dựng backend REST API hoàn chỉnh.\""),
    ("Slide 3: Overview, Scope & Workflow", "1.0 phút",
     "\"Trước khi thiết kế schema, em xây dựng Requirement & Domain Analysis Document xác định scope, workflows, business rules, entities và relationships. Hệ thống đi qua 5 giai đoạn: Requirement Analysis, Logical Design, Normalization, Physical Design, và Optimization & Transactions. Scope gồm 5 nhóm chức năng trên schema 13 bảng chuẩn 3NF.\""),
    ("Slide 4 & 5: Domain Analysis & ERD Walkthrough", "1.5 phút",
     "\"Hệ thống gồm 13 bảng chia thành 5 nhóm: Core (users, projects, tasks), Bridge (project_members, task_assignees với Composite PK), Supporting (comments, attachments), Lookup (statuses, priorities, categories - dùng bảng tra cứu thay ENUM để tránh ALTER TABLE lock DB) và Audit (activity_logs, notifications).\""),
    ("Slide 6: Normalization & Live Demo", "3.0 phút", slide6_content),
    ("Slide 7 - 11: Constraints, Indexing & EXPLAIN ANALYZE", "3.5 phút",
     "\"Về toàn vẹn, em dùng ON DELETE RESTRICT cho Project Owner và ON DELETE CASCADE cho Assignees/Comments. Về hiệu năng, em đặt 8 chỉ mục B-Tree.\nDemo EXPLAIN ANALYZE: Trước khi đánh Index trên project_id, query mất Cost 250 và loại bỏ 985 dòng rác. Sau khi tạo Index idx_tasks_project_id, Cost giảm xuống 8.3, thời gian chạy nhanh gấp 30 lần (<0.1ms).\""),
    ("Slide 12 - 14: Transaction Design & Decisions", "2.5 phút",
     "\"Nghiệp vụ Assign Task gồm: Ghi assignee -> Ghi log -> Tạo notification. Em demo 3 scenarios: Scenario A (không dùng TX gây Inconsistent data), Scenario B (dùng TX thành công), Scenario C (gặp lỗi tự động ROLLBACK đảm bảo Atomicity). Quyết định: UUID cho bảo mật API/phân tán, Soft Delete cho audit log, Lookup Tables thay ENUM.\""),
    ("Slide 15: Backend REST API Architecture", "1.5 phút",
     "\"Toàn bộ thiết kế CSDL trên đã được em hiện thực hóa thành dự án Task Management API với FastAPI, SQLAlchemy 2.x async, PostgreSQL (asyncpg), Alembic, OAuth2 JWT, Pytest test suite và Swagger UI tại /docs.\""),
    ("Slide 16: Q & A", "0.5 phút",
     "\"Em xin chân thành cảm ơn anh Nhân, anh Thiên và mọi người đã lắng nghe. Em rất mong nhận được những góp ý và câu hỏi từ anh/chị!\"")
]

for s in slides_data:
    add_slide_note(doc, s[0], s[1], s[2])

doc.save(r"C:\Users\sangd\Downloads\TMS_SpeakerNotes_15min_v4.docx")
print("Speaker notes docx updated successfully!")
