# Scope — W2 dry-run: runner `--dry-run`, W2 checkbox closure, M1 evidence update

Nguồn: `requirements.md` (cùng thư mục). Baseline contract: `CONTRACT.md`
(repo root). Văn bản mới trong các file ticket là tiếng Việt, định danh kỹ
thuật giữ nguyên (R18). Findings từ review đã fold vào văn bản này:
`review-qa.md` (C1–C15, R1–R13, T1–T14) và `review-be.md` (B1–B6, I1–I11)
cùng thư mục — mỗi quyết định resolve được ghi tại mục liên quan.

## Goal

W2 còn đúng một gap: runner `src/runner` chưa có cờ `--dry-run` (blocker mục 2
của ticket 15, blocker mục 4 của `docs/handoff/w2-sat/15-m1-gate-evidence.md`),
checklist W2 ticket 08..15 chưa được đóng kèm bằng chứng kiểm chứng được, và
bằng chứng gate M1 chưa ghi nhận output `--dry-run` thật. Task này đóng cả ba
mà không đụng vào quyết định **NO-GO** đã ghi ở mục 6 của evidence doc.

## In scope

- `src/runner/runner.py`: `run_one(..., dry_run=...)` (R1–R10), trả về
  `DryRunRecord` đúng shape của requirements (R8); `dry_run` là dict thường,
  `out_file` là `str` — không dataclass mới (I4). Thứ tự trong dry-run branch:
  `read_instance` → method check → `make_run_id` → `out_file` → return —
  không mkdir, không vào block `tempfile.TemporaryDirectory` (I2).
  `hard_limit` tính trong `runner.py`, đọc `KILL_GRACE_SECONDS` tại call time
  (R6). "Không import solver" theo nghĩa hẹp: không import module solver mới
  ngoài những gì `import src.runner.runner` đã load sẵn (`src.sat` stack,
  pysat — I1), và không execute solver nào. 1 dòng docstring: dry-run record
  không được persist (I11).
- `src/runner/__main__.py`: cờ `--dry-run`, stdout đúng 5 dòng `DRY_RUN`
  (R12) — bool render thường `true`/`false`, `None` render `none` (B2);
  exit 0/2 (R13) — `try/except (ValueError, OSError)` chỉ bọc nhánh
  `--dry-run`, đường run thật byte-identical (I3); compose được với
  `--resume` (R14).
- `tests/runner/test_runner.py`: test cho A1–A11; suite cũ giữ nguyên. Lệnh
  chạy: `.venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp`
  — temp mặc định của Windows bị khoá quyền (`PermissionError WinError 5`),
  basetemp đặt ngoài repo (R2/I10); global `python` 3.13 thiếu pysat, chỉ
  `.venv` có (I9).
- `docs/handoff/abp-sat-encoding/issues/W2/08..15*.md`: tick/annotate checkbox
  theo bằng chứng (R15–R17) + section `## Closure evidence (2026-11-03)`.
  Quy tắc sửa text dòng checkbox (carve-out của R15/R16 — B4): dòng checkbox
  08–14 giữ nguyên text gốc, chỉ đổi bracket; ngoại lệ duy nhất là 09 box 2
  được append tag N/A sau text gốc (Kissat N/A vĩnh viễn W2, R16) và 15 box 2
  thay parenthetical cũ bằng pointer (R17); 13 box 3 tick vô điều kiện (B5).
  Không xoá box, không đổi thứ tự, không đổi nghĩa phần text còn lại.
- `docs/handoff/w2-sat/15-m1-gate-evidence.md`: chỉ thêm §4.1 (lệnh + stdout
  thật, verbatim) và 1 pointer ở bullet "Việc còn mở của gate" của §6
  (R19–R20). Lệnh §4.1 dùng `.venv\Scripts\python.exe` và `--out results/raw`
  (path trong output là relative, không leak máy — B3) trên
  `benchmark/toy/path4.json`:
  `.venv\Scripts\python.exe -m src.runner --instance benchmark/toy/path4.json --method sat --abp-encoding pairwise --amo-encoding seqcounter --sat-solver cadical195 --search-mode multi --time-limit 1800 --out results/raw --dry-run`
  (hoặc tier-1 trong `benchmark/validation/`, vd
  `randconn16-seed20261026.json`); ghi kèm branch thật (`p2/w4-sat`) và
  `git describe --tags --always --dirty` thật — hậu tố `-dirty` là dirty sẵn
  có của `docs/handoff/sat-g1/`, không phải do task (R4 review-qa).
- Ticket 15: box 2 `[x]` + pointer về §4.1 (output thật) **và** §3 (ước tính
  compute — C8), thay parenthetical cũ (R17).

## Out of scope

- `CONTRACT.md` — không sửa §5; `"DRY_RUN"` chỉ là status cấp runner, không
  bao giờ ghi đĩa, không vào `runs.csv` (C1).
- `src/runner/schema.py` / `make_run_id` — không sửa: ví dụ run_id trong docs
  là phần sai, không phải code; đổi `make_run_id` sẽ đổi tên toàn bộ file
  `results/raw` cũ và phá `--resume` (B1/S4).
- `src/runner/worker.py`, `src/sat/**`, `src/exact/**`, `src/common/**`.
- Bất kỳ enforcement memory-limit nào; `memory_limit_enforced=false` là literal
  cố định nêu sự thật hiện tại (C2).
- GitHub issue state sync (labels, GH checkbox) — chỉ markdown trong repo
  (R18); `Status:`/`Owner:`/`Blocked by:` không đổi.
- Ước lượng CNF-size/runtime trong dry-run — §3 evidence doc đã có ước tính
  từ số liệu matrix; dry-run chỉ báo số đo được (n, m, budget, run_id, resume).
- Re-decide M1 GO/NO-GO; nội dung quyết định mục 6 giữ byte-identical — kể cả
  chỗ §4/§6 tự mâu thuẫn với §4.1 mới; đó là record có ngày, không "sửa giúp"
  (review-be, minor).
- `experiments/pilot_rq1.py` / `pilot_rq2.py` không thêm `--dry-run`.
- Stash/revert dirty sẵn có của `docs/handoff/sat-g1/` để cho `git status`
  sạch (S7) — D6 được viết lại theo baseline thay vì dọn repo.

## Prioritization

**Required (P0 — không có thì task không ship):**

1. API `run_one(..., dry_run=False)` keyword-only, hành vi run thật không đổi
   (R1, R4–R10) + shape `DryRunRecord` (R8) — `dry_run` dict thường (I4),
   dry-run không đụng block temp/mkdir (I2).
2. CLI `--dry-run`: 5 dòng stdout đúng định dạng — bool `true`/`false` thường
   (B2), exit 0/2, hợp `--resume` (R11–R14).
3. Test A1–A11; full suite xanh qua lệnh venv + `--basetemp` ở trên; test cũ
   không sửa (A11); "green" = passed + skipped (3 skip CPLEX CP engine là
   bình thường — R13 review-qa).
4. §4.1 trong `15-m1-gate-evidence.md`: chạy thật bằng
   `.venv\Scripts\python.exe` + `--out results/raw` trên
   `benchmark/toy/path4.json` (hoặc tier-1 trong `benchmark/validation/`),
   paste lệnh + stdout verbatim — không copy ví dụ R12 làm giá trị kỳ vọng
   (R5 review-qa); kèm nhận diện `run_id` (suffix
   `...__tl1800.0__mlNone` — `mlNone`, không bao giờ `mlna`;
   `--time-limit 1800` qua argparse là float),
   `hard_limit = time_limit + KILL_GRACE_SECONDS`,
   `memory_limit_enforced=false`, và tuyên bố scope: chỉ đóng blocker
   `--dry-run`, decision giữ NO-GO (R19–R20).
5. Ticket 15 box 2 `[x]` + pointer §4.1 + §3 (D4/C8).

**Should-have (P1 — ship cùng PR; cắt trước khi chậm):**

6. Tick checkbox 08–14 theo mapping bằng chứng đã kiểm của R17; box không tick
   được thì annotate lý do (R15–R16). Riêng **13 box 3: TICK** — kết luận review
   P1 đã được ghi nhận trên GH #20 / GH #42 và PR #48 (`p1/w2-review-closeout`)
   đã merge; bằng chứng: `docs/handoff/w2-sat/13-review-p1-formulation.md`,
   `docs/handoff/w2-exact/16-w2-acceptance.md` (không cần `gh issue view` lại
   lúc chạy — đã verify 2026-11-03; requirements R17/D2/Open question được
   amend theo state resolve này — B5). Riêng **09 box 2: giữ `[ ]` + tag N/A**,
   closure evidence ghi rõ nhánh đã chọn: Kissat bị loại vĩnh viễn → giữ
   CaDiCaL + Glucose cho RQ2 (`14-sat-methodology.md` §3.6 — C11). Ticket 12
   box 1: closure evidence ghi rõ "8/8 cho CaDiCaL + Glucose, cột Kissat N/A"
   — không phải 2×2×3 = 12 (C10). Pointer `_validate_solver` ghi đủ nguồn:
   `src/sat/solve.py` (dòng 424) cùng 2 file test (C12).
7. Section `## Closure evidence (2026-11-03)` trong từng file được tick
   (D1/D2); heading giữ nguyên như R15.

Thứ tự cắt khi chậm: 6 → 7 (đều là docs, ticket P2-owned, C5 cho phép hoãn);
**không bao giờ cắt** P0 (quy tắc "cắt Bonus trước, không cắt Core").

**Later (không làm trong task này):** GH sync, memory enforcement, ước lượng
trong dry-run, `--dry-run` cho pilot scripts, sửa CONTRACT §5, relabel ticket.

## Acceptance criteria (quan sát được)

Code (trong `tests/runner/test_runner.py`; chạy bằng
`.venv\Scripts\python.exe -m pytest ... --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp`):

- **A1** Record dry-run có đủ `RUN_FIELDS` + `config` + `solution` +
  `metadata` + `dry_run`; `status == "DRY_RUN"`; mọi trường result-derived và
  `solution` là `None`; `metadata == {}`; `error is None`; `dry_run` là dict
  thường và `dry_run["out_file"]` là `str` (I4).
- **A2** Sau dry-run với `out_dir` chưa tồn tại: thư mục vẫn chưa tồn tại;
  với thư mục có sẵn: không file nào thêm/sửa **dưới `out_dir`** (T5);
  dry-run không vào block `tempfile.TemporaryDirectory` (I2).
- **A3** `dry_run.hard_limit == time_limit + KILL_GRACE_SECONDS`; monkeypatch
  `KILL_GRACE_SECONDS = 7.5` thì giá trị theo — tức constant được đọc tại
  call time trong `runner.py`, không copy lúc import ở `__main__.py`
  (R6/T13); `time_limit=None` → `None` (API-only; CLI `--time-limit` luôn
  float nên không bao giờ in `hard_limit=none` — C7). Không hardcode `30.0`
  trong code mới.
- **A4** `run_id` dry-run == `make_run_id(instance, cfg)` == `run_id` run thật
  cùng tham số; tính theo `instance.id` + config, không theo nội dung file
  (C13). Ví dụ suffix (theo `make_run_id` thật, không phải ví dụ cũ `mlna`):
  `Config(time_limit=30)` int qua API → `...__tl30__mlNone`; CLI
  `--time-limit 1800` float → `...__tl1800.0__mlNone` — type-sensitive (B1).
  Run thật chạy sau với `out_dir` sạch trong `tmp_path` (không phải
  `results/raw`) và ghi file cùng `run_id` thành công — "không collision" =
  không lỗi, không ghi nhầm chỗ khác (C14/T8). Run_id tính bằng code, không
  copy ví dụ docs.
- **A5** File rác tại `out_file` (path tính từ `make_run_id`, không copy ví dụ
  — T7): `exists=True`; `resume=True` → `resume_would_skip=True` và record
  trả về là `"DRY_RUN"`, không phải nội dung rác; `resume=False` →
  `resume_would_skip=False`.
- **A6** Spy `subprocess.run` record cả `args` lẫn `kwargs` (I7): không call
  nào khớp worker pattern
  `[sys.executable, "-m", "src.runner.worker", ...]`; call `git describe`
  (kèm `capture_output`/`text`/`timeout`/`cwd`) được phép và không được làm
  fail assertion. Nếu implementation dùng `Popen`/`check_output` cho worker,
  spy phải bắt được — assert không call nào chứa `"src.runner.worker"` (T12).
- **A7** Instance invalid → dry-run raise cùng kiểu + cùng message như run
  thật; test dùng instance `n>0` với edges rỗng để trúng đúng
  `ValueError("Instance is empty (n = 0 or no edges).")` — `n=0` + edges sẽ
  trúng message out-of-range (C15/T6); không ghi gì.
- **A8** `method="nope"` → `ValueError` chứa "không có trong registry";
  dotted-path không tồn tại pass. Kiểm import bằng snapshot:
  `set(sys.modules)` ngay trước call dry-run, sau call không có module mới
  nào xuất hiện (I8) — kiểm "module X không có trong `sys.modules`" với
  module không có thật là vacuous (T1). Ghi chú: `import src.runner.runner`
  đã load sẵn `src.sat` stack + pysat (I1); test A8 không chạy được trên
  interpreter thiếu pysat.
- **A9** CLI hợp lệ (`--out <tmp_path>`, không bao giờ assert path absolute
  của repo — B3): stdout đúng 5 dòng R12 — so qua
  `out.splitlines() == [5 chuỗi]`; 4 dòng đầu exact, dòng `output` tách
  prefix `DRY_RUN output out_file=` + so `Path(value)` + so phần
  `exists=...` (R9/T3); bool trong output là `true`/`false` thường (B2);
  `err == ""` (I6); `main()` return 0 (T14); không ghi gì dưới `--out`.
- **A10** CLI lỗi (instance hỏng / method lạ): subprocess với
  `PYTHONIOENCODING=utf-8` — console cp1252 sẽ `UnicodeEncodeError` với
  message tiếng Việt (R1/T2); stderr bắt đầu `DRY_RUN ERROR:`, không
  traceback, exit code 2 (không phải 1/120), không ghi gì.
- **A11** Regression: test cũ trong `tests/runner/test_runner.py` xanh không
  sửa; full suite xanh qua
  `.venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp`
  — "green" = passed + skipped (3 skip CPLEX); không chạy được bằng global
  `python` (thiếu pysat) hay temp mặc định (R2/R3/I9/I10).

Docs:

- **D1** Mỗi box **do task này tick** trong 08..15 có pointer bằng chứng
  trong section `## Closure evidence (2026-11-03)` của chính file đó (R10
  review-qa: 3 box cũ đã `[x]` của ticket 15 không bắt thêm pointer).
- **D2** Mỗi box không tick có annotation lý do kèm pointer. Set không tick
  kỳ vọng: chỉ 09 box 2 (N/A vĩnh viễn W2). 13 box 3 tick vô điều kiện
  (B5 — requirements D2 được amend bỏ mệnh đề "iff GH #20 unconfirmed").
- **D3** `git diff -- docs/handoff/w2-sat/15-m1-gate-evidence.md` (so theo
  file, không so toàn repo — T9) chỉ chạm §4.1 (mới) và 1 bullet §6; §1–§3,
  §4, §5 và nội dung quyết định §6 byte-identical — kể cả chỗ §4/§6 tự mâu
  thuẫn với §4.1 (record có ngày, không sửa — review-be); output trong §4.1
  parse được theo R12 (5 dòng `DRY_RUN`, bool `true`/`false`,
  `run_id`/budget tự nhất quán với lệnh — suffix `...__tl1800.0__mlNone`,
  không `mlna`; ví dụ R12 là format mẫu, không phải giá trị bắt buộc).
- **D4** Ticket 15: box 2 `[x]` + pointer §4.1 (output thật) + §3 (ước tính
  compute — C8); parenthetical cũ thay bằng pointer; các dòng quyết định
  NO-GO byte-identical.
- **D5** `Status:`/`Owner:`/`Blocked by:` mọi file ticket không đổi; văn mới
  tiếng Việt.
- **D6** Không có thay đổi **do task này gây ra** ngoài danh sách:
  `src/runner/runner.py`, `src/runner/__main__.py`,
  `tests/runner/test_runner.py`,
  `docs/handoff/abp-sat-encoding/issues/W2/08..15*.md` (8 file),
  `docs/handoff/w2-sat/15-m1-gate-evidence.md`, và các file handoff
  `docs/handoff/w2-dry-run/` (`requirements.md`, `scope.md`, `review-qa.md`,
  `review-be.md`) — B6/T10. Dirty sẵn (11 file `docs/handoff/sat-g1/`) và
  untracked sẵn (`.pytest-tmp/`, `docs/handoff/w2-dry-run/`) tồn tại từ
  trước task, không tính là vi phạm; basetemp pytest đặt ngoài repo nên
  không tạo artifact mới trong repo. Không stash/revert để cho
  `git status` đẹp.

## Open questions

`none` — reviews đã chốt hết (fold từ `review-qa.md` §5 và `review-be.md`
B1–B6):

1. **GH #20 posting** (13 box 3): đã có — GH #42 + comment GH #20 ghi kết luận
   review P1, PR #48 `p1/w2-review-closeout` đã merge. **13 box 3 tick vô
   điều kiện** (B5; requirements R17/D2/Open question được amend theo state
   này). Bằng chứng: `docs/handoff/w2-sat/13-review-p1-formulation.md`,
   `docs/handoff/w2-exact/16-w2-acceptance.md`.
2. **Instance cho §4.1**: mặc định `benchmark/toy/path4.json` với lệnh R20
   (`.venv\Scripts\python.exe`, `--out results/raw`); người thực hiện được
   thay bằng tier-1 trong `benchmark/validation/` (vd
   `randconn16-seed20261026.json`) hoặc file do generator ghi ra, miễn ghi
   lệnh + output thật verbatim (I9/T11).
3. **`--dry-run` cho `experiments/pilot_rq*.py`**: out of scope (task chỉ nêu
   `src/runner`).
