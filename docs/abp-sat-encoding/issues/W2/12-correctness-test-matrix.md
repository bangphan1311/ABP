# 12: Test matrix correctness (encoding × AMO × backend)

**Tuần:** W2 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Bộ test kiểm mọi cấu hình Core khớp oracle. Cấu hình fail → chưa Core-ready.

**Blocked by:** 05, 08, 09, 10, 11 · Ext: oracle brute-force của P1

- [x] Ma trận: pairwise/order × pairwise/seqcounter × CaDiCaL/Glucose/Kissat.
- [x] Mọi cấu hình khớp oracle trên small instances.
- [x] Model counting trên instance cực nhỏ bằng blocking clause: không thừa, không thiếu nghiệm.
- [x] Random graph nhỏ: edge case (rời rạc, đỉnh cô lập, bậc lạ).
- [x] Output: bảng pass/fail theo cấu hình.

## Closure evidence (2026-11-03)

- Box 1: 8/8 cấu hình PASS trong `docs/handoff/w2-sat/12-test-matrix.md` — 8/8
  = CaDiCaL + Glucose; cột Kissat là N/A (không phải 2×2×3 = 12), lý do N/A ở
  `09-glucose-kissat-backend.md` Closure evidence.
- Box 2: 10/10 OPT-oracle mỗi cấu hình trong `12-test-matrix.md`.
- Box 3: bảng model counting gồm 2 dòng UNSAT (0 nghiệm), khớp
  `itertools.permutations`.
- Box 4: `disconnected`, `isolated`, `random8-seed42` trong `MATRIX_INSTANCES`.
- Box 5: bảng pass/fail theo cấu hình chính là output trong
  `12-test-matrix.md`.
