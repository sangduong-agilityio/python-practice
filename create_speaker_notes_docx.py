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
run_sub = sub.add_run("Báo Cáo Tiến Độ Training & Thiết Kế CSDL Task Management System\nPresenter: Sang Duong | Reviewer: Anh Nhân Đoàn & Anh Thiên Lê\n")
run_sub.font.name = "Calibri"
run_sub.font.size = Pt(11)
run_sub.font.italic = True
run_sub.font.color.rgb = RGBColor(100, 116, 139)

def add_slide_note(doc, slide_num, slide_title, duration, speech):
    h = doc.add_paragraph()
    r = h.add_run(f"Slide {slide_num}: {slide_title} ({duration})")
    r.font.name = "Calibri"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = RGBColor(30, 58, 138)
    
    p = doc.add_paragraph()
    r_sp = p.add_run(f"🎙️ Kịch bản nói:\n\"{speech}\"")
    r_sp.font.name = "Calibri"
    r_sp.font.size = Pt(10.5)
    r_sp.font.color.rgb = RGBColor(51, 65, 85)
    p.paragraph_format.space_after = Pt(12)

# Overview Table
doc.add_heading("⏱️ Phân Bổ Thời Gian 15 Phút Overview", level=2)
p_time = doc.add_paragraph()
p_time.add_run("• 00:00 – 01:30 (1.5 phút): Mở đầu & Báo cáo Tiến độ Lộ trình Học tập (Slide 1 – 2)\n"
               "• 01:30 – 04:00 (2.5 phút): Workflow, Phân tích Miền & Sơ đồ ERD (Slide 3 – 6)\n"
               "• 04:00 – 07:00 (3.0 phút): Chuẩn hóa 3NF & Demo loại bỏ Dị thường (Slide 7 – 8)\n"
               "• 07:00 – 10:30 (3.5 phút): Constraints, Indexes & EXPLAIN ANALYZE (Slide 9 – 11)\n"
               "• 10:30 – 13:00 (2.5 phút): Transaction Design & Consistency (Slide 12 – 14)\n"
               "• 13:00 – 14:30 (1.5 phút): Minh chứng Triển khai Backend REST API (Slide 15)\n"
               "• 14:30 – 15:00 (0.5 phút): Kết luận & Chuyển sang Q&A (Slide 16)\n")

doc.add_heading("🎙️ Chi Tiết Lời Thoại Cho Từng Slide", level=2)

slides_data = [
    (1, "Task Management System — Practice Presentation", "0.5 phút",
     "Em chào anh Nhân, anh Thiên cùng toàn thể mọi người. Hôm nay em xin trình bày báo cáo tổng kết lộ trình học tập Database & System Design, đồng thời báo cáo kết quả thiết kế CSDL cho dự án Task Management System."),
    (2, "Training Roadmap & Progress Status", "1.0 phút",
     "Trước khi đi vào kỹ thuật, em xin cập nhật nhanh tiến độ: Phase 1 Database Design và đọc sách System Design Interview của Alex Xu 16 chương đã hoàn thành 100%. Khóa Dometrain System Design đã xong 6/8 chương (xin gia hạn 2 ngày); khóa Python Interview Questions xin gia hạn 1 ngày. Toàn bộ kiến thức này đã được em áp dụng trực tiếp để xây dựng backend REST API hoàn chỉnh."),
    (3, "Agenda", "0.2 phút",
     "Nội dung báo cáo hôm nay gồm 5 phần chính: Phân tích miền dữ liệu, Chuẩn hóa 3NF, Đánh chỉ mục Index, Giao dịch ACID và Minh chứng triển khai API."),
    (4, "Database Design Workflow", "0.8 phút",
     "Quy trình thiết kế CSDL của em tuân theo 5 bước chuẩn kỹ thuật: từ Phân tích yêu cầu -> Thiết kế Logic (ERD) -> Chuẩn hóa 3NF -> Thiết kế Vật lý (DDL/Constraints) -> Tối ưu hóa truy vấn & Giao dịch."),
    (5, "Domain Analysis — Entity Categorization", "0.8 phút",
     "Hệ thống gồm 11 bảng chia thành 5 nhóm thực thể: Core (users, projects, tasks), Bridge (project_members, task_assignees), Supporting (comments, attachments), Lookup (statuses, priorities, categories) và Audit (activity_logs, notifications)."),
    (6, "ERD & Relationships", "0.7 phút",
     "Về mối quan hệ: User sở hữu nhiều Project (1-N), Project chứa nhiều Task (1-N). Với các quan hệ Nhiều-Nhiều như User tham gia Project hay User nhận Task, em sử dụng các bảng trung gian với Composite Primary Key để đảm bảo không bị trùng lặp bản ghi."),
    (7, "Normalization — What & Why", "1.0 phút",
     "Về chuẩn hóa: 1NF đảm bảo giá trị nguyên tố (Atomic), 2NF loại bỏ phụ thuộc một phần trên Composite Key, 3NF loại bỏ phụ thuộc bắc cầu, đảm bảo sửa 1 nơi dữ liệu cập nhật đồng bộ toàn hệ thống."),
    (8, "Normalization: Bad Design -> 3NF", "2.0 phút",
     "Em xin minh họa quá trình chuẩn hóa từ bảng phẳng tasks_flat: Tách mảng email ra bảng task_assignees (1NF), tách tên project về bảng projects (2NF), tách status_name ra bảng tra cứu task_statuses (3NF). Kết quả: Schema 11 bảng đạt 3NF sạch dư thừa và dị thường."),
    (9, "Constraints & Indexing Strategy", "1.0 phút",
     "Về toàn vẹn dữ liệu, em dùng ON DELETE RESTRICT cho Project Owner và ON DELETE CASCADE cho Assignees/Comments của Task. Về hiệu năng, em đặt 8 chỉ mục B-Tree trên các cột FK và các cột hay tìm kiếm như project_id, status_id, created_by."),
    (10, "Indexing: Seq Scan vs Index Scan", "1.2 phút",
     "Khi không có Index, PostgreSQL phải làm Sequential Scan — đọc từng dòng từ đầu đến cuối bảng, chi phí (Cost) rất cao và chậm khi dữ liệu lớn. Khi có Index B-Tree, PostgreSQL nhảy thẳng đến dòng cần tìm qua Index Scan, thời gian thực thi giảm từ vài chục ms xuống dưới 1ms."),
    (11, "EXPLAIN ANALYZE — Before vs After Index", "1.3 phút",
     "Em đã chạy thực nghiệm EXPLAIN ANALYZE: Trước khi đánh Index trên project_id, query mất Cost 250 với 985 dòng bị loại bỏ. Sau khi tạo Index idx_tasks_project_id, Cost giảm xuống còn 8.3, thời gian chạy nhanh gấp 30 lần (0.08ms)."),
    (12, "Transaction Design", "1.0 phút",
     "Đối với các luồng nghiệp vụ phức tạp như Chuyển trạng thái Task, em gom 3 câu lệnh vào khối Transaction (BEGIN ... COMMIT): 1. Update Task Status -> 2. Ghi Activity Log -> 3. Tạo Notification gửi cho Assignees."),
    (13, "Why Do We Need Transactions?", "1.0 phút",
     "Nếu không có Transaction, khi bước 3 bị lỗi mạng hay trùng constraint, bước 1 và 2 đã lỡ ghi vào DB sẽ gây rác dữ liệu (Inconsistent State). Nhờ Transaction, DB sẽ tự động ROLLBACK về trạng thái an toàn ban đầu."),
    (14, "Design Decisions & Trade-Offs", "0.5 phút",
     "Tóm tắt các quyết định thiết kế: Dùng UUID làm PK để bảo mật API và sẵn sàng cho Sharding; dùng Soft Delete (is_deleted) để bảo lưu dữ liệu Audit Log; dùng Lookup Tables thay Enum để dễ dàng thêm trạng thái mới mà không phải Migration Schema."),
    (15, "Backend REST API Architecture", "1.5 phút",
     "Toàn bộ thiết kế CSDL trên đã được em hiện thực hóa thành dự án Task Management API: Kiến trúc 4 lớp chuẩn Route -> Service -> Repository -> PostgreSQL (asyncpg). Đầy đủ bảo mật OAuth2 + JWT Token, Pytest in-memory test suite, Docker Compose và Swagger UI tại /docs."),
    (16, "Q & A", "0.5 phút",
     "Em xin chân thành cảm ơn anh Nhân, anh Thiên và mọi người đã lắng nghe. Em rất mong nhận được những góp ý và câu hỏi từ anh/chị!")
]

for s in slides_data:
    add_slide_note(doc, s[0], s[1], s[2], s[3])

doc.save(r"C:\Users\sangd\Downloads\TMS_SpeakerNotes_15min_v4.docx")
print("Speaker notes docx created successfully!")
