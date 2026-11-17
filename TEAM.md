# Team

## Thông tin nhóm

- Tên nhóm: X
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-X-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/bavuong2005/K5-L3B-DAY08-X-FromWorkflowsToAgents

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Cung Đức Anh | 2A202603814 | 26ai.anhcd2@vinuni.edu.vn | cungducanh2712 | Single Agent (Shape B) |
|   2 |        |      |       |        |         |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Cung Đức Anh | Single Agent | 7607db4 | tests/test_public_matrix.py (T01-T14 single shape) |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603814_CungDucAnh

### Phần việc phụ trách

- Shape B: Single ReAct Agent (`src/lab8/shapes/single.py`).

### Đóng góp cụ thể

- Triển khai `run_claim` cho Single Agent với vòng lặp ReAct `max_steps=8` và worker read-only tools.
- Đảm bảo ranh giới an toàn cho host: idempotency, crash resilience, canary secret isolation.
- Vượt qua 62/62 test student, đạt 20/20 crash safety và pass rate 1.000 trên toàn bộ seeds.

### Bằng chứng

-
