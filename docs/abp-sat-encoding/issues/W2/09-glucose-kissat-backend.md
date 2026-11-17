# 09: Glucose + Kissat qua SatBackend

**Tuần:** W2 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Glucose và Kissat chạy qua cùng `SatBackend`, không pipeline riêng.

**Blocked by:** 02, 03

- [x] Glucose: solve, model, status, timeout, decode đúng.
- [ ] Kissat: solve, model, status, decode đúng (qua PySAT hoặc binary ngoài theo kết luận ticket 02). *(N/A — xem Closure evidence)*
- [x] Limitation ghi rõ; không giả lập hành vi sai. Kissat không vào incremental.
- [x] Nếu Kissat khó: binary ngoài + ghi cách đo; nếu vẫn khó: giữ CaDiCaL + Glucose cho RQ2, nêu hạn chế.

## Closure evidence (2026-11-03)

- Box 1: glucose4 columns PASS toàn bộ trong `docs/handoff/w2-sat/12-test-matrix.md`;
  test E2E `tests/sat/test_glucose_e2e.py`.
- Box 2 (không tick): N/A vĩnh viễn W2 — Kissat bị loại; chặn tại
  `PYSAT_KISSAT_FAMILIES` (`src/sat/backend.py`) và `_validate_solver`
  (`src/sat/solve.py` dòng 424); tests `tests/sat/test_backend.py`,
  `tests/sat/test_solve.py`; xem `docs/sat_tooling.md` mục Kissat. Nhánh chọn:
  giữ CaDiCaL + Glucose cho RQ2 (`docs/handoff/w2-sat/14-sat-methodology.md`
  §3.6).
- Box 3: limitation Kissat ghi trong `docs/sat_tooling.md`;
  `INTERRUPTIBLE_FAMILIES` trong `src/sat/backend.py` xác nhận Kissat không
  vào incremental.
- Box 4: nhánh fallback đã áp dụng — RQ2 giữ CaDiCaL + Glucose, hạn chế nêu
  trong `docs/sat_tooling.md`.
