# 18: Đề xuất canonical SAT configuration

**Tuần:** W3 · **Owner:** P2 (Quang) đề xuất, P1/P3 cùng chốt · **Status:** decision recorded; host enforcement remains a separate freeze gate

**What to build:** Chọn cấu hình SAT cho RQ3 dựa trên pilot. Chọn trước khi chạy official.

**Blocked by:** 16, 17

- [x] `abp_encoding=order`, `amo_encoding=pairwise` theo pilot RQ1.
- [x] `sat_solver=glucose4` theo Protocol Core RQ2; `minisat22` chỉ là baseline ngoài Core.
- [x] `search_mode=multi`, `symmetry=false`, `warm_start=false`, `seed=0`.
- [x] Ghi pilot evidence và lý do chọn vào `docs/canonical_sat_config.md` trước official run.
- [x] Chốt `memory_limit=12.0 GiB` theo preflight candidate host; P3 phải xác nhận host/Job Object trước M2 freeze.

## Closure evidence (2026-11-09)

- Box 1–3: `docs/canonical_sat_config.md` — bảng quyết định
  (`order`, `pairwise`, `glucose4`, `multi`, `symmetry=false`, `warm_start=false`,
  `seed=0`) kèm số liệu pilot RQ1/RQ2 dùng để chọn.
- Hằng số đã khóa trong code: `CANONICAL_SAT_CONFIG` ở `src/sat/solve.py`, xuất qua
  `src/sat/__init__.py`; hàm dựng `canonical_sat_config()` mặc định `memory_limit=12.0`
  GiB và từ chối `None`/giá trị không hợp lệ cho run official.
- Box 4: lý do chọn ghi cùng file `docs/canonical_sat_config.md` (mục RQ1, RQ2,
  "Fixed axes", "Consequences for the official run"); quyết định lấy trước khi có
  bất kỳ official result nào.
