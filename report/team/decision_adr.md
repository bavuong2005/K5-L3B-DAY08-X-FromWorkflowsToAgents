# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.

- Shape chọn: workflow
- Commit hash: f1fa4ba
- Run id dẫn chứng: R-workflow-C-001-s11; R-workflow-C-002-s55
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000 (70 trial; public)
- Cost per success (mô phỏng, VND): 27.86
- Crash safety: 20/20 (`src/reports/crash.json`)
- Secret leak / approval bypass: 0 / 0 quan sát trên public benchmark và test host; hidden chưa chạy vì không có `src/student_drop/`

## Vì sao shape này

Workflow đạt 70/70 trên cùng public corpus và năm seed, bằng Single và Orchestrator về pass rate, nhưng có chi phí mô phỏng thấp nhất (27.86 VND/success) và không phụ thuộc seed trong bộ này. Nó cũng dùng 0 model call trong benchmark. Swarm giảm số bước trung bình còn 2.80 nhưng fail `C-002` ở seed 55; Orchestrator tốn 56.65 VND/success. Vì vậy chọn workflow để chấm hidden dựa trên bằng chứng hiện có. Nếu hidden cho thấy workflow dưới ngưỡng hoặc xuất hiện bypass/leak, quyết định này phải được xem lại.

## Có đáng đổi lấy multi-agent không

Trên bộ public hiện tại thì chưa: Swarm không tăng độ đúng, có một lỗi theo seed và có cost cao hơn workflow. Orchestrator cung cấp boundary handoff rõ và test bảo mật, nhưng cost mô phỏng gấp khoảng 2.03 lần workflow mà pass rate không tăng. Nhóm sẽ cân nhắc lại nếu bộ hidden chứng minh shape đó cải thiện pass rate hoặc xử lý được loại task mà workflow không biểu đạt được, đồng thời giữ must-pass về approval, secret và crash.

## Trace và bằng chứng

Trace v1 gắn `run_id` với danh sách event đã sanitize. Orchestrator ghi handoff allowlist, kết quả investigator đã lọc và quote; workflow ghi bước đọc/ra quyết định. `parent_secret`, raw headers, ticket prose và dữ liệu PII không được chuyển vào handoff/trace. Host giữ quyền kiểm approval và ghi ledger. Public tests và trial evaluator không phát hiện secret trong các case đã chạy; đây không thay thế hidden leak scan.

## Giới hạn

Đây là kết quả 14 public claim × 5 seed trên MockLLM, không đại diện model sản xuất; giá chỉ là mô phỏng và latency là `unavailable`. Không có hidden self-check trong workspace, nên các số 0 ở dòng secret/bypass chỉ áp dụng cho test public/host, không phải hidden grade. Bốn shape cũng khác nhau về control flow và prompt, nên kết quả không cô lập riêng topology.
