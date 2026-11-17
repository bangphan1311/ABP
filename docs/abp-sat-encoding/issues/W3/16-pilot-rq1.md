# 16: Pilot RQ1 (encoding × AMO)

**Tuần:** W3 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Chạy pilot RQ1 trên validation subset (8–10 instance) và vài instance lớn.

**Blocked by:** 11, 12 · Ext: P3 khóa validation subset

- [ ] Biến: pairwise vs order; pairwise vs seqcounter.
- [ ] Cố định: một solver, multi-run, symmetry OFF, warm start OFF.
- [ ] Đo: #variables, #clauses, t_encode, t_solve, t_total, peak memory, status.
- [ ] Lộ sớm: CNF quá lớn, MO, encode chậm. Ghi kết quả vào `results/` qua runner của P3.
- [ ] Không dùng RQ3 subset.
