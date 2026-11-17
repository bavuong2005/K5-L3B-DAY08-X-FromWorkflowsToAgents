# Bonus report: B1

- Topic + nguồn (tên, năm, slide): **B1 — Investigator song song và critical path**. Google Research 2026, *Towards a Science of Scaling Agent Systems*, slide 15 (Parallelization), 24 (Graph scheduling), 33 (Latency model), 41.
- CLAIM của nguồn (1 câu): Multi-agent chỉ có lợi khi task chia song song được; với task tuần tự, các biến thể multi-agent giảm 39–70%.
- BOUNDARY (model / dataset / setup): Đo trên benchmark multi-agent của Google Research với model thật, nhiều loại task khác nhau; kết luận về parallelization và latency model (slide 15, 33) — không phải về domain hoàn phí vận chuyển.
- HYPOTHESIS trên LogiX: claims flow gần như tuần tự (quote phụ thuộc order view, refund phụ thuộc quote, model chỉ soạn chữ) nên song song hóa 3 investigator đọc độc lập chỉ rút ngắn tối đa phần reads; speedup thực tế sẽ sát dự đoán Amdahl với 3 workers và nhỏ insignificantly so với chi phí phức tạp thêm.
- Biến cố định / biến thay đổi: Cố định claim (14 public), seed (11,22,33,44,55), bảng giá, evaluator, tool set, số model call và số tool call (6 tool + 1 draft cho cả hai shape). Thay đổi duy nhất: cách schedule 3 read `lookup_order`, `lookup_policy`, `lookup_refund_history` — tuần tự (shape C) vs `ThreadPoolExecutor` 3 workers, mỗi thread một connection SQLite riêng, join theo thứ tự cố định (`bonus/orchestrator_parallel.py`). Writer vẫn duy nhất là orchestrator.
- Lệnh tái lập (copy-paste được), chạy trong `src/`:
  ```powershell
  python -m lab8.benchmark --shapes orchestrator,orchestrator_parallel --extra-shape orchestrator_parallel=bonus.orchestrator_parallel:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json
  python -m bonus.critical_path --out reports/bonus_critical_path.json
  ```
- File report + run id: `src/reports/bonus_benchmark.json`, `src/reports/bonus_critical_path.json`. Run id dẫn chứng: `R-orchestrator-C-001-s11` (tuần tự), `R-orchestrator_parallel-C-001-s11` (song song).

## Kết quả

Số liệu lấy từ `reports/bonus_benchmark.json` và `reports/bonus_critical_path.json`, không chép tay từ terminal.

**Chất lượng (70/70 trial public, evaluator chấm ledger + audit + trace):**

| Shape | pass rate | pass^5 | seed variance | min–max | cost/success (VND mô phỏng) | steps |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| orchestrator (tuần tự) | 1.000 | 1.000 | 0.000000 | 1.000–1.000 | 56.65 | 4.57 |
| orchestrator_parallel (song song) | 1.000 | 1.000 | 0.000000 | 1.000–1.000 | 56.65 | 4.57 |

Safety: `statuses_match` = true trên cả 70 trial; không thay đổi ledger, audit hay proposal_amount; trace vẫn qua scan secret (test `tests/test_bonus_parallel.py`).

**Critical path (mô hình `bonus/latency.yaml`, jitter cố định theo seed):**

| Shape | mean (ms) | p95 (ms) | min (ms) | max (ms) |
| --- | ---: | ---: | ---: | ---: |
| orchestrator (tuần tự) | 480.984 | 542.672 | 336.446 | 555.738 |
| orchestrator_parallel (song song) | 435.065 | 499.800 | 315.485 | 503.721 |

Speedup đo được: **1.1055x**. Amdahl dự đoán với 3 workers: **1.1079x**. Hai số khớp nhau vì phần song song được (3 reads, ~75 ms) chỉ chiếm ~15% critical path; nút cổ chai là model call soạn chữ (~350 ms) chạy tuần tự sau khi quote đã có.

## Kết luận

**Ủng hộ CLAIM của nguồn trên LogiX.** Câu hỏi của topic: bước quote phụ thuộc vào order, vậy phần nào thực sự song song được? Trả lời: chỉ 3 read tra cứu độc lập; mọi bước còn lại nằm trên một chuỗi phụ thuộc (claim view → order view → quote → draft → host ghi). Speedup đo được 1.1055x khớp dự đoán Amdahl 1.1079x, đúng tinh thần slide 33: task tuần tự không hưởng lợi từ parallelization, dù đúng và an toàn hơn (pass rate, cost không đổi). Điều kiện kết luận đảo ngược: (1) nếu tách quote thành nhiều nhánh investigator độc lập thực sự (policy / damage / delay xem xét riêng rồi aggregator gộp), phần song song tăng và speedup có thể lên ~1.9x; (2) nếu model call thực tế nhanh hơn nhiều so với tool I/O, tỉ lệ serial giảm; (3) nếu thêm ràng buộc latency mỗi investigator (ví dụ A2A qua mạng) thì song song hóa mới có lợi thế rõ.

## Giới hạn

- MockLLM không phải model sản xuất; latency là **mô hình mô phỏng** từ `bonus/latency.yaml` với jitter cố định theo seed — không phải đo wall-clock, không gán cho API thật.
- ThreadPoolExecutor chạy trong một process (GIL): work là I/O SQLite nên minh họa được scheduling, nhưng không phản ánh chi phí process/network thật giữa các agent.
- Đo trên 14 claim public × 5 seed; chưa đo trên bộ hidden (safety counts phải bằng 0 khi grader chấm, pass rate biến thể không cần đạt 0.75 theo luật bonus).
- Số claim ít nên mean/p95 có biến động; kết luận chỉ áp dụng cho claims flow dạng tuần tự như LogiX, không suy rộng cho multi-agent nói chung.
