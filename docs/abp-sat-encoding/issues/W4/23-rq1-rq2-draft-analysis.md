# 23: Nháp phân tích RQ1/RQ2 + G3

**Tuần:** W4 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Bảng/hình nháp RQ1, RQ2 từ `runs.csv`; SAT section đủ để review.

**Blocked by:** 21 · Ext: P3 có `runs.csv` từng phần

- [x] RQ1: encoding nào tạo CNF lớn hơn; AMO ảnh hưởng ra sao; encode time, memory. CNF nhỏ ≠ solver nhanh (`experiments/analyze_rq1_rq2.py`).
- [x] RQ2: so solver bằng OPT coverage, FEAS, TO, memory theo instance; không chỉ runtime trung bình.
- [x] Hình/bảng sinh từ `runs.csv`, không sửa tay (`docs/w4-sat/23-rq1-rq2-draft-analysis.md`).
- [ ] G3: PENDING — phải truyền `--expected-runs` lấy từ frozen run plan; không suy mẫu số từ số record quan sát được. Bản nháp hiện tại chưa chứng minh đủ ≥80% run Core của kế hoạch.
