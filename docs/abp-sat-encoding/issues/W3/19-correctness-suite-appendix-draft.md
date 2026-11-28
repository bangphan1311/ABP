# 19: Correctness suite cuối + technical appendix nháp

**Tuần:** W3 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Chạy bộ correctness cuối; nháp appendix chứng minh công thức ABP.

**Blocked by:** 12, 18

- [x] Toy graphs, oracle instances, random graphs, edge cases: tất cả xanh. Fail → không freeze.
- [x] Appendix nháp chứng minh: assignment/permutation đúng; AMO đúng; distance đúng; SAT ↔ labeling hợp lệ; search không bỏ sót optimum.
- [x] Không copy chứng minh 2DBMP.

## Closure evidence (2026-11-09)

- Box 1: full suite `python -m pytest` tại commit đóng task: **568 passed, 3 skipped**
  (3 skip là test CPLEX CP engine vì `cpoptimizer.exe`/license không có trên máy,
  không phải fail). Ma trận encoding × AMO × backend và oracle brute-force ở
  `tests/sat/` + `docs/abp-sat-encoding/issues/W2/12-correctness-test-matrix.md`.
- Box 2: `docs/technical_appendix_draft.md` — A.1–A.5 (permutation, AMO, distance,
  SAT ↔ labeling, completeness của K-search).
- Box 3: `docs/technical_appendix_draft.md` ghi rõ chứng minh tự dựng, không copy
  2DBMP; đối chiếu `docs/sat_spec.md` và `docs/w2-sat/14-sat-methodology.md`.
