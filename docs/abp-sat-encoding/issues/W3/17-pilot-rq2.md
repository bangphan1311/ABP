# 17: Pilot RQ2 (solver)

**Tuần:** W3 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Pilot so sánh CaDiCaL, Glucose, Kissat với cùng canonical encoding và AMO.

**Blocked by:** 12 · Ext: P3 khóa validation subset

- [x] Cố định encoding + AMO; chỉ đổi solver.
- [x] Đo OPT coverage, FEAS, TO, MO, ERR, runtime, memory theo từng instance.
- [x] Ghi lại run lỗi/bất thường để phân loại.
- [x] Không dùng RQ3 subset.

## Closure evidence (2026-11-09)

- Box 1–2: `results/pilot_rq2.csv` — 40 run = 4 solver
  (`minisat22`, `glucose4`, `glucose42`, `cadical195`) × 10 instance trên cặp
  `order/pairwise` cố định; mỗi hàng có `status`, `t_total`, `peak_memory`.
  Bảng coverage/PAR2 ở `docs/canonical_sat_config.md` mục "RQ2 — solver".
- Box 3: 40/40 run `OPT`, không có run bất thường nào để phân loại; công cụ trực
  lỗi `src/sat/triage.py` chạy trên `results/raw/*.json` (ticket 22).
- Kissat bị loại theo thiết kế (`docs/sat_tooling.md` mục Kissat), lý do ghi trong
  `docs/canonical_sat_config.md` mục "Kissat".
- Box 4: chỉ dùng `benchmark/validation` + `benchmark/large`, không chạm RQ3 subset.
