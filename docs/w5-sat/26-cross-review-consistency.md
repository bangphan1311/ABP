> **Lưu ý:** File này được sinh tự động bằng `python -m experiments.w5_final_analysis`, không chỉnh sửa tay.
> Nguồn dữ liệu: `results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` (W3/W4 frozen pilot; `results/runs.csv` chưa có tại thời điểm chạy)

# 26 — Cross-review P1 + nhất quán code ↔ spec ↔ paper

## 1. Kết quả consistency checker (C1–C10)

| Check | Status | File | Symbol | Expected | Actual | Message |
|---|---|---|---|---|---|---|
| `C1` | **OK** | `docs/sat_spec.md` | `§2 pairwise/order variable ids` | v*n+p (n²) và v*(n-1)+p (n(n-1)) trong S §2, M §3.2, A §A.1/A.2 | pairwise n_vars=16, order n_vars=12 | — |
| `C2` | **OK** | `docs/sat_spec.md` | `§3 path4 clause table (56/74/86) + M §3.3 (32/50/62)` | path4 K=1/2/3: pairwise 56/74/86, order 32/50/62 | live={'pairwise': [56, 74, 86], 'order': [32, 50, 62]} | — |
| `C3` | **OK** | `docs/technical_appendix_draft.md` | `§A.5 _not_value boundaries` | q=1/-o[v][1], q=n/o[v][n-1], interior hai literal | q=1=[-7], q=n=[9], interior=[-8, 7] | — |
| `C4` | **OK** | `src/sat/solve.py` | `solve_sat K-search (k = lo + 1, first UNSAT)` | K <- B + 1, dừng ở lần UNSAT đầu tiên (S §5, A §A.5) | k = lo + 1; hi = k khi UNSAT | — |
| `C5` | **OK** | `src/sat/pairwise.py` | `trivial_unsat (k >= n) checked before build_cnf` | K >= n -> UNSAT trước khi dựng CNF (S §1, M §3.1, A.3.1) | live=True, probe_order=True | — |
| `C6` | **OK** | `src/sat/solve.py` | `CANONICAL_SAT_CONFIG` | order/pairwise/glucose4/multi/false/false/0 | {'method': 'sat', 'abp_encoding': 'order', 'amo_encoding': 'pairwise', 'sat_solver': 'glucose4', 'search_mode': 'multi', 'symmetry': False, 'warm_start': False, 'seed': 0} | — |
| `C7` | **OK** | `src/sat/solve.py` | `canonical_sat_config(memory_limit=...)` | default 12.0 GiB; None -> ValueError; nêu ở C/W4/S/M | default=12.0, rejects_none=True | — |
| `C8-R1` | **OK** | `tests/exact/test_exact_solvers.py` | `R1 skip-guards` | skip thay vì fail khi thiếu backend/engine/license | đủ | — |
| `C8-R2` | **OK** | `docs/exact_models.md` | `R2 timing scope` | runner wall_time + kill cứng time_limit + 30 s | đủ | — |
| `C8-R3` | **OK** | `src/exact/common.py` | `R3 validate_exact_input` | ValueError cho input xấu, hiện diện ở cả 4 solver | 4/4 file có ValueError/validate; 3/4 dùng validate_exact_input | — |
| `C8-R4` | **OK** | `src/exact/common.py` | `R4 warn_ignored_config` | warning cho field Config bị bỏ qua ở 3 solver | common + gurobi_mip/cplex_mip/cplex_cp | — |
| `C8-R5` | **OK** | `src/exact/cp_sat_solver.py` | `R5 _safe_upper_bound` | UNKNOWN/không hữu hạn -> ub = n-1 | return n - 1 khi UNKNOWN/non-finite | — |
| `C8-R6` | **OK** | `src/exact/gurobi_mip.py` | `R6 objective cross-check` | objective != model_objective -> ERR ở 3 backend | 3/3 backend trả ERR khi lệch | — |
| `C9` | **OK** | `docs/w5-sat` | `deliverable hygiene` | không placeholder, không tham chiếu handoff cũ, không link gãy | markers=[], handoff=[], broken=[] | — |
| `C10` | **OK** | `docs/w2-sat/13-review-p1-formulation.md` | `fairness of comparison` | wall_time, time_limit semantics, ub on TO, MIPGap=0, shared verify() | P1 review + paper 27 nêu đủ 5 điểm | — |

## 2. Recheck P1 R1–R6 (`docs/w2-sat/13-review-p1-formulation.md`)

| Mục | Trạng thái | Bằng chứng trong repo |
|---|---|---|
| R1 — skip-guard khi thiếu backend/engine/license | closed | `tests/exact/test_exact_solvers.py`: `_skip_if_backend_unavailable`, `pytest.skip`, guard `cpoptimizer.exe` |
| R2 — timing scope, dùng runner `wall_time` | closed | `docs/exact_models.md` §Time accounting: `wall_time`, kill cứng `time_limit + 30 seconds` |
| R3 — input validation raise `ValueError` | closed | `src/exact/common.py::validate_exact_input`; 3 solver mới gọi hàm này, CP-SAT giữ validation nội bộ |
| R4 — warning field Config bị bỏ qua | closed | `src/exact/common.py::warn_ignored_config`; gọi ở `gurobi_mip.py`, `cplex_mip.py`, `cplex_cp.py` |
| R5 — `ub` khi TO ở CP-SAT | closed | `src/exact/cp_sat_solver.py::_safe_upper_bound` trả `n - 1` khi `UNKNOWN`/non-finite |
| R6 — cross-check objective native vs `verify()` | closed | `gurobi_mip.py`, `cplex_mip.py`, `cplex_cp.py`: `objective != model_objective` → `ERR` |

Không phát hiện mục R1–R6 nào còn mở tại W5; không có patch nào bị thực hiện ngầm (OQ-5).

## 3. Fairness SAT vs exact — năm điểm bắt buộc

1. **`wall_time`:** so sánh chính thức dùng runner `wall_time`, không dùng `t_total` của solver (phạm vi import khác nhau).
2. **`time_limit` semantics:** SAT là ngân sách cho cả chuỗi K; exact chỉ giới hạn pha solve; runner hard-kill tại `time_limit + 30` giây.
3. **`ub` khi TO:** SAT trả `ub = hi − 1` (có thể là cận đếm `n − 1`); exact trả bound của solver hoặc `n − 1`; không đọc `ub` như “gần tối ưu”.
4. **`MIPGap = 0` / gap tolerance:** Gurobi `MIPGap=0`, CPLEX mipgap + absmipgap = 0; `MIP_optimal_tolerance` bị loại khỏi OPT.
5. **Shared `verify()`:** mọi nghiệm SAT và exact đi qua cùng `src/common/verify.py::verify()` trước khi vào `Result`.

## 4. Dọn link stale trỏ thư mục handoff cũ (BR-11)

- `docs/w2-sat/14-sat-methodology.md`: 5 link đã trỏ về `docs/w2-sat/12-test-matrix.md` và `docs/w2-sat/13-review-p1-formulation.md`.
- `docs/w2-sat/15-m1-gate-evidence.md`: link đã trỏ về `docs/w2-sat/12-test-matrix.md` và `docs/abp-sat-encoding/*`.
- `docs/sat_spec.md`, `docs/technical_appendix_draft.md`, `docs/canonical_sat_config.md`: không còn tham chiếu thư mục handoff cũ (checker C9 xác nhận).

## 5. G4 readiness

- **Statement:** G4 PASS: triage 70/70 run frozen (CODE_BUG=0); consistency C1–C10 PASS (15 finding); checkbox W5 12/12.
- Frozen triage: `70` run, `CODE_BUG = 0`, all_triaged = `True`.
- SAT discussion complete = `True`; checkbox W5 = `12`.
- **Kết luận G4:** PASS.

## 6. Provenance

- Nguồn dữ liệu: `results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` (W3/W4 frozen pilot; `results/runs.csv` chưa có tại thời điểm chạy).
- Consistency checker chỉ đọc text/AST; không import `src.exact.*` (tránh phụ thuộc Ortools/Gurobi/CPLEX).
