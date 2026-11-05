# Infrastructure & Verification — W2 dry-run (`--dry-run`)

Target environment: **dev/staging local only**. No production deploy authorized.
No deploy command in this document. Rollback named in §3.

---

## 1. Local dev/staging verification environment

### 1.1 Python interpreter

Use `.venv\Scripts\python.exe` (Python 3.11.x). The global `python` on this
machine is 3.13 and lacks `pysat`; the runner imports fail on it (scope I9).
The `.venv` is the only interpreter that can run the runner suite and the CLI.

```powershell
.venv\Scripts\python.exe --version
```

Expect `Python 3.11.x` (ENV.md records 3.11.17).

### 1.2 Pytest basetemp

The Windows default temp directory is locked (`PermissionError WinError 5`).
Always pass a basetemp outside the repo:

```powershell
.venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp
```

Rules:

- Never omit `--basetemp` on this machine.
- The path must stay outside the repository so pytest does not create
  `.pytest-tmp/` or any artifact that would dirty `git status`.
- "Green" means passed + skipped. Three CPLEX CP skips are expected and normal
  (scope A11).

### 1.3 Windows cp1252 console encoding

The console codepage is cp1252. Vietnamese error text from `--dry-run` raises
`UnicodeEncodeError` if stderr is not made lossy-safe.

Implementation requirement (api-contract §2.3): reconfigure stderr before
writing the error line, e.g. `sys.stderr.reconfigure(errors="replace")` when the
attribute exists. The Vietnamese method-error message must not crash the error
path.

Test requirement (scope A10): CLI failure subprocesses must set
`PYTHONIOENCODING=utf-8` so the test observes the real message and not a codec
crash. Assert stderr starts with `DRY_RUN ERROR:`, contains no traceback, exit
code is `2`, and nothing is written under `--out`.

### 1.4 Verification commands

Full suite:

```powershell
.venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp
```

Dry-run CLI smoke check on the toy instance:

```powershell
.venv\Scripts\python.exe -m src.runner --instance benchmark/toy/path4.json --method sat --abp-encoding pairwise --amo-encoding seqcounter --sat-solver cadical195 --search-mode multi --time-limit 1800 --out results/raw --dry-run
```

The command above is safe with `--dry-run`: it must print five `DRY_RUN` lines
and write nothing under `results/raw`. The same command without `--dry-run`
is **not** part of verification — it would write a real run output.

---

## 2. Branch & git hygiene

### 2.1 Branch policy

- Work on feature branch `p2/w4-sat` (branch named in the evidence doc).
- `main` is stable. Merge via PR.
- Never force-push shared history. Rebase only local, unpushed commits.

### 2.2 Artifact discipline in `results/raw/`

`results/raw/` holds real run outputs only. The dry-run path must never create a
file or directory there (scope A2/A9, api-contract §1.2 prohibitions).

Rules:

- Tests use `--out <tmp_path>` and never assert on a repo-absolute path (B3).
- The only evidence command that names `--out results/raw` is the §4.1 command;
  it includes `--dry-run`, so it writes nothing. The path in its output stays
  relative.
- Do not use `results/raw/` as a scratch directory for verification runs.
- Check after verification: `git status --porcelain results/raw` must show no
  new or modified files.

### 2.3 Preserve `git status` cleanliness

Pre-existing dirt exists and is **not** part of this task (scope D6/S7):

- dirty files under `docs/handoff/sat-g1/` (11 files);
- untracked `.pytest-tmp/`;
- untracked `docs/handoff/w2-dry-run/`.

Rules:

- Do not stash, revert, or delete the pre-existing dirt to make `git status`
  look clean. That dirt is baseline, not a violation.
- Do not add new artifacts: no `.pytest_cache/`, no `.pyc`, no temp dirs, no
  coverage files, no real run outputs in `results/raw/`.
- Tests that need files use `tmp_path` or the external basetemp.
- Intended changes are limited to the files listed in scope D6:
  - `src/runner/runner.py`
  - `src/runner/__main__.py`
  - `tests/runner/test_runner.py`
  - `docs/handoff/abp-sat-encoding/issues/W2/08..15*.md` (8 files)
  - `docs/handoff/w2-sat/15-m1-gate-evidence.md`
  - handoff docs in `docs/handoff/w2-dry-run/`
- Before commit: `git status --porcelain` and `git diff --stat`; confirm only
  intended paths plus known pre-existing dirt.
- Commit message follows Conventional Commits: `feat(runner): add --dry-run`
  or `fix(...)` as appropriate.

### 2.4 `git describe` dirty suffix

`git describe --tags --always --dirty` includes a `-dirty` suffix because of
the pre-existing `docs/handoff/sat-g1/` dirt. That suffix is expected in the
dry-run record and in the §4.1 evidence. Do not clean the repo to remove it
(scope R4 review-qa).

---

## 3. Rollback & verification

### 3.1 Rollback plan (dev/staging local)

Rollback targets local, unmerged work only. Name the branch first:

```powershell
git branch --show-current   # expect p2/w4-sat
```

If the branch is unpushed, restore tracked files:

```powershell
git checkout -- src/runner/runner.py src/runner/__main__.py tests/runner/test_runner.py
git checkout -- "docs/handoff/abp-sat-encoding/issues/W2/08..15*.md"
git checkout -- docs/handoff/w2-sat/15-m1-gate-evidence.md
git checkout -- docs/handoff/w2-dry-run/
```

Do **not** run `git checkout -- .` or `git reset --hard`: that would also wipe
the pre-existing dirt in `docs/handoff/sat-g1/` and the untracked handoff
directory. Roll back only the paths above.

If the branch is already pushed and the change merged, use `git revert <sha>`
on a new branch. Do not rewrite shared history.

After rollback, verify the repo state:

```powershell
git status --porcelain
git log --oneline -3
```

Expected: only pre-existing dirt remains; no new files in `results/raw/`.

### 3.2 Verification sequence

1. Confirm interpreter and branch:
   ```powershell
   .venv\Scripts\python.exe --version
   git branch --show-current
   ```
2. Run the full suite with the external basetemp (§1.2). Confirm passed +
   skipped, zero failures.
3. Run the dry-run CLI smoke check (§1.4). Confirm five `DRY_RUN` lines, exit
   code `0`, stderr empty.
4. Confirm no writes:
   ```powershell
   git status --porcelain results/raw
   ```
   Expect no output.
5. For the §4.1 evidence, capture the real command and stdout verbatim, plus
   the real `git describe --tags --always --dirty` output.
6. Rollback drill (optional, before merging): repeat step 1, then run the
   rollback commands in §3.1 and confirm `git status` matches the pre-change
   baseline. Re-apply the branch if the drill is done on a throwaway clone or
   worktree.
