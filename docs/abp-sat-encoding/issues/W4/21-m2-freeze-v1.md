# 21: M2 – Freeze v1.0 SAT

**Tuần:** W4 (giữa tuần) · **Owner:** P2 (Quang) cùng nhóm · **Status:** ready-for-human

**What to build:** Khóa SAT code và canonical config; tag `v1.0`.

**Blocked by:** 18, 19

- [x] Canonical config đã ghi trong repo (`CANONICAL_SAT_CONFIG` trong `src/sat/solve.py` và `docs/canonical_sat_config.md`).
- [x] Correctness suite đã xanh ở lần ghi nhận trước (`513 passed, 3 skipped`); **chưa phải evidence cho revision hiện tại**. Phải chạy lại full suite sau review fixes và gắn log với commit SHA trước khi freeze.
- [ ] Tag `v1.0` cùng nhóm (chỉ sau khi mọi điều kiện Protocol §12 có evidence, bao gồm P3 official-host sign-off, dataset, memory cap, checkpoint/resume và review; merge PR không tự động đủ điều kiện).
- [x] Từ đây: chỉ sửa crash/bug/kết quả sai. Đổi encoding/config → version mới + ghi quyết định.
