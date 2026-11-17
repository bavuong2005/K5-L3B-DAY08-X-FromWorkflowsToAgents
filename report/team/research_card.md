# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

## Phiếu của nhóm

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 — Failure taxonomy |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng | Mert Cemri et al., *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS 2025. [Trang proceedings](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html). Nghiên cứu thực nghiệm/taxonomy trên execution traces. |
| CLAIM | Một kết luận gốc của nguồn | Nhóm tác giả xây dựng MAST gồm 14 failure modes thuộc ba nhóm; taxonomy được phát triển từ 150 trace với κ=0.88, rồi dùng để phân tích hơn 1.600 trace từ bảy MAS framework. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Nguồn nghiên cứu các framework/task/model được mô tả trong paper (coding, math, general-agent); không nghiên cứu bộ synthetic LogiX-VN này. Nhóm dùng MockLLM, 14 public claim và 5 seed, nên chỉ mượn taxonomy làm từ vựng phân tích, không chuyển kết luận định lượng của paper sang lab. |
| HYPOTHESIS | Nếu đổi shape A→B, metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Khi đổi shape workflow → swarm, giả thuyết là failure do xác minh nguồn dữ liệu sẽ tăng từ 0/70 lên 1/70, tập trung ở `C-002` seed 55: swarm chấp nhận 5 ngày trong ticket thay vì 2 ngày trong order. Đây là giả thuyết phân loại của nhóm, không phải nhãn MAST chính thức. |
| METHOD | Biến giữ cố định; biến duy nhất thay đổi | Chạy cùng public claims, seed `11,22,33,44,55`, MockLLM, tools, pricing, fresh SQLite và evaluator. Biến so sánh duy nhất là shape triển khai (workflow so với swarm). Shape bao gồm control flow/prompt riêng, nên thí nghiệm không tách riêng topology khỏi các khác biệt đó. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó | Đếm trial sai nhãn và dùng trace để xác định claim/seed. `R-swarm-C-002-s55` fail `status resolved != denied`; `R-workflow-C-002-s55` pass. Swarm đạt 69/70 (98.57%), workflow 70/70 (100%). Nhóm diễn giải lỗi là thiếu kiểm chứng dữ kiện ticket với order; đây là phân loại thủ công trên một lỗi. |

## Kết quả ablation

- Lệnh đã chạy: `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `R-workflow-C-002-s55`, `R-swarm-C-002-s55`; số liệu đầy đủ ở `src/reports/benchmark.json`.
- Kết quả: hypothesis được ủng hộ trên public set: workflow pass 70/70 và swarm pass 69/70; lỗi duy nhất là swarm C-002 seed 55. Do chỉ có một failure và MockLLM, không đủ bằng chứng để khái quát cơ chế hoặc gán nhãn MAST chính thức.
- Giới hạn: MockLLM không phải model sản xuất; latency là `unavailable`; seed set và corpus đều nhỏ.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
