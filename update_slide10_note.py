import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = docx.Document()

# Set Margins
for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Title
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_title = title_p.add_run("TASK MANAGEMENT SYSTEM — DATABASE DESIGN\nSPEAKER NOTES & LIVE DEMO GUIDE")
r_title.font.name = "Calibri"
r_title.font.size = Pt(18)
r_title.font.bold = True
r_title.font.color.rgb = RGBColor(15, 23, 42)

sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_sub = sub_p.add_run("Presenter: Sang Duong  ·  Mentor: Nhan Doan  ·  Supporter: Thien Le  ·  June 2026\n(Đồng bộ chuẩn 100% với slide [SangDuong] Database Training - 2026 (4).pptx)\n")
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

# Overview Table
doc.add_heading("⏱️ Phân Bổ Thời Gian 15 Phút Overview (14 Slides)", level=2)
p_time = doc.add_paragraph()
p_time.add_run("• 00:00 – 01:00 (1.0 phút): Slide 1 (Opening) & Slide 2 (Agenda)\n"
               "• 01:00 – 04:00 (3.0 phút): Slide 3 (Workflow), Slide 4 (Domain) & Slide 5 (ERD)\n"
               "• 04:00 – 07:00 (3.0 phút): Slide 6 (Lý thuyết 3NF) & Slide 7 (Demo Bad Design -> 3NF)\n"
               "• 07:00 – 10:00 (3.0 phút): Slide 8 (Constraints/Indexes), Slide 9 (Seq vs Index) & Slide 10 (Demo EXPLAIN ANALYZE)\n"
               "• 10:00 – 13:00 (3.0 phút): Slide 11 (Transaction Design) & Slide 12 (Demo 3 Scenarios)\n"
               "• 13:00 – 14:00 (1.0 phút): Slide 13 (Design Decisions & FastAPI Integration)\n"
               "• 14:00 – 15:00 (1.0 phút): Slide 14 (Q & A & Thảo luận)\n")

doc.add_heading("🎙️ Chi Tiết Lời Thoại & Kịch Bản Cho Từng Slide", level=2)

# Slide 1 to 9
add_slide_section(doc, "Slide 1 — Opening (Cover)", "00:00 → 00:30", "\"Xin chào mọi người, em là Sang Duong. Hôm nay em xin trình bày về Database Design Practice — thiết kế cơ sở dữ liệu cho một Task Management System. Mentor hướng dẫn của em là anh Nhân Đoàn và supporter là anh Thiên Lê.\"")
add_slide_section(doc, "Slide 2 — Agenda", "00:30 → 01:00", "\"Nội dung bài báo cáo hôm nay gồm 8 phần chính: Từ Tổng quan & Phạm vi, Phân tích miền dữ liệu, Thiết kế ERD, Chuẩn hóa 3NF, Thiết lập Ràng buộc & Chỉ mục, Thiết kế Giao dịch, Các quyết định kỹ thuật cốt lõi và cuối cùng là phần Q&A.\"")
add_slide_section(doc, "Slide 3 — Database Design Workflow", "01:00 → 02:00", "\"Trước khi bắt tay vào thiết kế schema, em xây dựng tài liệu Requirement & Domain Analysis Document xác định scope, workflows, business rules, entities và relationships. Quy trình đi qua 5 giai đoạn: Requirement Analysis -> Logical Design -> Normalization (3NF) -> Physical Design -> Optimization & Transactions có 2 vòng lặp kiểm tra chặt chẽ là 'Normalized?' và 'Performance OK?'.\"")
add_slide_section(doc, "Slide 4 — Domain Analysis (5 Nhóm Thực Thể)", "02:00 → 03:00", "\"Hệ thống gồm 13 bảng chia thành 5 nhóm: Core (users, projects, tasks), Bridge (project_members, task_assignees với Composite PK), Supporting (comments, attachments), Lookup (statuses, priorities, categories - dùng bảng tra cứu thay ENUM để tránh ALTER TYPE lock DB) và Audit (activity_logs, notifications).\"")
add_slide_section(doc, "Slide 5 — ERD & Relationships", "03:00 → 04:00", "\"Sơ đồ quan hệ ERD: Users 1->N Projects (owner_id), Projects 1->N Tasks (project_id), Tasks 1->N Comments (task_id). Các quan hệ Nhiều-Nhiều dùng bảng bridge project_members và task_assignees với Composite PK. Toàn bộ thực thể chính dùng UUID Primary Key để bảo mật API và an toàn khi phân tán/sharding.\"")
add_slide_section(doc, "Slide 6 — Normalization — What & Why", "04:00 → 05:00", "\"Lý thuyết 3 Normal Forms:\n• 1NF: Mỗi ô chứa đúng 1 giá trị nguyên tố (Atomic), tách task_assignees mỗi dòng 1 assignee.\n• 2NF: Loại bỏ partial dependency khi có Composite Key, tách project_name sang bảng projects.\n• 3NF: Loại bỏ transitive dependency (A -> B -> C), tách status_name sang bảng tra cứu task_statuses.\"")

slide7_speech = "\"Để minh họa lý do cần normalize, em show thiết kế phẳng tasks_flat. 4 vấn đề chính: Data Redundancy, Update Anomaly, Insert Anomaly và Delete Anomaly. Sau đây em chuyển sang pgAdmin để demo trực tiếp.\""
slide7_actions = (
    "-- 1. SHOW BAD DESIGN:\nSELECT * FROM tasks_flat ORDER BY task_id, assignee_email;\n-> Giải thích: 'Task 1 lặp 3 dòng vì có 3 assignees, project_name và owner_email lặp lại 3 lần -> Redundancy.'\n\n"
    "-- 2. DEMO UPDATE ANOMALY:\nUPDATE tasks_flat SET project_name = 'Alpha Project v2' WHERE task_id = 1 AND assignee_email = 'tuyen@gmail.com';\nSELECT * FROM tasks_flat WHERE task_id = 1;\n-> Giải thích: 'Chỉ 1 dòng đổi thành Alpha Project v2, 2 dòng kia giữ nguyên -> Update Anomaly.'\n(Chạy ngầm: 02b_reset_tasks_flat.sql để reset sạch data).\n\n"
    "-- 3. SHOW 1NF, 2NF, 3NF:\n-- 1NF: SELECT t.title AS task, u.full_name AS assignee FROM task_assignees ta JOIN tasks t ON t.task_id = ta.task_id JOIN users u ON u.user_id = ta.user_id ORDER BY t.title, u.full_name;\n-- 2NF: SELECT t.title, p.project_name, u.full_name AS owner FROM tasks t JOIN projects p ON p.project_id = t.project_id JOIN users u ON u.user_id = p.owner_id WHERE t.is_deleted = false LIMIT 10;\n-- 3NF: SELECT t.title, ts.name AS status, tp.name AS priority FROM tasks t JOIN task_statuses ts ON ts.status_id = t.status_id LEFT JOIN task_priorities tp ON tp.priority_id = t.priority_id WHERE t.is_deleted = false LIMIT 10;"
)
add_slide_section(doc, "Slide 7 — Normalization: Bad Design → 3NF (Demo pgAdmin)", "05:00 → 07:00", slide7_speech, slide7_actions)

add_slide_section(doc, "Slide 8 — Constraints & Indexing", "07:00 → 07:45", "\"Về toàn vẹn, em áp dụng 5 loại Constraints: PK, FK (RESTRICT cho owner, CASCADE cho task_comments), UNIQUE, COMPOSITE PK trên bảng bridge, và CHECK constraints cho role, action, type. Về hiệu năng, em tạo 8 chỉ mục B-Tree trên các FK và các cột hay tìm kiếm như project_id, status_id, user_id, task_id.\"")
add_slide_section(doc, "Slide 9 — Indexing: Seq Scan vs Index Scan", "07:45 → 08:30", "\"So sánh cơ chế đọc của PostgreSQL trên bảng tasks 1000 dòng:\n• Without Index (Seq Scan - Trái): Quét tuần tự toàn bộ bảng. Cost cao từ 0..250, loại bỏ 985 dòng rác, chạy mất ~12ms.\n• With Index (Index Scan - Phải): Đi theo cây B-Tree nhảy trực tiếp tới đúng dòng cần tìm. Cost giảm xuống 0.28..8.30, 0 dòng rác bị loại bỏ, thời gian thực thi dưới 1ms.\"")

# -------------------------------------------------------------
# SLIDE 10 — EXPLAIN ANALYZE DEMO (CLEAR & STEP-BY-STEP)
# -------------------------------------------------------------
slide10_speech = (
    "\"Em sẽ demo live EXPLAIN ANALYZE trong pgAdmin để chứng minh hiệu quả thực tế trước và sau khi tạo Index:\n\n"
    "• Bước 1 (Trước khi có Index): Em chạy EXPLAIN ANALYZE trên câu query lọc theo project_id. PostgreSQL phải thực hiện Sequential Scan (quét toàn bộ bảng), Estimated Cost lên tới 250, và có đến 985 dòng bị loại bỏ bởi Filter.\n\n"
    "• Bước 2: Em thực hiện lệnh CREATE INDEX idx_tasks_project_id trên cột project_id của bảng tasks.\n\n"
    "• Bước 3 (Sau khi có Index): Chạy lại EXPLAIN ANALYZE. PostgreSQL lập tức chuyển sang Index Scan using idx_tasks_project_id. Cost giảm mạnh từ 250 xuống chỉ còn 8.3, số dòng bị filter loại bỏ về 0, và thời gian thực thi nhanh gấp hơn 30 lần (dưới 0.1ms).\""
)

slide10_actions = (
    "💻 THAO TÁC TỪNG BƯỚC TRÊN PGADMIN (Tab: 02_explain_analyze.sql):\n\n"
    "-- [Bước 0: Đảm bảo môi trường sạch trước khi demo (chạy ngầm nếu cần)]:\n"
    "DROP INDEX IF EXISTS idx_tasks_project_id;\n\n"
    "-- [Bước 1: Chạy BEFORE Index]:\n"
    "EXPLAIN ANALYZE\n"
    "SELECT * FROM tasks\n"
    "WHERE project_id = '10000000-0000-0000-0000-000000000001';\n"
    "👉 Hành động: Bấm F5 -> Chỉ chuột vào dòng Output:\n"
    "   'Seq Scan on tasks (cost=0.00..250.00 rows=15)'\n"
    "   'Rows Removed by Filter: 985'\n"
    "   'Execution Time: ~12ms'\n\n"
    "-- [Bước 2: Tạo Index]:\n"
    "CREATE INDEX idx_tasks_project_id ON tasks(project_id);\n"
    "👉 Hành động: Bấm F5 -> Output báo 'CREATE INDEX Query returned successfully'.\n\n"
    "-- [Bước 3: Chạy AFTER Index]:\n"
    "EXPLAIN ANALYZE\n"
    "SELECT * FROM tasks\n"
    "WHERE project_id = '10000000-0000-0000-0000-000000000001';\n"
    "👉 Hành động: Bấm F5 -> Chỉ chuột vào dòng Output:\n"
    "   'Index Scan using idx_tasks_project_id (cost=0.28..8.30 rows=15)'\n"
    "   'Planning: 0.2ms   Execution: 0.08ms'\n"
    "   'Rows Removed by Filter: 0'"
)

slide10_mentor = (
    "Key insights & Câu hỏi Mentor hay hỏi tại Slide 10:\n"
    "1. Key insight: Cost 250 -> 8.3, Rows removed by filter = 0, Execution nhanh gấp 30x.\n"
    "2. EXPLAIN vs EXPLAIN ANALYZE? -> EXPLAIN chỉ ước tính (Estimated plan, không chạy query thật). EXPLAIN ANALYZE thực sự chạy query trong DB và đo Actual execution time.\n"
    "3. Tại sao ON DELETE RESTRICT không phải CASCADE? -> RESTRICT an toàn hơn — ngăn xóa nhầm parent nếu còn children (dùng cho Project -> Tasks). CASCADE chỉ dùng khi xóa parent muốn xóa luôn children (như Task -> Comments).\n"
    "4. Index trên FK có luôn cần thiết không? -> Không tự động — Postgres chỉ tự index PK. FK phải tự tạo nếu hay dùng trong JOIN hoặc WHERE.\n"
    "5. Tại sao không index tất cả columns? -> Index tăng tốc đọc (SELECT) nhưng làm chậm ghi (INSERT/UPDATE) do phải cập nhật cây B-Tree, đồng thời tốn RAM/Disk."
)

add_slide_section(
    doc,
    "Slide 10 — EXPLAIN ANALYZE Demo (pgAdmin Live)",
    "08:30 → 10:00 (1.5 mins)",
    slide10_speech,
    slide10_actions,
    slide10_mentor
)

# Slide 11 to 14
slide11_speech = (
    "\"Sau khi tối ưu hiệu năng đọc bằng Indexing, em chuyển sang phần bảo vệ tính toàn vẹn khi ghi qua Transaction Design. Hệ thống có 3 transactions chính:\n"
    "1. Create Task: BEGIN -> INSERT tasks -> INSERT activity_logs (created) -> COMMIT.\n"
    "2. Assign Task: BEGIN -> INSERT task_assignees -> INSERT activity_logs (assigned) -> INSERT notifications -> COMMIT.\n"
    "3. Change Status: BEGIN -> UPDATE tasks -> INSERT activity_logs (status_changed) -> INSERT notifications cho từng assignee -> COMMIT.\n"
    "Điểm chung: Đảm bảo nguyên tắc Atomicity — nếu bất kỳ bước nào thất bại thì toàn bộ transaction sẽ Rollback.\""
)
add_slide_section(doc, "Slide 11 — Transaction Design", "10:00 → 11:00", slide11_speech, None, "Nêu nhanh cấu trúc 3 transactions, chuyển sang demo 3 scenarios ở slide tiếp theo.")

slide12_speech = (
    "\"Nghiệp vụ Assign Task là một chuỗi hành động: Ghi assignee -> Ghi log -> Tạo notification. Em trực quan hóa thành 3 kịch bản:\n"
    "• Scenario A (Không dùng TX): Nếu lệnh 2 gặp sự cố, database rơi vào trạng thái bất nhất quán (Inconsistent State) do mất log/thông báo.\n"
    "• Scenario B (Có TX thành công): Sử dụng BEGIN và COMMIT giúp đồng bộ dữ liệu ở cả 3 bảng.\n"
    "• Scenario C (Có TX gặp lỗi): Nếu lệnh 3 vi phạm Check Constraint, database tự động ROLLBACK để bảo vệ tính toàn vẹn (Atomicity).\n"
    "Sau đây em xin demo thực tế 3 kịch bản trong pgAdmin.\""
)
slide12_actions = (
    "-- BƯỚC 1: Check ban đầu:\nSELECT * FROM task_assignees WHERE task_id = '20000000-0000-0000-0000-000000000003';\n\n"
    "-- BƯỚC 2: Chạy TX THÀNH CÔNG (Scenario B):\nBEGIN;\nINSERT INTO task_assignees VALUES ('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001');\nINSERT INTO activity_logs (task_id, user_id, action, description) VALUES ('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'assigned', 'Assigned to Huy Ngo');\nINSERT INTO notifications (user_id, task_id, type, message) VALUES ('00000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000003', 'task_assigned', 'Assigned to: Fix login bug');\nCOMMIT;\n(Verify dữ liệu thành công -> Chạy lệnh DELETE dọn data test).\n\n"
    "-- BƯỚC 3: Chạy TX THẤT BẠI (Scenario C - Cố tình sai constraint):\nBEGIN;\nINSERT INTO task_assignees VALUES ('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001');\nINSERT INTO activity_logs (task_id, user_id, action, description) VALUES ('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'assigned', 'Assigned to Huy Ngo');\nINSERT INTO notifications VALUES ('00000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000003', 'invalid_type', 'Assigned to: Fix login bug');\nCOMMIT;\n-> Giải thích: 'PostgreSQL báo lỗi Check Constraint và tự động hủy bỏ. Bảng task_assignees vẫn trống trơn, chứng minh tính chất Atomicity.'"
)
add_slide_section(doc, "Slide 12 — Why Do We Need Transactions? (Demo pgAdmin)", "11:00 → 13:00", slide12_speech, slide12_actions)

add_slide_section(
    doc,
    "Slide 13 — Design Decisions & Trade-Offs",
    "13:00 → 14:00",
    "\"Em xin tóm tắt 6 quyết định kỹ thuật cốt lõi trong dự án:\n"
    "1. UUID Primary Keys: Tránh lộ sequential ID qua API, an toàn cho hệ thống phân tán, chấp nhận trade-off dung lượng 16 bytes.\n"
    "2. Soft Delete (is_deleted): Giữ dữ liệu phục vụ audit trail và activity logs, cho phép khôi phục khi cần.\n"
    "3. Lookup Tables vs ENUM: Dùng bảng tra cứu để thêm status mới chỉ bằng lệnh INSERT, không cần migration ALTER TYPE gây lock DB.\n"
    "4. Timestamps: created_at cho audit log, updated_at phục vụ cơ chế Cache Invalidation.\n"
    "5. Member Role: Dùng cột VARCHAR cho 3 role cố định, tránh over-engineering tạo bảng riêng.\n"
    "6. assigned_by: Ghi nhận ai phân công task, tăng tính minh bạch cho audit log.\n"
    "Toàn bộ thiết kế CSDL này đã được em ứng dụng để xây dựng thành công REST API hoàn chỉnh bằng FastAPI và SQLAlchemy 2.x async.\""
)

add_slide_section(
    doc,
    "Slide 14 — Q & A (Questions & Discussion)",
    "14:00 → 15:00",
    "\"Em xin chân thành cảm ơn anh Nhân Đoàn, anh Thiên Lê và mọi người đã lắng nghe bài thuyết trình của em. Em rất mong nhận được những góp ý và câu hỏi từ anh/chị!\""
)

# Q&A Section
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

# Save
out_file = r"C:\Users\sangd\Downloads\note demo.docx"
doc.save(out_file)
print(f"File updated successfully: {out_file}")
