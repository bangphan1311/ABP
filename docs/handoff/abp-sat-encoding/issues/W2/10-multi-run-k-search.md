# 10: Multi-run K search

**Tuần:** W2 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Vòng K-search theo `sat_spec.md`: SAT → decode, verify, cập nhật incumbent, K ← B+1; UNSAT → B tối ưu.

**Blocked by:** 04, 08, 09

- [ ] SAT: decode, verify, cập nhật incumbent, K ← B+1.
- [ ] UNSAT: kết luận OPT với B.
- [ ] Time limit 1800 s là ngân sách cả chuỗi K. Hết giờ: có incumbent verify → FEAS; chưa có → TO.
- [ ] Ghi đủ metrics: variables, clauses, t_encode, t_solve, t_total, peak_memory, status, lb, ub.
- [ ] Trả Result theo contract P1 (không field `encoding` chung).
- [ ] Test: K-search trên toy cho ra optimum đúng.
