# Technical appendix (draft) — SAT formulation for the Antibandwidth Problem

Status: draft for P1/P3 review (W3, issue #26). Applies to the code on `main` at
W3 (`src/sat/pairwise.py`, `src/sat/order.py`, `src/sat/solve.py`,
`src/common/verify.py`). Proofs are sketches: each lemma names the code that
implements it and the test that exercises it. Nothing here is copied from the
2DBMP write-up; the ABP formulation is derived from the definitions below.

Notation: `G = (V, E)` is a finite undirected simple graph with `n = |V| >= 1`
and `m = |E| >= 1`; vertices are `0..n-1`. A *labeling* is a bijection
`f: V -> {1..n}`. Its antibandwidth is
`B(f) = min_{ {u,v} in E } |f(u) - f(v)|`, and the optimum is
`B*(G) = max_f B(f)`. The decision problem at threshold `K >= 1` asks for a
labeling with `B(f) >= K`.

## A.1 Pairwise encoding (`src/sat/pairwise.py`)

Variables `x[v][p]`, id `v*n + p`, meaning "vertex `v` receives label `p`"
(`pairwise.py:110`). Clauses (`pairwise.py:114-134`):

* **assignment** — one ALO clause `(x[v][1] or ... or x[v][n])` per vertex, plus
  AMO clauses `(-x[v][p] or -x[v][q])` for `p < q`.
* **permutation** — one ALO clause `(x[0][p] or ... or x[n-1][p])` per label,
  plus AMO clauses `(-x[u][p] or -x[w][p])` for `u < w`.
* **distance** — for each stored edge `{u, v}`, each `p` and each `q` with
  `1 <= |p - q| <= K - 1`: the binary clause `(-x[u][p] or -x[v][q])`.

The `q` loop `max(1, p-K+1) .. min(n, p+K-1)` is exactly
`{q : 1 <= |p - q| <= K-1}`, so all ordered label pairs at distance below `K`
are covered; as `p` runs over all labels the clause list is closed under
swapping `(p, q)`, which is what an undirected edge needs.

**Lemma A.1 (assignment).** If a model satisfies the assignment group, then for
every vertex `v` exactly one literal `x[v][p]` is true. ALO gives at least one,
AMO gives at most one.

**Lemma A.2 (permutation and bijectivity).** If a model satisfies the
permutation group, then every label is true at exactly one vertex. Together with
A.1 the map `f(v) =` the unique true label of `v` is a bijection `V -> {1..n}`.

**Lemma A.3 (distance).** Let a model satisfy groups assignment, permutation and
distance, with `f` as in A.2. Fix an edge `{u, v}`. If `|f(u) - f(v)| < K`, set
`p = f(u)`, `q = f(v)`; then `p != q` and `|p - q| < K`, so the clause
`(-x[u][p] or -x[v][q])` belongs to the distance group and is falsified by the
model — contradiction. Hence `|f(u) - f(v)| >= K`, i.e. `B(f) >= K`.
Conversely, every bijection `f` with `B(f) >= K` satisfies every distance clause:
a falsified clause would force `f(u) = p`, `f(v) = q` with `|p - q| < K`, which
`B(f) >= K` excludes. A.1 and A.2 hold because `f` is a bijection.

**Corollary A.3.1 (threshold/trivial).** For `K >= n` no labeling reaches `K`:
a bijection into `{1..n}` uses all labels, so the largest possible difference is
`n - 1`. `solve.py` therefore answers UNSAT without building a CNF
(`trivial_unsat`, `pairwise.py:90-93`, called at `solve.py:325`).

## A.2 Order encoding (`src/sat/order.py`)

Variables `o[v][p]` for `p in 1..n-1`, id `v*(n-1) + p`, meaning
"`f(v) <= p`" (`order.py:62`). The boundaries `p = 0` (always false) and
`p = n` (always true) need no variable. Clauses (`order.py:64-82`):

* **chain** — `(-o[v][p] or o[v][p+1])` for `p in 1..n-2`.
* **permutation** — for every vertex pair `u < w` and every `q in 1..n`:
  `notq(u) or notq(w)`, where `notq(v)` is the disjunction that means
  `f(v) != q` (`_not_value`, `order.py:33-45`).
* **distance** — for each edge `(u, v)` and each `p`, `q` with
  `1 <= |p - q| <= K-1`: `notp(u) or notq(v)`.

**Lemma A.4 (chains correspond to labels).** A truth assignment of
`o[v][1..n-1]` satisfies the chain group iff it is monotone
(`o[v][p] -> o[v][p+1]`). Define `f(v) = min{p : o[v][p] = 1}`, or `n` when all
are false. Monotonicity makes the true indices a suffix, so `f(v)` is well
defined, and for every `q in 1..n-1`

```
o[v][q] = 1  <=>  f(v) <= q,
```

because `f(v)` is the smallest true index (if `f(v) = r <= q` monotonicity gives
`o[v][q] = 1`; if `f(v) > q` no index `<= q` is true). The correspondence is
bijective: the monotone chain of a label `r <= n-1` is `0...0 1...1` with the
suffix starting at `r`, and label `n` is the all-zero chain. Hence
A-satisfying assignments of the `o` variables and labelings are in bijection.

**Lemma A.5 (`_not_value` is the right disjunction).**
`f(v) != q` iff `f(v) <= q-1` or `f(v) >= q+1`. By A.4 the first case is
`o[v][q-1]` and the negation of the second case is `f(v) <= q`, i.e.
`o[v][q]`. So `f(v) != q` iff `(o[v][q-1] or -o[v][q])`. For `q = 1` the
`o[v][0]` disjunct is false and the disjunction is `-o[v][1]`; for `q = n` the
`-o[v][n]` disjunct is false and it is `o[v][n-1]`. These are exactly the three
cases in `_not_value` (`order.py:41-45`).

**Lemma A.6 (permutation for order).** The permutation group forbids
`f(u) = f(w) = q` for every `u < w` and every `q` (by A.5 each clause is
satisfied iff at least one of the two values differs from `q`). Hence `f` is
injective on `V`; an injection from an `n`-element set into `{1..n}` is a
bijection, so `f` is a valid labeling.

**Lemma A.7 (distance for order).** Same argument as A.3 with A.5: the clause
`notp(u) or notq(v)` forbids `f(u) = p` and `f(v) = q` simultaneously, so no edge
joins labels at distance below `K`; conversely a labeling with `B(f) >= K`
falsifies no distance clause.

**Note (AMO is not a factor for order).** The chain group replaces ALO + AMO, so
`amo_encoding` is recorded in the `CNF` object but changes no clause
(`order.py:19-21`, `order.py:85-97`). Two configurations that differ only in
`amo_encoding` are therefore expected to produce identical CNF size and results
for `abp_encoding = order`; the RQ1 pilot records this as a consistency check,
not as a hypothesis.

## A.3 At-most-one encodings (`src/sat/pairwise.py:54-79`, `src/sat/backend.py:108-112`)

A function `amo(L)` is *faithful* when, for every assignment, its clause set is
satisfied iff at most one literal of `L` is true, and its auxiliary variables can
always be extended to a satisfying assignment when at most one `l in L` is true.

* **pairwise**: the set of all `(-a or -b)`, `a < b` in `L`. A faithful AMO is
  immediate: a clause is falsified exactly by two true literals. No aux
  variables.
* **seqcounter** (sequential counter, bound 1, delegated to
  `pysat.card.CardEnc.atmost(..., encoding=EncType.seqcounter)`): auxiliary
  `s_1..s_{k-1}` with clauses `(-l_1 or s_1)`, `(-l_i or s_i)`,
  `(-s_{i-1} or s_i)`, `(-l_i or -s_{i-1})` for `i >= 2`, and
  `(-l_k or -s_{k-1})`. Soundness sketch: if `l_i` and `l_j` (`i < j`) were both
  true, `s_i` is true, monotonicity propagates `s_{j-1}`, and
  `(-l_j or -s_{j-1})` is falsified. Completeness sketch: with at most one true
  literal, set `s_i` to "some `l_1..l_i` is true"; every clause holds. Aux
  variables are free otherwise, so the encoding adds no constraint on `L` and
  every labeling extends to a model.

**Lemma A.8 (faithful AMO preserves the feasible set).** If `amo` is faithful and
both encodings emit the same ALO clauses, then the pairwise and seqcounter
variants of the same ABP encoding have the same projection on the label
variables: same satisfiability, same set of decoded labelings, different clause
and variable counts. Aux variables are eliminated existentially, which is sound
because they never appear in the distance or ALO groups.

Empirical anchors: exhaustive check of the `amo()` contract over all 64 subsets
of 6 literals (ticket 08 closure, `tests/sat/test_matrix.py`), and the 8-config
matrix `abp_encoding x amo_encoding x {cadical195, glucose4}` against the
brute-force oracle on `n <= 9` (`tests/sat/test_matrix.py`).

## A.4 Equivalence theorem

**Theorem A.9 (SAT at `K` iff a labeling with `B(f) >= K` exists).** For
`1 <= K < n`, `CNF_pairwise(K)` is satisfiable iff there is a bijection
`f: V -> {1..n}` with `B(f) >= K`; the same holds for `CNF_order(K)`. For
`K >= n` both are UNSAT (Corollary A.3.1).

*Proof.* (=>) A model yields `f` by A.1 + A.2 (pairwise) or A.4 + A.6 (order),
and A.3 or A.7 gives `B(f) >= K`. (<=) Given such `f`, set `x[v][f(v)] = 1` and
all other `x` to 0 (pairwise), or set `o[v][p] = 1` iff `f(v) <= p` (order).
A.1/A.2/A.5/A.6 clauses hold; distance clauses are not falsified by A.3/A.7; a
faithful AMO encoding extends the assignment to the aux variables by A.8.

**Theorem A.10 (decoding yields a valid labeling).** `decode_model`
(`pairwise.py:152-173`, `order.py:100-123`) reconstructs `f` from a model and
raises `ValueError` unless every vertex has exactly one label and the label set
is `1..n`. Therefore a decoded object is always a valid bijection, or the run is
an encoding error — never a silently malformed solution.

**Theorem A.11 (reported objective is recomputed, not assumed).**
`solve_sat` passes every decoded labeling through `verify()` before reporting it
(`solve.py:188`, `src/common/verify.py:9-53`), which independently checks the
vertex domain, that labels are exactly `1..n`, and recomputes
`B = min |f(u) - f(v)|` over the stored edge list. If `B` is smaller than the
threshold just solved, `solve_sat` reports an encoding contradiction instead of
the solver's answer (`solve.py:189-193`). Hence the objective in `Result.lb` is
a property of the labeling, not of the solver's claim.

## A.5 Multi-run K search: completeness

Let `B* = B*(G)`. `solve_sat` (`solve.py:155-220`) keeps `lo` = the largest
verified value (0 when none) and `hi` = a threshold already proven UNSAT
(initially `n` by Corollary A.3.1, `solve.py:155-157`), and while `lo + 1 < hi`
probes `k = lo + 1`. On SAT it decodes, verifies and sets `lo = B(f)`; on UNSAT
it sets `hi = k`; on timeout it stops (`solve.py:187-204`).

**Invariants.** (I1) `lo <= B*`: `lo` is the value of a real labeling, and `B*`
is the maximum. (I2) `hi > B*`: `hi` is UNSAT, so no labeling reaches it.
Both hold initially (`lo = 0`, `hi = n`).

**Progress.** If `lo < B*`, then `k = lo + 1 <= B*`; a labeling attaining `B*`
satisfies threshold `k`, so `CNF(k)` is satisfiable and the solver can return
SAT or UNKNOWN, never UNSAT (assuming solver answers are correct). On SAT with
value `v >= k = lo + 1`, `lo` strictly increases and (I1) is preserved because
`v` is verified.

**Optimality.** If the probe at `k = lo + 1` returns UNSAT, then `k > B*` by
(I2)'s contrapositive (`k <= B*` would be satisfiable). With `k = lo + 1` and
(I1), `B* < k = lo + 1` and `lo <= B*`, hence `lo = B*` and `hi = lo + 1`. This
is the only branch that reports OPT (`solve.py:199-201`, `summarise_result`,
`solve.py:375-376`), so OPT implies `lb = B*` and the omitted witness is exactly
the optimal labeling.

**No threshold is skipped.** After SAT at `k` with value `v`, the next threshold
is `v + 1`, not `k + 1` (`solve.py:198`). Every `t` with `k < t <= v` is
satisfiable by the same labeling, so skipping them cannot hide a satisfiable
frontier; the first UNSAT threshold — the thing the loop is looking for — is
unchanged. Jumping to `v + 1` therefore removes only thresholds already known
to be SAT.

**Termination.** Each iteration either strictly increases `lo` (bounded above by
`B* <= n - 1`) or strictly decreases `hi` (new `hi = lo + 1 < hi`), and the
interval `hi - lo` shrinks by at least one per iteration, so the loop runs at
most `n - 1` probes. A run that never times out ends with `lo + 1 == hi`, i.e.
OPT. A run that times out before any verified labeling reports TO with no
bounds; a run that times out after one reports FEAS with `lb = lo` (verified
lower bound) and `ub = hi - 1`, so `B*` lies in `[lb, ub]`
(`summarise_result`, `solve.py:356-380`).

**Trust boundary.** OPT's upper side relies on the solver's UNSAT answers being
correct; the lower side is checked by `verify()` (A.11). The design does not
attempt to certify UNSAT proofs, and a solver bug on UNSAT would show up as an
OPT claim that is too high, not as an invalid labeling.

## A.6 What this appendix does not claim

1. No claim that the solver's UNSAT answers are correct (A.5, trust boundary).
2. No claim about relative CNF size of `pairwise` vs `order` as a theorem; it is
   measured (RQ1 pilot, `results/pilot_rq1.csv`) and is instance-dependent
   (`order` has no AMO group, but wider permutation/distance clauses).
3. No memory guarantee: `Result.peak_memory` is the maximum of sampled working
   sets, not peak RSS and not an enforced cap (`solve.py:131-135`, 164, 182,
   341-350; `docs/sat_tooling.md`). `Config.memory_limit` is not implemented
   (`solve.py:39-45`), so status MO can only come from an out-of-process
   `MemoryError` mapping (`src/runner/worker.py:34-35`).
4. No timeout guarantee: the deadline is checked between phases and inside the
   solver, so `t_total` may exceed `Config.time_limit` slightly
   (`solve.py:125-129`; conflict-budget loop in `src/sat/backend.py:238-254`).
5. No claims from symmetry breaking, warm start or search modes: they are not
   implemented and are rejected with a warning (`solve.py:39-67`); all pilot and
   benchmark runs use the plain multi-run loop above.

## A.7 Empirical anchors

* Brute-force oracle agreement on `n <= 9` for every encoding/AMO/backend
  combination: `tests/sat/test_matrix.py`, `tests/sat/test_g1_oracle.py`.
* Solver-independent OPT on toy graphs, including Glucose:
  `tests/sat/test_glucose_e2e.py`, `tests/sat/test_solve.py`.
* Per-K SAT/UNSAT agreement with the oracle and clause-count checks:
  `tests/sat/test_pairwise.py`, `tests/sat/test_order.py`.
* AMO contract (exhaustive on 6 literals): `tests/sat/test_pairwise.py`,
  `tests/sat/test_matrix.py`.
* W3 pilots (RQ1/RQ2) record sizes, times and status coverage; they are
  measurements, not part of the proof.
