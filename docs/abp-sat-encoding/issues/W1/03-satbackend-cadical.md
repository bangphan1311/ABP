# 03: SatBackend interface + CaDiCaL

**Tuần:** W1 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Lớp `SatBackend` (add_clause(s), solve, get_model, status) chạy CaDiCaL. Encoding không gọi trực tiếp CaDiCaL.

**Blocked by:** 01

- [x] Interface đủ: add_clause(s), solve, get_model, status. (evidence: `src/sat/backend.py`)
- [x] Adapter CaDiCaL implement interface. (evidence: `src/sat/backend.py`)
- [x] Đổi backend không cần sửa encoding (kiểm bằng test giả backend hoặc đổi tên solver). (evidence: `tests/sat/test_backend.py`)
- [x] Test: clause nhỏ SAT/UNSAT đúng; model đọc được. (evidence: `tests/sat/test_backend.py`)
- [x] Đặt tại `src/sat/`. (evidence: `src/sat/backend.py`)
