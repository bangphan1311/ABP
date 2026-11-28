# 25: RQ2 final

**Tuần:** W5 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Xếp hạng solver CaDiCaL / Glucose / Kissat từ dữ liệu official.

**Blocked by:** 23 · Ext: P3 data-final

- [x] Xếp hạng theo OPT coverage, timeout, memory, độ nhạy theo instance.
- [x] Chỉ dùng dữ liệu trong protocol làm bằng chứng chính.
- [x] Case study: solver A thắng graph thưa, B thắng graph dày; SAT chỉ FEAS không OPT.

## Evidence

- Bảng xếp hạng + kết luận Core: `docs/w5-sat/25-rq2-final.md` §1–§2, nguồn `results/pilot_rq2.csv`.
- Độ nhạy theo instance (n/m/density/Δ/UB + `t_total`/cv): `docs/w5-sat/25-rq2-final.md` §4; câu trả lời thưa/dày là scope limitation có số liệu.
- FEAS-not-OPT + chuỗi probe `randconn40`: `docs/w5-sat/25-rq2-final.md` §5, dựng từ `results/raw/*.json`.
- Kissat exclusion: `docs/w5-sat/25-rq2-final.md` §6 (BR-6).
