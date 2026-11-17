# Team

## Thông tin nhóm

- Tên nhóm: X
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-X-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo: https://github.com/bavuong2005/K5-L3B-DAY08-X-FromWorkflowsToAgents
- Nhánh tích hợp đang chuẩn bị: `team-integration` (tạo từ `main`).

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
| 1 | Mai Lê Bá Vương | 2A202603872 | 26ai.vuongmlb@vinuni.edu.vn | bavuong2005 | Swarm reference, approval test, benchmark tổng hợp |
| 2 | Cung Đức Anh | 2A202603814 | 26ai.anhcd2@vinuni.edu.vn | cungducanh2712 | Shape B — Single ReAct |
| 3 | Phạm Thanh An | 2A202603913 | 26ai.anpt3@vinuni.edu.vn | thanhanbk02 | Shape A — workflow |
| 4 | Đỗ Quốc Khánh | 2A202603823 | 26ai.khanhdq2@vinuni.edu.vn | dqk2210 | Shape C — orchestrator, handoff security |

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Mai Lê Bá Vương | swarm reference, approval, benchmark | `9f7faa6` → `ef981bf` (tích hợp) | `src/tests/test_swarm_approval_seed55.py` |
| Cung Đức Anh | single ReAct | `0c9297f` → `bb0efbd` (tích hợp) | `src/tests/test_public_matrix.py` bao phủ Single trong T01–T14; file test không đổi trong commit `0c9297f` |
| Phạm Thanh An | workflow | `bac2ac4` | `test_workflow_ignores_ticket_delay_on_the_swarm_weak_seed`; `test_workflow_keeps_the_full_quote_when_the_host_pays_the_difference`; `test_workflow_lets_the_injected_crash_escape_and_retries_once` |
| Đỗ Quốc Khánh | orchestrator, handoff security | `5299e15` | `test_handoff_in_trace_is_allowlisted_and_readonly`; `test_resolved_path_trace_leaks_nothing`; `test_escalated_path_trace_leaks_no_pii`; `test_needs_info_path_valid_trace_and_no_ledger_row` |

## Báo cáo cá nhân

Mỗi thành viên có báo cáo riêng trong `report/team/`:

- `report/team/2A202603872_MaiLeBaVuong.md`
- `report/team/2A202603814_CungDucAnh.md`
- `report/team/2A202603913_PhamThanhAn.md`
- `report/team/2A202603823_DoQuocKhanh.md`
