# 18: Đề xuất canonical SAT configuration

**Tuần:** W3 · **Owner:** P2 (Quang) đề xuất, P1/P3 cùng chốt · **Status:** ready-for-human

**What to build:** Chọn cấu hình SAT cho RQ3 dựa trên pilot. Chọn trước khi chạy official.

**Blocked by:** 16, 17

- [x] `abp_encoding`, `amo_encoding` theo pilot RQ1.
- [x] `sat_solver` theo pilot RQ2.
- [x] `search_mode = multi`, `symmetry = false`, `warm_start = false`.
- [x] Ghi lý do chọn vào `docs/`. Không xem official result trước khi chọn.

## Closure evidence (2026-11-09)

- Box 1–3: `docs/canonical_sat_config.md` — bảng quyết định
  (`order`, `pairwise`, `glucose4`, `multi`, `symmetry=false`, `warm_start=false`,
  `seed=0`) kèm số liệu pilot RQ1/RQ2 dùng để chọn.
- Hằng số đã khóa trong code: `CANONICAL_SAT_CONFIG` ở `src/sat/solve.py`, xuất qua
  `src/sat/__init__.py`; hàm dựng `canonical_sat_config()` bắt buộc `memory_limit`
  tường minh cho run official (memory-limit validation, ticket B3).
- Box 4: lý do chọn ghi cùng file `docs/canonical_sat_config.md` (mục RQ1, RQ2,
  "Fixed axes", "Consequences for the official run"); quyết định lấy trước khi có
  bất kỳ official result nào.
