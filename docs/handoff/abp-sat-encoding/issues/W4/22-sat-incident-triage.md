# 22: Trực lỗi SAT khi official run

**Tuần:** W4 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Tái hiện trên máy dev các run bất thường P3 báo; phân loại.

**Blocked by:** 21

- [x] Với run bất thường: raw result → decode → verify → so objective. Không chỉ nhìn exit code (`src/sat/triage.py`).
- [x] Tái hiện crash, output hỏng, decode lỗi, memory lạ, timeout lạ trên máy dev (không tạo kết quả official) (`reproduce_on_dev`).
- [x] Phân loại: bug code / lỗi môi trường / hành vi solver thật (`CODE_BUG`, `ENV_ERROR`, `SOLVER_BEHAVIOR`).
- [x] Bug correctness: sửa ngay, chạy lại run bị ảnh hưởng (0 `CODE_BUG` trên toàn bộ 70 run hiện có).
