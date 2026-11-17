# Báo cáo cá nhân — Phạm Thanh An

## 1. Thông tin thành viên

- Họ tên: Phạm Thanh An
- MSSV: 2A202603913
- Email: 26ai.anpt3@vinuni.edu.vn
- GitHub: thanhanbk02

## 2. Phần việc phụ trách

Shape A `workflow`: `src/lab8/shapes/workflow.py`.

Quy trình Python cố định, cùng chữ ký `run_claim` với các shape khác. Tiền do `compute_compensation` tính trên dòng order. Shape truyền quote đầy đủ vào `durability.issue_refund`. Host kiểm approval, trần theo đơn và idempotency rồi mới ghi ledger. Model không chọn số tiền và không ghi refund.

Không làm benchmark bốn shape, ADR, research card hay báo cáo nhóm.

## 3. Đóng góp cụ thể

- Commit chính: `bac2ac4` — `Implement the deterministic workflow claim path.`
- Test thêm: `src/tests/test_workflow_shape.py`
  - `test_workflow_ignores_ticket_delay_on_the_swarm_weak_seed`
  - `test_workflow_keeps_the_full_quote_when_the_host_pays_the_difference`
  - `test_workflow_lets_the_injected_crash_escape_and_retries_once`
- Dòng đóng góp trong `TEAM.md` trỏ về `bac2ac4` và ba test trên (commit dòng đó: `a26d4bc`).

Quyết định kỹ thuật:

- Đọc claim bằng `get_claim_view`, đọc đơn bằng `lookup_order`. Trace chỉ ghi field đã lọc, không ghi ticket, số điện thoại, địa chỉ, tên hàng, ghi chú nội bộ hay `parent_secret`.
- Bỏ qua số ngày trễ viết trong ticket. Seed 55 với claim `C-002` vẫn `denied`.
- Quote = 0 thì `denied` và không gọi `issue_refund`. Quote > 0 thì truyền nguyên quote. `proposal_amount` giữ quote đầy đủ khi host cap hoặc từ chối.
- Truyền `crash_at` vào `issue_refund`. `InjectedCrash` được ném lại. Exception thường trả `failed`. Shape không tự ghi ledger.

## 4. Bằng chứng

Commit `bac2ac4` trên nhánh `main` của máy local. Chưa push trong phiên làm việc này.

Run id của các lần tự kiểm:

- `R-workflow-C-002-s55` — ticket nói trễ 5 ngày, đơn trễ 2 ngày → `denied`, không có dòng ledger.
- `R-workflow-C-014-s11` — `proposal_amount` 150000, ledger 120000, một audit `refund_committed`, trace không chứa `CANARY_SECRET_`.
- `R-workflow-C-012-s11` — crash `after_effect_before_checkpoint` thoát khỏi `run_claim`; gọi lại vẫn một refund.

Lệnh đã chạy trong `src/` với Python 3.13.17:

- `python -m pytest -q -m student -o addopts= -k workflow` → 62 passed.
- `python -m pytest -q -m student -o addopts= -k "workflow and (t11 or t12)"` → 2 passed.
- `python -m pytest -q tests/test_workflow_shape.py` → 3 passed.
- `python -m pytest -q` → 57 passed, 248 deselected.

## 5. Công cụ AI đã dùng

Cursor (Grok) được dùng để đọc đề, viết `workflow.py`, viết `src/tests/test_workflow_shape.py`, và soạn báo cáo này.

Tự kiểm bằng pytest ở mục 4, không dùng số benchmark. Cổng host và bộ student của workflow đều xanh sau khi sửa.

## 6. Tự đánh giá

Shape workflow trả `RunResult` đúng contract trên bộ public đã chạy: T11, T12, quote đầy đủ, và trace không lộ `CANARY_SECRET_*` trong các case đã kiểm. Chưa có số pass rate trên bộ hidden và chưa có benchmark bốn shape. Hai phần đó thuộc phần chung của nhóm.
