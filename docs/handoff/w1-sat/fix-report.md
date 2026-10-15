# Fix report — PR #3 (`w1-sat`), theo `pr3-review.md`

Owner: P2. Ngày: 2026-10-13. Branch: `p2/w1-sat` (push lên cùng PR #3).
Verify cuối: `.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-w1`
→ **`72 passed`** (2026-10-14, sau khi bỏ Kissat — xem B1). Số `80 passed, 2 skipped` ghi ở
bản trước là trạng thái cũ, còn adapter/test Kissat.

## Blocker

### B1 — Kissat: gác sang W2, adapter đã bỏ

- Quyết định cuối: **bỏ Kissat khỏi W1, gác sang W2** (`pr3-review.md` R3 hướng B). W1 không
  có đường chạy Kissat.
- Thay đổi: xóa `src/sat/kissat.py` và `tests/sat/test_kissat.py`; bỏ hết wiring Kissat khỏi
  `src/sat/solve.py` / `src/sat/backend.py`.
- `Config(sat_solver="kissat")` nay ném `ValueError` (`"kissat chưa hỗ trợ ở W1; gác sang W2."`)
  trong `src/sat/solve.py` — chặn trước khi dựng backend, không để native crash.
- Lý do: family `kissat404` của PySAT giết process khi nạp clause (access violation, wheel
  `1.9.dev15` trên Windows); đường chạy binary ngoài **chưa kiểm chứng** được trên máy dev
  (không có binary, không có toolchain C); upstream `arminbiere/kissat` `rel-4.0.4` không có
  bản Windows. Chi tiết ở `docs/sat_tooling.md` mục 7.
- Verify: `tests/sat/test_solve.py::test_kissat_solver_is_deferred_to_w2` chốt `ValueError`.
  (Commit `15a5879` `feat(sat): run kissat as external binary` đã bị revert.)

### B2 — Duyệt K từ B+1, dừng ở UNSAT đầu tiên

- Commit: `cb3425c` `fix(sat): search K from B+1 and stop at first UNSAT`.
- `src/sat/solve.py::solve_sat`: bỏ tìm kiếm nhị phân; vòng lặp `K = lo + 1`, SAT → verify lấy
  `B` thực tế → `lo = B` → `K = B + 1`; UNSAT → `hi = K = lo + 1` → `OPT`. `B < K` từ một model
  SAT → `ERR` (mâu thuẫn encoding), chặn lặp vô hạn. `metadata["probes"]` thêm `"b"`.
- `docs/sat_spec.md` mục 5: viết lại chiến lược + giải thích vì sao `K ← B + 1` không bỏ sót
  ngưỡng, và `hi` chỉ nhận `n` (hết giờ) hoặc `lo + 1` (đã tối ưu).
- Verify: `test_k_search_increases_from_lower_bound_and_stops_at_first_unsat` (path6: mọi
  `probes[i+1]["k"] == probes[i]["b"] + 1`, probe cuối UNSAT, `lb == ub == k_last - 1`);
  `test_sat_reports_verified_value_and_encoding_size` khoá `probes.k == [1, 2, 3]` trên path4.

### B3 — `time_limit` bao cả encode, nạp clause và solve cho cả chuỗi K

- Commit: `338763e` `fix(sat): include encoding time in time_limit` (+ test tất định ở `3155f07`).
- `_probe` nhận "ngân sách còn lại": `≤ 0` trước encode → `UNKNOWN` (không dựng CNF); sau
  `add_clauses` → `remaining = budget - (perf_counter() - t0)` truyền vào `backend.solve`.
- `docs/sat_tooling.md` mục 4 và `docs/sat_spec.md` mục 7: bỏ ghi chú "encoding không tính vào
  deadline", ghi cơ chế mới + số đo (`grid(10,10)` limit 1.0 s → `t_total` 1.19 s; `grid(8,8)`
  limit 1.0 s → 1.10 s; limit 2.0 s → 2.29 s).
- Verify: `test_time_limit_covers_encoding_and_solve` (grid(8,8), limit 0.05 → `TO`/`FEAS`,
  `t_total < 2*limit + 2.0`) và test tất định
  `test_probe_passes_remaining_budget_to_solver_after_loading` (add_clauses tiêu hết ngân sách
  → `solve` nhận budget âm, trả `UNKNOWN`, CNF vẫn được giữ).

## Nên sửa

### S1 — `ub = hi - 1` khi FEAS

- Commit: `c3ca67f`. `summarise_result` trả `ub = hi - 1` (hi là ngưỡng đã chứng minh UNSAT);
  `docs/sat_spec.md` mục 6 cập nhật bảng + giải thích `hi = n` → `ub = n - 1`.
- Verify: `test_summarise_status_mapping` → `("FEAS", 2, 3, 1.0, 2)`; test FEAS qua API vẫn khớp
  `gap == ub - lb`.

### S2 — Số liệu RQ1 có cả khi TO

- Commit: `aeb739a`. `Result.variables/clauses` = CNF của **lần dò đầu tiên** (`K = 1`);
  `metadata["probes"]` ghi thêm `variables`, `clauses`, `t_encode` cho từng lần dò. Quy ước ghi
  rõ ở `docs/sat_spec.md` mục 6 và `docs/sat_tooling.md` mục 8.
  **Đã bị R1 thay (review lần 2)**: `Result.variables/clauses` nay lấy từ CNF ở lần dò **cuối
  cùng** trước khi chốt kết quả — quy ước hiện hành ở `docs/sat_spec.md` mục 6.
- Verify: path4 → `clauses` per probe `[56, 74, 86]` cho `K = [1, 2, 3]`;
  `test_cnf_size_is_reported_even_when_no_sat_probe` (solve bị giả lập trả `UNKNOWN` → `TO`,
  vẫn có `variables`/`clauses`).

### S3 — Phiên bản thư viện + chạy test trên Python 3.11

- Commit: `6a69b82` (+ ghi chú ở `338763e`). Kiểm PyPI ngày 2026-10-13
  (`https://pypi.org/pypi/python-sat/json`): bản mới nhất là `1.9.dev15`, **không có bản stable
  nào** → giữ pin `python-sat==1.9.dev15`.
- Đã chạy toàn bộ suite trên venv 3.11 của repo, lệnh + kết quả ghi ở `docs/sat_tooling.md` mục 9:
  `72 passed` (Python `3.11.15`; `docs/ENV.md` ghi `3.11.17` cho env conda của P1 — cùng minor).
- `solver_family()` vẫn đọc `vars(SolverNames)`; đã ghi rõ hệ quả (family lạ → `BackendError`
  khi có `time_limit`, không im lặng trả sai) ở `docs/sat_tooling.md` mục 1.

### S4 — Test dễ vỡ

- Commit: `3155f07`. `test_time_limit_stops_hard_instance` bỏ `assert < 3.0` giây, thay bằng
  `backend.solve_time < 2 * limit + 1.0` (bám theo limit truyền vào, không bám tốc độ máy).
  `_summarise` → `summarise_result` (public), test không import hàm private nữa.
  `test_solution_never_violates_proven_unsat_threshold` giờ khoá đúng `lb == ub == 2`, `gap == 0.0`
  trên path4 + kiểm `K = 3` UNSAT bằng `solve_decision` + `k_unsat == 3`, `unsat_source == "solver"`.

## So sánh oracle (bắt buộc)

```
path4     sat: OPT  lb=2 ub=2 gap=0.0 vars=16 cls=56  probes=[1, 2, 3]     | oracle: OPT lb=2 ub=2
cycle5    sat: OPT  lb=2 ub=2 gap=0.0 vars=25 cls=110 probes=[1, 2, 3]     | oracle: OPT lb=2 ub=2
complete3 sat: OPT  lb=1 ub=1 gap=0.0 vars=9  cls=24  probes=[1, 2]        | oracle: OPT lb=1 ub=1
path6     sat: OPT  lb=3 ub=3 gap=0.0 vars=36 cls=192 probes=[1, 2, 3, 4]  | oracle: OPT lb=3 ub=3
```

## Chưa làm (và lý do)

- **Kissat**: gác sang W2 (xem B1); adapter và test đã xóa, W1 không có đường chạy Kissat.
- **S5** (cận trên từ bậc đỉnh, `memory_limit` thực thi, order encoding): ngoài phạm vi được giao.
- **Hygiene**: newline cuối file của `src/sat/*.py`, `tests/sat/*.py` đã thêm (`9ac0d15`);
  `pyproject.toml`, `.python-version`, `AGENTS.md`, `docs/agents/` vẫn untracked (quyết định commit
  hay bỏ thuộc P1/P3 — NOTE 7 trong PR body).
- `docs/handoff/w1-sat/impl-report.md` vẫn nhắc `_summarise`/tìm kiếm nhị phân (tài liệu lịch sử,
  không sửa; `sat_spec.md` là nguồn hiện hành).
