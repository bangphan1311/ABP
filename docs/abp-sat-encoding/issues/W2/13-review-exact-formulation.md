# 13: Review formulation exact của P1

**Tuần:** W2 · **Owner:** P2 (Quang) review, P1 viết · **Status:** ready-for-human

**What to build:** Review MIP/CP model của P1 về đúng đắn và độ công bằng so với SAT.

**Blocked by:** 12 · Ext: P1 hoàn thành formulation Gurobi/CPLEX MIP/CP

- [x] MIP: biến nhị phân theo cạnh cho |f(u) − f(v)| ≥ K; không dùng big-M yếu.
- [x] CP model cùng semantic với SAT và MIP.
- [x] Ghi kết luận review (đồng ý / yêu cầu sửa) vào ticket của P1.

## Closure evidence (2026-11-03)

- Box 1: kết luận review P1 "đồng ý" — indicator constraints không phải big-M
  yếu; `docs/handoff/w2-sat/13-review-p1-formulation.md`.
- Box 2: CP semantics khớp SAT/MIP, ghi chú non-blocking — cùng file.
- Box 3: đã ghi kết luận vào ticket P1; xác nhận 2026-11-03 qua GH #20
  (comment kết luận), GH #42, PR #48 (`p1/w2-review-closeout`),
  `docs/handoff/w2-sat/13-review-p1-formulation.md`,
  `docs/handoff/w2-exact/16-w2-acceptance.md`.
