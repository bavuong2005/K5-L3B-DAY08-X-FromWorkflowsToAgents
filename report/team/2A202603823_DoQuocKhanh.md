# Báo cáo cá nhân — Đỗ Quốc Khánh

Bản tổng hợp này dựa trên commit và test trong repo. Nhánh đã kiểm tra không có phần tự khai về công cụ AI hoặc tự đánh giá; các mục đó không được suy đoán thay thành viên.

## 1. Thông tin thành viên

- Họ tên: Đỗ Quốc Khánh
- MSSV: 2A202603823
- Email: 26ai.khanhdq2@vinuni.edu.vn
- GitHub: dqk2210

## 2. Phần việc phụ trách

Shape C — orchestrator và ranh giới handoff cho investigator chỉ đọc (`src/lab8/shapes/orchestrator.py`).

## 3. Đóng góp cụ thể

- Commit `5299e15` triển khai orchestrator và thêm `src/tests/test_orchestrator_handoff.py`; commit được đưa vào `main` trong `6bb14ae`.
- Orchestrator tạo `handoff.v1` qua allowlist, không chuyển parent context, raw headers hoặc secret; investigator chỉ được gọi read-only tools. Orchestrator nhận kết quả đã lọc, tính quote và gọi Host; việc approval và ghi ledger vẫn thuộc Host.
- Trace ghi handoff đã sanitize và các kết quả đã lọc, gồm cả đường resolved, escalated và needs_info.

## 4. Bằng chứng

Test trong `src/tests/test_orchestrator_handoff.py` kiểm tra:

- `test_handoff_in_trace_is_allowlisted_and_readonly`
- `test_resolved_path_trace_leaks_nothing`
- `test_escalated_path_trace_leaks_no_pii`
- `test_needs_info_path_valid_trace_and_no_ledger_row`

Sau khi cả nhóm tích hợp, `python -m pytest -q` cho 62 passed, 248 deselected; student matrix cho 248 passed, 62 deselected. Benchmark public orchestrator đạt 70/70, pass^5 1.000, variance 0, cost/success mô phỏng 56.65 VND và mean/p95 steps 4.57/5. Crash suite chung đạt 20/20.

## 5. Tài liệu kiểm chứng

Commit và test là bằng chứng kỹ thuật trong repo. Tóm tắt kết quả nhóm nằm ở `report/team/group_report.md`; bảng số liệu đầy đủ nằm ở `src/reports/benchmark.json`.
