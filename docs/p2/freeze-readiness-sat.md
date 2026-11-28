# P2 — Trạng thái điều kiện freeze `v1.0` (SAT)

**Ngày:** 2026-11-28 · **Owner:** P2 (Quang) · **Kết luận: CHƯA ĐỦ ĐIỀU KIỆN — giữ `1.0-rc`, không tag `v1.0`.**

Đối chiếu `docs/experimental_protocol.md` §12 (7 điều kiện) và §13 (việc còn xong trước freeze).

## 1. Bảng điều kiện §12

| # | Điều kiện §12 | Trạng thái | Bằng chứng / thiếu gì |
|---|---|---|---|
| 1 | Đủ 24 file dữ liệu, `MANIFEST.csv`, loader test 24/24 | **Một phần** | `benchmark/hb/instances.csv` 24 dòng, `benchmark/hb/MANIFEST.csv` 24 dòng; `tests/sat/test_hb_loader.py` + `tests/benchmark` → 19 passed. 24 file `.mtx.rnd` có trên máy chạy (`ABP-rq3/benchmark/hb/raw`, 24 file) nhưng **không nằm trong Git tree** → chưa ai kiểm SHA-256 đối chiếu manifest ở chỗ lưu chính thức |
| 2 | Correctness suite + oracle/cross-solver đạt | **Đạt** | `pytest -q` → 643 passed; `src.sat.triage` → `CODE_BUG=0` trên 70 run pilot |
| 3 | Canonical config chọn từ pilot, có raw + report, P1/P2/P3 review | **Một phần** | `docs/canonical_sat_config.md` + `CANONICAL_SAT_CONFIG`; P1 chấp nhận tạm. **Mở:** pilot RQ1/RQ2 ghi `time_limit=60.0` trong khi Protocol §6.2 ghi 1800 s — nhóm phải chọn giữ pilot lịch sử (sửa budget trong protocol) hoặc chạy lại pilot 1800 s |
| 4 | Runner enforce memory limit cấp process/OS + kill/resume + `MO` có evidence | **Chưa đạt** | `src/runner/memory_limit.py` + `tests/runner/test_checkpoint.py`, `test_sat_checkpoint.py` có; nhưng 12/24 run SAT official trả `MO` với `peak_memory=null`, `lb/ub=null`, `metadata={}` → không chứng minh được ngưỡng 12 GiB bị chạm (xem issue dữ liệu RQ3) |
| 5 | `t_total` tính cả build/encode; thời gian còn lại truyền cho từng probe/optimizer | **Đạt (SAT)** | `Config.time_limit` là ngân sách cả chuỗi K; `docs/sat_spec.md` §5 + `docs/exact_models.md` §Time accounting; `tests/exact/test_time_budget.py` |
| 6 | Tập con, RQ, time/memory limit, máy, version solver đã khóa; license ghi rõ | **Một phần** | `docs/w3_preflight.md` + `docs/ENV.md`; license CPLEX/Gurobi ghi `ERR`. **Mở:** P3 phải xác nhận host official (`DESKTOP-K0QBAQP`) và cap thực thi |
| 7 | SAT spec/methodology được P1/P2 review chéo; góp ý protocol đã xử lý | **Chưa đạt** | P1 review `docs/p1/sat-cross-review-2026-11-17.md` có 6 mục mở; P2 chưa trả lời từng mục bằng commit/evidence |

## 2. Việc P2 phải làm để đóng phần mình

1. Trả lời 6 mục mở trong `docs/p1/sat-cross-review-2026-11-17.md`, mỗi mục kèm commit/test (mục 1 cần quyết định nhóm về budget 60 s vs 1800 s).
2. Xác nhận lập luận UB = `n − Δ` trên 24 instance và đối chiếu `docs/w2-sat/14-sat-methodology.md` (§13 dòng "Kiểm tra cận").
3. Xác nhận AMO `pairwise` không sinh clause trùng và `order` AMO là no-op (§13 dòng "Kiểm tra AMO").
4. Chốt cách ghi `MO` cho RQ3: cần `peak_memory` trước khi raise, và `search_mode` phải là `multi` (2 issue dữ liệu đã mở với P3).

## 3. Việc của P1/P3 (không phải P2)

- P3: ký host official + test kill/MO có raw evidence; sửa exporter (`peak_memory`, `search_mode`).
- P1: quyết định budget pilot, review cuối protocol, tag `v1.0` khi đủ.

## 4. Ghi chú

- Không có tag `v1.0` nào được tạo. `git tag --list` chỉ có `v0.1-contract`.
- Official RQ3 đã chạy 120 run (24 instance × 5 method) nhưng `runs.csv` đó không nằm trong Git tree của repo chính; phân tích RQ3 thuộc P1.
