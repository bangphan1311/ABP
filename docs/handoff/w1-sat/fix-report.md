# Fix report — PR #3 (`w1-sat`), theo `pr3-review.md`

Owner: P2. Ngày: 2026-10-13. Branch: `p2/w1-sat` (push lên cùng PR #3).
Verify cuối: `.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-w1`
→ **`75 passed, 2 skipped in 2.40s`** (2 skip = test cần binary Kissat thật).

## Blocker

### B1 — Kissat ngoài binary: adapter xong, máy dev chưa có binary

- Commit: `15a5879` `feat(sat): run kissat as external binary`.
- Thay đổi:
  - `src/sat/kissat.py` (mới): `KissatBackend` cùng interface `SatBackend` (add_clause(s),
    solve(time_limit), get_model, status, n_vars, n_clauses, delete); ghi DIMACS ra file
    tạm, chạy `subprocess.run([binary, cnf])`, đọc exit code 10/20 + model ở dòng `v`.
  - `src/sat/solve.py`: `_open_backend()` → `Config(sat_solver="kissat")` dùng `KissatBackend`.
  - `src/sat/backend.py`: `SatBackend.add_clause` chặn family `kissat404` của PySAT bằng
    `BackendError` (trước đây native access violation giết process); bỏ `kissat404` khỏi
    `BUDGETED_FAMILIES`; tách `validate_clause()` dùng chung cho hai backend.
  - `docs/sat_tooling.md` mục 7: cách cài/trỏ binary (`ABP_KISSAT` hoặc `PATH`), cách đo
    `t_encode`/`t_solve` khi gọi ngoài, và bảng bằng chứng đã thử trên máy này.
- Verify: `tests/sat/test_kissat.py` — parser DIMACS/model, exit code lạ, thiếu binary → `ERR`
  không crash, binary hỏng → `ERR`; hai test chạy binary thật `skip` khi thiếu binary
  (đang skip: `2 skipped`).
- **Kết quả Kissat trên máy này: CHƯA CHẠY ĐƯỢC** (`kissat_path() -> None`). Lý do cụ thể:
  release upstream `arminbiere/kissat` `rel-4.0.4` chỉ có `apple-amd64/arm64`, `linux-amd64`
  (không có bản Windows); `winget search kissat` → không có; scoop main bucket không có
  manifest `kissat.json`; conda-forge `kissat` không có file `win-64`; PyPI `kissat`/`pykissat`
  → 404; máy không có `cl`/`gcc`/`clang`/`conda` để build từ source. Vì vậy trạng thái vẫn là
  **"chưa hỗ trợ"**, không giả lập hỗ trợ; có binary thì đặt `ABP_KISSAT` là test tự chạy.

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
- Verify: path4 → `clauses` per probe `[56, 74, 86]` cho `K = [1, 2, 3]`;
  `test_cnf_size_is_reported_even_when_no_sat_probe` (solve bị giả lập trả `UNKNOWN` → `TO`,
  vẫn có `variables`/`clauses`).

### S3 — Phiên bản thư viện + chạy test trên Python 3.11

- Commit: `6a69b82` (+ ghi chú ở `338763e`). Kiểm PyPI ngày 2026-10-13
  (`https://pypi.org/pypi/python-sat/json`): bản mới nhất là `1.9.dev15`, **không có bản stable
  nào** → giữ pin `python-sat==1.9.dev15`.
- Đã chạy toàn bộ suite trên venv 3.11 của repo, lệnh + kết quả ghi ở `docs/sat_tooling.md` mục 9:
  `75 passed, 2 skipped in 2.40s` (Python `3.11.15`; `docs/ENV.md` ghi `3.11.17` cho env conda
  của P1 — cùng minor).
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
kissat_path() -> None
```

## Chưa làm (và lý do)

- **Kissat chạy thật**: không có binary Windows trên máy này và không có toolchain C (chi tiết
  ở B1). Adapter + test + tài liệu đã xong; đặt `ABP_KISSAT` là chạy.
- **S5** (cận trên từ bậc đỉnh, `memory_limit` thực thi, order encoding): ngoài phạm vi được giao.
- **Hygiene**: newline cuối file của `src/sat/*.py`, `tests/sat/*.py` đã thêm (`9ac0d15`);
  `pyproject.toml`, `.python-version`, `AGENTS.md`, `docs/agents/` vẫn untracked (quyết định commit
  hay bỏ thuộc P1/P3 — NOTE 7 trong PR body).
- `docs/handoff/w1-sat/impl-report.md` vẫn nhắc `_summarise`/tìm kiếm nhị phân (tài liệu lịch sử,
  không sửa; `sat_spec.md` là nguồn hiện hành).
