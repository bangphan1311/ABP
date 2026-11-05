# Review QA — `w2-dry-run`: requirements, scope, code, evidence

Phạm vi review: `requirements.md` + `scope.md` (cùng thư mục) đối chiếu
`CONTRACT.md`, `src/runner/` (`runner.py`, `__main__.py`, `schema.py`,
`registry.py`), `tests/runner/test_runner.py`, `docs/handoff/abp-sat-encoding/issues/W2/08..15*.md`,
`docs/handoff/w2-sat/15-m1-gate-evidence.md`, `docs/handoff/w2-sat/12-test-matrix.md`,
`docs/handoff/w2-sat/13-review-p1-formulation.md`, `docs/handoff/w2-exact/16-w2-acceptance.md`.
Môi trường kiểm tra: Windows, `.venv` Python 3.11 (có `python-sat`), global
Python 3.13 (không có `python-sat`); branch `p2/w4-sat`; `git describe` =
`v0.1-contract-126-g6b6b8b5-dirty`.

Mục tiêu của file này: liệt kê chỗ requirements/scope **mâu thuẫn với code
thực tế**, chỗ **không thể kiểm được**, và chỗ **sẽ làm hỏng A1–A11 / D1–D6**
nếu implementer làm đúng câu chữ. Không phải danh sách khen.

## 1. Kết luận ngắn

Requirements và scope nhìn chung khớp nhau về mục tiêu, nhưng có **6 mâu thuẫn
chặn** (run_id, bool rendering, sửa text checkbox, ticket 13 box 3, D6 git
status, "no solver import") và **4 lỗ hổng kiểm thử** (Unicode/console,
pytest temp, python venv, §4.1 branch). Nếu không sửa các mục này trước khi
code, A9/A10/A11 và D3/D6 sẽ fail hoặc evidence §4.1 sẽ sai sự thật.

## 2. Mâu thuẫn (contradictions)

### C1 — `run_id` ví dụ trong requirements sai so với `make_run_id` (Chặn)

Requirements R4/R12 dùng các ví dụ:

```text
path4__oracle__na__na__na__na__sym0__ws0__s0__tl30.0__mlna
path4__oracle__na__na__na__na__sym0__ws0__s0__tl1800.0__mlna
```

Chạy thật `make_run_id` (`src/runner/schema.py` dòng 25–32) với
`generator.path(4)`:

```text
Config(method="oracle", time_limit=30)       -> ...__tl30__mlNone
Config(method="oracle", time_limit=1800.0)   -> ...__tl1800.0__mlNone
Config(method="oracle")                      -> ...__tlNone__mlNone
```

Nguyên nhân: `make_run_id` tạo `f"tl{config.time_limit}"` và
`f"ml{config.memory_limit}"`; phép thay `"na"` chỉ áp dụng khi **cả phần tử**
là `None`, không bao giờ đúng với hai chuỗi `"tl..."`/`"ml..."` này. Vì vậy
`memory_limit=None` render thành `mlNone`, không phải `mlna`; `time_limit=30`
(int) render `tl30`, không phải `tl30.0`.

Phân biệt:
- Ví dụ R4 (`Config(method="oracle", time_limit=30)`) sai **cả hai**: `tl30.0`
  phải là `tl30` (int), `mlna` phải là `mlNone`.
- Ví dụ R12 dùng CLI `--time-limit 1800` (argparse float) nên `tl1800.0`
  **đúng**; chỉ `mlna` sai → `mlNone`.

Hệ quả:
- A4/A9 viết theo ví dụ R12 sẽ fail (`mlna` không tồn tại).
- §4.1 "run_id matches make_run_id" nếu copy ví dụ `mlna` là ghi sai.
- D3 "output parses against R12" không được hiểu là khớp giá trị ví dụ.

Sửa: đổi ví dụ R4/R12 sang `mlNone` (và `tl30` cho ví dụ API); giữ nguyên
`make_run_id` (sửa `schema.py` sẽ đổi toàn bộ run_id cũ — ngoài scope).

### C2 — Quy tắc render bool mâu thuẫn với ví dụ R12 (Chặn cho A9)

R12 nói "every value via `str(value)`, except `None` renders as `none`".
Ví dụ R12 lại in `exists=false resume_would_skip=false` (chữ thường).
`str(False)` là `"False"`, không phải `"false"`. A9 "assert exact strings"
không thể thỏa cả hai. Sửa: thêm quy tắc "bool render `true`/`false`" vào
R12, hoặc đổi ví dụ thành `exists=False resume_would_skip=False`.

### C3 — R15 cấm sửa text checkbox, R16/R17 bắt buộc sửa (Chặn)

- R15: "The checkbox line text itself is not edited beyond the bracket."
- R16: "Every checkbox that stays unticked gets an **inline** reason
  annotation" (sửa text dòng checkbox).
- R17: ticket 15 box 2 "stale parenthetical ... **is replaced** by a short
  pointer" (sửa text dòng checkbox).

Ba câu không thể cùng đúng. Sửa: R15 phải ghi rõ ngoại lệ — được phép
thêm annotation sau text gốc và thay parenthetical của ticket 15 box 2;
cấm xóa/đổi nghĩa phần còn lại.

### C4 — Ticket 13 box 3: requirements và scope ra hai lệnh ngược nhau (Chặn quyết định)

- Requirements R17: chỉ tick nếu xác nhận được kết luận đã post lên GH #20
  (`gh issue view 20 ...` lúc chạy); nếu không thì để `[ ]` + annotation.
- Requirements D2: "13 box 3 **iff** GH #20 posting unconfirmed".
- Requirements Open questions: "check ... at execution time".
- Scope P1 mục 6: "**13 box 3: TICK** — ... đã verify 2026-11-03" (không điều kiện).
- Scope D2: "13 box 3 **tick** (đã resolve)".
- Scope Open questions: "none — cả ba đã resolve ... GH #20 posting ... đã có".

Không thể vừa "tick vô điều kiện" vừa "chỉ tick nếu check lúc chạy". Cần chốt:
hoặc chấp nhận bằng chứng scope (GH #42 + comment GH #20 + PR #48) và sửa
requirements R17/D2/Open questions; hoặc giữ requirements và sửa scope.
Nếu không chốt, implementer sẽ tick sai hoặc annotate sai.

### C5 — D6 "git status chỉ chứa ..." không thực hiện được (Chặn D6)

Scope D6 liệt kê file được phép thay đổi, nhưng thực tế `git status` trước
task đã có:
- 10 file `docs/handoff/sat-g1/instances/*.json` + `docs/handoff/sat-g1/results.json`
  đã modified từ trước.
- `docs/handoff/w2-dry-run/` là thư mục untracked, chứa `requirements.md`,
  `scope.md`, và chính `review-qa.md` — **không** nằm trong danh sách D6.

Vì vậy check tuyệt đối "git status chỉ chứa ..." fail ngay từ baseline.
Sửa: D6 phải là "diff so với baseline trước task" và bổ sung
`docs/handoff/w2-dry-run/requirements.md` + `review-qa.md` (hoặc ghi rõ
file handoff untracked được miễn check).

### C6 — "Dry-run không import solver module" mâu thuẫn với import graph hiện có (Chặn)

R3/R7 yêu cầu dry-run "does NOT import or execute any solver module" và A8
kiểm `sys.modules` không có solver module mới. Nhưng `src/runner/runner.py`
dòng 25 đã `from src.sat.loader import read_instance`; import này chạy
`src/sat/__init__.py` → `from src.sat.solve import ...` (dòng 3) →
`src.sat.solve` → `src.sat.backend` → `pysat`. Tức là **import `src.runner.runner`
đã kéo theo pysat và solver stack**, không phải chỉ khi gọi solver.

Hệ quả:
- Ví dụ OK "dry-run on a read-only checkout succeeds" sai trên máy không có
  pysat: global `python` 3.13 ở đây không có pysat; chỉ `.venv` có.
- R3 chỉ có thể đúng theo nghĩa hẹp: "không import module solver của config
  đang dry-run" — không phải "không import bất kỳ solver module nào".
- A8 dùng `tests.runner.nonexistent_module:solve` (module không tồn tại) nên
  phép kiểm `sys.modules` là **vacuous**: module đó không bao giờ xuất hiện dù
  code có import hay không. Cần dùng module có thật nhưng chưa import
  (ví dụ `tests.runner.slow_solver:solve_boom`) và kiểm bằng subprocess hoặc
  thứ tự test cẩn thận — `test_wrong_solution_is_caught_by_runner` đã
  `import tests.runner.slow_solver` trong parent process nên thứ tự test
  ảnh hưởng.

Sửa: cập nhật R3/R7/A8 theo nghĩa hẹp + ghi rõ import `src.sat` là có sẵn;
hoặc chuyển `read_instance` ra khỏi `src.sat` (đổi scope — không nên).

### C7 — `time_limit=None` không thể xuất hiện trên CLI (Trung bình)

R6/Edge case nói "`time_limit = None` → `hard_limit=none` in CLI output".
CLI hiện tại (`src/runner/__main__.py` dòng 20) là
`--time-limit type=float default=1800.0`; argparse không có đường truyền
`None`. R11 cấm đổi cách parse flag cũ. Vậy CLI **không bao giờ** in
`hard_limit=none`; chỉ API làm được. Sửa: bỏ claim CLI cho `None`, hoặc ghi
"API-only; CLI luôn float".

### C8 — Ticket 15 box 2 có 2 nửa, pointer §4.1 chỉ phủ 1 nửa (Trung bình)

Box 2: "Xem kết quả `--dry-run` của P3; **ước tính compute**." R17/D4 thay
parenthetical bằng pointer chỉ tới §4.1. Ước tính compute nằm ở §3 (đã có
từ trước), không phải §4.1. Sửa: pointer phải ghi "output thật ở §4.1;
ước tính compute ở §3" — nếu không, tick box 2 là tick thiếu nửa sau.

### C9 — Heading `## Closure evidence (2026-11-03)` là tiếng Anh, R18 bắt tiếng Việt (Thấp)

R15 cố định heading tiếng Anh; R18 nói "New prose added to these Vietnamese
files is written in Vietnamese". Heading là prose trong file tiếng Việt.
Sửa: hoặc cho phép heading là nhãn kỹ thuật cố định (carve-out trong R15),
hoặc đổi thành `## Bằng chứng đóng ticket (2026-11-03)`.

### C10 — Ticket 12 box 1 "8/8" không phải 2×2×3 như text ticket (Thấp)

Ticket 12 box 1: "pairwise/order × pairwise/seqcounter × CaDiCaL/Glucose/Kissat"
= 12 cấu hình. Bằng chứng `12-test-matrix.md` dòng 16 là "Ma trận 2 × 2 × 2 +
cột kissat N/A" = 8/8 cho 2 solver. Requirements R17 viết "8/8 config matrix
with kissat column documented N/A" — đúng nhưng dễ đọc thành "đủ 12". Sửa:
ghi rõ "8/8 cho CaDiCaL+Glucose; Kissat N/A" trong closure evidence.

### C11 — Ticket 09 box 4 là điều kiện, R17 không nói nhánh nào (Thấp)

Box 4: "Nếu Kissat khó: binary ngoài + ghi cách đó; nếu vẫn khó: giữ CaDiCaL +
Glucose cho RQ2, nêu hạn chế." R17 chỉ nói "boxes 1, 3, 4 tick" mà không nói
nhánh đã chọn. Sửa: closure evidence phải ghi rõ nhánh "Kissat bị loại vĩnh
viễn → giữ CaDiCaL + Glucose" (đúng `14-sat-methodology.md` §3.6).

### C12 — `_validate_solver` pointer thiếu vị trí nguồn (Thấp)

R16 ví dụ: "chặn tại `PYSAT_KISSAT_FAMILIES` và `_validate_solver`
(`tests/sat/test_backend.py`, `tests/sat/test_solve.py`)". Thực tế
`_validate_solver` nằm ở `src/sat/solve.py` dòng 424 (test files chỉ gọi).
Sửa: thêm `src/sat/solve.py` vào pointer.

### C13 — R4 "same instance content" không đúng; `make_run_id` dùng `instance.id` (Thấp)

R4 criterion nói "two dry-runs of the same (instance content, config) ...
produce the same run_id". `make_run_id` chỉ dùng `instance.id`, không dùng
edges/n/name. Hai file cùng `id` nhưng khác edges cho cùng run_id (edge case
đã ghi nhận). Sửa criterion: "same `instance.id` and config".

### C14 — A4 "does not collide" mơ hồ với cùng run_id (Thấp)

A4: "the real run writes its file and does not collide". Vì real run dùng
cùng `run_id`, nó ghi đúng path đó (kể cả đè file rác do A5 tạo). "Does not
collide" nên hiểu là "overwrite thành công, không lỗi"; test nên assert file
tồn tại + nội dung mới. Sửa wording.

### C15 — A7 ví dụ "empty graph" dễ trúng lỗi khác khi `n=0` (Thấp)

`read_instance` kiểm `0 <= endpoint < n` trước khi kiểm empty (dòng 81–91).
Instance `n=0` mà có edges sẽ raise "Cạnh ... ngoài khoảng đỉnh 0..-1", không
phải "Instance is empty (n = 0 or no edges)." A7 nên dùng `n>0` + edges rỗng
để trúng đúng message. Sửa ví dụ.

## 3. Rủi ro (risks)

### R1 — Unicode/console làm hỏng nhánh lỗi CLI (Chặn cho A10)

`python -m src.runner --help` crash thật trên console cp1252:

```text
UnicodeEncodeError: 'charmap' codec can't encode character '\u1ea1' ...
```

Nguyên nhân: `argparse.ArgumentParser(description="Chạy một solver ...")`
(`src/runner/__main__.py` dòng 12) có tiếng Việt; `print_help()` ghi ra
cp1252. Cùng rủi ro với `DRY_RUN ERROR: Method 'nope' không có trong registry...`
— message lỗi method chứa tiếng Việt; in ra stderr trên cp1252 sẽ raise
`UnicodeEncodeError`, tạo traceback và exit khác 2, vi phạm R13/A10.
Đường thành công in `DRY_RUN ...` toàn ASCII nên an toàn.

Sửa: ghi rõ CLI/test phải chạy với `PYTHONIOENCODING=utf-8` (hoặc
`sys.stderr.reconfigure(errors="replace")`), hoặc đổi message lỗi method
sang ASCII-safe (nhưng R3 yêu cầu cùng wording `registry.resolve` — không
đổi được). A10 phải set UTF-8 hoặc chấp nhận message thay thế.

### R2 — `pytest tests -q` fail mặc định vì quyền temp (Cao cho A11)

Chạy thật:

```text
pytest tests/runner/test_runner.py -q
PermissionError: [WinError 5] Access is denied:
'C:\Users\ducqu\AppData\Local\Temp\pytest-of-ducqu'
```

Với `--basetemp=.pytest-tmp`: 6/6 runner tests pass; full suite
`514 passed, 3 skipped in 27.00s`. Vậy A11 "pytest tests -q green" chỉ đạt
nếu dùng `--basetemp` hoặc sửa ACL temp. Requirements/scope nên ghi
workaround. Ngoài ra số test hiện tại là 514, không phải 422 như
`15-m1-gate-evidence.md` §1 (số liệu 2026-10-20 đã cũ — không chặn nhưng
đừng trích lại 422).

### R3 — `python` toàn cục không có pysat; `.venv` mới có (Cao cho §4.1)

Global `python` = 3.13, `ModuleNotFoundError: No module named 'pysat'`;
`.venv\Scripts\python.exe` = 3.11 có pysat. Câu lệnh mẫu `python -m src.runner ...`
trong R20 và "real execution" cho §4.1 phải dùng `.venv\Scripts\python.exe`
hoặc activate venv. Nếu implementer chạy bằng global python, dry-run crash
ngay ở import `src.sat` (xem C6), không có output để paste. Ghi rõ trong
§4.1 và trong hướng dẫn chạy.

### R4 — `git describe` có hậu tố `-dirty` do dirty tree sẵn có (Trung bình)

`git describe --tags --always --dirty` = `v0.1-contract-126-g6b6b8b5-dirty`
vì `docs/handoff/sat-g1/` đã modified từ trước. §4.1 "with branch and git_tag"
phải ghi đúng giá trị dirty và note rằng dirty là pre-existing (không phải
do task này). Nếu không, evidence trông như task làm bẩn repo.

### R5 — §4.1 "verbatim stdout" dễ copy nhầm ví dụ R12 sai (Cao)

Nếu implementer dùng ví dụ R12 (`mlna`, `false`) làm mẫu, output paste sẽ
không phải output thật. §4.1 phải chạy thật và paste nguyên văn; giá trị
`run_id` thực sẽ là `...mlNone`; bool thực sẽ là `False`/`false` tùy quyết
định C2. Ghi rõ "không copy ví dụ R12; tính từ `make_run_id` và output thật".

### R6 — `A3` monkeypatch `KILL_GRACE_SECONDS` phụ thuộc vị trí tính `hard_limit` (Trung bình)

A3 monkeypatch `runner_mod.KILL_GRACE_SECONDS = 7.5` và kỳ vọng
`dry_run.hard_limit == time_limit + 7.5`. Chỉ đúng nếu `hard_limit` được
tính **trong `src/runner/runner.py`** và đọc constant tại call time. Nếu
implementer đặt helper ở module mới hoặc `from ... import KILL_GRACE_SECONDS`
ở `__main__.py` (copy giá trị lúc import), monkeypatch `runner_mod` không
ảnh hưởng. Ghi rõ: tính trong `runner.py` hoặc đọc `runner.KILL_GRACE_SECONDS`
tại call time; CLI cũng phải dùng cùng nguồn.

### R7 — `A2` "không file nào thêm/sửa" dễ vỡ vì `tempfile.TemporaryDirectory` (Trung bình)

`run_one` hiện tạo `tempfile.TemporaryDirectory()` (dòng 50) trước khi ghi
record. Dry-run phải **bỏ qua toàn bộ block temp** (config.json/result.json)
trước khi làm bất cứ gì; nếu không, A2 sẽ thấy file mới trong temp (dù
`out_dir` không đổi). Ghi rõ thứ tự: `read_instance` → method check →
`make_run_id` → `exists` → `build_record`; không vào temp block, không mkdir.

### R8 — `A6` spy `subprocess.run` phải phân biệt `git describe` và worker (Thấp)

`build_record` gọi `git_tag()` → `subprocess.run(["git","describe",...])`
(`src/runner/schema.py` dòng 37–41); worker spawn dùng
`[sys.executable, "-m", "src.runner.worker", ...]` (`runner.py` dòng 60).
Spy phải cho phép `git describe` và chỉ fail worker pattern. Nếu spy thay
`subprocess.run` bằng mock trả `stdout=""`, `git_tag()` trả "unknown" — chấp
nhận được; nhưng nếu mock raise, `git_tag()` catch và trả "unknown"; fine.

### R9 — `A9` "exact strings" vs separator path (Thấp)

A9 vừa nói "assert exact strings" vừa nói "compare paths via `Path`". Dòng
`out_file` trên Windows dùng `\`, trên Linux `/`; không thể vừa exact vừa
platform-native. Sửa: so 4 dòng đầu exact; dòng `output` tách prefix
`DRY_RUN output out_file=` + so `Path(value)` + so phần `exists=...`.
Không so nguyên dòng có path.

### R10 — `D1` "mọi box ticked trong 08..15" bao gồm tick cũ của ticket 15 (Trung bình)

Ticket 15 có 3 box `[x]` từ trước (box 1, 3, 4). D1 đọc literally sẽ bắt task
thêm evidence pointer cho cả 3 box cũ — việc không nằm trong scope tick của
task. Sửa D1: "mọi box **do task này tick**" hoặc bổ sung pointer cho 3 box
cũ (nếu muốn đóng gói đầy đủ).

### R11 — §4.1 branch thực tế là `p2/w4-sat`, không phải `p2/w2-sat` (Thấp)

`15-m1-gate-evidence.md` dòng 3 ghi "Branch `p2/w2-sat`"; branch hiện tại là
`p2/w4-sat`. §4.1 phải ghi branch thật (`p2/w4-sat`) hoặc note branch đã đổi;
nếu không, evidence không tái lập được.

### R12 — R20 "recommended command" dùng `benchmark/` nhưng tier-1 nằm trong subdir (Thấp)

`benchmark/` chỉ có `toy/`, `validation/`, `large/`; không có file JSON ở
top-level. Tier-1 thực tế nằm ở `benchmark/validation/randconn10/12/14/16-seed20261026.json`
(`randconn8` là tier0; 20/24/28 vượt 16). Sửa ví dụ: dùng
`benchmark/validation/randconn16-seed20261026.json` hoặc file do generator ghi.

### R13 — `A11` "pytest tests -q green" phụ thuộc venv + quyền temp (Cao)

Như R2/R3. A11 chỉ đạt với `.venv\Scripts\python.exe` + `--basetemp` (hoặc
temp sạch). Nếu không ghi rõ, implementer sẽ báo A11 fail và tưởng code sai.
Ngoài ra suite có 3 skip (CPLEX CP engine thiếu — theo `13-review-p1-formulation.md`
R1); "green" phải hiểu là "passed + skipped", không phải "0 skip".

## 4. Lỗ hổng kiểm thử (testability gaps)

### T1 — A8 không chứng minh được "không import" (Cao)

Như C6: `tests.runner.nonexistent_module:solve` không tồn tại nên
`sys.modules` check luôn đúng. Đổi sang module thật chưa import
(`tests.runner.slow_solver:solve_boom`) và kiểm bằng subprocess
(`python -c "import src.runner.runner; ...; assert 'tests.runner.slow_solver' not in sys.modules"`).
Nếu chạy trong cùng process, `test_wrong_solution_is_caught_by_runner` đã
import `tests.runner.slow_solver`; thứ tự test sẽ làm A8 pass giả. Subprocess
là cách duy nhất đáng tin.

### T2 — A10 không kiểm được trên console cp1252 (Chặn)

Như R1: message lỗi method chứa tiếng Việt; `print(..., file=sys.stderr)`
raise `UnicodeEncodeError`. A10 phải set `PYTHONIOENCODING=utf-8` trong
subprocess hoặc `monkeypatch` `sys.stderr` với `errors="replace"`; nếu không,
test sẽ thấy traceback thay vì `DRY_RUN ERROR:`. Cũng phải assert exit code 2,
không phải 1/120.

### T3 — A9 không kiểm được path separator (Trung bình)

Như R9. Test phải normalize path; không so nguyên dòng. Nếu không, test pass
trên Windows và fail trên Linux CI (hoặc ngược lại).

### T4 — A11 không chạy được ngoài `--basetemp` (Cao)

Như R2. Ghi rõ lệnh chạy trong requirements/scope:
`.venv\Scripts\python.exe -m pytest tests -q --basetemp=.pytest-tmp`
(hoặc `TMPDIR` sạch). Không ghi rõ thì A11 "pytest tests -q" fail vì
`PermissionError`, không phải vì code.

### T5 — A2 "pre-existing dir containing files" chưa nói file ở đâu (Thấp)

A2 nói "with a pre-existing dir containing files, no file is added or
modified" — cần chỉ rõ "dưới `out_dir`" và "không tính temp dir"; nếu không,
`tempfile.TemporaryDirectory` (nếu lỡ vào block) sẽ tạo file ngoài `out_dir`
và test có thể bỏ sót hoặc fail oan.

### T6 — A7 "empty graph" chưa nói `n>0` (Thấp)

Như C15. Test nên dùng instance `n=4, edges=[]` để trúng message
"Instance is empty (n = 0 or no edges)."; `n=0` + edges trúng message khác.

### T7 — A5 "garbage bytes" chưa nói cách tạo `out_file` (Thấp)

A5 cần pre-create `out_file` = `out_dir / f"{run_id}.json"`, nhưng `run_id`
phải tính bằng `make_run_id(read_instance(p), cfg)` trước. Nếu test hardcode
`run_id` theo ví dụ R12 (`mlna`), file rác sẽ nằm sai path và `exists` sai.
Test phải tính `run_id` từ code, không copy ví dụ.

### T8 — A4 "real run" sau dry-run có thể đè file rác (Thấp)

Như C14. A4 nên chạy real run với `out_dir` sạch (không pre-create) để
"does not collide" có nghĩa; hoặc assert overwrite thành công nếu pre-create.

### T9 — D3 "git diff only §4.1 and §6 bullet" không kiểm được nếu baseline dirty (Trung bình)

`15-m1-gate-evidence.md` hiện không dirty, nhưng repo có dirty files khác.
D3 nên so `git diff -- docs/handoff/w2-sat/15-m1-gate-evidence.md` (file-specific),
không so toàn repo. Nếu không, D3 fail vì dirty files khác.

### T10 — D6 không kiểm được vì pre-existing dirty + untracked handoff dir (Chặn)

Như C5. Sửa D6 thành baseline diff và bổ sung `requirements.md`/`review-qa.md`;
hoặc chấp nhận untracked dir là ngoại lệ.

### T11 — §4.1 "verbatim command" thiếu môi trường chạy (Cao)

Như R3. Câu lệnh trong §4.1 phải ghi rõ interpreter
(`.venv\Scripts\python.exe -m src.runner ...`) và biến môi trường
(`PYTHONIOENCODING=utf-8` nếu console cp1252), nếu không người đọc không
tái lập được output.

### T12 — A6 spy chỉ bắt `subprocess.run`, không bắt `Popen`/`check_output` (Thấp)

Hiện worker dùng `subprocess.run`; nhưng nếu implementation mới dùng
`subprocess.Popen` hoặc `check_output` cho worker, spy A6 sẽ bỏ sót. Ghi rõ
A6 phải spy cả `run`/`Popen`/`check_output` hoặc ít nhất `run` + assert
không có call nào chứa `"src.runner.worker"`.

### T13 — A3/A9 không kiểm `KILL_GRACE_SECONDS` qua CLI (Thấp)

A3 chỉ test API; CLI dùng cùng constant nhưng nếu CLI copy giá trị lúc
import, monkeypatch không ảnh hưởng. Thêm test CLI với monkeypatch hoặc
ghi rõ CLI đọc `runner.KILL_GRACE_SECONDS` tại call time.

### T14 — A8/A9 không kiểm `sys.argv` vs `main()` return code (Thấp)

A9 nói "with sys.argv monkeypatched ... main() returns 0"; cần assert
`main()` return 0 và stdout 5 dòng. Nếu dùng subprocess, assert exit code 0.
Fine, nhưng ghi rõ một trong hai, không "or".

## 5. Việc cần chốt trước khi code (blockers)

1. **Sửa ví dụ run_id R4/R12** sang `mlNone` (và `tl30` cho API) — hoặc sửa
   `make_run_id` (không nên; đổi toàn bộ run_id cũ).
2. **Chốt quy tắc render bool** `true`/`false` hay `True`/`False`; sửa R12
   example tương ứng; A9/§4.1 theo quy tắc đó.
3. **Chốt quyền sửa text checkbox**: R15 phải carve-out annotation + ticket
   15 box 2 parenthetical; nếu không R16/R17 vi phạm R15.
4. **Chốt ticket 13 box 3**: requirements (conditional) hay scope
   (unconditional). Sửa bên thua; không để implementer tự quyết.
5. **Sửa D6**: baseline diff + thêm `requirements.md`/`review-qa.md`; hoặc
   ghi rõ untracked handoff dir được miễn.
6. **Sửa R3/R7/A8** theo nghĩa hẹp "không import solver module của config";
   ghi rõ `src.sat` package import là có sẵn; A8 dùng module thật + subprocess.
7. **Ghi rõ môi trường chạy** cho A11/§4.1: `.venv\Scripts\python.exe`,
   `--basetemp`, `PYTHONIOENCODING=utf-8` (nếu cp1252).
8. **Sửa C7** (time_limit=None CLI-only), **C8** (pointer §4.1 + §3),
   **C9** (heading language), **C10** (8/8 vs 2×2×3), **C11** (box 4 branch),
   **C12** (`_validate_solver` source path), **C13** (instance.id),
   **C15** (empty graph n>0) — nhỏ nhưng ảnh hưởng A7/A9/closure evidence.

Không có mâu thuẫn nào đòi đổi `CONTRACT.md` §5; `"DRY_RUN"` là status cấp
runner như C1 trong requirements đã ghi. Nhưng nếu record dry-run bị đưa vào
`runs.csv` (ngoài ý định), nó vi phạm CONTRACT §5 — cần giữ nguyên nguyên tắc
"dry-run không ghi đĩa" (R5/R7).
