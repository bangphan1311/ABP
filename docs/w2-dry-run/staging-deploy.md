# Staging verification — W2 `--dry-run`

Date: 2026-11-03 · Branch: `p2/w4-sat` · Executed per `infra.md` §1–§3.
Target environment: **dev/staging local only**. No production deploy. No commit,
no push, no merge to `main` was performed.

---

## 1. Environment state

| Item | Recorded value | Expected (source) | Match |
|---|---|---|---|
| Interpreter | `Python 3.11.15` | 3.11.x, ENV.md says 3.11.17 | yes (patch differs) |
| Interpreter path | `.venv\Scripts\python.exe` | same (infra §1.1) | yes |
| Branch | `p2/w4-sat` | `p2/w4-sat` (infra §2.1) | yes |
| HEAD | `6b6b8b5` | — | — |
| `git describe --tags --always --dirty` | `v0.1-contract-126-g6b6b8b5-dirty` | `-dirty` suffix expected (infra §2.4) | yes |
| `git diff --check` | exit `0`, no output | clean | yes |
| Console codepage | cp1252 | cp1252 (infra §1.3) | yes |

`-dirty` suffix is caused by the uncommitted W2 `--dry-run` work itself, not by
`docs/handoff/sat-g1/` (see §2.1).

### 1.1 Interpreter note

`3.11.15` vs ENV.md `3.11.17`. Same minor line, `pysat` present, runner suite
green. No action; recorded as observed rather than adjusted to match the doc.

---

## 2. Git hygiene

### 2.1 Baseline deviations from `infra.md` §2.3

`infra.md` §2.3 lists three pre-existing dirt items. Two are **not present** on
this machine at verification time:

| Item in infra §2.3 | Observed | Note |
|---|---|---|
| dirty files under `docs/handoff/sat-g1/` (11 files) | **clean** — `git status --porcelain docs/handoff/sat-g1` empty | matches `dev-notes.md` §3.4 observation |
| untracked `.pytest-tmp/` | **absent** | external basetemp used, nothing created in repo |
| untracked `docs/handoff/w2-dry-run/` | present | expected, this directory |

Consequence: the `-dirty` suffix in §1 comes from the W2 changes themselves.
`infra.md` §2.4 attributes it to `sat-g1` dirt; that attribution is stale. The
suffix itself is still expected and was not cleaned.

### 2.2 Working tree

`git status --porcelain` — 12 modified files + 1 untracked directory, all inside
the scope D6 intended set:

```
 M docs/handoff/abp-sat-encoding/issues/W2/08-amo-pairwise-seqcounter.md
 M docs/handoff/abp-sat-encoding/issues/W2/09-glucose-kissat-backend.md
 M docs/handoff/abp-sat-encoding/issues/W2/10-multi-run-k-search.md
 M docs/handoff/abp-sat-encoding/issues/W2/11-loader-generator-full.md
 M docs/handoff/abp-sat-encoding/issues/W2/12-correctness-test-matrix.md
 M docs/handoff/abp-sat-encoding/issues/W2/13-review-exact-formulation.md
 M docs/handoff/abp-sat-encoding/issues/W2/14-sat-methodology-draft.md
 M docs/handoff/abp-sat-encoding/issues/W2/15-m1-gate-bonus-decision.md
 M docs/handoff/w2-sat/15-m1-gate-evidence.md
 M src/runner/__main__.py
 M src/runner/runner.py
 M tests/runner/test_runner.py
?? docs/handoff/w2-dry-run/
```

`git diff --stat`: 12 files changed, 708 insertions(+), 34 deletions(-).
No file outside the intended set. No `.pytest_cache/`, no `.pyc`, no coverage
file, no temp directory added.

### 2.3 `results/raw/` discipline

`results/raw/` is gitignored (`.gitignore:10`) and has **0 tracked files**, so
`git status --porcelain results/raw` is empty regardless of content. That check
alone cannot prove "no writes". A filesystem snapshot was used instead:

- 70 pre-existing entries (files + dirs) captured before the smoke checks.
- Same snapshot captured after both dry-runs.
- `Compare-Object` result: **identical** — no new file, no modified size, no
  changed mtime.

`git status --porcelain results/raw` → empty (as expected, and now corroborated
by the snapshot).

---

## 3. Commands run

All from repo root `C:\Users\ducqu\workspace\ABP`.

### 3.1 Environment and hygiene

```powershell
.venv\Scripts\python.exe --version
git branch --show-current
git status --porcelain
git diff --check
git describe --tags --always --dirty
git log --oneline -3
git check-ignore -v results/raw
git ls-files results/raw
```

Results: `Python 3.11.15`; `p2/w4-sat`; status as §2.2; `git diff --check` exit
`0`; `v0.1-contract-126-g6b6b8b5-dirty`; HEAD `6b6b8b5`; `results/raw` ignored by
`.gitignore:10`; 0 tracked files under `results/raw`.

### 3.2 Dry-run smoke check — toy instance

```powershell
.venv\Scripts\python.exe -m src.runner --instance benchmark/toy/path4.json --method sat --abp-encoding pairwise --amo-encoding seqcounter --sat-solver cadical195 --search-mode multi --time-limit 1800 --out results/raw --dry-run
```

Exit `0`. stderr `0` bytes. stdout `5` lines:

```
DRY_RUN run_id=path4__sat__pairwise__seqcounter__cadical195__multi__sym0__ws0__s0__tl1800.0__mlNone
DRY_RUN instance=path4 n=4 m=3
DRY_RUN config method=sat abp_encoding=pairwise amo_encoding=seqcounter sat_solver=cadical195 search_mode=multi symmetry=false warm_start=false seed=0
DRY_RUN budget time_limit=1800.0 hard_limit=1830.0 memory_limit=none memory_limit_enforced=false
DRY_RUN output out_file=results\raw\path4__sat__pairwise__seqcounter__cadical195__multi__sym0__ws0__s0__tl1800.0__mlNone.json exists=false resume_would_skip=false
```

`hard_limit=1830.0` = `time_limit + KILL_GRACE_SECONDS` (1800 + 30). `out_file`
is relative. `exists=false resume_would_skip=false`.

### 3.3 Dry-run smoke check — validation instance

```powershell
.venv\Scripts\python.exe -m src.runner --instance benchmark/validation/randconn16-seed20261026.json --method sat --abp-encoding pairwise --amo-encoding seqcounter --sat-solver cadical195 --search-mode multi --time-limit 1800 --out results/raw --dry-run
```

Exit `0`. stdout `5` lines:

```
DRY_RUN run_id=randconn16-seed20261026__sat__pairwise__seqcounter__cadical195__multi__sym0__ws0__s0__tl1800.0__mlNone
DRY_RUN instance=randconn16-seed20261026 n=16 m=32
DRY_RUN config method=sat abp_encoding=pairwise amo_encoding=seqcounter sat_solver=cadical195 search_mode=multi symmetry=false warm_start=false seed=0
DRY_RUN budget time_limit=1800.0 hard_limit=1830.0 memory_limit=none memory_limit_enforced=false
DRY_RUN output out_file=results\raw\randconn16-seed20261026__sat__pairwise__seqcounter__cadical195__multi__sym0__ws0__s0__tl1800.0__mlNone.json exists=false resume_would_skip=false
```

Second instance confirms the path is not toy-specific: `n=16 m=32` read from the
real validation file, `run_id` derived from its `instance.id`.

### 3.4 No-write confirmation

```powershell
Get-ChildItem -Force -Recurse results/raw | ... | Out-File raw-before.txt   # before
Get-ChildItem -Force -Recurse results/raw | ... | Out-File raw-after.txt    # after
Compare-Object (Get-Content raw-before.txt) (Get-Content raw-after.txt)
git status --porcelain results/raw
```

`Compare-Object` → no differences. `git status --porcelain results/raw` → empty.

### 3.5 Test suite

```powershell
.venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp
```

`538 passed, 3 skipped in 20.44s`, exit `0`. The 3 skips are the expected CPLEX
CP engine skips (scope A11). Zero failures.

```powershell
.venv\Scripts\python.exe -m pytest tests/runner -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp-runner
```

`30 passed in 5.55s`. Matches `dev-notes.md` §2.

Post-suite `git status --porcelain` unchanged from §2.2 — the external basetemp
left no artifact in the repo.

---

## 4. Verification matrix

| # | Check | Source | Result |
|---|---|---|---|
| 1 | `.venv` interpreter is 3.11.x | infra §1.1 | PASS (3.11.15) |
| 2 | Branch is `p2/w4-sat` | infra §2.1 | PASS |
| 3 | `git diff --check` clean | infra §2.3 | PASS (exit 0) |
| 4 | `docs/handoff/sat-g1/` untouched | task brief | PASS (clean, no writes) |
| 5 | `results/raw/` untouched | infra §2.2 | PASS (snapshot identical) |
| 6 | Toy dry-run: 5 lines, exit 0, stderr empty | infra §1.4 | PASS |
| 7 | Validation dry-run: 5 lines, exit 0 | task brief | PASS |
| 8 | Full suite green | infra §3.2 step 2 | PASS (538/3) |
| 9 | Runner suite green | dev-notes §2 | PASS (30) |
| 10 | No commit / push / merge | task brief | PASS (none run) |

---

## 5. Readiness for QA & UAT before Gate 2

**Ready.** All ten checks pass. The `--dry-run` path is verified on two
instances of different size, writes nothing, and the full suite is green with
only the baseline CPLEX skips.

Handover points for QA:

1. **`results/raw` check is weak on its own.** The directory is gitignored with
   0 tracked files, so `git status --porcelain results/raw` is always empty.
   QA should use a filesystem snapshot (or `Get-ChildItem` count) to prove
   "no writes", not the git check alone. `infra.md` §2.2/§3.2 step 4 should be
   amended.
2. **`infra.md` §2.3 baseline is stale.** `docs/handoff/sat-g1/` is clean and
   `.pytest-tmp/` is absent. The `-dirty` suffix in §2.4 comes from the W2
   changes, not from `sat-g1`. Do not "restore" that dirt to match the doc.
3. **Interpreter patch level** is 3.11.15, not the 3.11.17 in ENV.md. Harmless;
   ENV.md may be updated.
4. **Known limits unchanged** (`dev-notes.md` §4): dotted-path methods and
   registry methods with a missing backend pass dry-run and fail on a real run;
   dry-run does not estimate CNF size or runtime; exit `1` still means "real run
   produced an `ERR` record", validation dry-run uses `2`.

UAT scope: the dry-run contract only. Gate 2 decision on the real-run path is
out of scope for this document.

---

## 6. Rollback

Not executed — nothing was deployed, committed, or pushed. Working tree is
exactly as handed over.

If the W2 changes must be discarded, follow `infra.md` §3.1 and name the branch
first:

```powershell
git branch --show-current   # expect p2/w4-sat
git checkout -- src/runner/runner.py src/runner/__main__.py tests/runner/test_runner.py
git checkout -- "docs/handoff/abp-sat-encoding/issues/W2/08..15*.md"
git checkout -- docs/handoff/w2-sat/15-m1-gate-evidence.md
git checkout -- docs/handoff/w2-dry-run/
```

Do **not** run `git checkout -- .` or `git reset --hard`. `docs/handoff/w2-dry-run/`
is untracked, so `git checkout --` will not remove it; delete it explicitly if
that is the intent.

---

## 7. Risks

- **`results/raw` write regression goes undetected by the git check** — signal:
  file count under `results/raw` grows after a dry-run while
  `git status --porcelain results/raw` stays empty. Mitigation: snapshot check
  (§3.4).
- **cp1252 console** — signal: `UnicodeEncodeError` on a dry-run error path with
  a non-ASCII `--out` or Vietnamese method message. Not observed here; covered
  by the suite's cp1252/utf-8 CLI tests.
- **Stale `infra.md` baseline** — signal: a reviewer tries to reproduce the
  `sat-g1` dirt and dirties the tree. Mitigation: §2.1 of this document.
