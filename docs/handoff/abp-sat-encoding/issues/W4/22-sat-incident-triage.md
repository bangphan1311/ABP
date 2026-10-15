# 22: Trực lỗi SAT khi official run

**Tuần:** W4 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Tái hiện trên máy dev các run bất thường P3 báo; phân loại.

**Blocked by:** 21

- [ ] Với run bất thường: raw result → decode → verify → so objective. Không chỉ nhìn exit code.
- [ ] Tái hiện crash, output hỏng, decode lỗi, memory lạ, timeout lạ trên máy dev (không tạo kết quả official).
- [ ] Phân loại: bug code / lỗi môi trường / hành vi solver thật.
- [ ] Bug correctness: sửa ngay, chạy lại run bị ảnh hưởng.
