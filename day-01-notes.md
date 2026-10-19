# Day 01: Mental Model + Claude Basics — Training Notes

- **Học viên**: Developer
- **Ngày học**: 2026-10-12
- **Dự án**: Task Management API (`d:\python\task-management-api`)
- **Git Branch**: `training/day-01-mental-model`
- **Môi trường**: Claude Pro (Sonnet 4.6), Claude Desktop, Claude Code CLI v2.1.97

---

## I. TỔNG KẾT LÝ THUYẾT (COURSEWORK)

### 1. Khung 4D (AI Fluency Framework)
- **Delegation (Giao việc)**: Giao việc có phạm vi rõ ràng (đọc log, debug lỗi, viết test, soạn thảo PR). Giữ quyền quyết định kiến trúc, logic nghiệp vụ cốt lõi và bảo mật.
- **Description (Mô tả bài toán)**: Cung cấp đầy đủ **Role + Context + Constraints + Expected Output**.
- **Discernment (Thẩm định bén nhạy)**: Nhận diện ảo giác (hallucination), kiểm tra tính chính xác của thư viện và API được gợi ý.
- **Diligence (Kiểm chứng cẩn trọng)**: Nguyên tắc **"Verification beats trust"** — Không tin tưởng câu trả lời chỉ vì văn phong mượt mà; luôn kiểm chứng bằng cách chạy code, xem log và chạy test.

### 2. Bản chất LLM (Capabilities & Limitations)
- LLM sinh token theo xác suất (**Next-token prediction**), không có suy nghĩ nội tại.
- Giới hạn bộ nhớ làm việc (**Context window**): Các hội thoại quá dài sẽ bị pha loãng ngữ cảnh. Khi chuyển sang bài toán/ticket mới, nên mở session mới.

---

## II. THỰC HÀNH PROMPTING LẶP (3 BÀI TOÁN THỰC TẾ)

### Task 1: Bug Summary & Root Cause Analysis

#### 1. Ngữ cảnh & Lỗi
```text
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00 (Background on this error at: https://sqlalche.me/e/20/3o7r)
```

#### 2. Prompt v1 (Sơ khai)
```text
Sửa giúp tôi lỗi này với:
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00
```
- **Nhận xét kết quả v1**: Claude giải thích chung chung, đề xuất tăng pool size hoặc restart service, chưa chỉ ra được nguyên nhân gốc rễ (connection leak) trong mô hình async context manager của FastAPI.

#### 3. Prompt v2 (Kỹ thuật chuẩn)
```text
Bạn là Senior Backend Engineer chuyên sâu về FastAPI và Async SQLAlchemy 2.0.
Dự án của tôi là REST API chạy trên Uvicorn với nhiều request concurrent. Chúng tôi vừa gặp lỗi sau trong môi trường staging:
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00

Hãy phân tích và phản hồi theo đúng cấu trúc sau:
1. Root Cause: Giải thích ngắn gọn cơ chế vì sao connection bị rò rỉ (connection leak) trong mô hình async context manager/dependency injection của FastAPI (tối đa 3 câu).
2. 3 Bước khắc phục thực tế: Từ nhanh nhất (quick fix) đến triệt để nhất (architectural fix).
3. Code Snippet: 1 ví dụ code chuẩn get_db() session lifecycle trong FastAPI để đảm bảo connection luôn được giải phóng an toàn.
```
- **Nhận xét kết quả v2**: Trả lời trúng đích, chỉ ra session không được close trong exception path, cung cấp đúng pattern `yield` trong FastAPI dependency, code có thể áp dụng ngay.

---

### Task 2: Explain Technical Concept

#### 1. Khái niệm: Idempotency trong REST API

#### 2. Prompt v1 (Sơ khai)
```text
Giải thích Idempotency trong REST API là gì?
```
- **Nhận xét kết quả v1**: Mang tính học thuật, định nghĩa toán học khô khan, thiếu hướng dẫn áp dụng thực tế cho lập trình viên.

#### 3. Prompt v2 (Kỹ thuật chuẩn)
```text
Bạn là Tech Lead. Hãy giải thích khái niệm "Idempotency trong REST API" cho một Junior Developer:
1. Định nghĩa súc tích bằng ngôn ngữ đời thường (tối đa 2 câu).
2. Bảng so sánh tính Idempotent của các HTTP method: GET, POST, PUT, DELETE, PATCH kèm lý do.
3. Bài toán thực tế: Khi client gọi API thanh toán (payment) bị timeout mạng và retry nhiều lần, thiết kế Idempotency Key hoạt động như thế nào? (Kèm flowchart hoặc 4 bước xử lý cụ thể).
```
- **Nhận xét kết quả v2**: Cực kỳ dễ hiểu, phân biệt rõ POST vs PUT, minh họa chuẩn cơ chế `Idempotency-Key` với Redis/DB cache, junior có thể code theo được ngay.

---

### Task 3: Drafting PR Description

#### 1. Bài toán: Thêm tính năng Filter & Pagination cho Task API

#### 2. Prompt v1 (Sơ khai)
```text
Viết giúp tôi PR description cho tính năng thêm filter và phân trang cho tasks API.
```
- **Nhận xét kết quả v1**: Bản PR chung chung, thiếu ngữ cảnh kỹ thuật, không có hướng dẫn test và checklist.

#### 3. Prompt v2 (Kỹ thuật chuẩn)
```text
Bạn là Developer trong dự án Task Management API (FastAPI + Pydantic v2 + SQLAlchemy).
Hãy soạn thảo một Pull Request Description hoàn chỉnh cho ticket: "FEAT-102: Add Pagination & Status/Priority Filters for GET /api/v1/tasks".

Yêu cầu định dạng Markdown gồm các mục bắt buộc sau:
- Summary of Changes (Tóm tắt thay đổi): 3 gạch đầu dòng ngắn gọn.
- Query Parameters Added: Bảng mô tả các param (page, page_size, status, priority).
- How to Test: Lệnh curl cụ thể hoặc hướng dẫn chạy pytest.
- Breaking Changes: Có hay không.
- Reviewer Checklist: Danh sách 4 mục cần kiểm tra trước khi approve.
```
- **Nhận xét kết quả v2**: PR chỉn chu, chuyên nghiệp, người review có thể đọc hiểu và test được ngay mà không cần hỏi lại.

---

## III. BÀI HỌC RÚT RA (RETROSPECTIVE & SURPRISES)

1. **Điểm bất ngờ tích cực (Good Surprises)**:
   - Khi được cấp đúng vai trò và cấu trúc yêu cầu, Claude cấu trúc thông tin rất mạch lạc, sinh code đúng idiom của framework.
   - Tiết kiệm hơn 80% thời gian viết tài liệu kỹ thuật (PR, docs, commit messages).
2. **Điểm bất ngờ tiêu cực / Cần cảnh giác (Bad Surprises & Limits)**:
   - Nếu prompt mơ hồ, Claude có xu hướng đưa ra giải pháp "chữa cháy" bề nổi (như tăng connection pool) thay vì giải quyết lỗi gốc rễ.
   - Thỉnh thoảng Claude có thể đề xuất các tham số thư viện của phiên bản cũ (ví dụ Pydantic v1 vs v2).
3. **Quy tắc vàng**:
   - **Verification beats trust**: Mọi gợi ý phải được run/test và review bởi lập trình viên trước khi merge.
