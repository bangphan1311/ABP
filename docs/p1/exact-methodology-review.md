# P1 Exact methodology audit — open review items

**Review date:** 2026-11-06  
**Owner:** P1  
**Scope:** source/documentation review only; no benchmark solver was executed for this audit  
**Status:** reviewed with open consistency items; not a W5/W6 completion record

## 1. Formulation review

The four Exact backends target the same ABP objective on a validated simple undirected graph:

- **Gurobi MIP and CPLEX MIP:** integer labels, one binary orientation variable for every unordered vertex pair to enforce pairwise distinctness, and one binary direction variable per graph edge to enforce the selected separation direction. Both use native indicator constraints rather than a manually chosen big-M constant.
- **CPLEX CP Optimizer:** integer labels, one global `all_diff` constraint, and one absolute-distance constraint per edge.
- **OR-Tools CP-SAT:** integer labels, one `all_different` constraint, and one integer absolute-distance variable per edge.

Structural counts in the current implementation:

| Backend | Structural decision variables |
|---|---:|
| Gurobi MIP / CPLEX MIP | `n + 1 + C(n,2) + m` |
| CPLEX CP | `n + 1` |
| CP-SAT | `n + 1 + m` |

For MIP, there are two indicator implications per vertex pair and two per edge. CP/CP-SAT counts do not describe the solvers' internal expansions or presolved representations.

The shared verifier checks that every vertex has exactly one label, labels form a permutation of `1..n`, and the objective recomputed over the input edges matches the reported objective. The brute-force oracle enumerates permutations only for small test instances (default maximum `n=9`).

## 2. Bound and optimality review

For `Delta = max_v deg(v)`, the bound `UB_degree = n - Delta` is valid for an instance with at least one edge. It is recorded in the HB manifest and can be used to sanity-check returned bounds. The current Exact models do not pass this degree-based bound into the `K` variable domain; their natural upper domain remains `n-1`. The degree bound is not an optimality certificate.

The MIP implementations use `K in [1,n-1]`. CPLEX CP uses the same lower bound. CP-SAT currently uses `K in [0,n-1]`; because every valid labeling on an instance with an edge has positive minimum edge distance, this wider domain does not change the optimum, but it is a small implementation-level modeling difference worth preserving in the methods description.

## 3. Timing and resource review

Each Exact backend accounts for model-construction time before passing the remaining time budget to its optimizer. The runner measures end-to-end `wall_time` around the worker process, including process startup and input loading. The protocol selects runner `wall_time` as the primary comparison metric; backend `t_encode`, `t_solve`, and `t_total` remain diagnostic fields.

The Exact solver APIs do not themselves enforce `Config.memory_limit`; the shared process supervisor applies the OS-level cap. The candidate P1 setup is Windows build `10.0.26200`, 12 logical CPUs, 15.21 GiB RAM, 12 GiB per run and sequential execution. This is a candidate snapshot, not P3's final official-host sign-off.

## 4. Open implementation/contract consistency items

These items should be resolved or explicitly accepted by the group before the protocol is frozen. They are recorded as review findings, not silently changed in this documentation-only pass.

### E1 — Memory-stop status when an incumbent exists

- In `src/exact/cplex_cp.py::_classify_status`, the `has_solution` branch is evaluated before the memory-stop check. A non-optimal verified incumbent therefore returns `FEAS` even when the stop cause contains `Out of memory`.
- `tests/exact/test_solver_status.py::test_cplex_cp_incumbent_preserved_after_memory_stop` explicitly expects `FEAS`.
- Gurobi MIP and CPLEX MIP classify recognized memory-limit termination as `MO` even when an incumbent exists.
- The shared documentation describes `MO` as a memory-limit event and permits preserving an incumbent when available. The adapters therefore do not currently normalize this case uniformly.

**Decision required:** choose whether status records the termination cause (`MO` with a retained verified incumbent) or prioritizes incumbent availability (`FEAS` with a separate memory-stop reason). Apply one policy to all adapters, update tests and CONTRACT/protocol/schema guidance, and make the analysis distinguish memory stops from timeouts.

### E2 — CPLEX CP incumbent extraction exceptions

In `src/exact/cplex_cp.py`, the block that extracts and verifies the labeling catches every exception and sets `has_solution=False`. The subsequent classifier can return `TO` when the fail status is `SearchStoppedByLimit`. This conflates (a) no incumbent being available and (b) an incumbent being present but failing extraction or verification.

**Action:** distinguish the solver's no-incumbent case from decode/verification failure. An invalid or malformed incumbent must be recorded as `ERR`, not silently normalized to `TO`. Add focused regression tests for both cases.

### E3 — CP-SAT ignored-configuration warnings

Gurobi MIP, CPLEX MIP and CPLEX CP call `warn_ignored_config`; `src/exact/cp_sat_solver.py` currently does not. CP-SAT uses its seed and time budget, while symmetry, warm-start, and search-mode fields are not implemented by this adapter; the memory cap is external to the solver function.

**Action:** make warnings/configuration metadata consistent across the Exact adapters, or document precisely which fields are applied by each adapter. A caller should not infer that a shared configuration field is effective merely because it appears in `Config`.

### E4 — Candidate Python version discrepancy

- `docs/w3_preflight.md` records Python 3.11.16 for the candidate run environment.
- `docs/ENV.md` records Python 3.11.17 in the Conda development environment.

**Action:** record the actual interpreter version from the selected `uv` environment at pilot/official execution and bind it to the raw records/commit. Do not silently select one documentation value as authoritative.

### E5 — Solver entitlement and scale evidence

The preflight records a successful small Gurobi Academic/WLS probe, but that is not benchmark-scale evidence. CPLEX MIP Community/Promotional Edition size limits and CPLEX CP Community Edition search-space limits have been observed; CPLEX Academic entitlement is not verified.

**Action:** preserve license/edition failures as `ERR` with raw reason. Do not interpret such records as solver timeouts or performance failures.

## 5. References and source locations

- `docs/exact_models.md`
- `docs/experimental_protocol.md`
- `docs/w3_preflight.md`
- `src/exact/gurobi_mip.py`
- `src/exact/cplex_mip.py`
- `src/exact/cplex_cp.py`
- `src/exact/cp_sat_solver.py`
- `src/exact/common.py`
- `src/exact/oracle.py`
- `src/common/verify.py`
- `src/runner/runner.py`
- `tests/exact/test_solver_status.py`
- `tests/exact/test_time_budget.py`

No solver experiment, official benchmark run, status sign-off, or W5/W6 completion is claimed by this audit.
