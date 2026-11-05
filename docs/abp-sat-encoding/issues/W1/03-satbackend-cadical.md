# 03: SatBackend interface + CaDiCaL

**Tuần:** W1 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Lớp `SatBackend` (add_clause(s), solve, get_model, status) chạy CaDiCaL. Encoding không gọi trực tiếp CaDiCaL.

**Blocked by:** 01

- [ ] Interface đủ: add_clause(s), solve, get_model, status.
- [ ] Adapter CaDiCaL implement interface.
- [ ] Đổi backend không cần sửa encoding (kiểm bằng test giả backend hoặc đổi tên solver).
- [ ] Test: clause nhỏ SAT/UNSAT đúng; model đọc được.
- [ ] Đặt tại `src/sat/`.
