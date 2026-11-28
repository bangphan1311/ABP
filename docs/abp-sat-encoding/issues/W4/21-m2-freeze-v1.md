# 21: M2 – Freeze v1.0 SAT

**Tuần:** W4 (giữa tuần) · **Owner:** P2 (Quang) cùng nhóm · **Status:** NOT FROZEN — current-head evidence and operational gates pending

**What to build:** Khóa SAT code và canonical config; tag `v1.0`.

**Blocked by:** 18, 19

- [x] Canonical config đã ghi trong repo (`CANONICAL_SAT_CONFIG` trong `src/sat/solve.py` và `docs/canonical_sat_config.md`).
- [x] Full correctness suite PASS trên implementation/test SHA `a5d58821393448cc1f019e7860c6546a4bedd907`: GitHub Actions [run #44040260149](https://github.com/bangphan1311/ABP/actions/runs/44040260149) — Ubuntu `556 passed`, Windows `556 passed`; SAT/W4 focused suite `452 passed` trên mỗi OS. Branch tip sau đó chỉ có cập nhật tài liệu, không thay source/tests. Mọi thay đổi source/tests sau SHA này phải chạy lại suite trước freeze. Số liệu lịch sử `513 passed, 3 skipped` không phải acceptance evidence.
- [ ] Tag `v1.0` cùng nhóm (chỉ sau khi mọi điều kiện Protocol §12 có evidence, bao gồm P3 official-host sign-off, dataset, memory cap, checkpoint/resume và review; merge PR không tự động đủ điều kiện).
- [x] Từ đây: chỉ sửa crash/bug/kết quả sai. Đổi encoding/config → version mới + ghi quyết định.
