> **Lưu ý:** File này được sinh tự động bằng `python -m experiments.w6_signoff`, không chỉnh sửa tay.
> Nguồn: `docs/sat_spec.md`, `docs/technical_appendix_draft.md`, `docs/w5-sat/24..27`, `docs/canonical_sat_config.md`, `docs/sat_tooling.md`, `requirements.txt`, `src/sat/*`, `results/raw/*.json` (chỉ đọc).
> Phạm vi: in-repo SAT scope. Prose paper/LaTeX, P3 `runs.csv`, manuscript merge là deferred/external (mục 5).

# W6 — P2 SAT technical sign-off (in-repo scope)

## 1. Ticket 28 — Proofread thuật ngữ & ký hiệu SAT

Ticket 28 kết luận: **PASS** trên 7 check terminology/notation (W6-T1..W6-T7).

| Check | Status | File | Symbol | Expected | Actual | Message |
|---|---|---|---|---|---|---|
| `W6-T1` | **OK** | `docs/sat_spec.md` | `tên encoding + miền nhãn/đỉnh` | pairwise, order, nhãn 1..n, đỉnh 0..n-1 | đủ | — |
| `W6-T2` | **OK** | `docs/sat_spec.md` | `nhóm clause` | assignment, permutation, distance, threshold (không 'uniqueness') | đủ | — |
| `W6-T3` | **OK** | `docs/sat_spec.md` | `công thức biến` | x[v][p] (v*n+p, n²), o[v][p] (v*(n-1)+p, n(n-1)) | đủ | — |
| `W6-T4` | **OK** | `docs/sat_spec.md` | `mã trạng thái` | chỉ OPT/FEAS/TO/MO/ERR, không SATISFIABLE/TIMEOUT/OOM | đủ | — |
| `W6-T5` | **OK** | `docs/canonical_sat_config.md` | `tên/version solver + Kissat bị chặn` | python-sat==1.9.dev15; cadical195/glucose4/glucose42/minisat22; Kissat không là ứng viên | đủ | — |
| `W6-T6` | **OK** | `docs/sat_spec.md` | `var_of/n_vars live ↔ công thức tài liệu` | A.1: v*n+p (n²), A.2: v*(n-1)+p (n(n-1)) | pairwise n_vars=16, order n_vars=12 | — |
| `W6-T7` | **OK** | `docs/sat_spec.md` | `ngữ nghĩa ngưỡng` | trivial_unsat(n,k)==(k>=n), K=1 luôn SAT, không tài liệu nào nói K > n | đủ | — |

## 2. Ticket 29 — Claim verification + appendix audit

Ticket 29 kết luận: **PASS** (W6-C1 claim, W6-C2 lemma numbering, W6-C3 appendix integrity).

| Check | Status | File | Symbol | Expected | Actual | Message |
|---|---|---|---|---|---|---|
| `W6-C1` | **OK** | `docs/technical_appendix_draft.md` | `claim verification` | không claim định tính thiếu bằng chứng | 0 vi phạm | — |
| `W6-C2` | **OK** | `docs/technical_appendix_draft.md` | `dãy nhãn Lemma/Corollary/Theorem` | A.1..A.8, A.3.1, A.9..A.11 không trùng/thiếu | 12 nhãn | — |
| `W6-C3` | **OK** | `docs/technical_appendix_draft.md` | `section A.1–A.7 + số liệu path4` | A.1..A.7 đúng thứ tự; pairwise 56/74/86, order 32/50/62 | live={'pairwise': (56, 74, 86), 'order': (32, 50, 62)} | — |

## 3. Ticket 30 — Cross-read P3 + định dạng

Ticket 30 kết luận: **PASS** (W6-L1 correlation≠causation, W6-L2 Markdown table/format). Phần chữ nghĩa P3 (LaTeX, English copy-edit, hình/bảng/reference) deferred — xem mục 5.

| Check | Status | File | Symbol | Expected | Actual | Message |
|---|---|---|---|---|---|---|
| `W6-L1` | **OK** | `docs/canonical_sat_config.md` | `correlation hygiene` | không viết tương quan thành nhân quả | 0 vi phạm | — |
| `W6-L2` | **OK** | `docs/canonical_sat_config.md` | `markdown table lint` | bảng đủ cột, code span cân backtick | 0 vi phạm | — |

## 4. Ticket 31 — M3 technical sign-off

- Consistency W5 C1–C10: **PASS** (15 finding; nguồn `experiments/w5_final_analysis.py`, chi tiết `docs/w5-sat/26-cross-review-consistency.md` §1).
- Frozen triage: `70` run, `CODE_BUG = 0` (`src/sat/triage.py`, `results/raw/*.json`).
- Audit W6 FR-1..FR-8: **PASS** (12 finding, bảng BR-9 ở mục 6).
- Checkbox W1 01–07 + W6 28–31: **PASS**.
- **Statement:** P2 SAT Technical Sign-off = PASS (in-repo SAT scope). Triage 70/70 run frozen (CODE_BUG=0); consistency W5 C1–C10 PASS (15 finding); audit W6 PASS (12 finding); checkbox W1/W6 PASS. Deferred/external (không blocking): P3 LaTeX sections (P3, deferred); final English copy-edit (P3, deferred); paper/LaTeX prose (P1 writing the manuscript) (P1, deferred); paper/p2_sat_*.tex drafts from main (not audited by W6) (P1+P2, deferred); P3 official 24-instance runs.csv (P3, deferred); P3 manuscript merge (P3, deferred).

### Finding tổng hợp W6-M3

| Check | Status | File | Symbol | Expected | Actual | Message |
|---|---|---|---|---|---|---|
| `W6-M3` | **OK** | `docs/w6-sat/signoff_report.md` | `M3 aggregate (W5 C1–C10 + triage + W6 audit + checkbox)` | PASS (in-repo SAT scope) + danh sách deferred/external | PASS | — |

## 5. Deferred / external gates (không blocking)

| Hạng mục | Owner | Trạng thái |
|---|---|---|
| P3 LaTeX sections | P3 | deferred |
| final English copy-edit | P3 | deferred |
| paper/LaTeX prose (P1 writing the manuscript) | P1 | deferred |
| paper/p2_sat_*.tex drafts from main (not audited by W6) | P1+P2 | deferred |
| P3 official 24-instance runs.csv | P3 | deferred |
| P3 manuscript merge | P3 | deferred |

### Trạng thái đã biết (pre-existing, không phải W6 FAIL)

- `search_mode` stale-warning (`IGNORED_CONFIG_FIELDS` cảnh báo cho mode duy nhất đã cài đặt): ghi nhận tại `docs/canonical_sat_config.md` §Fixed axes, W2 resolve; W6 không mở lại.
- Hàng CNF trùng `order/seqcounter` ≡ `order/pairwise`: kiểm tra nhất quán RQ1 (BR-3 W5), không phải lỗi dữ liệu, không bị W6-L2 flag.
- Bằng chứng chặn Kissat nằm ở `docs/sat_tooling.md` mục Kissat; từ khoá `kissat` trong bảng incremental ở đó là evidence, không phải ứng viên.

## 6. Findings W6 (schema BR-9)

| Check | Status | File | Symbol | Expected | Actual | Message |
|---|---|---|---|---|---|---|
| `W6-T1` | **OK** | `docs/sat_spec.md` | `tên encoding + miền nhãn/đỉnh` | pairwise, order, nhãn 1..n, đỉnh 0..n-1 | đủ | — |
| `W6-T2` | **OK** | `docs/sat_spec.md` | `nhóm clause` | assignment, permutation, distance, threshold (không 'uniqueness') | đủ | — |
| `W6-T3` | **OK** | `docs/sat_spec.md` | `công thức biến` | x[v][p] (v*n+p, n²), o[v][p] (v*(n-1)+p, n(n-1)) | đủ | — |
| `W6-T4` | **OK** | `docs/sat_spec.md` | `mã trạng thái` | chỉ OPT/FEAS/TO/MO/ERR, không SATISFIABLE/TIMEOUT/OOM | đủ | — |
| `W6-T5` | **OK** | `docs/canonical_sat_config.md` | `tên/version solver + Kissat bị chặn` | python-sat==1.9.dev15; cadical195/glucose4/glucose42/minisat22; Kissat không là ứng viên | đủ | — |
| `W6-T6` | **OK** | `docs/sat_spec.md` | `var_of/n_vars live ↔ công thức tài liệu` | A.1: v*n+p (n²), A.2: v*(n-1)+p (n(n-1)) | pairwise n_vars=16, order n_vars=12 | — |
| `W6-T7` | **OK** | `docs/sat_spec.md` | `ngữ nghĩa ngưỡng` | trivial_unsat(n,k)==(k>=n), K=1 luôn SAT, không tài liệu nào nói K > n | đủ | — |
| `W6-C1` | **OK** | `docs/technical_appendix_draft.md` | `claim verification` | không claim định tính thiếu bằng chứng | 0 vi phạm | — |
| `W6-C2` | **OK** | `docs/technical_appendix_draft.md` | `dãy nhãn Lemma/Corollary/Theorem` | A.1..A.8, A.3.1, A.9..A.11 không trùng/thiếu | 12 nhãn | — |
| `W6-C3` | **OK** | `docs/technical_appendix_draft.md` | `section A.1–A.7 + số liệu path4` | A.1..A.7 đúng thứ tự; pairwise 56/74/86, order 32/50/62 | live={'pairwise': (56, 74, 86), 'order': (32, 50, 62)} | — |
| `W6-L1` | **OK** | `docs/canonical_sat_config.md` | `correlation hygiene` | không viết tương quan thành nhân quả | 0 vi phạm | — |
| `W6-L2` | **OK** | `docs/canonical_sat_config.md` | `markdown table lint` | bảng đủ cột, code span cân backtick | 0 vi phạm | — |
| `W6-M3` | **OK** | `docs/w6-sat/signoff_report.md` | `M3 aggregate (W5 C1–C10 + triage + W6 audit + checkbox)` | PASS (in-repo SAT scope) + danh sách deferred/external | PASS | — |

## 7. Provenance

- Module `experiments/w6_signoff.py` chỉ đọc text + dựng CNF `path4`; không chạy solver, không ghi `results/`.
- Không import `src.exact.*` (tránh Ortools/Gurobi/CPLEX).
- Test: `tests/experiments/test_w6_signoff.py`; checkbox W1/W6 do `emit_w1_checkbox_edits` / `emit_w6_checkbox_edits` sinh text.
