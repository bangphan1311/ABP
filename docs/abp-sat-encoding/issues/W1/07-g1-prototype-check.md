# 07: G1 – Prototype khớp oracle

**Tuần:** W1 (cuối tuần) · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Một encoding chạy end-to-end trên graph nhỏ, khớp oracle của P1.

**Blocked by:** 02, 04, 06 · Ext: oracle của P1 (CP-SAT + brute-force) có sẵn

- [ ] Pipeline: instance → encoding → CaDiCaL → model → decode → verify() chạy được.
- [ ] Kết quả khớp oracle trên test set nhỏ.
- [ ] `SatBackend` được P1/P3 dùng mà không cần đọc bên trong.
- [ ] Loader tối thiểu chạy; `sat_tooling.md` có kết luận.
- [ ] Demo G1 cho nhóm: chạy được, lưu result theo schema.
