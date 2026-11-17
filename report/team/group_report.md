# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: X; lớp: L3B.
- Repo: [bavuong2005/K5-L3B-DAY08-X-FromWorkflowsToAgents](https://github.com/bavuong2005/K5-L3B-DAY08-X-FromWorkflowsToAgents).
- Thành viên và phân công: xem `TEAM.md`.
- Mã nguồn đã tích hợp được kiểm tra tại commit `ef981bf`; số liệu dưới đây do lệnh lab sinh từ đúng snapshot đó.

## 2. Mục tiêu và cách tiếp cận

Lab yêu cầu xây dựng và so sánh bốn cách xử lý cùng yêu cầu hoàn tiền: workflow xác định, một Single ReAct agent, orchestrator có investigator chỉ đọc, và swarm tham chiếu. Mỗi shape nhận cùng claim, seed, dữ liệu order/policy, giá và evaluator. Host giữ quyền quyết định policy, approval, idempotency và ghi ledger; agent không được tự quyết số tiền hay ghi refund. Quy tắc chi tiết nằm ở `docs/business_rules.md`, ranh giới kiến trúc ở `docs/architecture.md` và chỉ số ở `docs/metrics.md`.

Nhóm làm song song theo bốn vai trong `TEAM.md`: An triển khai workflow; Cung triển khai single; Khánh triển khai orchestrator và kiểm tra handoff; Vương kiểm tra swarm, approval và baseline. Workflow và orchestrator đã lên `main`; phần single và Swarm được đưa vào nhánh tích hợp mà vẫn giữ nguyên các thay đổi đã có trên `main`. Sau khi tích hợp, nhóm chạy cả bộ test, student matrix, benchmark đủ bốn shape và crash suite.

## 3. Giải pháp

- **Workflow (A):** các bước cố định do Python điều khiển. Đọc claim/order, tính quote bằng code, rồi chuyển nguyên quote cho Host. Không gọi model trong benchmark.
- **Single (B):** một vòng ReAct có giới hạn tối đa 8 bước. Agent dùng công cụ đọc; Host vẫn kiểm approval, cap theo order, idempotency và ghi ledger.
- **Orchestrator (C):** orchestrator gửi `handoff.v1` đã lọc cho investigator. Handoff chỉ cho phép các field và read-only tools trong allowlist; investigator không có quyền ghi. Host nhận quote đầy đủ và thực hiện bước có tác dụng phụ.
- **Swarm (D):** shape tham chiếu dùng để đối chứng về số bước, chi phí và độ nhạy theo seed; không mặc định xem multi-agent là tốt hơn.

Trace ghi run id và event đã sanitize như quyết định, handoff, kết quả investigator và quote. Handoff không mang `parent_secret`, raw headers hoặc quyền ghi. Tool Host là nguồn chân lý cho approval, policy và ledger.

## 4. Kết quả

Benchmark public gồm 14 claim × 5 seed = 70 trial/shape, cùng MockLLM, tool, giá mô phỏng và evaluator. `pass^5` là tỷ lệ claim pass trên cả năm seed.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean / p95 steps |
|---|---:|---:|---:|---:|---:|---:|
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 27.86 | 4.43 / 5 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 29.77 | 4.57 / 5 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.65 | 4.57 / 5 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 |

Các số trên được sinh trong `src/reports/benchmark.json`. Crash suite đạt **20/20** trong `src/reports/crash.json`. Kiểm tra tích hợp: `python -m pytest -q` → **62 passed, 248 deselected**; `python -m pytest -q -m student -o addopts=` → **248 passed, 62 deselected**.

Trial duy nhất fail là `R-swarm-C-002-s55`: order `O-202` ghi trễ 2 ngày nên kết quả đúng là `denied`, nhưng ở seed 55 swarm dùng nội dung ticket nói 5 ngày và trả `resolved`. Cùng claim ở seed 11, và cả ba shape còn lại ở seed 55, đều `denied` như nhãn. Test approval riêng ở seed yếu xác nhận approval hết hạn vẫn bị Host từ chối, không ghi refund.

Nhóm chọn **workflow** trong ADR vì đạt cùng 70/70 với single và orchestrator, có variance 0 trên public, và cost/success thấp nhất. Swarm có ít bước nhất nhưng vừa có một public failure vừa tốn nhiều hơn workflow; orchestrator có handoff rõ nhưng cost mô phỏng cao nhất. Đây là lựa chọn dựa trên bộ public, không phải kết luận về bộ hidden.

## 5. Khó khăn và cách xử lý

Các nhánh được cập nhật không đồng thời: An và Khánh đã có nội dung trên `main`, còn Cung và Vương dùng nhánh riêng. Cung phát triển từ một base cũ nên không thể thay toàn bộ cây bằng snapshot nhánh đó. Nhóm chỉ đưa commit single cần thiết vào nhánh tích hợp, giữ nguyên workflow, orchestrator và test đã có, rồi chạy lại toàn bộ student matrix và benchmark.

Lỗi public có ý nghĩa nhất là Swarm tin số ngày do khách viết trong ticket thay vì `delay_days` trong order. Đây là phân loại định tính của nhóm theo hướng *task verification*; nhóm không chạy bộ gán nhãn chính thức MAST. Cổng approval vẫn nằm ở Host và test approval seed 55 xanh.

## 6. Tổng hợp đóng góp

Đóng góp, commit và test được liệt kê trong `TEAM.md`; báo cáo cá nhân có trong `report/team/`. Commit single của Cung triển khai `single.py`; commit đó không sửa file test. Single được bao phủ bởi public student matrix chạy sau tích hợp, nhưng đây là điểm khác với yêu cầu rubric về test do từng thành viên thêm hoặc sửa và cần được nhóm lưu ý.

## 7. Hạn chế và hướng cải thiện

- Không có `src/student_drop/` trong workspace, nên nhóm chưa chạy hidden self-check và không thể báo cáo pass rate hidden, secret-leak count hay approval-bypass count của 200 hidden trial. ADR chỉ nêu kết quả public và test host.
- Bộ public chỉ có 14 claim và dùng MockLLM; giá là VND mô phỏng, không phải hóa đơn API. Latency là `unavailable`.
- So sánh giữ nguyên corpus, seed, tool, giá và evaluator, nhưng mỗi shape cũng có control flow/prompt riêng. Vì vậy đây là so sánh các shape triển khai trong lab, không cô lập được riêng ảnh hưởng topology.
- Cần chạy lại hidden grader chính thức và xác nhận mọi thành viên đã nộp link repo trên LMS trước khi chốt nộp.

## 8. Tài liệu tham khảo

- Tài liệu lab: `docs/business_rules.md`, `docs/architecture.md`, `docs/contracts.md`, `docs/metrics.md`, `SUBMISSION.md`, `RUBRIC.md`.
- Mert Cemri et al., [“Why Do Multi-Agent LLM Systems Fail?” — NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html). Dùng taxonomy làm khung tham khảo; phân loại lỗi của nhóm là nhận định trên trace public, không phải nhãn MAST chính thức.
