# 08: AMO – pairwise + sequential counter

**Tuần:** W2 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Hàm `amo(literals, encoding)` với hai Core: pairwise và sequential counter (PySAT có sẵn). Đổi AMO không sửa encoding ABP.

**Blocked by:** 04

- [x] `amo(literals, encoding)` trả clause đúng cho pairwise và sequential counter.
- [x] Encoding ABP không đổi khi đổi AMO.
- [x] Test: AMO đúng với 0, 1, nhiều literal true (model counting nhỏ).
- [x] Không làm commander/product (Bonus, sau khi Core ổn).

## Closure evidence (2026-11-03)

- Box 1–3: `docs/handoff/w2-sat/12-test-matrix.md` mục "Ticket 08 closure — AMO
  exhaustive" — 64 tập con × mọi assignment, cả hai encoding, gồm 0/1 literal;
  test `tests/sat/test_matrix.py::test_amo_exhaustive_closure_over_all_subsets`.
- Box 2: ma trận 8/8 cấu hình trong `12-test-matrix.md` cho thấy đổi AMO không
  đổi encoding ABP và không đổi kết quả.
- Box 4: `SUPPORTED_AMO_ENCODINGS` trong `src/sat/pairwise.py` không chứa
  commander/product — xác nhận negative (Bonus bị cắt).
