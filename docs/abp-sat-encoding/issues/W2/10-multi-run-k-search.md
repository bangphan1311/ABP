# 10: Multi-run K search

**Tuần:** W2 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Vòng K-search theo `sat_spec.md`: SAT → decode, verify, cập nhật incumbent, K ← B+1; UNSAT → B tối ưu.

**Blocked by:** 04, 08, 09

- [x] SAT: decode, verify, cập nhật incumbent, K ← B+1.
- [x] UNSAT: kết luận OPT với B.
- [x] Time limit 1800 s là ngân sách cả chuỗi K. Hết giờ: có incumbent verify → FEAS; chưa có → TO.
- [x] Ghi đủ metrics: variables, clauses, t_encode, t_solve, t_total, peak_memory, status, lb, ub.
- [x] Trả Result theo contract P1 (không field `encoding` chung).
- [x] Test: K-search trên toy cho ra optimum đúng.

## Closure evidence (2026-11-03)

- Box 1–2: `docs/handoff/w2-sat/14-sat-methodology.md` §3.5 — K ← B+1, UNSAT
  ⇒ OPT; `docs/sat_spec.md` §5.
- Box 3: `Config.time_limit` là ngân sách cả chuỗi K; hết giờ có incumbent
  verify → FEAS, chưa có → TO (`14-sat-methodology.md` §3.5).
- Box 4: metrics `variables, clauses, t_encode, t_solve, t_total, peak_memory`
  đo trong `12-test-matrix.md`; §3.7 của `14-sat-methodology.md`.
- Box 5: `src/common/models.py` — `Config` tách `abp_encoding`/`amo_encoding`;
  `Result` không có field `encoding` chung (CONTRACT §4).
- Box 6: test OPT-oracle toy trong `tests/sat/test_matrix.py` và bảng
  `12-test-matrix.md`.
