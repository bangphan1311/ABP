# W1 — P2 SAT & Encoding: báo cáo triển khai

Branch: `p2/w1-sat` (từ `main` @ `7c7a858`). Chưa push, chưa mở PR.
Trạng thái: T1–T8 xong phần Core; các mục Bonus/Out-of-scope bị bỏ có ghi lý do bên dưới.

## Lưu ý môi trường (cần P1/P3 đọc)

- Máy này **không có** conda env `abp` (không tìm thấy `conda` trong PATH hay trên ổ C:),
  và `docs/ENV.md` ghi Python 3.11.17. Không có Python 3.11 trên máy.
- Đã chạy toàn bộ W1 bằng `.venv` của repo: **Python 3.14.6**, cài qua `uv`:
  `uv pip install python-sat pytest ortools --python .venv\Scripts\python.exe`
  → `python-sat==1.9.dev15`, `pytest==9.1.1`, `ortools==9.15.6755`.
- Vì vậy các số đo (thời gian, kích thước) là của Python 3.14.6 + PySAT 1.9.dev15, không
  phải của môi trường ghi trong `docs/ENV.md`. Cần xác nhận lại trên env `abp` chính thức
  (không sửa `docs/ENV.md`).
- `requirements.txt` đã thêm `python-sat==1.9.dev15` (pin theo bản đã kiểm chứng).

## T1 — Chốt PySAT

- File: `requirements.txt` (thêm `python-sat==1.9.dev15`), `docs/sat_tooling.md` mục 1.
- Verify: `python -m pytest tests/sat/test_backend.py -q` → `10 passed`.
  Script solve CNF toy: `tests/sat/test_backend.py::test_solve_toy_cnf_sat`.
- Kết luận: CaDiCaL (`cadical195`) là mặc định; lấy model, timeout đều chạy
  (xem T3/T8).

## T2 — Đặc tả SAT

- File: `docs/sat_spec.md` (~1.5 trang).
- Nội dung: bài toán quyết định K, biến `x[v][p] = v*n + p`, 4 nhóm ràng buộc
  (`assignment`, `permutation`, `distance`, `threshold`), SAT/UNSAT, decode, chiến lược
  duyệt K (tìm kiếm nhị phân `[1, n]`), bảng status/lb/ub/gap, interface
  (`solve_sat`, `solve_decision`), format JSON của loader.
- Verify: `docs/sat_spec.md` khớp với code — số clause ví dụ (path4 K=2: 16 biến, 74 clause,
  assignment 28 / permutation 28 / distance 18) được assert trong `tests/sat/test_pairwise.py`.

## T3 — `SatBackend`

- File: `src/sat/backend.py`.
- Interface: `add_clause`, `add_clauses`, `solve(time_limit)`, `get_model`, `status`,
  thêm `n_vars`/`n_clauses`/`solve_time`/`delete`.
- Verify: `.\.venv\Scripts\python.exe -m pytest tests/sat/test_backend.py -v`
  → `10 passed` (CNF toy SAT/UNSAT, model, literal biên, solver sai, timeout thật,
  family solver dựng được).

## T4 — Một encoding (pairwise)

- File: `src/sat/pairwise.py` — `build_cnf` tách theo 4 nhóm, `amo(literals, encoding, pool)`,
  `decode_model`, `trivial_unsat`.
- Encoding thứ hai (`order`): **bỏ**, ngoài phạm vi W1 (plan mục "Out").
- Verify (đếm tay): `tests/sat/test_pairwise.py`
  - path4 K=2 → 16 biến, 74 clause, nhóm 28/28/18.
  - path4 K=3 → 86 clause, distance 30.
  - path4 K=1 → distance 0.
  - `amo([1,2,3,4], "pairwise")` → đúng 6 clause liệt kê tay.
  - Kết quả: `12 passed`.

## T5 — Pipeline solve một K

- File: `src/sat/solve.py` (`solve_sat`, `solve_decision`, `_probe`, `_summarise`).
- Verify (khớp oracle, chạy tay):

```
instance sat.status  sat.lb oracle.lb  ub  verify  match
path4    OPT              2         2   2       2   True
cycle5   OPT              2         2   2       2   True
K3       OPT              1         1   1       1   True
P6       OPT              3         3   3       3   True
OK: solve_sat matches solve_oracle on all 4 toy instances
```

- Cùng nội dung ở dạng test: `tests/sat/test_solve.py::test_sat_matches_oracle_on_toy_instances`.

## T6 — Loader + generator

- File: `src/sat/loader.py` (JSON, validate biên), `src/sat/generator.py`
  (`path`, `cycle`, `grid`, `complete`).
- Verify: `tests/sat/test_io.py` → `14 passed` (roundtrip, file viết tay, 9 ca file sai:
  thiếu trường, `n` sai kiểu/âm, cạnh sai dạng/ngoài khoảng/tự khuyên, `id` không phải chuỗi;
  số cạnh generator).
- Format đã chốt trong `docs/sat_spec.md` mục 8 — cần P3 xác nhận trước khi dùng chung.

## T7 — Test

- File: `tests/sat/test_backend.py`, `test_pairwise.py`, `test_solve.py`, `test_io.py`.
- Verify: `.\.venv\Scripts\python.exe -m pytest tests/sat -v` → `46 passed in 1.23s`.
- Full suite: `.\.venv\Scripts\python.exe -m pytest tests/ -q` → `58 passed in 2.00s`.
- Có random graph nhỏ (seed cố định, n=5..7), graph rời + đỉnh cô lập, và so oracle.

## T8 — Tooling note

- File: `docs/sat_tooling.md` — mỗi mục có kết luận hoặc "chưa hỗ trợ".
- Kết luận đáng chú ý:
  - Timeout: 2 cơ chế theo family — `interrupt()` (MiniSat-like, chính xác theo đồng hồ) và
    `conf_budget()` tăng dần (CaDiCaL/Kissat). Đo trên PHP(13 lỗ) với `time_limit=0.3`:
    glucose4 dừng ở 0.30 s, cadical195 ở 0.33 s. `lingeling` **chưa hỗ trợ** timeout.
  - Kissat: **chưa hỗ trợ** — `Solver(name='kissat')` dựng được nhưng crash access violation
    (`0xC0000005`) khi nạp clause trong wheel PySAT 1.9.dev15 (Windows/py3.14). Có lệnh tái hiện
    trong doc. Không suy đoán thêm, không tự chế hỗ trợ.
  - `amo` có sẵn: `pysat.card.EncType` (pairwise/seqcounter/cardnetwrk/totalizer/...);
    `native` **chưa hỗ trợ** (ràng buộc nằm ngoài clause).
  - `peak_memory`: **chưa đo** ở W1 (`None`), đề xuất `psutil` RSS cho chạy chính thức;
    `tracemalloc` không thấy bộ nhớ native.

## Đã bỏ (có lý do)

- Encoding thứ hai (`order`), AMO sequential counter tự kiểm, Glucose/Kissat tích hợp đầy đủ,
  multi-run K search, staircase/incremental/assumption/symmetry/commander/product: ngoài phạm vi
  W1 (plan, mục "Out"/"Bonus").
- Chưa đo `peak_memory`, chưa tách `t_add_clauses` khỏi `t_total`.
- Chưa push/PR (Tech Lead làm sau review).

## Rủi ro mở

1. **Môi trường**: số đo trên Python 3.14.6/PySAT 1.9.dev15, không phải env `abp` 3.11 như
   `docs/ENV.md`. Cần P1/P3 chạy lại `pytest tests/` trong env `abp` và xác nhận (đặc biệt
   `python-sat` có wheel cho 3.11 không).
2. **Timeout của CaDiCaL** là theo ngân sách xung đột, không theo giây: `time_limit` sát ngưỡng
   có thể vượt deadline (bounded bởi vòng trước). Cần đo kỹ ở W2 nếu `PROTOCOL.md` yêu cầu
   cắt cứng theo giây (khi đó phải chuyển mặc định sang `glucose4` hoặc chạy subprocess).
3. **Cờ interrupt còn sót** ở family dùng `interrupt()`: hướng sai là thận trọng (`FEAS`/`TO`
   thay vì `OPT`), không cho nghiệm sai; W1 dựng backend mới mỗi ngưỡng nên ảnh hưởng cục bộ.
4. **Chất lượng encoding** chỉ được kiểm chứng trên graph nhỏ (n ≤ 7 vs oracle) và đếm clause
   tay. Chưa có model counting / kiểm chứng độc lập ở n=8..12 (đề xuất W2).
5. **`Config.method`** hiện chỉ là nhãn; chưa có runner phân nhánh theo method (P3 sở hữu).
6. **Kissat** chỉ dùng được nếu gọi binary ngoài; PySAT 1.9.dev15 wheel này không dùng được.

## QA fixes (theo `docs/handoff/w1-sat/test-report.md`)

Owner: P2. Branch `p2/w1-sat`, 4 commit riêng, chưa push/PR.

| WARN | Commit | Nội dung |
|---|---|---|
| WARN-2 (trust boundary) | `b56a3c4` `fix(sat): raise ValueError on invalid edge endpoints` | `_validate_instance` kiểm mọi đầu mút cạnh phải là `int` trong `0..n-1`; trước đây instance dựng tay làm `build_cnf` ném `KeyError` |
| WARN-4 (Kissat) | `b21286f` `fix(sat): drop kissat from supported solvers` | `kissat` ra khỏi `SUPPORTED_SOLVERS`/`supported_solvers()` (crash process khi nạp clause); kết luận "chưa hỗ trợ" giữ ở `docs/sat_tooling.md` mục 7 |
| WARN-1 (time_limit) | `10a09d0` `docs(sat): state time_limit scope` | Ghi rõ `time_limit` chỉ chặn phần solve; encode + nạp clause không tính vào deadline, vượt đo được tới ~20 lần — trong `docs/sat_tooling.md` mục 4, `docs/sat_spec.md` mục 7, docstring `solve_sat`. **Không** thêm deadline logic mới |
| WARN-3 (field bị bỏ qua) | `67739ab` `fix(sat): warn on ignored config fields` | `memory_limit`/`search_mode`/`symmetry`/`warm_start`/`seed` khác mặc định → một `UserWarning` từ `solve_sat`/`solve_decision`; ghi chú ở `docs/sat_spec.md` mục 7 |

Test mới: 4 ca `test_invalid_edge_endpoint_raises_value_error` (ngoài khoảng, âm, không phải
`int`, `bool`) + `test_ignored_config_fields_emit_one_warning` +
`test_default_config_fields_emit_no_warning` (`tests/sat/test_solve.py`).

Đếm test (Python 3.14.6, PySAT 1.9.dev15, `.venv`):

```
$ .\.venv\Scripts\python.exe -m pytest tests/sat -q
52 passed in 1.38s          # trước QA: 46

$ .\.venv\Scripts\python.exe -m pytest tests -q
64 passed in 1.83s          # trước QA: 58
```

Đếm lại sau review PR #3 (lần 2) — head `20f8b25`, `.venv` Python `3.11.15`, PySAT `1.9.dev15`:

```
$ .\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-w1
80 passed, 2 skipped in 5.09s
```

Đây là **số đúng** (2 skip = test cần binary Kissat thật). Các số `64`/`58` và `75 passed,
2 skipped in 2.40s` ghi ở các báo cáo trước là ảnh chụp cũ, thiếu test thêm sau đó.

Kiểm chứng WARN-2 bằng tay (trước đây `KeyError`):

```
ValueError: Cạnh (0, 9) chứa đỉnh ngoài khoảng 0..3.
ValueError: Đỉnh trong cạnh (0, 1) phải là số nguyên: '1'.
ValueError: Cạnh (-1, 1) chứa đỉnh ngoài khoảng 0..3.
```

Không đụng `src/common/`, `src/exact/`, `docs/ENV.md` (`git diff main --name-only` giữ nguyên
13 file như trên). Các NOTE của QA (đặc biệt NOTE 2 mất số đo khi `ERR`, NOTE 4 comment test
`K = n`, NOTE 5 phạm vi lỗi Kissat, NOTE 7 `pyproject.toml`/`.python-version` untracked)
**chưa** xử lý — ngoài phạm vi 4 WARN này.
