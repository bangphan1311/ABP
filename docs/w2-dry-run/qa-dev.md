# QA — W2 dry-run (`--dry-run`) — Phase 3 early API/component + unit/CLI

Ngày: 2026-11-03 · Branch: `p2/w4-sat` · Interpreter: `.venv\Scripts\python.exe` (3.11.15)
Nguồn: `test-plan.md`, `api-contract.md`, `requirements.md`, `scope.md`,
`dev-notes.md`, `infra.md` (cùng thư mục).

## Verdict

**BLOCK** — dry-run crash (exit 1, traceback, 4/5 dòng) khi `--out` chứa ký tự
non-ASCII trên console cp1252, trong khi run thật cùng `--out` exit 0; thêm một
test A8 không chứng minh được điều nó tuyên bố.

## Tests written

Không thêm file test mới (A11: test cũ không sửa). Đã chạy suite hiện có và
probe thủ công:

- `pytest tests/runner/test_runner.py -v` — 29 passed (6 test cũ + 23 test mới).
- `pytest tests -q` — 537 passed, 3 skipped (CPLEX CP engine), khớp `dev-notes.md`.
- Probe CLI: `--method` ∈ {sat, cp_sat, gurobi_mip, cplex_cp, cplex_mip, oracle},
  dotted path, `--sat-solver kissat` (thiếu backend), `--time-limit` {0, -5, nan,
  inf}, `--memory-limit -1`, `--seed -1`, `--method ""`, `--method ":"`,
  `--out` {file, `CON`, `a*b`, 300 ký tự, `Z:\nope`, UNC, trailing separator,
  non-ASCII}, `--resume` + out_dir vắng, `--instance` là thư mục, id chứa
  `\n`, `\0`, `../evil`, `..\evil`, non-ASCII.
- Probe API: `sys.modules` snapshot trong interpreter trần; `out_dir` str vs
  `Path`; `resume=1`; `wall_time` độc lập `time_limit`.
- Probe docs: chạy lại đúng lệnh §4.1 — stdout khớp verbatim, exit 0,
  `git status --porcelain results/raw` rỗng.

## Bugs

### B1 — `src/runner/__main__.py:55-57` — non-ASCII `--out` + cp1252 làm dry-run crash

`_print_dry_run` in `out_file` (dòng 5) bằng `print()` không có lossy-safe.
`out_file` là `str(Path(out_dir) / ...)`, nên `--out` do người dùng nhập là
nội dung non-ASCII. Trên console cp1252 (`PYTHONIOENCODING=cp1252`), `print`
raise `UnicodeEncodeError`; `_print_dry_run` nằm ngoài `try/except` (dòng 93),
nên traceback + exit 1, sau khi đã in 4/5 dòng.

Kịch bản thật (đã chạy):

```
$env:PYTHONIOENCODING="cp1252"
.venv\Scripts\python.exe -m src.runner --instance benchmark/toy/path4.json `
  --method oracle --out "C:\Users\ducqu\AppData\Local\Temp\opencode\đường" --dry-run
# exit 1, 4 dòng DRY_RUN + traceback UnicodeEncodeError tại __main__.py:55
```

Run thật cùng `--out` + cp1252: exit 0, không crash (run thật không in
`out_file`). Đây là **regression do dry-run**, không phải hành vi cũ.

Trái với giả định trong `review-qa.md:219` ("Đường thành công in `DRY_RUN ...`
toàn ASCII nên an toàn") và `api-contract.md:193-195` ("The five lines are pure
ASCII; instance.id and paths are the only user-controlled content, and their
exposure is identical to the existing result line"). Câu "identical to the
existing result line" sai với path: result line thật không in `out_file`.

Fix hint: trong nhánh `--dry-run`, gọi `sys.stdout.reconfigure(errors="replace")`
khi có (giống `_make_stderr_lossy_safe`), hoặc render `out_file` lossy-safe
(`ascii(info["out_file"], "backslashreplace")`), hoặc sửa R12/api-contract:
path non-ASCII là exposure mới, không "identical". Thêm test CLI với `--out`
non-ASCII + `PYTHONIOENCODING=cp1252`.

### B2 — `tests/runner/test_runner.py:331` — test A8 không chứng minh "no new modules"

`test_dry_run_method_check_imports_nothing` assert
`set(sys.modules) - before == set()`. Test chỉ pass vì `pytest` đã import sẵn
`socket` (và các test trước trong file đã gọi `build_record`). Trong
interpreter trần, dry-run **có** import module mới:

```
$ .venv\Scripts\python.exe -c "import sys; import src.runner.runner as rm; ..."
new: ['_socket', 'select', 'selectors', 'socket']
```

Nguyên nhân: `build_record` → `host_name()` → `platform.node()` → `socket`.
Đây là stdlib, không phải solver module, nên ý định R3/R7 ("no NEW solver-module
import") vẫn đúng; nhưng câu chữ A8/R7 ("no NEW module appears") bị vi phạm và
test không bắt được. Test order-dependent: chạy riêng vẫn pass vì pytest
pre-import `socket`; chạy assertion trong interpreter trần thì fail.

Fix hint: thu hẹp assertion về solver module (ví dụ
`{m for m in after - before if m.startswith(("src.sat", "src.exact", "pysat", "gurobipy", "cplex"))} == set()`),
hoặc pre-import `socket` trong test và ghi carve-out vào R7/A8. Không sửa
`build_record` (ngoài scope).

### B3 — `tests/runner/test_runner.py:430-447` — cp1252 test không chạm message tiếng Việt

`test_cli_dry_run_failure_exits_2_cp1252_safe` dùng instance empty-graph →
message ASCII (`"Instance is empty (n = 0 or no edges)."`). Message tiếng Việt
(`"không có trong registry"`) chỉ được test ở `test_cli_dry_run_unknown_method_exits_2:450`
**không** set `PYTHONIOENCODING=cp1252`. Tổ hợp rủi ro thật (cp1252 + tiếng
Việt) không được test. Probe thủ công xác nhận code chạy đúng (exit 2,
`DRY_RUN ERROR:` lossy, không traceback), nhưng test-plan C4 yêu cầu chạy C3b
với cp1252 — test hiện tại không làm.

Fix hint: thêm `env_extra={"PYTHONIOENCODING": "cp1252"}` vào
`test_cli_dry_run_unknown_method_exits_2` (hoặc tham số hoá codec).

### B4 — `src/runner/__main__.py:55-57` — `--out` là file / drive không tồn tại / UNC → báo "OK" giả

`--out` trỏ tới file (`afile`), `Z:\nope`, `\\server\share\x`: dry-run in
`exists=false`, exit 0. Run thật crash tại `out_dir.mkdir(...)`
(`runner.py:79`). Đã ghi nhận là edge case chấp nhận trong
`review-be.md:281-284`; không phải bug mới, nhưng chưa có trong danh sách edge
case của `requirements.md`/`api-contract.md`. Fix hint: thêm một dòng vào
"Known divergences" (không thêm validation — R10 cấm).

### B5 — `src/runner/__main__.py:35-36` — `instance.id` chứa `\n` phá hợp đồng 5 dòng

`id = "a\nb"` → dòng 1 và dòng 2 tách thành 4 dòng; `splitlines()` trả 7 dòng.
Run thật cũng vỡ (result line đơn cũng chứa `\n`), nên đây là exposure cũ,
không phải regression. Mức thấp; generator id là ASCII. Fix hint: ghi nhận
trong edge cases; không cần sửa nếu chấp nhận "exposure giống result line".

### B6 — `src/runner/schema.py:30` — path traversal qua `instance.id` (pre-existing)

`id = "../evil"` → `run_id = "../evil__oracle__..."` → `out_file` nằm ngoài
`out_dir`. Dry-run chỉ báo path; run thật sẽ ghi ra ngoài `out_dir`. Không do
task này gây ra (`make_run_id` ngoài scope), nhưng dry-run làm lộ ra. Mức
thông tin; không chặn.

## Could not check

- Run thật với solver (`sat`, `cp_sat`, `gurobi_mip`, `cplex_cp`, `cplex_mip`) —
  dry-run không chạy solver; chỉ kiểm tra dry-run pass.
- Linux/macOS separator rendering (`out_file` dùng `/`) — chỉ chạy Windows.
- Console cp1252 thật (không phải pipe) — probe dùng pipe; crash giống nhau vì
  `sys.stdout` vẫn encoding cp1252.
- `--help` cp1252 crash — pre-existing, ngoài scope (R13 giữ nguyên).
- `--dry-run` cho `experiments/pilot_rq*.py` — ngoài scope.
