import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = docx.Document()

# Set Margins
for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Document Header
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_title = title_p.add_run("TASK MANAGEMENT SYSTEM — DATABASE DESIGN\nSPEAKER NOTES & LIVE DEMO GUIDE")
r_title.font.name = "Calibri"
r_title.font.size = Pt(18)
r_title.font.bold = True
r_title.font.color.rgb = RGBColor(15, 23, 42)

sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_sub = sub_p.add_run("Presenter: Sang Duong  ·  Mentor: Nhan Doan  ·  Supporter: Thien Le  ·  June 2026\n(Khớp chuẩn 100% với slide [SangDuong] Database Training - 2026 (4).pptx)\n")
r_sub.font.name = "Calibri"
r_sub.font.size = Pt(10.5)
r_sub.font.italic = True
r_sub.font.color.rgb = RGBColor(100, 116, 139)

def add_slide_section(doc, slide_title, timing, speech, actions=None, mentor_tips=None):
    h = doc.add_paragraph()
    r = h.add_run(f"📌 {slide_title}  [{timing}]")
    r.font.name = "Calibri"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = RGBColor(30, 58, 138)
    
    # Speech
    p_sp = doc.add_paragraph()
    r_sp_lbl = p_sp.add_run("🎙️ Lời thoại thuyết trình:\n")
    r_sp_lbl.font.bold = True
    r_sp_lbl.font.color.rgb = RGBColor(15, 23, 42)
    r_sp = p_sp.add_run(speech)
    r_sp.font.color.rgb = RGBColor(51, 65, 85)
    
    # Live Actions
    if actions:
        p_act = doc.add_paragraph()
        r_act_lbl = p_act.add_run("💻 Thao tác Demo (pgAdmin / Slide):\n")
        r_act_lbl.font.bold = True
        r_act_lbl.font.color.rgb = RGBColor(180, 83, 9)
        r_act = p_act.add_run(actions)
        r_act.font.color.rgb = RGBColor(55, 65, 81)
        r_act.font.name = "Consolas"
        r_act.font.size = Pt(9.5)
        
    # Mentor Tips
    if mentor_tips:
        p_tip = doc.add_paragraph()
        r_tip_lbl = p_tip.add_run("💡 Mentor Triggers & Lưu ý:\n")
        r_tip_lbl.font.bold = True
        r_tip_lbl.font.color.rgb = RGBColor(21, 128, 61)
        r_tip = p_tip.add_run(mentor_tips)
        r_tip.font.color.rgb = RGBColor(55, 65, 81)
        r_tip.font.italic = True
        
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

# -------------------------------------------------------------
# SLIDE 1
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 1 — Opening (Cover)",
    "00:00 → 00:30 (30s)",
    "\"Xin chào mọi người, em là Sang Duong. Hôm nay em xin trình bày về Database Design Practice — thiết kế cơ sở dữ liệu cho một Task Management System. Mentor hướng dẫn của em là anh Nhân Đoàn và supporter là anh Thiên Lê.\"",
    None,
    "Nói rõ ràng, tự tin, mắt nhìn thẳng vào mentor/hội đồng."
)

# -------------------------------------------------------------
# SLIDE 2
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 2 — Agenda",
    "00:30 → 01:00 (30s)",
    "\"Nội dung bài báo cáo hôm nay gồm 8 phần chính:\n"
    "1. Overview & Scope — Xác định phạm vi hệ thống.\n"
    "2. Domain Analysis — Phân tích thực thể và nghiệp vụ.\n"
    "3. ERD & Relationships — Sơ đồ quan hệ thực thể.\n"
    "4. Normalization — Chuẩn hóa dữ liệu từ Bad design lên 3NF.\n"
    "5. Constraints & Indexing — Toàn vẹn dữ liệu và tối ưu chỉ mục.\n"
    "6. Transaction Design — Đảm bảo tính nguyên tố ACID.\n"
    "7. Design Decisions — Các quyết định kỹ thuật cốt lõi.\n"
    "8. Q & A — Thảo luận và giải đáp thắc mắc.\"",
    None,
    "Nói ngắn gọn mục tiêu, lướt nhanh để dành thời gian cho các phần kỹ thuật sâu."
)

# -------------------------------------------------------------
# SLIDE 3
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 3 — Database Design Workflow",
    "01:00 → 02:00 (1 min)",
    "\"Trước khi bắt tay vào thiết kế schema, em bắt đầu bằng việc xây dựng tài liệu Requirement & Domain Analysis Document để xác định scope, workflows, business rules, entities và relationships.\n"
    "Quy trình thiết kế CSDL của em đi qua 5 giai đoạn có vòng lặp kiểm tra chặt chẽ:\n"
    "• Bước 1 - Requirement Analysis: Xác định rõ scope và nghiệp vụ.\n"
    "• Bước 2 - Logical Design: Định nghĩa Entity, Attributes và vẽ ERD.\n"
    "• Bước 3 - Normalization: Chuẩn hóa 3NF và có bước kiểm tra 'Normalized?' để quay lại nếu chưa đạt.\n"
    "• Bước 4 - Physical Design: Viết DDL PostgreSQL, gán Constraints và Seed dữ liệu thử nghiệm.\n"
    "• Bước 5 - Optimization & Transactions: Viết query, kiểm tra 'Performance OK?' để quyết định thêm Index và thiết kế Transaction.\"",
    None,
    "Nhấn mạnh tính kỹ thuật ở các feedback loops (Normalized? và Performance OK?)."
)

# -------------------------------------------------------------
# SLIDE 4
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 4 — Domain Analysis (5 Nhóm Thực Thể)",
    "02:00 → 03:00 (1 min)",
    "\"Hệ thống gồm 13 bảng được em phân tích và chia thành 5 nhóm chức năng rõ rệt:\n"
    "• Core Zone (users, projects, tasks): Xương sống của hệ thống.\n"
    "• Bridge Zone (project_members, task_assignees): Xử lý quan hệ Nhiều-Nhiều, dùng Composite Primary Key để ngăn trùng lặp bản ghi ngay tầng database.\n"
    "• Supporting Zone (task_comments, task_attachments): Lưu tương tác và tài liệu đính kèm liên kết vào Task.\n"
    "• Lookup Zone (task_statuses, task_priorities, categories, project_statuses): Dùng bảng tra cứu riêng thay cho kiểu ENUM để tránh ALTER TABLE lock DB khi thêm mới trạng thái.\n"
    "• Audit Zone (activity_logs, notifications): Lưu vết lịch sử và thông báo người dùng.\"",
    None,
    "💡 Mentor Trigger:\n- Tại sao tách project_statuses và task_statuses? -> Vì trạng thái dự án (Planning, Active, Completed) khác hoàn toàn với trạng thái task (Todo, In Progress, Done).\n- Categories là Global hay Per-project? -> Hiện tại là Global. Nếu cần per-project sẽ thêm FK project_id."
)

# -------------------------------------------------------------
# SLIDE 5
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 5 — ERD & Relationships",
    "03:00 → 04:00 (1 min)",
    "\"Về mối quan hệ trong sơ đồ ERD:\n"
    "• Users 1 → N Projects (qua owner_id): 1 User sở hữu nhiều Project.\n"
    "• Projects 1 → N Tasks (qua project_id): 1 Project chứa nhiều Tasks.\n"
    "• Tasks 1 → N Task Comments (qua task_id): 1 Task có nhiều Comments.\n"
    "• Users M ↔ N Projects (qua bridge table project_members): User là thành viên nhiều dự án.\n"
    "• Users M ↔ N Tasks (qua bridge table task_assignees): Phân công nhiều người làm 1 task.\n"
    "Điểm cốt lõi: Sử dụng UUID cho Primary Key của các bảng chính để bảo mật API và an toàn cho hệ thống phân tán.\"",
    None,
    "💡 Mentor Trigger:\n- Tại sao dùng UUID thay vì SERIAL? -> UUID tránh bị lộ tuần tự ID qua API (chống Enumeration attack) và an toàn khi scale/sharding, chấp nhận trade-off lưu 16 bytes."
)

# -------------------------------------------------------------
# SLIDE 6
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 6 — Normalization — What & Why",
    "04:00 → 05:00 (1 min)",
    "\"Trước khi vào schema thực tế, em giải thích nhanh 3 Normal Forms là gì và tại sao cần chúng:\n"
    "• 1NF (First Normal Form): Mỗi cell chỉ chứa một giá trị nguyên tố duy nhất, không được gộp nhiều giá trị vào một ô như 'tuyen@gmail.com, huy@gmail.com'. Trong schema: em tách bảng task_assignees — mỗi dòng 1 assignee.\n"
    "• 2NF (Second Normal Form): Mọi cột phải phụ thuộc vào TOÀN BỘ Primary Key (loại bỏ partial dependency khi có Composite Key). Trong schema: project_name được tách khỏi tasks đưa sang bảng projects.\n"
    "• 3NF (Third Normal Form): Không được có transitive dependency (A -> B -> C). Mọi cột phải phụ thuộc trực tiếp vào Primary Key. Trong schema: status_name được tách khỏi tasks đưa sang bảng tra cứu task_statuses.\"",
    None,
    "💡 Mentor Trigger:\n- Khác nhau 2NF và 3NF? -> 2NF loại bỏ phụ thuộc một phần trên composite key; 3NF loại bỏ phụ thuộc bắc cầu giữa các cột không khóa.\n- Schema có đạt BCNF không? -> Có, vì không có overlapping candidate keys."
)

# -------------------------------------------------------------
# SLIDE 7
# -------------------------------------------------------------
slide7_speech = (
    "\"Để minh họa lý do cần normalize, em show một thiết kế flat — tasks_flat gộp tất cả vào một bảng.\n"
    "4 vấn đề chính của bảng phẳng: Data Redundancy, Update Anomaly, Insert Anomaly và Delete Anomaly.\n\n"
    "Áp dụng 1NF -> 2NF -> 3NF:\n"
    "• 1NF: Tách assignees sang task_assignees.\n"
    "• 2NF: Tách projects ra bảng riêng, không còn project_name trong tasks.\n"
    "• 3NF: Tách task_statuses lookup, status quản lý qua FK không còn text tự do.\n"
    "Sau đây em xin chuyển sang pgAdmin để demo trực tiếp trên dữ liệu thật.\""
)

slide7_actions = (
    "-- 1. SHOW BAD DESIGN (Data Redundancy):\n"
    "SELECT * FROM tasks_flat ORDER BY task_id, assignee_email;\n"
    "-> Giải thích: 'Task 1 xuất hiện 3 lần vì có 3 assignees, project_name và owner_email bị lặp lại 3 lần.'\n\n"
    "-- 2. DEMO UPDATE ANOMALY:\n"
    "UPDATE tasks_flat SET project_name = 'Alpha Project v2' WHERE task_id = 1 AND assignee_email = 'tuyen@gmail.com';\n"
    "SELECT * FROM tasks_flat WHERE task_id = 1;\n"
    "-> Giải thích: 'Chỉ 1 dòng đổi thành Alpha Project v2, 2 dòng kia giữ nguyên -> Dữ liệu bất nhất quán.'\n"
    "(Chạy ngầm: 02b_reset_tasks_flat.sql để reset dữ liệu sạch).\n\n"
    "-- 3. SHOW ĐẠT 1NF, 2NF, 3NF:\n"
    "-- 1NF:\n"
    "SELECT t.title AS task, u.full_name AS assignee FROM task_assignees ta JOIN tasks t ON t.task_id = ta.task_id JOIN users u ON u.user_id = ta.user_id ORDER BY t.title, u.full_name;\n"
    "-- 2NF:\n"
    "SELECT t.title, p.project_name, u.full_name AS owner FROM tasks t JOIN projects p ON p.project_id = t.project_id JOIN users u ON u.user_id = p.owner_id WHERE t.is_deleted = false LIMIT 10;\n"
    "-- 3NF:\n"
    "SELECT t.title, ts.name AS status, tp.name AS priority FROM tasks t JOIN task_statuses ts ON ts.status_id = t.status_id LEFT JOIN task_priorities tp ON tp.priority_id = t.priority_id WHERE t.is_deleted = false LIMIT 10;"
)

add_slide_section(
    doc,
    "Slide 7 — Normalization: Bad Design → 3NF (Live Demo)",
    "05:00 → 07:00 (2 mins)",
    slide7_speech,
    slide7_actions,
    "Demo dứt khoát trên pgAdmin, chỉ rõ 3 dòng lặp lại và sự bất nhất quán của Update Anomaly."
)

# -------------------------------------------------------------
# SLIDE 8
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 8 — Constraints & Indexing",
    "07:00 → 07:45 (45s)",
    "\"Về Ràng buộc & Chỉ mục trong hệ thống:\n"
    "• Constraints: Em áp dụng 5 loại: PRIMARY KEY, FOREIGN KEY (RESTRICT cho owner, CASCADE cho comments/assignees), UNIQUE trên email/username, COMPOSITE PK trên bảng trung gian, và CHECK constraints cho role, action, type.\n"
    "• Indexing: Em tạo 8 B-Tree Indexes trên các cột Foreign Key và các cột xuất hiện nhiều trong mệnh đề JOIN/WHERE (như project_id, status_id, user_id, task_id).\n"
    "Trước khi demo, em giải thích nhanh: Không có index, PostgreSQL phải Sequential scan toàn bộ bảng. Có index, PostgreSQL dùng B-Tree nhảy trực tiếp đến dòng cần tìm.\"",
    None,
    "💡 Mentor Trigger:\n- Tại sao PostgreSQL không tự động index FK? -> Vì Postgres chỉ tự động index PK và Unique. FK phải tự tạo index nếu có nhu cầu JOIN/Filter thường xuyên.\n- Tại sao không index tất cả? -> Index tăng tốc SELECT nhưng làm chậm INSERT/UPDATE và tốn dung lượng RAM/Disk."
)

# -------------------------------------------------------------
# SLIDE 9
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 9 — Indexing: Seq Scan vs Index Scan",
    "07:45 → 08:30 (45s)",
    "\"Em so sánh trực quan cách PostgreSQL đọc bảng tasks ~1000 dòng với điều kiện WHERE project_id = ... :\n"
    "• Bên trái (Without index — Seq Scan): Quét tuần tự toàn bộ bảng. Chi phí (Cost) rất cao từ 0..250, loại bỏ 985 dòng rác, thời gian thực thi khoảng 12ms.\n"
    "• Bên phải (With index — Index Scan): Đi theo cây B-Tree nhảy thẳng tới 15 dòng cần tìm. Cost giảm xuống 0.28..8.30, 0 dòng rác bị loại bỏ, thời gian dưới 1ms.\n"
    "Sau đây em xin demo EXPLAIN ANALYZE thực tế trong pgAdmin.\"",
    None,
    "Nhấn mạnh sự chênh lệch: Cost 250 -> 8.3 và Rows removed by filter = 0."
)

# -------------------------------------------------------------
# SLIDE 10
# -------------------------------------------------------------
slide10_actions = (
    "-- Bước 1: BEFORE Index (Quan sát Seq Scan & Cost cao):\n"
    "EXPLAIN ANALYZE SELECT * FROM tasks WHERE project_id = '10000000-0000-0000-0000-000000000001';\n"
    "-> Output: Seq Scan on tasks (cost=0.00..250.00 rows=15), Rows Removed by Filter: 985\n\n"
    "-- Bước 2: CREATE INDEX:\n"
    "CREATE INDEX idx_tasks_project_id ON tasks(project_id);\n\n"
    "-- Bước 3: AFTER Index (Quan sát Index Scan):\n"
    "EXPLAIN ANALYZE SELECT * FROM tasks WHERE project_id = '10000000-0000-0000-0000-000000000001';\n"
    "-> Output: Index Scan using idx_tasks_project_id (cost=0.28..8.30 rows=15), Execution: 0.08ms"
)

add_slide_section(
    doc,
    "Slide 10 — EXPLAIN ANALYZE — Before vs. After Index (Demo)",
    "08:30 → 10:00 (1.5 mins)",
    "\"Em xin demo EXPLAIN ANALYZE để chứng minh hiệu năng thực tế:\n"
    "• Trước khi có index: PostgreSQL thực hiện Seq Scan, cost 250, loại bỏ 985 dòng rác.\n"
    "• Sau khi tạo index idx_tasks_project_id: Query chuyển ngay sang Index Scan, cost giảm xuống 8.3, thời gian chạy nhanh hơn 30 lần (dưới 0.1ms).\"",
    slide10_actions,
    "💡 Mentor Trigger:\n- EXPLAIN vs EXPLAIN ANALYZE? -> EXPLAIN chỉ show kế hoạch ước tính. EXPLAIN ANALYZE thực sự chạy query và đo thời gian thực tế."
)

# -------------------------------------------------------------
# SLIDE 11
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 11 — Transaction Design",
    "10:00 → 11:00 (1 min)",
    "\"Sau khi tối ưu phần đọc, em thiết kế Transaction để đảm bảo tính toàn vẹn khi ghi dữ liệu. Hệ thống có 3 transactions chính:\n"
    "1. Create Task: BEGIN -> INSERT tasks -> INSERT activity_logs (created) -> COMMIT.\n"
    "2. Assign Task: BEGIN -> INSERT task_assignees -> INSERT activity_logs (assigned) -> INSERT notifications -> COMMIT.\n"
    "3. Change Status: BEGIN -> UPDATE tasks -> INSERT activity_logs (status_changed) -> INSERT notifications cho từng assignee -> COMMIT.\n"
    "Điểm chung: Đảm bảo tính nguyên tố (Atomicity) — nếu bất kỳ bước nào fail, toàn bộ transaction sẽ Rollback.\"",
    None,
    "Nêu cấu trúc 3 transactions trước khi sang demo 3 scenarios ở slide tiếp theo."
)

# -------------------------------------------------------------
# SLIDE 12
# -------------------------------------------------------------
slide12_speech = (
    "\"Nghiệp vụ gán việc (Assign Task) là một chuỗi hành động: Ghi assignee -> Ghi log -> Tạo notification. Em trực quan hóa thành 3 kịch bản:\n"
    "• Scenario A (Không dùng TX): Nếu lệnh 2 gặp lỗi DB/crash, có assignee nhưng mất log/notification -> Rơi vào Inconsistent State.\n"
    "• Scenario B (Có TX thành công): Dùng BEGIN và COMMIT đồng bộ dữ liệu ở cả 3 bảng -> Consistent State.\n"
    "• Scenario C (Có TX gặp lỗi): Lệnh cuối vi phạm ràng buộc Check Constraint, database tự động ROLLBACK toàn bộ -> Consistent State.\n"
    "Sau đây em xin demo thực tế 3 kịch bản trên pgAdmin.\""
)

slide12_actions = (
    "-- BƯỚC 1: Check ban đầu:\n"
    "SELECT * FROM task_assignees WHERE task_id = '20000000-0000-0000-0000-000000000003';\n\n"
    "-- BƯỚC 2: Chạy TX THÀNH CÔNG:\n"
    "BEGIN;\n"
    "INSERT INTO task_assignees VALUES ('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001');\n"
    "INSERT INTO activity_logs (task_id, user_id, action, description) VALUES ('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'assigned', 'Assigned to Huy Ngo');\n"
    "INSERT INTO notifications (user_id, task_id, type, message) VALUES ('00000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000003', 'task_assigned', 'Assigned to: Fix login bug');\n"
    "COMMIT;\n"
    "(Verify dữ liệu thành công -> Chạy lệnh DELETE dọn data test).\n\n"
    "-- BƯỚC 3: Chạy TX THẤT BẠI (Cố tình sai type notification):\n"
    "BEGIN;\n"
    "INSERT INTO task_assignees VALUES ('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001');\n"
    "INSERT INTO activity_logs (task_id, user_id, action, description) VALUES ('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'assigned', 'Assigned to Huy Ngo');\n"
    "INSERT INTO notifications VALUES ('00000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000003', 'invalid_type', 'Assigned to: Fix login bug');\n"
    "COMMIT;\n"
    "-> Giải thích: 'PostgreSQL báo lỗi Check Constraint và tự động hủy bỏ. Bảng task_assignees vẫn trống trơn, chứng minh tính chất Atomicity.'"
)

add_slide_section(
    doc,
    "Slide 12 — Why Do We Need Transactions? (Live Demo)",
    "11:00 → 13:00 (2 mins)",
    slide12_speech,
    slide12_actions,
    "💡 Mentor Trigger:\n- ACID là gì? -> Atomicity (nguyên tố), Consistency (nhất quán), Isolation (cô lập), Durability (bền vững)."
)

# -------------------------------------------------------------
# SLIDE 13
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 13 — Design Decisions & Trade-Offs",
    "13:00 → 14:00 (1 min)",
    "\"Em xin tóm tắt 6 quyết định kỹ thuật cốt lõi trong dự án:\n"
    "1. UUID Primary Keys: Tránh lộ sequential ID qua API, an toàn cho hệ thống phân tán, chấp nhận trade-off dung lượng 16 bytes.\n"
    "2. Soft Delete (is_deleted): Giữ dữ liệu phục vụ audit trail và activity logs, cho phép khôi phục khi cần.\n"
    "3. Lookup Tables vs ENUM: Dùng bảng tra cứu để thêm status mới chỉ bằng lệnh INSERT, không cần migration ALTER TYPE gây lock DB.\n"
    "4. Timestamps: created_at cho audit log, updated_at phục vụ cơ chế Cache Invalidation.\n"
    "5. Member Role: Dùng cột VARCHAR cho 3 role cố định, tránh over-engineering tạo bảng riêng.\n"
    "6. assigned_by: Ghi nhận ai phân công task, tăng tính minh bạch cho audit log.\n"
    "Toàn bộ thiết kế CSDL này đã được em ứng dụng để xây dựng thành công REST API hoàn chỉnh bằng FastAPI và SQLAlchemy 2.x async.\"",
    None,
    "Nhấn mạnh 1 câu ngắn gọn cho mỗi decision, không đọc lê thê."
)

# -------------------------------------------------------------
# SLIDE 14
# -------------------------------------------------------------
add_slide_section(
    doc,
    "Slide 14 — Q & A (Questions & Discussion)",
    "14:00 → 15:00 (1 min)",
    "\"Em xin chân thành cảm ơn anh Nhân Đoàn, anh Thiên Lê và mọi người đã lắng nghe bài thuyết trình của em. Em rất mong nhận được những góp ý và câu hỏi từ anh/chị!\"",
    None,
    "Sẵn sàng mở danh sách Q&A Prep bên dưới để trả lời hoặc đặt câu hỏi mở cho mentor."
)

# -------------------------------------------------------------
# Q&A PREP & PROACTIVE QUESTIONS
# -------------------------------------------------------------
doc.add_heading("🎯 Q&A PREP — BỘ CÂU HỎI MENTOR HAY HỎI NHẤT", level=2)

qa_list = [
    ("Sự khác nhau giữa 2NF và 3NF?", "2NF xử lý Partial Dependency (cột không khóa phụ thuộc một phần vào Composite Key). 3NF xử lý Transitive Dependency (cột không khóa phụ thuộc bắc cầu vào cột không khóa khác)."),
    ("Schema có đạt BCNF không?", "Có. BCNF là phiên bản chặt hơn của 3NF cho trường hợp có overlapping candidate keys. Schema này không có vấn đề đó nên 3NF và BCNF là tương đương."),
    ("Tại sao không dùng ENUM cho status?", "ENUM trong PostgreSQL cần schema migration (ALTER TYPE) gây lock table. Lookup table chỉ cần INSERT dữ liệu mới, dễ bảo trì hơn."),
    ("Tại sao project_members dùng composite PK?", "Cặp (project_id, user_id) tự nhiên là unique — 1 user chỉ có thể là member của 1 project 1 lần. Composite PK bảo vệ nghiệp vụ này ở tầng DB."),
    ("RESTRICT vs CASCADE?", "RESTRICT ngăn xóa parent nếu còn children (an toàn, tránh mất task khi xóa project). CASCADE xóa luôn children khi parent bị xóa (dùng cho task_comments)."),
    ("Nếu hard delete 1 user đang có task thì sao?", "FK constraint chặn lại vì tasks.created_by có ON DELETE RESTRICT. Hệ thống dùng is_active = false để vô hiệu hóa tài khoản mà không xóa data."),
    ("Pagination cho danh sách tasks thế nào?", "Offset-based (LIMIT/OFFSET) đơn giản nhưng chậm ở trang sâu. Cursor-based (WHERE task_id > :last_id) tối ưu hơn vì dùng Index.")
]

for q, a in qa_list:
    p = doc.add_paragraph()
    r_q = p.add_run(f"❓ {q}\n")
    r_q.font.bold = True
    r_q.font.color.rgb = RGBColor(30, 58, 138)
    r_a = p.add_run(f"👉 Trả lời: {a}")
    r_a.font.color.rgb = RGBColor(51, 65, 85)

doc.add_heading("💡 CÂU HỎI MỞ BẠN CHỦ ĐỘNG HỎI MENTOR", level=2)
p_pro = doc.add_paragraph()
p_pro.add_run("1. 'Em assume project owner cũng có một record trong project_members với role = owner. Anh thấy approach này ổn không?'\n"
              "2. 'Với notification hiện tại em đang INSERT trực tiếp trong transaction. Nếu hệ thống scale lên hàng triệu users thì theo anh có nên chuyển sang Message Queue (như Celery / RabbitMQ / Kafka) không?'\n"
              "3. 'Em chưa thêm trigger cho updated_at — anh recommend em nên handle việc cập nhật updated_at ở tầng Database trigger hay tầng Application service?'")

# Save directly to note demo.docx
output_path = r"C:\Users\sangd\Downloads\note demo.docx"
doc.save(output_path)
print(f"File successfully updated and saved to: {output_path}")
