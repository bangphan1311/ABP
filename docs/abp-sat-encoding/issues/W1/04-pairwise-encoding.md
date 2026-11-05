# 04: Pairwise encoding (`src/sat/pairwise.py`)

**Tuần:** W1 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Encode ABP theo pairwise: nhận Instance và K, build CNF, solve, decode, verify(), trả Result theo contract P1.

**Blocked by:** 01, 03

- [ ] Tách nhóm ràng buộc: assignment, uniqueness/permutation, ABP distance, threshold.
- [ ] Trả Result theo contract P1 (status, lb/ub, t_encode, t_solve, variables, clauses, peak_memory).
- [ ] Decode model → labeling; verify() pass.
- [ ] Test toy: số biến, số clause, assignment hợp lệ, SAT/UNSAT đúng.
- [ ] Mô tả semantic khớp `sat_spec.md`.
