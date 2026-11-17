# Release — W2 `--dry-run` (Gate 2, local-only mode)

Date: 2026-11-03 · Branch: `p2/w4-sat` · HEAD `6b6b8b5`
Target environment: **dev/staging local only**. No production deploy.
Release mode: **local only** — customer approved Gate 2 with all changes left
uncommitted in the working tree for review.

No `git commit`, `git push`, `git tag`, or `git merge` was run. Nothing was
deployed. The working tree is the release artifact.

Upstream: `infra.md`, `staging-deploy.md`, `qa-staging.md`, `uat.md`, `uat-ba.md`.

---

## 1. Step 15 — Local-only release verification

### 1.1 Release decision

| Item | Value |
|---|---|
| Gate | Gate 2 (W2 `--dry-run`) |
| Customer instruction | Local only: leave changes uncommitted, no commit/push/merge |
| QA verdict (`qa-staging.md`) | PASS — 538 passed, 3 skipped |
| UAT verdict (`uat.md`) | PASS — accepted |
| BA UAT verdict (`uat-ba.md`) | PASS — sign-off granted |
| Release action taken | none (no commit, no push, no tag, no merge, no deploy) |
| Release artifact | uncommitted working tree on `p2/w4-sat` |

### 1.2 Final git state (recorded verbatim)

Commands, from repo root `C:\Users\ducqu\workspace\ABP`:

```powershell
git branch --show-current
git rev-parse --short HEAD
git status --short
git diff --check
git describe --tags --always --dirty
git diff --stat
```

Results:

- `git branch --show-current` → `p2/w4-sat`
- `git rev-parse --short HEAD` → `6b6b8b5`
- `git describe --tags --always --dirty` → `v0.1-contract-126-g6b6b8b5-dirty`
- `git diff --check` → exit `0`, no output
- `git diff --stat` → `12 files changed, 708 insertions(+), 34 deletions(-)`

`git status --short` — 12 modified files + 1 untracked directory:

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

Every path is inside the scope D6 intended set. No file outside it.

### 1.3 Release-mode compliance

| Prohibition | Check | Result |
|---|---|---|
| No commit | `git log --oneline -3` → HEAD still `6b6b8b5` | PASS |
| No push | `git rev-list --left-right --count '@{u}...HEAD'` → `0	0` (in sync with `origin/p2/w4-sat`) | PASS |
| No tag | `git tag --points-at HEAD` → empty | PASS |
| No merge | branch is `p2/w4-sat`, not `main`; no merge commit in `git log -3` | PASS |
| No stash | `git stash list` → empty | PASS |
| No deploy | no deploy command run in this phase | PASS |

`0	0` means the branch is level with its upstream: the W2 work exists only as
uncommitted changes, so nothing reached the remote.

### 1.4 Artifact discipline

| Check | Command | Result |
|---|---|---|
| `results/raw/` untouched | `git status --porcelain results/raw` | empty; entry count `70` (matches `staging-deploy.md` §2.3 and `uat.md` §1.3) |
| `docs/handoff/sat-g1/` untouched | `git status --porcelain docs/handoff/sat-g1` | empty |
| No test/build artifacts | `git status --porcelain` filtered for `pytest\|pyc\|coverage` | no hits |
| Handoff dir contents | `Get-ChildItem docs/handoff/w2-dry-run` | 13 files before this document, 14 after |

`results/raw/` is gitignored with 0 tracked files, so the git check alone cannot
prove "no writes" (`staging-deploy.md` §2.3). The entry count `70` is the
corroborating evidence; it is unchanged from the pre-verification snapshot.

---

## 2. Step 16 — Post-release verification

### 2.1 Verification checks

Run these against the working tree. All are read-only.

| # | Check | Command | Expected |
|---|---|---|---|
| 1 | Branch unchanged | `git branch --show-current` | `p2/w4-sat` |
| 2 | HEAD unchanged | `git rev-parse --short HEAD` | `6b6b8b5` |
| 3 | Nothing committed | `git log --oneline -1` | `6b6b8b5 fix(sat): catch license-as-TO ...` |
| 4 | Nothing pushed | `git rev-list --left-right --count '@{u}...HEAD'` | `0	0` |
| 5 | No tag created | `git tag --points-at HEAD` | empty |
| 6 | Working tree matches handover | `git status --short` | the 13 lines in §1.2 |
| 7 | No whitespace damage | `git diff --check` | exit `0`, no output |
| 8 | Diff size unchanged | `git diff --stat` | `12 files changed, 708 insertions(+), 34 deletions(-)` |
| 9 | `results/raw/` untouched | `git status --porcelain results/raw` + entry count | empty; `70` |
| 10 | `sat-g1` untouched | `git status --porcelain docs/handoff/sat-g1` | empty |
| 11 | Suite still green | `.venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp` | `538 passed, 3 skipped` |
| 12 | Dry-run still writes nothing | §2.2 smoke command | exit `0`, 5 `DRY_RUN` lines, `results/raw` count still `70` |

Check 11 and 12 are the only ones that execute code. Both are safe: the suite
uses an external basetemp, and the smoke command carries `--dry-run`.

### 2.2 Smoke command (read-only)

```powershell
.venv\Scripts\python.exe -m src.runner --instance benchmark/toy/path4.json --method sat --abp-encoding pairwise --amo-encoding seqcounter --sat-solver cadical195 --search-mode multi --time-limit 1800 --out results/raw --dry-run
```

Expected: exit `0`, stderr empty, exactly 5 `DRY_RUN` lines, `hard_limit=1830.0`,
`exists=false resume_would_skip=false`, and no new entry under `results/raw`.
The same command **without** `--dry-run` is not a verification step — it writes a
real run output.

### 2.3 Hygiene alerts

Raise an alert and stop the handover if any of these appear.

| Alert | Signal | Meaning | Action |
|---|---|---|---|
| A1 Commit appeared | `git log --oneline -1` no longer `6b6b8b5` | Gate 2 local-only instruction violated | Stop. Report to customer before any further git action. |
| A2 Push happened | `git rev-list --left-right --count '@{u}...HEAD'` shows a non-zero left or right count | Work left the machine | Stop. Report to customer. Do not force-push. |
| A3 Tag created | `git tag --points-at HEAD` non-empty | Release tagged without authorization | Stop. Report; do not delete the tag without instruction. |
| A4 Unexpected path in status | `git status --short` shows a path outside §1.2 | Out-of-scope change or new artifact | Identify the path. Do not revert pre-existing dirt. |
| A5 `results/raw` grew | entry count > `70` after a dry-run | Dry-run write regression (A2 scope) | Treat as a defect. Capture the new file name before deleting anything. |
| A6 `sat-g1` dirt returned | `git status --porcelain docs/handoff/sat-g1` non-empty | Someone "restored" the stale baseline from `infra.md` §2.3 | Do not clean it. Record it; it is not part of this task. |
| A7 Whitespace damage | `git diff --check` non-zero | Trailing whitespace or conflict marker introduced | Fix the offending line only. |
| A8 Suite red | pytest reports any failure | Regression | Stop the handover. Report the failing test id. |
| A9 `-dirty` suffix gone | `git describe` has no `-dirty` | Changes were committed or reverted | Cross-check A1/A2 before concluding anything. |

A9 is informational: the `-dirty` suffix is expected while the work is
uncommitted. Its disappearance means the tree changed, not that the release is
better.

### 2.4 Known non-blocking observations (carried, not fixed)

From `qa-staging.md` and `uat-ba.md`, accepted at Gate 2:

1. `src/runner/runner.py:51` — `start = perf_counter()` is taken after
   `read_instance` (line 48), so dry-run `wall_time` excludes instance parsing.
   Cosmetic for a pre-flight report.
2. `make_run_id` is computed in both the dry-run and real-run paths. Pure
   function, redundant not wrong.
3. `qa-staging.md` B4 probe (`--out` at an existing file, `--out Z:\nope`) has no
   automated test; manual probe only.

None of these block the local-only handover.

---

## 3. Rollback runbook

Nothing was deployed, committed, pushed, or tagged, so there is no release to
roll back. The only rollback that can apply is discarding the uncommitted W2
work.

**Name the branch first. Do not run any rollback command until it prints
`p2/w4-sat`.**

```powershell
git branch --show-current   # must print p2/w4-sat
```

### 3.1 Discard the W2 code and doc changes

```powershell
git checkout -- src/runner/runner.py src/runner/__main__.py tests/runner/test_runner.py
git checkout -- "docs/handoff/abp-sat-encoding/issues/W2/08-amo-pairwise-seqcounter.md" "docs/handoff/abp-sat-encoding/issues/W2/09-glucose-kissat-backend.md" "docs/handoff/abp-sat-encoding/issues/W2/10-multi-run-k-search.md" "docs/handoff/abp-sat-encoding/issues/W2/11-loader-generator-full.md" "docs/handoff/abp-sat-encoding/issues/W2/12-correctness-test-matrix.md" "docs/handoff/abp-sat-encoding/issues/W2/13-review-exact-formulation.md" "docs/handoff/abp-sat-encoding/issues/W2/14-sat-methodology-draft.md" "docs/handoff/abp-sat-encoding/issues/W2/15-m1-gate-bonus-decision.md"
git checkout -- docs/handoff/w2-sat/15-m1-gate-evidence.md
```

The glob form `"docs/handoff/abp-sat-encoding/issues/W2/08..15*.md"` in
`infra.md` §3.1 does not expand in PowerShell. The explicit list above is the
working equivalent.

### 3.2 Remove the untracked handoff directory

`docs/handoff/w2-dry-run/` is untracked, so `git checkout --` will not remove it.
Delete it only if that is the intent:

```powershell
Remove-Item -Recurse -Force docs/handoff/w2-dry-run
```

This deletes every document in this handoff, including this one. Confirm with the
customer before running it.

### 3.3 Forbidden commands

Do **not** run:

- `git checkout -- .`
- `git reset --hard`
- `git clean -fd`
- `git push --force`

Each of these also destroys work outside the W2 scope, or rewrites shared
history. `infra.md` §3.1 forbids the first two for the same reason.

### 3.4 Verify the rollback

```powershell
git status --short
git log --oneline -3
git rev-list --left-right --count '@{u}...HEAD'
```

Expected after a full rollback: `git status --short` empty (or only the
pre-existing dirt, if any exists at that time), HEAD still `6b6b8b5`, and `0	0`
against `origin/p2/w4-sat`. `results/raw` entry count stays `70`.

### 3.5 If the work was already committed and pushed

That state does not exist today (§1.3). If it ever does, use `git revert <sha>`
on a new branch. Do not rewrite shared history.

---

## 4. Handover state

| Item | State |
|---|---|
| Environment | dev/staging local only |
| Deployed | nothing |
| Committed | nothing |
| Pushed | nothing |
| Tagged | nothing |
| Working tree | 12 modified files + untracked `docs/handoff/w2-dry-run/` |
| Branch vs upstream | `0	0` |
| Suite | 538 passed, 3 skipped |
| `results/raw` | 70 entries, unchanged |
| Rollback | §3, local only, no deploy to undo |

The working tree is the deliverable. A reviewer can inspect it with
`git diff` and `git status`, and can discard it with §3.1–§3.2.

---

## 5. Risks

- **Reviewer commits or pushes by habit** — signal: alert A1 or A2 fires.
  Mitigation: §2.3, and the release-mode table in §1.3.
- **`results/raw` write regression is invisible to the git check** — signal:
  entry count rises above `70` while `git status --porcelain results/raw` stays
  empty. Mitigation: count the entries, do not trust the git check alone.
- **Stale `infra.md` §2.3 baseline** — signal: `docs/handoff/sat-g1/` becomes
  dirty after a reviewer tries to reproduce the documented baseline. Mitigation:
  `staging-deploy.md` §2.1; do not restore that dirt.
- **PowerShell glob in `infra.md` §3.1 does not expand** — signal: `git checkout`
  reports a pathspec that did not match. Mitigation: use the explicit file list
  in §3.1 of this document.
- **Untracked handoff directory is easy to lose** — signal: `docs/handoff/w2-dry-run/`
  missing after a `git clean` or a fresh clone. Mitigation: it is untracked by
  design in local-only mode; copy it out before any cleanup.
