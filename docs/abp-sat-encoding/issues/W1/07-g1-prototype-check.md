# 07: G1 – Prototype khớp oracle

**Tuần:** W1 (cuối tuần) · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Một encoding chạy end-to-end trên graph nhỏ, khớp oracle của P1.

**Blocked by:** 02, 04, 06 · Ext: oracle của P1 (CP-SAT + brute-force) có sẵn

- [x] Pipeline: instance → encoding → CaDiCaL → model → decode → verify() chạy được. (evidence: `docs/sat-g1/run_g1.py`)
- [x] Kết quả khớp oracle trên test set nhỏ. (evidence: `tests/sat/test_g1_oracle.py`)
- [x] `SatBackend` được P1/P3 dùng mà không cần đọc bên trong. (evidence: `src/sat/backend.py`)
- [x] Loader tối thiểu chạy; `sat_tooling.md` có kết luận. (evidence: `docs/sat_tooling.md`)
- [x] Demo G1 cho nhóm: chạy được, lưu result theo schema. (evidence: `docs/sat-g1/results.json`)
