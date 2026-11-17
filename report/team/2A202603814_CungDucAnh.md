# Báo cáo cá nhân — 2A202603814_CungDucAnh

## 1. Thông tin thành viên

- Họ tên: Cung Đức Anh
- MSSV: 2A202603814
- Email: 26ai.anhcd2@vinuni.edu.vn
- GitHub: cungducanh2712

## 2. Phần việc phụ trách

- **Kiến trúc phụ trách:** Shape B — Single ReAct Agent (`src/lab8/shapes/single.py`).
- **Nhiệm vụ chính:**
  - Thiết kế và triển khai vòng lặp ReAct có chặn trên số bước (`max_steps=8`) cho bài toán bồi thường LogiX-VN.
  - Đảm bảo ranh giới bảo mật nghiêm ngặt giữa Agent và Host: Agent chỉ có quyền gọi các read-only tools (`worker=True`), việc kiểm tra điều kiện bồi hoàn, phê duyệt (approval), trần hạn mức đơn hàng (cap) và ghi sổ cái (ledger) hoàn toàn do code Host đảm nhiệm.
  - Xử lý tính bền bỉ tài chính (Idempotency, Crash Handling) và ranh giới dữ liệu nhạy cảm (Canary Secret, Customer PII).
  - Thu thập số liệu đo lường thực nghiệm (Pass rate, Pass^5, Variance, Cost/success) để phục vụ lập luận ra quyết định kiến trúc của nhóm trong ADR.

## 3. Đóng góp cụ thể

1. **Hiện thực hóa Single ReAct Agent (`src/lab8/shapes/single.py`):**
   - Tích hợp vòng lặp `lab8.runtime.run_react` kết hợp gọi `MockLLM` có seed để hạch toán chính xác chi phí mô hình vào `Budget`.
   - Thiết kế logic trạng thái `decide()` gọn gàng, điều hướng tuần tự qua các công cụ đọc: `lookup_order` $\rightarrow$ `compute_compensation` $\rightarrow$ kết luận `final`.
   - Xử lý triệt để các ca biên theo đúng contract:
     - Thiếu `order_id` $\rightarrow$ trả về trạng thái `needs_info`, `proposal_amount = 0`.
     - Đơn hàng không tồn tại hoặc sai phạm vi sở hữu (`principal_id`) $\rightarrow$ trả về `escalated`.
     - Quote tính ra $\le 0$ $\rightarrow$ trả về `denied`, không gọi ghi tiền.
     - Quote $> 0$ $\rightarrow$ chuyển tiếp nguyên văn giá trị quote đầy đủ vào `durability.issue_refund`, không tự ý cấn trừ phần tiền đã hoàn trước đó (để Host tự đối chiếu lịch sử hoàn tiền và enforce cap).
2. **Khắc phục lỗi Hallucination & Seed Variance (Điểm yếu của Swarm):**
   - Ở claim `C-002` (khách khai trễ 5 ngày trong ticket nhưng DB chỉ ghi trễ 2 ngày), Swarm bị lệch quyết định ở seed 55 (`seed % 5 == 0`) do tin vào văn bản ticket, dẫn đến bồi thường sai và fail test.
   - Trong Single Agent, tôi thiết kế agent luôn lấy dữ liệu thực tế từ Database (`order['delay_days']`) làm chân lý (ground truth), bỏ qua các tuyên bố chủ quan của khách hàng. Nhờ đó, Single Agent đạt độ ổn định tuyệt đối (Variance = 0.000000).
3. **Đảm bảo Crash Safety và Ranh giới Bảo mật (CP3 & CP4):**
   - Chuyển tiếp tham số `crash_at` vào hàm `durability.issue_refund` và tuyệt đối **không bắt ngoại lệ `InjectedCrash`** (chỉ flush trace trước khi re-raise) để harness kiểm tra độ bền khi crash.
   - Tuân thủ nghiêm ngặt Trace Contract v1: Chỉ ghi các event đã sanitize vào `_Trace`, tuyệt đối không in log thô claim row hay order row, bảo vệ 100% không làm lộ `CANARY_SECRET_*` và thông tin cá nhân khách hàng.

## 4. Bằng chứng

- **Kết quả kiểm thử Student Matrix (T01–T14 trên Shape Single):**
  - Đạt tuyệt đối **62/62 test passed** (bao gồm 60 test single-run từ C-001 đến C-014 trên cả 5 seeds 11, 22, 33, 44, 55; cùng 2 bài test đa lần chạy T11 retry idempotency và T12 crash resilience).
  - Lệnh kiểm tra: `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator"`
- **Kết quả kiểm tra Cổng Host:**
  - `python -m pytest -q` $\rightarrow$ **54 passed, 0 failed**.
- **Kết quả Crash Safety Suite (CP4):**
  - Chạy `python -m lab8.crash_test --count 20 --out reports/crash.json` $\rightarrow$ đạt **`crash_safety: 20/20`** (vượt qua tất cả kịch bản crash trước và sau khi ghi ledger).
- **Số liệu Benchmark so sánh thực nghiệm (trên 14 claims $\times$ 5 seeds):**
  - **Single Agent:** Pass rate = **1.000** | Pass^5 = **1.000** | Variance = **0.000000** | Cost/success = **29.77 VND** | Steps = **4.57**.
  - **Swarm (Đối chứng):** Pass rate = **0.986** | Pass^5 = **0.929** | Variance = **0.000816** | Cost/success = **49.57 VND** | Steps = **2.80** *(bị lỗi ở seed 55: status resolved != denied)*.
  - *Nhận xét:* Single Agent tiết kiệm chi phí hơn 40% so với Swarm và đạt độ tin cậy hoàn hảo 100% trên mọi seed.
- **Run ID mẫu được sinh ra và kiểm tra:**
  - `R-single-C-001-s11` (status: `resolved`, proposal: 35000, trace clean).
  - `R-single-C-002-s55` (status: `denied`, proposal: 0, không bị ảnh hưởng bởi seed 55).

## 5. Công cụ AI đã dùng

- **Công cụ:** Antigravity AI Assistant (mô hình Gemini 3.8 Flash).
- **Mục đích sử dụng:**
  - Hỗ trợ phân tích chi tiết các yêu cầu kỹ thuật và hợp đồng dữ liệu trong `docs/contracts.md` và `docs/business_rules.md`.
  - Thảo luận thiết kế kiến trúc thông qua quy trình `/grill-me` để thống nhất phương án xử lý vòng lặp ReAct, phân định quyền hạn Host/Agent và chiến lược chống ghi đè dữ liệu.
- **Cách tự kiểm tra và kiểm chứng kết quả:**
  - Không sao chép mã nguồn một cách cảm tính; mọi đoạn code đều được tự động xác minh thông qua bộ kiểm thử chuẩn của bài lab (`pytest -q`, test ma trận T01–T14, test crash suite 20/20 và benchmark đối chiếu với file json output).

## 6. Tự đánh giá

- **Mức độ hoàn thành:** 100% yêu cầu của Shape B (Single Agent) từ CP1 đến CP5.
- **Điểm mạnh:**
  - Code ngắn gọn, phân tách trách nhiệm rõ ràng, tuân thủ đúng chuẩn ReAct nguyên bản.
  - Xử lý triệt để bài toán rò rỉ dữ liệu nhạy cảm và crash safety, giúp shape đạt kết quả hoàn hảo trên mọi chỉ số benchmark.
- **Điểm tự chấm:** 10/10 cho phần việc cá nhân phụ trách.
