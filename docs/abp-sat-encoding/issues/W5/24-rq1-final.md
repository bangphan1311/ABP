# 24: RQ1 final

**Tuần:** W5 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Kết luận RQ1 từ dữ liệu official đã freeze.

**Blocked by:** 23 · Ext: P3 data-final

- [x] Trả lời: encoding/AMO nào biểu diễn tốt hơn; có giúp solving không.
- [x] Kết quả mâu thuẫn được ghi nguyên, không ép "CNF nhỏ → nhanh".
- [x] Case study từ dữ liệu thật: encoding nhỏ nhưng chậm; lớn nhưng nhanh; pairwise MO.

## Evidence

- Kết luận + bảng RQ1: `docs/w5-sat/24-rq1-final.md` §1–§2 (sinh bởi `python -m experiments.w5_final_analysis`).
- Cặp đảo chiều cả hai hướng: `docs/w5-sat/24-rq1-final.md` §3.1–§3.2, số lấy từ `results/pilot_rq1.csv`.
- Pairwise blowup + projection + MO semantics: `docs/w5-sat/24-rq1-final.md` §3.3 (BR-7).
- Kiểm tra `order/seqcounter` ≡ `order/pairwise`: `docs/w5-sat/24-rq1-final.md` §4.
