> **Lưu ý:** File này được sinh tự động bằng `python -m experiments.w5_final_analysis`, không chỉnh sửa tay.
> Nguồn dữ liệu: `results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json` (W3/W4 frozen pilot; `results/runs.csv` chưa có tại thời điểm chạy)

# Paper v0.9 — SAT sections (W5)

Phần SAT của paper: §3 methodology, RQ1 final, RQ2 final, technical appendix A.1–A.7. Mọi số lấy từ frozen dataset và sinh tự động.

## §3 SAT methodology

### §3.1 Bài toán quyết định

Cho đồ thị đơn vô hướng `G = (V, E)`, `n = |V|`, `m = |E|`. Antibandwidth của song ánh `f: V → {1..n}` là `B(f) = min_{{u,v} ∈ E} |f(u) − f(v)|`. Bài toán quyết định tại ngưỡng `K ≥ 1`: tồn tại `f` với `B(f) ≥ K`. `K` phải là `int ≥ 1`; `n = 0` hoặc `m = 0` là `ValueError`; `K ≥ n` là UNSAT trước khi dựng CNF (`trivial_unsat`, `src/sat/pairwise.py`).

### §3.2 Biến SAT

- `pairwise`: `x[v][p] = 1` khi đỉnh `v` nhận nhãn `p ∈ {1..n}`; `id = v * n + p`; `n²` biến chính. Aux của AMO bắt đầu từ `n² + 1`.
- `order`: `o[v][p] = 1` khi `f(v) ≤ p`, `p ∈ 1..n−1`; `id = v * (n − 1) + p`; `n(n−1)` biến. Biên `p = 0` luôn sai, `p = n` luôn đúng.

### §3.3 Ràng buộc

| Nhóm | `pairwise` | `order` |
|---|---|---|
| `assignment` | ALO + AMO mỗi đỉnh: `n + n·C(n,2)` | chuỗi đơn điệu: `n(n−2)` |
| `permutation` | ALO + AMO mỗi nhãn: `n + n·C(n,2)` | no-good mỗi cặp đỉnh × nhãn: `n·C(n,2)` |
| `distance` | binary clause mỗi cạnh × cặp nhãn: `m·2·Σ max(0, n−d)` | no-good trên nhãn, cùng phép duyệt: `m·2·Σ max(0, n−d)` |
| `threshold` | `K ≥ n` → UNSAT, 0 clause | như `pairwise` |

Đếm tay `path4` (`n = 4`, `m = 3`) khớp code và test: `pairwise` K = 1/2/3 có 56/74/86 clause; `order` có 32/50/62 clause.

### §3.4 AMO

`amo(literals, encoding, pool)` (`src/sat/pairwise.py`). `pairwise` AMO là `C(m,2)` clause `(¬a ∨ ¬b)`, không thêm biến; `seqcounter` dùng `pysat.card.CardEnc.atmost(bound=1)`. Encoding `order` không dùng AMO: chuỗi đơn điệu thay ALO + AMO nên `amo_encoding` chỉ là metadata. Hệ quả: `order/pairwise` và `order/seqcounter` có CNF trùng — kiểm tra nhất quán, không phải bằng chứng AMO.

### §3.5 Chiến lược duyệt K

Duyệt `K ← B + 1` từ cận dưới đã verify; SAT thì decode, `verify`, lấy `B`; UNSAT đầu tiên thì `K − 1 = B` tối ưu và dừng. Timeout thì dừng. Không incremental, không binary search; mỗi ngưỡng dựng CNF và backend mới. `Config.time_limit` là ngân sách cho cả chuỗi K. Anti-bandwidth được làm tròn; xem `docs/sat_spec.md` §5.

### §3.6 Backend solver

`SatBackend` (`src/sat/backend.py`) bọc PySAT. Solver default `cadical195`; timeout theo family: interrupt + watchdog cho Glucose/MiniSat, conflict-budget loop cho CaDiCaL. Kissat bị chặn vĩnh viễn. RQ2 dùng CaDiCaL + Glucose (Core) và thêm `minisat22`, `glucose42` (baseline).

### §3.7 Đo lường

`t_encode` quanh `build_cnf`; `t_solve` quanh `backend.solve`; `t_total` toàn bộ `solve_sat`; `peak_memory` là max working set đo bằng `GetProcessMemoryInfo` tại các mốc (không phải peak liên tục). Incremental load clause nằm trong `t_total`, không trong `t_encode`/`t_solve`.

### §3.8 Decode và verify

`decode_model` dựng labeling từ model; vi phạm hoán vị là `ValueError`. Mọi nghiệm đi qua `verify(instance, labeling)` trước khi vào `Result`; model chưa phải nghiệm.

### §3.9 Bằng chứng

`tests/sat/test_matrix.py` (ma trận encoding × AMO × solver), `tests/sat/test_order.py`, `tests/sat/test_pairwise.py`, `tests/sat/test_glucose_e2e.py`; appendix chứng minh trong `docs/technical_appendix_draft.md`.

### §3.10 Giới hạn

Chỉ hai encoding Core (không staircase); không incremental; không symmetry breaking/warm start (off by design); memory đo trên Windows và là max của điểm chụp; dữ liệu frozen chỉ tới `n = 50`.

## RQ1 Final

| `abp_encoding` | `amo_encoding` | OPT | FEAS | TO | PAR2 (s) | Σ `t_total` (s) | Max Clauses | Max Mem (MB) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `order` | `seqcounter` | 10/10 | 0 | 0 | 23.12 | 23.12 | 196450 | 112.99 |
| `order` | `pairwise` | 10/10 | 0 | 0 | 23.24 | 23.24 | 196450 | 111.41 |
| `pairwise` | `seqcounter` | 9/10 | 1 | 0 | 130.81 | 88.50 | 147500 | 87.62 |
| `pairwise` | `pairwise` | 9/10 | 1 | 0 | 133.76 | 86.43 | 255400 | 126.53 |

**Kết luận:** `order`/`pairwise` biểu diễn bài toán tốt hơn và giúp solving trên tập frozen: 10/10 OPT, PAR2 23.24 s, max 196450 clause / 111.41 MB. Không có suy luận “CNF nhỏ → nhanh”: cả hai chiều đảo được ghi ở `docs/w5-sat/24-rq1-final.md` §3.

**Case study (a) CNF nhỏ nhưng chậm:** xem bảng đảo chiều `docs/w5-sat/24-rq1-final.md` §3.1 (`pairwise`/`seqcounter` vs `order`/`pairwise` trên `randconn20/24/28/40`).

**Case study (b) CNF lớn nhưng nhanh:** `order`/`pairwise` nhiều clause hơn nhưng đạt OPT trên `randconn40` trong 16.249 s, trong khi `pairwise`/`seqcounter` 82 160 clause lại FEAS 77.684 s; và `n = 50` giải nhanh hơn `n = 40` dưới cả 4 solver RQ2.

**Case study (c) pairwise blowup:** `pairwise`/`pairwise` có `n²` biến và tổng clause `O(n³)`; đo được 255 400 clause / 126.53 MB tại `n = 50`. Projection HB-scale (mẫu dày `m = n(n−1)/8`, cap `12288` MB) cho thấy `pairwise`/`pairwise` vượt cap trong khi `order` bị chặn bởi `n(n−1)` biến và không có nhóm AMO. MO chỉ đến từ `MemoryError` ngoài process, không phải solver enforce cap.

## RQ2 Final

| Hạng | Solver | Vai trò | OPT | PAR2 (s) | Max Mem (MB) |
|---:|---|---|---:|---:|---:|
| 1 | `minisat22` | PySAT baseline | 10/10 | 16.61 | 99.30 |
| 2 | `glucose4` | Protocol Core | 10/10 | 17.13 | 100.26 |
| 3 | `glucose42` | PySAT baseline | 10/10 | 17.49 | 99.91 |
| 4 | `cadical195` | Protocol Core | 10/10 | 23.24 | 111.41 |

**Kết luận Core:** `glucose4` thắng trong `{cadical195, glucose4}` theo OPT coverage → PAR2 → memory. Caveat: `cadical195` chịu chi phí conflict-budget wrapper (`src/sat/backend.py:238-254`).

**Case study (a) độ nhạy:** xem bảng density/Δ/UB và `t_total` từng solver trong `docs/w5-sat/25-rq2-final.md` §4. Subset frozen không tách được “A thắng thưa, B thắng dày”; đó là scope limitation.

**Case study (b) FEAS không OPT:** hai run `randconn40` với `pairwise`/`pairwise` và `pairwise`/`seqcounter` có `lb = 14`, `ub = 39`, `gap = 25`; `ub = 39` là cận đếm `n − 1`, không phải bound chặt. Chuỗi probe đầy đủ ở `docs/w5-sat/25-rq2-final.md` §5.

**Kissat:** loại vĩnh viễn (model sai, assumptions bị bỏ qua, abort sau `add_clause`, không có binary ngoài). Không có hàng Kissat trong bảng.

## Technical Appendix A.1–A.7 (W5 state)

### A.1 Pairwise encoding

`x[v][p]`, `id = v*n + p`, `n²` biến. Clause: assignment (ALO + AMO), permutation (ALO + AMO), distance (binary no-good mỗi cạnh × cặp nhãn cách nhau dưới K). Lemma A.1–A.3 và Corollary A.3.1 giữ nguyên; `K ≥ n` UNSAT trước khi dựng CNF.

### A.2 Order encoding

`o[v][p]`, `id = v*(n-1) + p`, `n(n-1)` biến. Chain thay ALO + AMO; permutation và distance dùng `_not_value`; `q = 1`/`q = n` còn một literal, interior còn hai. Lemma A.4–A.7 giữ nguyên.

### A.3 At-most-one encodings

`pairwise` và `seqcounter` faithful; Lemma A.8: cùng projection trên biến nhãn. Với `order`, AMO là metadata, không đổi clause.

### A.4 Equivalence theorem

Theorem A.9: SAT tại `K` ⇔ tồn tại labeling `B(f) ≥ K`, cho cả hai encoding; `K ≥ n` UNSAT. Theorem A.10: decode luôn trả hoán vị hoặc `ValueError`. Theorem A.11: objective được tính lại bởi `verify()`.

### A.5 Multi-run K search: completeness

Invariants `lo ≤ B*` và `hi > B*`; mỗi vòng `k = lo + 1`; SAT tăng `lo`, UNSAT đặt `hi = k`; dừng ở UNSAT đầu tiên. Không bỏ ngưỡng vì nhảy `K ← B + 1`. Tối đa `n − 1` probe. OPT chỉ khi `lo + 1 == hi`; FEAS giữ `lb = lo`, `ub = hi − 1`.

### A.6 What this appendix does not claim

1. Không claim UNSAT proof đúng (trust boundary).
2. Không claim thứ tự kích thước CNF như định lý; đó là đo đạc instance-dependent.
3. Không claim bảo đảm bộ nhớ: `memory_limit` không được solver enforce trong process; `canonical_sat_config()` mặc định cap `12.0` GiB và từ chối `None`/giá trị không hợp lệ cho run official; MO chỉ từ `MemoryError` ngoài process.
4. Không claim timeout cứng: deadline kiểm giữa các pha nên `t_total` có thể vượt `time_limit`.
5. Không claim từ symmetry/warm start: chưa cài đặt, đặt khác mặc định thì warning; `search_mode="multi"` là mode duy nhất đã cài đặt và không warning.

### A.7 Empirical anchors

`tests/sat/test_matrix.py`, `tests/sat/test_g1_oracle.py`, `tests/sat/test_glucose_e2e.py`, `tests/sat/test_pairwise.py`, `tests/sat/test_order.py`; frozen W3/W4 pilots; W5 generated reports 24–26.

## Fairness SAT vs exact

1. `wall_time` của runner là metric chính thức.
2. `time_limit` SAT là ngân sách cả chuỗi K; exact chỉ pha solve; runner hard-kill tại `time_limit + 30` giây.
3. `ub` khi TO là cận (SAT `hi − 1`; exact bound hoặc `n − 1`), không phải gap tới optimum.
4. `MIPGap = 0` / gap tolerances: `MIP_optimal_tolerance` bị loại khỏi OPT.
5. Mọi nghiệm dùng chung `verify()`.

## Trace table

| Mục | Nguồn |
|---|---|
| §3.1–§3.2 | `docs/sat_spec.md` §1–§2; `src/sat/pairwise.py`; `src/sat/order.py` |
| §3.3 | `docs/sat_spec.md` §3; `docs/w2-sat/14-sat-methodology.md` §3.3; `tests/sat/test_pairwise.py`; `tests/sat/test_order.py` |
| §3.4 | `src/sat/pairwise.py::amo`; `docs/technical_appendix_draft.md` A.3/A.8 |
| §3.5 | `docs/sat_spec.md` §5; `src/sat/solve.py`; `docs/technical_appendix_draft.md` A.5 |
| §3.6 | `src/sat/backend.py`; `docs/sat_tooling.md` |
| §3.7 | `src/sat/solve.py`; `docs/sat_tooling.md` |
| §3.8 | `src/sat/solve.py`; `src/common/verify.py`; `docs/sat_spec.md` §4 |
| RQ1 | `docs/w5-sat/24-rq1-final.md`; `results/pilot_rq1.csv` |
| RQ2 | `docs/w5-sat/25-rq2-final.md`; `results/pilot_rq2.csv` |
| Appendix | `docs/technical_appendix_draft.md`; `docs/canonical_sat_config.md` |

## G4 status

- G4 PASS: triage 70/70 run frozen (CODE_BUG=0); consistency C1–C10 PASS (15 finding); checkbox W5 12/12.
- Consistency C1–C10: PASS (15 finding); xem `docs/w5-sat/26-cross-review-consistency.md`.
- Không còn placeholder; mọi bảng nêu nguồn frozen.
