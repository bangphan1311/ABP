# 12: Test matrix correctness (encoding × AMO × backend)

**Tuần:** W2 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Bộ test kiểm mọi cấu hình Core khớp oracle. Cấu hình fail → chưa Core-ready.

**Blocked by:** 05, 08, 09, 10, 11 · Ext: oracle brute-force của P1

- [ ] Ma trận: pairwise/order × pairwise/seqcounter × CaDiCaL/Glucose/Kissat.
- [ ] Mọi cấu hình khớp oracle trên small instances.
- [ ] Model counting trên instance cực nhỏ bằng blocking clause: không thừa, không thiếu nghiệm.
- [ ] Random graph nhỏ: edge case (rời rạc, đỉnh cô lập, bậc lạ).
- [ ] Output: bảng pass/fail theo cấu hình.
