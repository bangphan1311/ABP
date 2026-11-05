# 11: Loader + generator hoàn chỉnh (Tier 0/1)

**Tuần:** W2 · **Owner:** P2 (Quang) cùng P3 · **Status:** ready-for-human

**What to build:** Generator sinh đủ họ graph Tier 0/1; loader đọc đúng định dạng đã chốt.

**Blocked by:** 06 · Ext: P3 chốt định dạng instance

- [x] Sinh đủ họ Tier 0 (rất nhỏ) và Tier 1 (path, cycle, grid, complete, vài họ khác).
- [x] Loader đọc mọi file generator xuất ra.
- [x] Random graph nhỏ có seed; bắt đỉnh cô lập, graph rời rạc.
- [x] Định dạng khớp contract với P3.

## Closure evidence (2026-11-03)

- Box 1: `src/sat/generator.py` sinh path, cycle, grid, complete, star,
  binary_tree, disconnected, isolated, `random_graph` có seed; tier0 n ≤ 8,
  tier1 9–16 (docstring module).
- Box 2: `src/sat/loader.py` `read_instance`/`write_instance` nhận mọi payload
  generator — cùng shape `Instance`, `REQUIRED_KEYS`.
- Box 3: `random8-seed42`, `disconnected`, `isolated` có trong
  `MATRIX_INSTANCES` của `12-test-matrix.md`.
- Box 4: `Instance` khớp CONTRACT §2 đúng các field id, name, n, edges, source,
  tier.
