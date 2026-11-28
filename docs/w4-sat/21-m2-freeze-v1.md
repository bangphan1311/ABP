# 21: M2 – Freeze v1.0 SAT (Evidence & Checklist)

**Tuần:** W4 · **Owner:** P2 (Quang) · **Issues:** #28 (`21`), #29 (`22`), #30 (`23`)

## 1. Canonical SAT Configuration đã khóa trong code (`src/sat/solve.py`)

Hằng số `CANONICAL_SAT_CONFIG` và hàm `canonical_sat_config()` đã được định nghĩa tại `src/sat/solve.py` và xuất qua `src/sat/__init__.py`:

```python
CANONICAL_SAT_CONFIG = Config(
    method="sat",
    abp_encoding="order",
    amo_encoding="pairwise",
    sat_solver="glucose4",
    search_mode="multi",
    symmetry=False,
    warm_start=False,
    seed=0,
    time_limit=1800.0,
    memory_limit=None,
)
```

- Đã cập nhật `_warn_ignored_config` trong `src/sat/solve.py`: không phát cảnh báo giả khi `search_mode="multi"` (vì `multi` là chế độ duy nhất đã cài đặt của vòng dò K).
- `canonical_sat_config()` từ nay **bắt buộc** `memory_limit` tường minh (số hữu hạn > 0) cho run official: `memory_limit=None` raise `ValueError` trừ khi caller truyền escape hatch `allow_unbounded_memory=True` (chỉ dùng cho dev/unit test). Hằng số `CANONICAL_SAT_CONFIG.memory_limit` vẫn là `None`; số cap cuối cùng (candidate `12.0` GiB = `12288.0` MB) do P1/P3 chốt — xem `docs/canonical_sat_config.md`.
- Lý do chọn và bảng số liệu chi tiết (OPT coverage, PAR2, median `peak_memory`, median `clauses`) được lưu tại `docs/canonical_sat_config.md`.

## 2. Correctness Suite & Test Matrix

- Toàn bộ suite kiểm thử tự động (`python -m pytest -q`) gồm:
  - Unit tests cho `pairwise` encoding, `order` encoding, AMO (`pairwise`, `seqcounter`, và các biến thể `pysat.card`), `SatBackend` (`cadical195`, `glucose4`, `glucose42`, `minisat22`, chặn vĩnh viễn `kissat404`).
  - Test đối chiếu với `solve_oracle` trên đồ thị toy, đồ thị không liên thông có đỉnh cô lập, và đồ thị ngẫu nhiên (`n <= 9`).
  - Test công cụ trực lỗi SAT (`tests/sat/test_triage.py`) và bộ sinh phân tích RQ1/RQ2 + G3 (`tests/experiments/test_analyze_rq1_rq2.py`).
- Tất cả các test đều xanh (**568 passed, 3 skipped**; 3 skip là test CPLEX CP engine vì `cpoptimizer.exe`/license không có trên máy, không phải fail).

## 3. Công cụ trực lỗi SAT (`src/sat/triage.py`, Issue #29 / ticket 22)

- Kiểm tra từng file raw JSON theo chuỗi: đọc raw record → giải mã `solution` → gọi `verify(instance, solution)` → đối chiếu `lb`, `ub` và chuỗi `metadata.probes`.
- Phân loại tự động vào 4 nhãn: `OK`, `SOLVER_BEHAVIOR` (`FEAS`/`TO` hợp lệ), `ENV_ERROR` (`MO`, worker bị kill cứng, lỗi đọc file/JSON), `CODE_BUG` (sai lệch `verify()`, `lb != verified`, `lb > ub`, thiếu nghiệm ở `OPT`, mâu thuẫn `probes`).
- Hỗ trợ tái hiện trên máy dev (`reproduce_on_dev` / `--reproduce`) chạy trực tiếp trong bộ nhớ mà không ghi đè vào `results/raw/`.

## 4. Nháp phân tích RQ1/RQ2 + Cổng G3 (`experiments/analyze_rq1_rq2.py`, Issue #30 / ticket 23)

- Tự động đọc từ `results/runs.csv` (hoặc `results/pilot_rq1.csv` + `results/pilot_rq2.csv` + `results/raw/*.json`) và sinh báo cáo `docs/w4-sat/23-rq1-rq2-draft-analysis.md`.
- RQ1/RQ2 chỉ tính trên lát cắt một trục: RQ1 cố định `solver` (`--rq1-solver`, mặc định `cadical195`); RQ2 cố định cặp `abp_encoding`/`amo_encoding` (`--rq2-abp-encoding`/`--rq2-amo-encoding`, mặc định `order`/`pairwise`); cả hai cố định `search_mode ∈ {"", "multi"}`, `symmetry = false`, `warm_start = false`.
- Cổng G3 chỉ `PASS`/`FAIL` khi có `--expected-runs` từ kế hoạch đã khóa; bỏ trống flag thì cổng báo `PENDING` (không fallback về số run quan sát được).
- Chỉ rõ bằng chứng thực nghiệm **CNF nhỏ hơn (ít mệnh đề hơn) không đồng nghĩa solver nhanh hơn**, bảng so sánh solver theo instance, và kiểm tra cổng G3 (≥ 80% run hoàn thành, 100% run bất thường đã phân loại, 0 `CODE_BUG`).

## 5. Chính sách Freeze `v1.0`

- Từ mốc M2 này, nhánh SAT không tự ý thay đổi encoding, AMO hay chiến lược tìm kiếm K. Mọi thay đổi chỉ giới hạn ở sửa lỗi crash/bug correctness nếu phát sinh trong đợt chạy chính thức; nếu buộc phải đổi cấu hình hoặc encoding thì phải ghi quyết định nhóm và tăng version mới.
- **Điều kiện tag `v1.0` (Experimental Protocol §12):** chỉ tag khi **tất cả** freeze gate cùng đạt — dataset (subset đã khóa), host (môi trường chạy thống nhất), solver (backend + phiên bản), resource enforcement (memory cap do runner áp, Protocol §6.3), cross-review (P1/P3 đã review) và evidence (mọi link bằng chứng trong checklist resolve tại commit đóng). Thiếu một gate → chưa tag.
- Tham chiếu chéo: `docs/sat_spec.md` (contract), `docs/w2-sat/14-sat-methodology.md` (methodology §3), `docs/technical_appendix_draft.md` (chứng minh completeness), `docs/canonical_sat_config.md` (config + số liệu pilot), `docs/w4-sat/23-rq1-rq2-draft-analysis.md` (bảng RQ1/RQ2 + G3 sinh tự động).
