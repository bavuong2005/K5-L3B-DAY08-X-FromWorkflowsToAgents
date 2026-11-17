# Báo cáo cá nhân — Mai Lê Bá Vương

## 1. Thông tin thành viên

- Họ tên: Mai Lê Bá Vương
- MSSV: 2A202603872
- Email: 26ai.vuongmlb@vinuni.edu.vn
- GitHub: bavuong2005

## 2. Phần việc phụ trách

Phụ trách kiểm tra shape swarm tham chiếu, baseline public và hành vi approval ở seed yếu. Sau khi các shape thành viên đã có, tham gia tích hợp và tổng hợp benchmark bốn shape, ADR và báo cáo nhóm.

## 3. Đóng góp cụ thể

- Đối chiếu `src/lab8/shapes/swarm_reference.py` với luật nghiệp vụ, contract và nhãn public.
- Phân tích T02: order `O-202` có `delay_days=2`; ở seed 55 swarm dùng số 5 ngày từ ticket, phát `model_override`, quote 20.000 VND và trả `resolved`, trong khi nhãn yêu cầu `denied`.
- Thêm `src/tests/test_swarm_approval_seed55.py`. Test xác nhận claim C-007 có approval hết hạn vẫn bị Host từ chối, không ghi refund và tạo `policy_denied`.
- Tạo baseline Swarm public và tích hợp phần thay đổi vào nhánh nhóm. Commit gốc test `9f7faa6`; commit tích hợp hiện tại `ef981bf`.

## 4. Bằng chứng

- Baseline riêng `src/reports/swarm_baseline.json`: 69/70 pass; pass rate 0.985714; pass^5 13/14 = 0.928571; variance 0.0008163; cost/success mô phỏng 49.57 VND; mean/p95 steps 2.8/3.
- Benchmark đầy đủ sau tích hợp: `src/reports/benchmark.json`; Swarm vẫn 69/70, còn workflow, single và orchestrator đều 70/70.
- `R-swarm-C-002-s11`: `denied`, quote 0, pass. `R-swarm-C-002-s55`: `resolved`, fail vì dùng ticket nói trễ 5 ngày thay cho order ghi 2 ngày.
- `python -m pytest -q tests/test_swarm_approval_seed55.py` → 1 passed trong lần kiểm tra trước; sau tích hợp cả bộ `python -m pytest -q` → 62 passed, 248 deselected và student matrix → 248 passed, 62 deselected.
- Crash suite chung: 20/20.

## 5. Công cụ AI đã dùng

Dùng ChatGPT/Codex để đối chiếu tài liệu lab, trace và benchmark, hỗ trợ soạn test và báo cáo. Tự kiểm bằng dữ liệu order, nhãn T02, trace của seed 11/55, file benchmark do công cụ lab sinh ra và kết quả pytest.

## 6. Tự đánh giá

Đã xác định được nguyên nhân và phạm vi lỗi seed 55 của swarm, lưu baseline public, thêm test kiểm approval hết hạn và hoàn thành so sánh bốn shape. Dựa trên public benchmark, nhóm chọn workflow vì giữ 100% pass rate trên 70 trial với cost/success mô phỏng thấp nhất. Chưa có dữ liệu hidden để khẳng định kết quả trên 200 hidden trial. MockLLM và giá mô phỏng không đại diện cho model hay chi phí sản xuất; latency không được đo.
