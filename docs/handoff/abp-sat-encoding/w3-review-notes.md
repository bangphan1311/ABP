# W3 review notes — P2 view on Experimental Protocol v1.0-rc (issue #49)

Read-only review. Scope: SAT side of the protocol (RQ1/RQ2 design, encoding × AMO,
solver availability, multi-run K search, `ub` handling, correctness/oracle tests,
objective verification, canonical-config criteria). Line references are against
the W3 branch (`p2/w3-pilots`, code identical to `main` for the reviewed files).

Severity tags: **blocker** (protocol claim would be false), **should-fix**
(protocol needs a wording/parameter change before freeze), **note** (known
behaviour, record it so results are read correctly).

## 1. Solver availability — Kissat stays out (resolved, no blocker)

* `src/sat/backend.py:44-53` — `PYSAT_KISSAT_FAMILIES = {"kissat404"}` and the
  single `KISSAT_LIMITATION` message.
* `src/sat/backend.py:137-138` — `SatBackend.__init__` raises before building the
  solver.
* `src/sat/solve.py:383-391` — `_validate_solver` rejects the family before any
  CNF is built.
* Evidence behind the ban (`docs/sat_tooling.md`, section "Kissat"): through PySAT
  `kissat404` ignores assumptions silently (wrong SAT/UNSAT answers), returns a
  model violating its own clauses, aborts the process on `add_clause` after
  `solve`, and crashes on small random 3-SAT; no external `kissat` binary is on
  `PATH`.
* **Protocol action:** list exactly four solvers in RQ2 — `cadical195`,
  `glucose4`, `glucose42`, `minisat22` (`experiments/pilot_rq2.py:RQ2_SOLVERS`)
  — and state that Kissat is a permanent exclusion with the reason above, not an
  unavailable-but-planned solver. No Kissat row, no "N/A (not installed)" entry
  that implies it could be installed and compared later.
* `src/sat/backend.py:60-77` (`SUPPORTED_SOLVERS`) is wider than the RQ2 set; the
  protocol should name the four chosen ones rather than "all supported solvers",
  otherwise the RQ2 table size is ambiguous.

## 2. Multi-run K search — implementation matches, one wording mismatch

* `src/sat/solve.py:168-218` — the loop: `k = lo + 1`, SAT → decode → verify →
  `lo = B(f)` (`:187-198`), UNSAT → `hi = k` (`:199-201`), timeout → stop
  (`:202-204`).
* `src/sat/solve.py:375-376` — OPT only when `lo + 1 == hi`; `:356-380` —
  FEAS gives `ub = hi - 1`, TO has no bounds.
* Jump to `B + 1` instead of `K + 1` (`:198`) is what makes the search complete;
  see `docs/technical_appendix_draft.md` A.5.
* **Should-fix:** `search_mode` is listed in `IGNORED_CONFIG_FIELDS`
  (`src/sat/solve.py:39-45`) and `_warn_ignored_config` (`:51-67`) emits a
  warning saying `search_mode` "thuộc P3", but multi-run search *is* the only
  implemented mode. The canonical config sets `search_mode = "multi"`, so every
  official run would emit a warning that contradicts the protocol. Either drop
  `search_mode` from the ignored list when the value is `"multi"`, or reword the
  warning to "search_mode has a single implemented value `multi`".
* **Note:** `t_encode` and `t_solve` accumulate over all probes in the chain
  (`src/sat/solve.py:180-181`), and `t_total` covers the whole chain (`:152`,
  `:220`). RQ1/RQ2 tables must say "per run (whole K chain)", not "per CNF";
  otherwise the numbers are not comparable with single-threshold timings.
* **Note:** every probe builds a fresh CNF and backend (`src/sat/solve.py:338-353`);
  there is no incremental/assumption reuse. RQ2 therefore measures solvers in
  "repeated one-shot solve" mode, which penalizes solvers with high per-instance
  startup cost. State this in the protocol.

## 3. Upper-bound handling — `ub` cannot prune, and is not plumbed

* `src/sat/solve.py:394-399` — `ub` must be an `int >= 1` (`bool` rejected).
* `src/sat/solve.py:121-123` — `ub` is a *check only*: OPT still requires solver
  UNSAT.
* `src/sat/solve.py:194-197` — a verified `B > ub` raises `ValueError` (the
  external bound was wrong, not the encoding).
* `src/sat/solve.py:168-218` — the loop never reads `ub`; it starts at `lo + 1`
  and stops at the first UNSAT, so `ub` neither bounds `hi` nor saves probes.
* **Blocker for a protocol claim:** `Config` has no `ub` field
  (`src/common/models.py:22-34`), and the worker calls
  `resolve(config.method)(instance, config)` with two arguments
  (`src/runner/worker.py:28`), so no runner/benchmark run can pass `ub`. If the
  protocol says "external upper bound supplied to the solver", it is wrong.
  Either (a) delete `ub` from the protocol, or (b) add `ub` to `Config` and the
  worker call — a code change outside this read-only review.
* **Note:** inside the runner a wrong `ub` surfaces as status ERR through the
  worker's `except Exception` (`src/runner/worker.py:36-41`), not as a
  `ValueError` at the caller. Any protocol rule "invalid ub aborts the run"
  should say ERR record, not exception.

## 4. Memory — hard limit is not enforced, MO is improbable

* `src/sat/solve.py:39-45` — `memory_limit` is in the ignored fields; the
  warning text states status MO never appears from the solver.
* `src/runner/runner.py:55` — the hard kill limit is time-based only
  (`time_limit + KILL_GRACE_SECONDS`); no RSS cap.
* `src/runner/worker.py:34-35`, `src/runner/runner.py:97-99` — MO exists only as a
  mapping of `MemoryError`.
* `src/sat/solve.py:131-135`, `:164`, `:182`, `:341-350` — `peak_memory` is the
  maximum of sampled working sets (before solve, after each probe, inside each
  probe), not peak RSS and not a cap.
* **Blocker for the P3 checklist item** "Xác nhận hard memory limit thực sự được
  enforce": it is not enforced anywhere in P2 code. The protocol must either drop
  the hard-memory-limit claim or defer it to a runner-level implementation.
  Expected consequence for RQ2: MO column will be 0 by construction; report that
  explicitly instead of reading it as "no memory pressure".

## 5. Order encoding and the AMO axis of RQ1

* `src/sat/order.py:19-21`, `:85-97` — the order encoding has no AMO group; the
  monotone chain replaces ALO + AMO, and `amo_encoding` is recorded but changes
  no clause.
* **Note:** in the RQ1 2×2, `order/pairwise` and `order/seqcounter` must produce
  identical CNF sizes, times (within noise) and status. Two identical rows are
  the expected result, not a bug and not "AMO had no effect on solving". The
  protocol should say this before the table is read.
* Consequence for the canonical config: if `abp_encoding = order` wins, the
  `amo_encoding` choice is inert; pick `pairwise` (default, no auxiliary
  variables) and state that the AMO axis matters only for `pairwise`.

## 6. CNF size metrics are per last probe, not per optimum

* `src/sat/solve.py:269-270` — `Result.variables` / `Result.clauses` come from
  `last_cnf`, i.e. the last threshold probed (normally the first UNSAT `K = hi`),
  not from the optimal threshold.
* Asserted in `tests/sat/test_solve.py:48-51` ("kích thước CNF của Result là của
  lần dò CUỐI"). Note the test comment points at "`docs/sat_spec.md` mục 6", but
  that file currently stops at section 5 — documentation gap, not a code bug.
* **Note:** RQ1's "variables" and "clauses" columns are "CNF at `K = hi`".
  Comparing `pairwise` and `order` at that K is fair (same K per instance), but
  the column must not be labelled "CNF at optimum" and must not be compared
  across instances with different `hi`.

## 7. Correctness and objective verification claims

* Encoding matrix vs brute-force oracle, `n <= 9`, all
  encoding × AMO × {cadical195, glucose4} combinations:
  `tests/sat/test_matrix.py`.
* Pipeline vs oracle and per-K SAT/UNSAT: `tests/sat/test_g1_oracle.py`,
  `tests/sat/test_solve.py`; Glucose end-to-end: `tests/sat/test_glucose_e2e.py`.
* Objective is recomputed by `verify()` on every decoded labeling
  (`src/sat/solve.py:188`, `src/common/verify.py:9-53`), and the runner re-checks
  worker output independently (`src/runner/runner.py:107-124`). The protocol's
  "objective verification" claim is supported for `solve_sat`.
* `src/sat/solve.py:277-300` — `solve_decision` returns a labeling **without**
  `verify()`; documented in `docs/sat_spec.md` §4. Do not cite
  `solve_decision` as the verification path.
* **Note:** the correctness suite does not cover `n > 9` against an independent
  oracle; `n >= 10` correctness rests on solver UNSAT plus the invariants in the
  appendix. Say that in the protocol's validity section.

## 8. Canonical-config criteria — what the pilots can and cannot decide

* RQ1 (`experiments/pilot_rq1.py`) fixes `cadical195`, `search_mode = multi`,
  `symmetry = false`, `warm_start = false`; it varies `abp_encoding` ∈
  {`pairwise`, `order`} and `amo_encoding` ∈ {`pairwise`, `seqcounter`}.
* RQ2 (`experiments/pilot_rq2.py`) fixes the encoding pair and varies the four
  available solvers; it refuses any kissat-family name at grid construction.
* Selection criterion must be stated before official runs: primary = OPT coverage
  (count of OPT at fixed `time_limit`), secondary = `t_total` on instances solved
  by both, tertiary = CNF size (`variables`, `clauses`) and `peak_memory`.
  Coverage on the two large instances (`n = 40, 50`) separates the encodings
  strongly, so it must be reported per size bucket, not only as a total.
* **Note:** the validation subset in `benchmark/validation/` +
  `benchmark/large/` is provisional (P3 has not locked one). The protocol should
  record the generator seed and file hashes, or the pilot numbers are not
  reproducible if the subset is regenerated later.

## 9. Environment note (not a repo defect)

On the review machine `%TEMP%\pytest-of-ducqu` exists with an ACL owned by
another security context; `pytest` fixtures using `tmp_path` fail with
`PermissionError` until `TEMP`/`TMP` point to an accessible directory (full suite
with the W3 tests: 498 passed, 3 skipped). Anyone reproducing the correctness
suite on Windows should check this first.
