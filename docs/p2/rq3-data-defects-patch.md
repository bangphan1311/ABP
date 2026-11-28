# RQ3 data defects: proposed patch (not applied)

Ngày: 2026-11-28. Phạm vi: workspace `C:\Users\ducqu\workspace\ABP-rq3`, branch
`p3/rq3-official-results`, commit `09e8e3b` (`v0.1-contract-268-g09e8e3b`).

Hai issue:

- [#56](https://github.com/bangphan1311/ABP/issues/56) — record `MO` mất toàn bộ bằng chứng tài nguyên.
- [#57](https://github.com/bangphan1311/ABP/issues/57) — `search_mode = null` trong 24 run SAT.

Tài liệu này chứa unified diff **đề xuất, chưa apply**, giải thích từng chỗ sửa, và các
giới hạn còn lại. Không có file nào trong `ABP-rq3` bị thay đổi bởi tài liệu này.

## 0. Quy tắc bất di bất dịch

**Không sửa tay 120 raw file trong `results/rq3_official/`.** Mỗi file là bằng chứng của
một lần chạy thật. Sửa `search_mode`, `peak_memory` hay `config` trong raw sẽ:

- làm sai provenance (record không còn là output của runner tại commit đã ghi trong `git_tag`),
- làm `_valid_resume_record` (`src/runner/runner.py:42-89`) từ chối record cũ, vì nó so
  sánh `record["config"] == asdict(config)`,
- làm `run_id` không còn khớp nội dung, trong khi `run_id` đã được trích trong issue, log
  và bảng phân tích.

Mọi thay đổi dữ liệu phải đi qua một trong hai đường: **chạy lại** (archive bản cũ vào
`attempt_history/`), hoặc **backfill tường minh ở tầng export** với provenance ghi lại
(patch 5 dưới đây).

## 1. Lỗi 1 — record `MO` không có bằng chứng tài nguyên

### 1.1 Chuỗi nguyên nhân

| Bước | File | Hành vi hiện tại |
|---|---|---|
| 1 | `src/sat/solve.py` (`solve_sat`) | Chỉ bắt `BackendError` quanh `_probe(...)`; `MemoryError` thoát ra, mang theo `probes`, `peak_ws`, `t_encode`, `t_solve`, `last_cnf`, `best_solution` |
| 2 | `src/runner/worker.py:34-35` | Bắt `MemoryError`, ghi `{"status": "MO"}` — không `peak_memory`, không pha, không thời gian |
| 3 | `src/runner/runner.py:286-288` | Thấy `MO` thiếu `t_total` → `build_record(instance, config, None, ...)` |
| 4 | `src/runner/schema.py:91-98,115` | `result is None` → mọi metric `None`, `metadata={}`, chỉ còn `error="MemoryError"` |

Đường "OS/Job Object kill" **không** bị lỗi này: `runner.py:234-272` trả `TO`/`FEAS` từ
checkpoint và có `recovery_reason`. Chỉ đường `MemoryError` của Python là mất trắng.

### 1.2 Patch 1 — `src/sat/solve.py`: bắt `MemoryError` có pha và working set

- Thêm `MemoryExhausted(MemoryError)` mang `phase` và `ws_mb`, cùng helper `_ws_mb_safe()`
  (đo working set, không để lỗi đo che lỗi gốc).
- `_probe` bọc riêng hai pha: dựng CNF → `phase="encode"`, nạp clause → `phase="load_clauses"`.
  Đây chính là chỗ trả lời câu hỏi "chạm cap hay MemoryError khi nạp clause".
- `solve_sat` thêm biến `memory_phase`, bắt `MemoryError` (kể cả loại không có pha → `"unknown"`),
  lấy `peak_ws = max(peak_ws, exc.ws_mb, _ws_mb_safe())`, đặt `error = "MemoryError: <phase>"`,
  rồi `break` thay vì để exception thoát.
- `summarise_result` nhận `memory_exhausted=True` → trả `MO` với `lb` = incumbent đã verify
  (nếu có) và `ub = hi - 1`. Không tuyên bố `OPT`.
- Nhánh hạ trạng thái về `ERR` được chặn cho `MO` (`status != "MO"`).
- `peak_memory` chỉ `None` khi `status == "ERR"`; `solution` được giữ cho cả `MO`
  (incumbent đã verify vẫn là bằng chứng, và không làm sai `_valid_resume_record` vì
  `lb` vẫn bằng objective verify lại).
- `metadata.memory_phase` được ghi thêm.

### 1.3 Patch 2 — `src/runner/worker.py`: fallback vẫn có bằng chứng

Nếu `MemoryError` thoát ra ngoài `solve_sat` (ví dụ method khác, hoặc lỗi trước vòng K),
worker vẫn ghi `peak_memory` hiện tại và `metadata.memory_phase="unknown"`. Helper
`_current_ws_mb()` import `src.sat.solve` **cục bộ** để không kéo pysat vào các method exact.

### 1.4 Patch 3 — `src/runner/runner.py`: nhánh legacy và cột `error`

- Nhánh `MO` không có `t_total` dựng `Result` tạm với `peak_memory`/`metadata` từ payload
  worker, thay vì luôn truyền `None`.
- `_recheck` lấy `error` từ `metadata` cho cả `MO`, không chỉ `ERR`. Trước patch, record `MO`
  do solver trả về có cột `error` rỗng dù `metadata.error` có text.

Kết quả kiểm chứng trên bản nháp (giả lập `MemoryExhausted("load_clauses", 11500.0)`
tại probe thứ 3, instance 6 đỉnh):

```
status MO  lb 2  ub 5  peak_memory 11500.0  t_total 0.0016
variables 36  clauses 252  error "MemoryError: load_clauses"
metadata keys: abp_encoding, abp_encoding_stats, amo_encoding, error,
               k_best, k_unsat, memory_phase, method, probes, sat_solver,
               unsat_source
solution kept: True
```

## 2. Lỗi 2 — `search_mode` null trong 24 run SAT

### 2.1 Chuỗi nguyên nhân

| Bước | File | Hành vi hiện tại |
|---|---|---|
| 1 | `run_rq3.ps1:17-31` | Chỉ thêm `--abp-encoding`, `--amo-encoding`, `--sat-solver`; **không** có `--search-mode` |
| 2 | `run_rq3_parallel.ps1:18-33` | Lặp lại đúng thiếu sót đó |
| 3 | `results/official-plan.csv` | Không có cột `search_mode`, nên script không có nguồn để lấy |
| 4 | `src/runner/__main__.py:74,84-88` | `--search-mode` mặc định `None`, chuyển nguyên vào `Config` |
| 5 | `src/runner/schema.py:29,89` | Ghi `config.search_mode` thẳng vào record; `make_run_id` render `None` → `na` |

Solver không hề chạy single-shot: `src/sat/solve.py:40,48` đặt `DEFAULT_SEARCH_MODE = "multi"`,
và `metadata.probes` dài 7–46 entry trên 12 run SAT hoàn tất. Vấn đề thuần tuý ở tầng CLI.

### 2.2 Patch 4 — `src/runner/__main__.py`: default đúng cho SAT

Khi `--search-mode` vắng và `method == "sat"`, lấy `DEFAULT_SEARCH_MODE` từ `src.sat.solve`
(import cục bộ để không kéo pysat vào mọi method). Đây là sửa gốc: mọi entry point dùng
`python -m src.runner` đều ghi đúng mode thực thi.

Kiểm chứng:

```
DRY_RUN run_id=toy__sat__na__na__na__multi__sym0__ws0__s0__tl30.0__ml12.0
DRY_RUN config ... search_mode=multi
```

`--method cp_sat` vẫn `search_mode=none`.

Hai script `run_rq3.ps1` / `run_rq3_parallel.ps1` **không bắt buộc** phải sửa sau patch này.
Nếu muốn script tự mô tả cấu hình, thêm `--search-mode "multi"` vào block
`if ($_.method -eq "sat")`; đó là thay đổi 1 dòng, không nằm trong diff dưới đây để giữ
patch tối thiểu.

### 2.3 Patch 5 — `scripts/export_runs_csv.py`: backfill có điều kiện

Thêm `--backfill-search-mode {multi}`. Chỉ điền khi **cả ba** điều kiện đúng:

1. `method == "sat"`,
2. `search_mode` rỗng,
3. `metadata.probes` không rỗng.

Điều kiện 3 là bằng chứng nội tại rằng multi-run K search đã chạy. Nhờ vậy patch không
suy đoán. Hệ quả: **12 run SAT hoàn tất** (`OPT`/`FEAS`) được backfill; **12 run `MO`**
vẫn `null` vì không có probe nào. Không đổi `run_id`, không ghi file raw.

Flag mặc định tắt, nên `results/runs.csv` hiện có không đổi cho tới khi ai đó chủ động chạy lại
export với flag này.

## 3. Unified diff đề xuất

Áp dụng tại root của `ABP-rq3` (branch `p3/rq3-official-results`). File nguồn dùng CRLF;
diff dưới đây chuẩn hoá LF, nên dùng `git apply --ignore-whitespace` hoặc apply thủ công.

```diff
diff --git a/src/sat/solve.py b/src/sat/solve.py
--- a/src/sat/solve.py
+++ b/src/sat/solve.py
@@ -235,6 +235,7 @@
     peak_ws = working_set_mb()  # mốc chụp đầu tiên: trước khi giải
     error: str | None = None
     timed_out = False
+    memory_phase: str | None = None
 
     while lo + 1 < hi:
         k = lo + 1  # cận dưới: ngưỡng nhỏ nhất chưa bị bác
@@ -246,6 +247,11 @@
             )
         except BackendError as exc:  # lỗi backend/giấy phép -> ERR
             error = str(exc)
+            break
+        except MemoryError as exc:  # hết bộ nhớ -> MO, giữ bằng chứng đã có
+            memory_phase = getattr(exc, "phase", "unknown")
+            peak_ws = max(peak_ws, getattr(exc, "ws_mb", 0.0), _ws_mb_safe())
+            error = f"MemoryError: {memory_phase}"
             break
 
         t_encode += probe_encode
@@ -305,7 +311,8 @@
     t_total = perf_counter() - start
 
     status, lb, ub_out, gap, verified = summarise_result(
-        instance, lo, hi, best_solution, timed_out, error is not None
+        instance, lo, hi, best_solution, timed_out, error is not None,
+        memory_exhausted=memory_phase is not None,
     )
 
     # Nghiệm phải khớp bằng chứng của vòng dò K, nếu không là lỗi encoding.
@@ -326,7 +333,7 @@
             "trạng thái bất khả (K=1 luôn SAT khi đồ thị có cạnh)."
         )
 
-    if error is not None:
+    if error is not None and status != "MO":
         status, lb, ub_out, gap = "ERR", None, None, None
 
     metadata: dict[str, object] = {
@@ -340,6 +347,8 @@
         "unsat_source": unsat_source,
         "abp_encoding_stats": dict(best_cnf.stats) if best_cnf else None,
     }
+    if memory_phase is not None:
+        metadata["memory_phase"] = memory_phase
     if error is not None:
         metadata["error"] = error
 
@@ -353,8 +362,8 @@
         t_total=t_total,
         variables=last_cnf.n_vars if last_cnf else None,
         clauses=len(last_cnf.clauses) if last_cnf else None,
-        peak_memory=None if error is not None else peak_ws,  # max các mốc chụp, MB
-        solution=best_solution if status in ("OPT", "FEAS") else None,
+        peak_memory=peak_ws if status != "ERR" else None,  # max các mốc chụp, MB
+        solution=best_solution if status in ("OPT", "FEAS", "MO") else None,
         metadata=metadata,
     )
 
@@ -383,6 +392,23 @@
         instance, k, abp_encoding, amo_encoding, solver_name, cfg.time_limit
     )
     return status, solution
+
+
+class MemoryExhausted(MemoryError):
+    """MemoryError kèm pha và working set tại điểm hỏng (bằng chứng cho record MO)."""
+
+    def __init__(self, phase: str, ws_mb: float) -> None:
+        super().__init__(phase)
+        self.phase = phase
+        self.ws_mb = ws_mb
+
+
+def _ws_mb_safe() -> float:
+    """Working set hiện tại; lỗi đo không được che lỗi gốc."""
+    try:
+        return working_set_mb()
+    except MemoryError:
+        return 0.0
 
 
 def _probe(
@@ -414,15 +440,21 @@
         return "UNKNOWN", None, None, 0.0, 0.0, working_set_mb()
 
     t0 = perf_counter()
-    if abp_encoding == "order":
-        cnf = order.build_cnf(instance, k, amo_encoding=amo_encoding)
-    else:
-        cnf = build_cnf(instance, k, amo_encoding=amo_encoding)
+    try:
+        if abp_encoding == "order":
+            cnf = order.build_cnf(instance, k, amo_encoding=amo_encoding)
+        else:
+            cnf = build_cnf(instance, k, amo_encoding=amo_encoding)
+    except MemoryError:
+        raise MemoryExhausted("encode", _ws_mb_safe()) from None
     t_encode = perf_counter() - t0
 
     backend = SatBackend(solver_name)
     try:
-        backend.add_clauses(cnf.clauses)
+        try:
+            backend.add_clauses(cnf.clauses)
+        except MemoryError:
+            raise MemoryExhausted("load_clauses", _ws_mb_safe()) from None
         ws_peak = working_set_mb()  # mốc: trước solve (đã nạp clause, solver còn sống)
         remaining = None if time_limit is None else time_limit - (perf_counter() - t0)
         t1 = perf_counter()
@@ -445,8 +477,17 @@
     best_solution: dict[int, int] | None,
     timed_out: bool,
     has_error: bool,
+    memory_exhausted: bool = False,
 ) -> tuple[str, int | None, int | None, float | None, int | None]:
     """Chuyển trạng thái tìm kiếm thành ``(status, lb, ub, gap, giá trị verify)``."""
+    if memory_exhausted:
+        # MO: lỗi tài nguyên, không phải kết luận tìm kiếm. Giữ incumbent đã verify
+        # (nếu có) làm bằng chứng; không tuyên bố OPT.
+        if best_solution is None:
+            return "MO", None, hi - 1, None, None
+        value = verify(instance, best_solution)
+        return "MO", value, hi - 1, None, value
+
     if has_error:
         return "ERR", None, None, None, None
 

diff --git a/src/runner/worker.py b/src/runner/worker.py
--- a/src/runner/worker.py
+++ b/src/runner/worker.py
@@ -19,6 +19,16 @@
 from src.sat.loader import read_instance
 
 
+def _current_ws_mb() -> float | None:
+    """Working set hiện tại (MB); import cục bộ để không kéo pysat vào mọi method."""
+    try:
+        from src.sat.solve import working_set_mb
+
+        return working_set_mb()
+    except Exception:  # đo lường là best-effort, không được che lỗi gốc
+        return None
+
+
 def main(argv: list[str]) -> int:
     instance_path, config_path, out_path = argv
     out: dict
@@ -32,7 +42,16 @@
         )
         out = {"ok": True, "result": payload}
     except MemoryError:
-        out = {"ok": True, "result": {"status": "MO"}, "note": "MemoryError"}
+        # Giữ bằng chứng tài nguyên tối thiểu thay vì record MO rỗng.
+        out = {
+            "ok": True,
+            "result": {
+                "status": "MO",
+                "peak_memory": _current_ws_mb(),
+                "metadata": {"error": "MemoryError", "memory_phase": "unknown"},
+            },
+            "note": "MemoryError",
+        }
     except Exception as exc:  # license, input hỏng, bug solver...
         out = {
             "ok": False,

diff --git a/src/runner/runner.py b/src/runner/runner.py
--- a/src/runner/runner.py
+++ b/src/runner/runner.py
@@ -284,8 +284,15 @@
 
     raw = out["result"]
     if raw.get("status") == "MO" and "t_total" not in raw:
-        return build_record(instance, config, None, wall_time=wall,
-                            status_override="MO", error="MemoryError")
+        partial = Result(
+            status="MO",
+            peak_memory=raw.get("peak_memory"),
+            metadata=dict(raw.get("metadata") or {}),
+        )
+        return build_record(
+            instance, config, partial, wall_time=wall, status_override="MO",
+            error=raw.get("note") or partial.metadata.get("error") or "MemoryError",
+        )
 
     sol = raw.get("solution")
     raw["solution"] = {int(k): v for k, v in sol.items()} if sol else None
@@ -310,4 +317,4 @@
                 instance, config, result, wall_time=wall, status_override="ERR",
                 error=f"lb={result.lb} khác objective tính lại={value}.")
     return build_record(instance, config, result, wall_time=wall,
-                        error=result.metadata.get("error") if result.status == "ERR" else None)
+                        error=result.metadata.get("error") if result.status in ("ERR", "MO") else None)

diff --git a/src/runner/__main__.py b/src/runner/__main__.py
--- a/src/runner/__main__.py
+++ b/src/runner/__main__.py
@@ -81,9 +81,16 @@
                    help="Chỉ báo cáo run_id/budget/resume; không chạy solver.")
     a = p.parse_args()
 
+    search_mode = a.search_mode
+    if search_mode is None and a.method == "sat":
+        # solve_sat luôn chạy multi-run K search; record phải ghi đúng mode.
+        from src.sat.solve import DEFAULT_SEARCH_MODE
+
+        search_mode = DEFAULT_SEARCH_MODE
+
     config = Config(
         method=a.method, abp_encoding=a.abp_encoding, amo_encoding=a.amo_encoding,
-        sat_solver=a.sat_solver, search_mode=a.search_mode, seed=a.seed,
+        sat_solver=a.sat_solver, search_mode=search_mode, seed=a.seed,
         time_limit=a.time_limit, memory_limit=a.memory_limit,
     )
     if a.dry_run:

diff --git a/scripts/export_runs_csv.py b/scripts/export_runs_csv.py
--- a/scripts/export_runs_csv.py
+++ b/scripts/export_runs_csv.py
@@ -29,11 +29,34 @@
     return rows
 
 
+def backfill_search_mode(rows: list[dict], mode: str) -> int:
+    """Điền search_mode cho record sat thiếu field; không đổi run_id hay file raw.
+
+    Chỉ điền khi record có metadata.probes, tức multi-run K search đã thật sự chạy.
+    Record MO không có probes thì để nguyên: không đủ bằng chứng để suy ra mode.
+    """
+    filled = 0
+    for row in rows:
+        if (
+            row["method"] == "sat"
+            and not row["search_mode"]
+            and (row.get("metadata") or {}).get("probes")
+        ):
+            row["search_mode"] = mode
+            filled += 1
+    return filled
+
+
 def main() -> int:
     p = argparse.ArgumentParser(description=__doc__)
     p.add_argument("--raw-dir", type=Path, default=ROOT / "results/rq3_official")
     p.add_argument("--output", type=Path, default=ROOT / "results/runs.csv")
     p.add_argument("--expected-runs", type=int)
+    p.add_argument(
+        "--backfill-search-mode", choices=("multi",),
+        help="Điền search_mode cho record sat thiếu field; provenance: "
+             "docs/p2/rq3-data-defects-patch.md",
+    )
     a = p.parse_args()
 
     try:
@@ -43,6 +66,13 @@
     except (OSError, json.JSONDecodeError, ValueError) as e:
         print(f"ERROR: {e}", file=sys.stderr)
         return 2
+
+    if a.backfill_search_mode:
+        filled = backfill_search_mode(rows, a.backfill_search_mode)
+        print(
+            f"# backfill search_mode={a.backfill_search_mode} rows={filled}",
+            file=sys.stderr,
+        )
 
     rows.sort(key=lambda r: (r["instance"], r["method"]))
     a.output.parent.mkdir(parents=True, exist_ok=True)

diff --git a/tests/test_export_runs_csv.py b/tests/test_export_runs_csv.py
--- a/tests/test_export_runs_csv.py
+++ b/tests/test_export_runs_csv.py
@@ -62,3 +62,27 @@
 
     assert result.returncode == 2
     assert "expected 2 records, found 1" in result.stderr
+
+
+def test_backfill_search_mode_only_for_sat_with_probes(tmp_path):
+    raw_dir = tmp_path / "raw"
+    sat = make_record("sat-with-probes")
+    sat["metadata"] = {"probes": [{"k": 1}]}
+    mo = make_record("sat-mo", status="MO")
+    mo["metadata"] = {}
+    cp = make_record("cp-no-probes", method="cplex_cp")
+    write_raw(raw_dir, [sat, mo, cp])
+
+    result = subprocess.run(
+        [sys.executable, SCRIPT, "--raw-dir", str(raw_dir),
+         "--output", str(tmp_path / "runs.csv"), "--backfill-search-mode", "multi"],
+        capture_output=True, text=True,
+    )
+
+    assert result.returncode == 0, result.stderr
+    assert "rows=1" in result.stderr
+    with (tmp_path / "runs.csv").open(encoding="utf-8-sig", newline="") as f:
+        by_id = {r["run_id"]: r for r in csv.DictReader(f)}
+    assert by_id["sat-with-probes"]["search_mode"] == "multi"
+    assert by_id["sat-mo"]["search_mode"] == ""
+    assert by_id["cp-no-probes"]["search_mode"] == ""
```

Đã kiểm chứng trên bản sao tạm: `git apply --check --ignore-whitespace` pass,
apply xong nội dung trùng khớp 6/6 file, `py_compile` pass, `pytest tests/test_export_runs_csv.py`
pass 4/4 (gồm test mới cho backfill).

## 4. Việc phải làm sau khi apply

```powershell
cd C:\Users\ducqu\workspace\ABP-rq3
.venv\Scripts\python.exe -m pytest tests\test_export_runs_csv.py -q
.venv\Scripts\python.exe scripts\export_runs_csv.py --expected-runs 120 --backfill-search-mode multi
```

Sau đó kiểm tra:

- `peak_memory` khác `null` cho mọi record `MO` **mới**; record cũ vẫn `null` (không hồi tố).
- `metadata.memory_phase` có giá trị `encode` / `load_clauses` / `unknown`.
- `search_mode` = `multi` cho 12 run SAT hoàn tất; 12 run `MO` vẫn `null` và phải được nêu
  rõ trong phần giới hạn của paper.

Muốn có `peak_memory` thật cho 12 run `MO`, phải chạy lại sau khi apply patch:

```powershell
# archive bản cũ trước, nếu không run mới trùng run_id cũ sẽ bị archive tự động
.\run_rq3.ps1
```

Record mới sẽ có token `multi` trong `run_id` (vì config đổi), nên phải archive bản `na`
trước khi chạy, và mọi bảng phân tích phải chọn một trong hai bộ `run_id`, không trộn.

## 5. Giới hạn và quyết định còn mở

1. **12 record `MO` hiện có không thể cứu.** Chúng không có probe, không có CNF, không có
   working set. Cách duy nhất để có bằng chứng là chạy lại với patch. Nếu không chạy lại,
   paper phải viết "12/24 run SAT hết bộ nhớ; không có số đo tài nguyên cho các run này",
   không được viết "chạm cap 12 GiB".
2. **`run_id` cũ giữ token `na`** sau backfill. Cột `search_mode` đúng nhưng `run_id` vẫn
   `...__na__...`. Mọi trích dẫn phải dùng `run_id` như file, không tự sửa tên.
3. **Filter phân tích.** Cách an toàn nhất cho RQ3 hiện tại là lọc theo `method`, không theo
   `search_mode`, cho tới khi 12 run `MO` được chạy lại. `experiments/triage.py:483` đã có
   fallback `or "multi"`, nhưng fallback đó cũng là suy đoán cho record `MO`.
4. **Resume vẫn bỏ qua `MO`.** `_valid_resume_record` chấp nhận `MO` là record dùng lại được
   (`runner.py:57`). Patch này không đổi hành vi đó: sau khi có `lb`/`solution` cho `MO`,
   resume còn chặt hơn (phải verify lại khớp `lb`). Nếu muốn `MO` luôn được chạy lại, đó là
   ticket riêng, không gộp vào đây.
5. **Exact solver vẫn `peak_memory = null`.** `src/exact/cplex_mip.py:150`,
   `cplex_cp.py:297`, `gurobi_mip.py:114` bắt `MemoryError` và trả `MO` không có
   `peak_memory`. Không thuộc phạm vi 2 issue này; nếu muốn nhất quán thì mở issue riêng.
6. **`docs/p3/rq3-official-run-2026-11-28.md` có một câu sai**: mục 3 viết "`t_total` is 0 for
   them", thực tế là `null`. Sửa tài liệu đó là việc riêng, không nằm trong patch code.
7. **Ba worker chạy song song** (protocol deviation #2 trong tài liệu P3) làm `wall_time` của
   một phần batch bị nhiễu. Patch này không sửa được; nếu chạy lại 12 run `MO` thì nên chạy
   tuần tự để số đo bộ nhớ và thời gian sạch.
