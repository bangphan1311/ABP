# 16: Pilot RQ1 (encoding × AMO)

**Tuần:** W3 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Chạy pilot RQ1 trên validation subset (8–10 instance) và vài instance lớn.

**Blocked by:** 11, 12 · Ext: P3 khóa validation subset

- [x] Biến: pairwise vs order; pairwise vs seqcounter.
- [x] Cố định: một solver, multi-run, symmetry OFF, warm start OFF.
- [x] Đo: #variables, #clauses, t_encode, t_solve, t_total, peak memory, status.
- [x] Lộ sớm: CNF quá lớn, MO, encode chậm. Ghi kết quả vào `results/` qua runner của P3.
- [x] Không dùng RQ3 subset.

## Closure evidence (2026-11-09)

- Box 1–3: `results/pilot_rq1.csv` — 40 run = 4 cặp `(abp_encoding, amo_encoding)`
  (`order/pairwise`, `order/seqcounter`, `pairwise/pairwise`, `pairwise/seqcounter`)
  × 10 instance, mỗi hàng có `variables`, `clauses`, `t_encode`, `t_solve`,
  `t_total`, `peak_memory`, `status`.
- Box 2: `run_id` mang token `__cadical195__multi__sym0__ws0__`, khớp cấu hình cố
  định ở `docs/canonical_sat_config.md` mục "Fixed axes".
- Box 4: ngưỡng cảnh báo sớm (`variables > 200 000`, `t_encode > 5 s`) không kích
  hoạt trên tập này; bảng số liệu và kết luận ở `docs/canonical_sat_config.md`
  mục "RQ1 — encoding × AMO".
- Box 5: chỉ dùng `benchmark/validation` + `benchmark/large` (sinh bởi
  `experiments/make_validation_subset.py`), không chạm RQ3 subset.
