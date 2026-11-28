# 05: Order encoding (`src/sat/order.py`)

**Tuần:** W1 (stretch) → W2 nếu quá tải · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Encoding order giải cùng decision problem với pairwise. Thay pairwise ↔ order không viết lại solver.

**Blocked by:** 01, 03

- [x] Dùng cùng module phân nhóm ràng buộc với pairwise (ticket 04). (evidence: `src/sat/order.py`)
- [x] Cùng semantic: cùng input → cùng SAT/UNSAT với pairwise trên toy. (evidence: `tests/sat/test_order.py`)
- [x] Verify() pass trên toy. (evidence: `tests/sat/test_order.py`)
- [x] Nếu không kịp W1: ghi rõ trong G1 và chuyển sang W2, không bỏ. (evidence: `docs/w2-sat/14-sat-methodology.md`)
