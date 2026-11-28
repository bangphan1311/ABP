# 04: Pairwise encoding (`src/sat/pairwise.py`)

**Tuần:** W1 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Encode ABP theo pairwise: nhận Instance và K, build CNF, solve, decode, verify(), trả Result theo contract P1.

**Blocked by:** 01, 03

- [x] Tách nhóm ràng buộc: assignment, uniqueness/permutation, ABP distance, threshold. (evidence: `src/sat/pairwise.py`)
- [x] Trả Result theo contract P1 (status, lb/ub, t_encode, t_solve, variables, clauses, peak_memory). (evidence: `src/common/models.py`)
- [x] Decode model → labeling; verify() pass. (evidence: `tests/sat/test_pairwise.py`)
- [x] Test toy: số biến, số clause, assignment hợp lệ, SAT/UNSAT đúng. (evidence: `tests/sat/test_pairwise.py`)
- [x] Mô tả semantic khớp `sat_spec.md`. (evidence: `docs/sat_spec.md`)
