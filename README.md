# ABP – Antibandwidth Problem: SAT vs Exact Solvers

BTL #2 – Các vấn đề hiện đại KHMT.

## Cấu trúc
- `src/common/` – Instance, Config, Result, verify (contract chung)
- `src/sat/` – SAT encoding và backend (P2)
- `src/exact/` – Gurobi, CPLEX MIP, CPLEX CP, CP-SAT (P1)
- `src/runner/` – Runner và validation (P3)
- `benchmark/`, `experiments/`, `results/`, `visualization/`, `paper/`, `docs/`, `tests/`

## Quy tắc git
`main` là branch ổn định. Mỗi người làm trên feature branch và merge qua PR (ít nhất 1 review).
