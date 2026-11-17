# Dev notes — W2 `--dry-run` (handover)

Ngày: 2026-11-03 · Branch: `p2/w4-sat` · Nguồn: `requirements.md`, `scope.md`,
`api-contract.md`, `test-plan.md`, `infra.md` (cùng thư mục).

## 1. Đã làm

### 1.1 API — `src/runner/runner.py`

- `run_one(instance_path, config, out_dir=DEFAULT_OUT_DIR, *, resume=False,
  dry_run=False)` thêm tham số keyword-only `dry_run`; caller cũ không đổi.
- Nhánh `dry_run=True` theo đúng thứ tự `read_instance` → method check tĩnh →
  `make_run_id` → dựng `out_file` → return. Không `mkdir`, không vào block
  `tempfile.TemporaryDirectory`, không spawn worker, không ghi file.
- Method check: `config.method in METHODS or ":" in config.method`; lỗi
  `ValueError` dùng đúng câu của `registry.resolve` (kèm `sorted(METHODS)`).
- `hard_limit = None if time_limit is None else time_limit +
  KILL_GRACE_SECONDS`; constant đọc tại call time, không hardcode `30.0`.
- Record = `build_record(instance, config, None, wall_time=<đo thật>,
  status_override="DRY_RUN")` cộng key `dry_run` là **dict thường**
  (`out_file` là `str`), đúng R8/Data model. `dry_run` record không persist.
- `run_id` dùng `make_run_id` nguyên bản — không sửa `schema.py`.

### 1.2 CLI — `src/runner/__main__.py`

- Cờ `--dry-run` (`store_true`); compose được với `--resume`.
- In đúng 5 dòng `DRY_RUN` (R12); `None` → `none`, bool → `true`/`false`.
- Exit `0` khi in xong; `2` khi lỗi validation (`ValueError`/`OSError`) với
  một dòng `DRY_RUN ERROR: <message>` trên stderr. `_make_stderr_lossy_safe()`
  gọi `sys.stderr.reconfigure(errors="replace")` khi có, để console cp1252
  không `UnicodeEncodeError` với message tiếng Việt.
- Nhánh `--dry-run` cũng gọi `_make_lossy_safe(sys.stdout)` trước khi in, vì
  `out_file` (và `instance.id`) có thể chứa ký tự non-ASCII từ `--out`; console
  cp1252 render thành `?` thay vì crash. Đường chạy thật không đổi.
- Đường chạy thật giữ nguyên từng dòng; `try/except` chỉ bọc nhánh dry-run.

### 1.3 Test — `tests/runner/test_runner.py`

- Thêm 24 test mới; 6 test cũ và fixture `path4` không sửa.
- Phủ A1–A11: shape record, không side effect (kể cả pre-existing dir),
  không vào tempdir, thứ tự nhánh, budget theo grace constant, `run_id` khớp
  run thật và không phụ thuộc nội dung cạnh, resume với file rác, không spawn
  worker, validation parity (empty/missing/malformed), method check không
  import module solver mới, dedup cạnh, `memory_limit` verbatim, `instance.id`
  non-ASCII, CLI 5 dòng, CLI memory/resume, CLI `--out` non-ASCII + cp1252,
  CLI lỗi cp1252 + utf-8 (cả empty-graph lẫn unknown-method tiếng Việt), CLI
  không `--dry-run` giữ nguyên hành vi, CLI dotted-path.
- `_run_cli` nhận `encoding=` để decode đúng codec con (cp1252/utf-8) thay vì
  dựa vào locale của process test.
- Test A8 pre-warm `platform.node()` trước snapshot `sys.modules`, rồi assert
  không module mới **và** không `src.exact.*` / dotted target module mới.
- CLI test chạy subprocess với `sys.executable`, `cwd=REPO_ROOT`, luôn
  `--out <tmp_path>` — không đụng `results/raw`.

### 1.4 Docs

- `docs/handoff/abp-sat-encoding/issues/W2/08..15*.md`: tick box theo R17,
  thêm section `## Closure evidence (2026-11-03)`; 09 box 2 giữ `[ ]` kèm
  suffix `*(N/A — xem Closure evidence)*`; 15 box 2 thay parenthetical bằng
  pointer §4.1/§3.
- `docs/handoff/w2-sat/15-m1-gate-evidence.md`: thêm `### 4.1 Cập nhật
  2026-11-03: --dry-run đã có trên runner` (lệnh + stdout thật verbatim, đọc
  kết quả, phạm vi NO-GO giữ nguyên) và 1 pointer ở bullet §6. §1–§3, §4 gốc,
  §5, nội dung quyết định §6 giữ byte-identical.

## 2. Kiểm chứng

Lệnh chạy thật cho §4.1 (đã chạy, stdout dán verbatim vào evidence doc):

```powershell
.venv\Scripts\python.exe -m src.runner --instance benchmark/toy/path4.json --method sat --abp-encoding pairwise --amo-encoding seqcounter --sat-solver cadical195 --search-mode multi --time-limit 1800 --out results/raw --dry-run
```

Kết quả: exit `0`, stderr rỗng, 5 dòng `DRY_RUN`, `out_file` relative dưới
`results\raw`, `run_id` suffix `...__tl1800.0__mlNone`, `hard_limit=1830.0`,
`memory_limit_enforced=false`, `exists=false resume_would_skip=false`.
`git status --porcelain results/raw` rỗng sau lệnh.

Full suite:

```powershell
.venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp
```

Kết quả lần chạy cuối: **538 passed, 3 skipped in 19.91s** — 3 skip CPLEX CP
engine như baseline; không failure. Riêng file runner: **30 passed**.

## 3. Quyết định / lệch spec (đã chọn, ghi lại)

1. **Record là plain `dict`, không dataclass** — theo R8/Data model và
   `test-plan.md` §7; brief Phase-2 nói "string representation" không được
   dùng vì trái nguồn chuẩn.
2. **Message method lỗi lặp inline trong `runner.py`** — `registry.py` nằm
   ngoài danh sách file được sửa; giữ đúng câu của `registry.resolve` để A8
   và người dùng thấy cùng thông điệp. Nếu sau này sửa message registry, phải
   sửa cả hai chỗ.
3. **`memory_limit` chỉ xuất hiện ở dòng budget** (R12): dòng config không
   liệt kê `memory_limit`; test CLI memory-limit kiểm dòng budget.
4. **`git describe` lúc chạy §4.1 trả `v0.1-contract-126-g6b6b8b5-dirty`** —
   hậu tố `-dirty` do working tree còn thay đổi chưa commit **của chính task
   này**; `docs/handoff/sat-g1/` đã sạch tại thời điểm chạy (khác giả định
   baseline trong scope). Ghi đúng thực tế, không sửa cho khớp giả định.
5. **Codec stderr** — `scope.md` ghi `PYTHONIOENCODING=utf-8`; R13 (bản sửa
   sau) yêu cầu chịu được cp1252. Đã implement `reconfigure(errors="replace")`
   và test cả `cp1252` lẫn `utf-8`; coi R13 là văn bản thay thế.
6. **Không enforce memory limit** — `memory_limit_enforced=false` là literal
   cố định nêu sự thật hiện tại; nếu sau này thêm enforcement, phải sửa literal
   này cùng lúc.
7. **Không thêm import solver mới** — chỉ thêm `from src.runner.registry import
   METHODS` (module registry không import solver ở top level). Test A8 pre-warm
   `platform.node()` rồi snapshot `sys.modules`: không module mới, và cụ thể
   không `src.exact.*` / dotted target module. `src.sat`/pysat vẫn được load
   sẵn bởi `import src.runner.runner` (tồn tại trước, ngoài phạm vi).

## 4. Hạn chế đã biết (đúng như spec)

- Dotted-path method không tồn tại vẫn pass dry-run (không import); run thật
  sẽ tạo record `ERR`. Dry-run cố ý strict hơn ở method registry (R3/R10).
- Method có trong registry nhưng backend thiếu (gurobipy/cplex) cũng pass
  dry-run; run thật `ERR`.
- Dry-run không ước lượng CNF-size/runtime; chỉ báo số đo được.
- Exit code `1` vẫn là "run thật tạo record `ERR`"; validation dry-run dùng
  `2`.

## 5. Việc còn lại / gợi ý

- Không có việc code bắt buộc còn lại cho blocker `--dry-run`.
- Nếu muốn giảm lặp message method: tách helper dùng chung trong
  `src/runner/registry.py` — cần mở phạm vi file.
- PR description nên ghi rõ quyết định §3.1 (dict theo R8) như
  `test-plan.md` §7 yêu cầu.

## 6. Sửa theo QA (`qa-dev.md`, 2026-11-03)

- **B1** — `src/runner/__main__.py`: thêm `_make_lossy_safe(stream)` dùng chung;
  nhánh `--dry-run` gọi `_make_lossy_safe(sys.stdout)` trước khi in. `--out`
  non-ASCII + `PYTHONIOENCODING=cp1252` giờ exit `0`, đủ 5 dòng `DRY_RUN`,
  không `UnicodeEncodeError`. `api-contract.md` §2.2 sửa lại: path non-ASCII là
  exposure mới, không "identical to the existing result line".
- **B2** — `test_dry_run_method_check_imports_nothing` pre-warm
  `platform.node()` (stdlib `socket` do `build_record` chạm lần đầu), rồi assert
  `set(sys.modules) - before == set()` **và** không `src.exact.*` / dotted
  target module mới. `api-contract.md` §1.2/§4 đổi "no new imports" thành
  "no new solver-module imports" kèm carve-out stdlib.
- **B3** — `test_cli_dry_run_unknown_method_exits_2` chạy cả `cp1252` lẫn
  `utf-8`, assert message tiếng Việt `không có trong registry` và không
  traceback. `_run_cli` thêm tham số `encoding=` để decode đúng codec con.
- **B4/B5/B6** — không sửa code (ngoài scope, pre-existing hoặc đã chấp nhận);
  ghi nhận ở `api-contract.md` §3 nếu cần.
- Thêm test CLI `--out` non-ASCII (`kết_quả`) + cp1252: exit `0`, stderr rỗng,
  5 dòng `DRY_RUN`.
