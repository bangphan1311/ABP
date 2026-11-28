# 06: Loader + generator toy tối thiểu

**Tuần:** W1 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Đọc instance từ file và sinh graph nhỏ (path, cycle, grid, complete). Chưa tối ưu.

**Blocked by:** 01 (định dạng instance chốt cùng P3)

- [x] Đọc được một instance từ file theo định dạng đã chốt với P3 (`id, name, n, edges, source, tier`). (evidence: `src/sat/loader.py`)
- [x] Sinh path, cycle, grid, complete nhỏ. (evidence: `src/sat/generator.py`)
- [x] Test: số đỉnh, số cạnh đúng với từng họ graph. (evidence: `tests/sat/test_generator.py`)
- [x] Bản đầy đủ làm ở ticket 11. (evidence: `src/sat/loader.py`)
