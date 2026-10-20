# 15 — M1 gate evidence: bằng chứng cho quyết định GO/NO-GO Bonus SAT

Ticket 15 (GH #22) · Ngày: 2026-10-20 · Branch `p2/w2-sat` · Owner: P2 (Quang).

Tính chất của doc: trình bày **bằng chứng + ước tính + hai phương án kèm lý
do** để nhóm/customer quyết ở gate M1. **Doc này không quyết GO/NO-GO và không
chốt phương án nào** (ticket 15 là quyết định của nhóm).

## 1. Trạng thái Core SAT (bằng chứng từ test matrix)

Nguồn: `docs/handoff/w2-sat/12-test-matrix.md`, lần chạy thật 2026-10-20,
branch `p2/w2-sat`.

- Lệnh chạy thật: `tests/sat/test_matrix.py` → **213 passed in 3.48s**; toàn
  suite `tests -q` → **422 passed in 15.58s**.
- **8/8 cấu hình Core xanh**: `abp_encoding ∈ {pairwise, order}` ×
  `amo_encoding ∈ {pairwise, seqcounter}` × `sat_solver ∈ {cadical195,
  glucose4}`. Mỗi cấu hình 26 test: 10 OPT khớp oracle brute-force + 10
  SAT/UNSAT tại mọi `K ∈ 1..n` + 6 model counting — mọi nghiệm SAT đều qua
  `verify()` trước khi so oracle.
- Cột kissat: **N/A vĩnh viễn W2** — bị chặn ở khởi tạo backend
  (`PYSAT_KISSAT_FAMILIES`) và pipeline (`_validate_solver`), lý do trong
  `docs/sat_tooling.md` mục Kissat.
- Model counting bằng blocking clause khớp đếm `itertools.permutations` trên 6
  cặp (instance, K), gồm 2 cặp UNSAT (0 nghiệm): không thừa, không thiếu
  nghiệm, ở cả 8 cấu hình.
- AMO closure (ticket 08): kiểm exhaustive 64 tập con × mọi assignment (729
  lần kiểm mỗi encoding) — `pairwise` và `seqcounter` đều PASS.
- Tier 1 (n ≤ 12, cấu hình mặc định): 3/3 PASS, OPT tự chứng minh bằng UNSAT
  tại `K = B + 1`, hai encoding cùng B.
- Ghi chú order: không có ràng buộc AMO, `amo_encoding` được chấp nhận + ghi
  nhận trong `CNF` nhưng không đổi clause, không đổi kết quả; matrix vẫn chạy
  đủ 2 giá trị AMO cho order để khẳng định đường config hoạt động.

Ánh xạ checklist ticket 12 ("Test matrix correctness") → bằng chứng:

| Mục ticket 12 | Bằng chứng |
|---|---|
| Ma trận pairwise/order × pairwise/seqcounter × CaDiCaL/Glucose/Kissat | 8/8 cấu hình PASS (bảng trong 12-test-matrix.md); kissat N/A có bằng chứng chặn trong `tests/sat/test_backend.py`, `tests/sat/test_solve.py` |
| Mọi cấu hình khớp oracle trên small instances | 10 instance × 8 cấu hình: OPT, `lb == ub ==` B oracle, nghiệm verify đúng B |
| Model counting bằng blocking clause: không thừa, không thiếu | 6 cặp, bằng đúng `itertools` ở 8/8 cấu hình, gồm cả UNSAT = 0 |
| Random graph nhỏ: edge case (rời rạc, đỉnh cô lập, bậc lạ) | `disconnected`, `isolated`, `random8-seed42` nằm trong `MATRIX_INSTANCES` |
| Output: bảng pass/fail theo cấu hình | Bảng ma trận trong `docs/handoff/w2-sat/12-test-matrix.md` |

Kết luận của mục này (mức bằng chứng, không phải quyết định gate): checklist
"Core SAT khớp oracle" — mục đầu của ticket 15 — có bằng chứng **ĐẠT**: 8/8
cấu hình xanh, model counting khớp, AMO closure PASS, toàn suite 422 xanh.

## 2. Phạm vi Bonus SAT (từ WORK BREAKDOWN)

Danh sách theo ticket 15: **staircase, incremental, symmetry, AMO phụ
(commander/product)**; phạm vi thực hiện nếu GO là W3 ticket 20: "Staircase
hoặc incremental ở mức prototype và test nhỏ". Thứ tự cắt khi chậm theo WORK
BREAKDOWN (`docs/handoff/abp-sat-encoding/README.md`): Staircase →
commander/product AMO → binary search theo K → Bonus; không cắt: pairwise,
order, correctness, RQ1/RQ2, tái lập.

Mỗi mục dưới đây: là gì / giá trị kỳ vọng / rủi ro / blocker. Mục "giá trị kỳ
vọng" phần lớn là **đánh giá định tính** — repo chưa có số đo nào cho Bonus.

### 2.1 Staircase encoding

- **Là gì**: encoding ABP thứ ba ngoài Core. Repo hiện chưa có đặc tả
  staircase: `docs/sat_spec.md` chỉ đặc tả pairwise/order;
  `ABP_ENCODINGS = ("pairwise", "order")` trong `src/sat/solve.py`.
- **Giá trị kỳ vọng (đánh giá)**: hướng encoding mới để giảm quy mô CNF hoặc
  tăng hiệu năng solve so với hai encoding Core — chưa có số đo trong repo;
  giá trị thực phải đo qua pilot RQ1 sau khi có prototype.
- **Rủi ro**: encoding mới phải lập lại dạng kiểm đúng của Core (OPT-oracle,
  SAT/UNSAT mọi K, model counting) trước khi số liệu của nó đáng tin; là mục
  **đầu tiên bị cắt** theo WORK BREAKDOWN khi chậm.
- **Blocker**: không blocker kỹ thuật; chặn bởi quyết định gate và khối lượng
  W3.

### 2.2 Incremental solving

- **Là gì**: giữ solver sống giữa các lần dò K (thêm clause sau khi solve rồi
  giải lại, hoặc dùng assumptions) thay vì dựng CNF + backend mới mỗi lần dò.
  Hiện trạng: "mỗi ngưỡng dựng CNF mới và dùng backend mới; không dùng
  incremental/assumption ở W1" (`docs/sat_spec.md` §5); `_probe` tạo
  `SatBackend` mới mỗi lần dò.
- **Bằng chứng tooling** (`docs/sat_tooling.md`): họ cadical (103/153/195/300)
  và glucose3/4/42 hỗ trợ thêm mệnh đề sau solve + assumptions (kiểm trên
  instance nhỏ); **kissat không incremental** (nạp clause sau solve làm
  process abort) — kissat đã bị loại vĩnh viễn nên Bonus này không mở cửa cho
  kissat.
- **Giá trị kỳ vọng (đánh giá)**: tránh lặp chi phí encode + nạp clause mỗi
  lần dò K. Trật tự đại lượng tham chiếu từ tooling: nạp clause một CNF lớn
  (196 900 clause, cadical195) mất 0.19–0.21 s (`t_load` đo riêng trong
  `docs/sat_tooling.md`) — chỉ để tham chiếu quy mô, không phải đo trên ABP
  tier của dự án.
- **Rủi ro**: budget của glucose không ổn định khi giải nhiều lần trong cùng
  một process (`docs/sat_tooling.md`) — pilot dùng glucose phải đặt ngân sách
  rộng; tính đúng của mỗi lần dò phải được bảo toàn khi chia sẻ solver (mỗi
  ngưỡng phải cô lập đúng clause của nó), phải test lại theo dạng ticket 12.
- **Blocker**: kissat ra khỏi phạm vi vĩnh viễn; không blocker với
  cadical/glucose.

### 2.3 Symmetry breaking

- **Là gì**: `Config.symmetry` đã có trong contract nhưng pipeline SAT hiện
  bỏ qua kèm warning (`IGNORED_CONFIG_FIELDS` trong `src/sat/solve.py`; không
  bỏ qua im lặng). Bài toán có đối xứng hiển nhiên: đổi nhãn
  `f(v) ↦ n + 1 − f(v)` giữ nguyên mọi `|f(u) − f(v)|` (đại số trực tiếp:
  `|(n+1−p) − (n+1−q)| = |p − q|`), nên nghiệm đi theo cặp đối xứng cùng giá
  trị; symmetry breaking nhắm vào nhóm đối xứng kiểu này.
- **Giá trị kỳ vọng (đánh giá)**: thu hẹp không gian tìm kiếm; mức gain chưa
  đo trong repo.
- **Rủi ro**: ràng buộc phá đối xứng phải giữ lại ít nhất một nghiệm ở mọi
  mức tối ưu — cần kiểm lại với oracle theo dạng ticket 12 trước khi dùng số
  liệu.
- **Blocker**: không có. Lưu ý pilot RQ1 (ticket 16) đặt `symmetry OFF` nên
  pilot W3 không phụ thuộc mục Bonus này.

### 2.4 AMO phụ — commander/product

- **Là gì**: AMO encoding ngoài Core (Core: pairwise, seqcounter). Ticket 08
  ghi rõ: "Không làm commander/product (Bonus, sau khi Core ổn)".
- **Bằng chứng code**: `SUPPORTED_AMO_ENCODINGS` (`src/sat/pairwise.py`) gồm 9
  encoding lấy từ `pysat.card`; commander/product **không nằm trong danh
  sách** — pysat.card không cung cấp sẵn, làm thì phải tự viết encoding + kiểm
  closure như ticket 08 (exhaustive mọi tập con × mọi assignment).
- **Giá trị kỳ vọng (đánh giá)**: giảm số clause so với AMO pairwise `C(m,2)`
  khi `m` lớn, đổi bằng biến phụ — cùng hướng với kết quả đã kiểm trên 6
  literal: pairwise 15 clause vs seqcounter 14 (`docs/sat_tooling.md`); chưa
  có số đo cho commander/product trong repo.
- **Rủi ro**: đổi AMO phải không đổi encoding ABP và không đổi kết quả
  (pattern ticket 08 đã đúng với seqcounter); closure phải kiểm lại exhaustive.
- **Blocker**: không có blocker kỹ thuật.

Ghi chú: "binary search theo K" cũng nằm trong bậc cắt của WORK BREAKDOWN
(README) nhưng không thuộc danh sách 4 mục Bonus của ticket 15; K-search hiện
tại là duyệt tăng dần (`docs/sat_spec.md` §5).

Hạn chế chung cho mọi mục Bonus khi đo số liệu so sánh:

- Đo bộ nhớ chỉ chạy trên Windows: `peak_memory` dùng `GetProcessMemoryInfo`
  (psapi) và là max của các điểm chụp, không phải peak liên tục
  (`src/sat/solve.py`, `docs/sat_tooling.md`) — so peak_memory giữa máy khác
  nền tảng không được.
- Kissat đã loại vĩnh viễn khỏi mọi so sánh solver (mục 1), nên Bonus không
  thể mở rộng trục solver.

## 3. Ước tính compute cho pilot W3 — **ước tính thô**

Ghi rõ: toàn bộ mục này là **ước tính** suy từ số liệu matrix + công thức đặc
tả, không phải số đo của pilot.

Số đo được (thật, 2026-10-20, `12-test-matrix.md`):

- 213 test matrix (8 cấu hình, K-search đầy đủ, n ≤ 9 có oracle): **3.48 s**.
- Toàn suite 422 test: **15.58 s** — gồm cả 3 test tier 1 chạy full K-search
  tới `n = 12` (path10, grid3x4, random12-seed42) ở cấu hình mặc định + order.

Quy mô CNF theo công thức đặc tả (`docs/sat_spec.md` §3, tính tay — không đo):
với `n = 16`, random thưa (`generator.random_graph`: 2n cạnh = 32 cạnh):

- biến pairwise: `n² = 256`;
- assignment + permutation (AMO pairwise): `2(n + n·C(n,2)) = 3 872` clause;
- distance tại `K = 8`: `m · 2 · Σ_{d=1..7}(n − d) = 32 · 2 · 84 = 5 376`
  clause;
- tổng ≈ 9 200 clause — quy mô nhóm `n³` nên chỉ ~2.4× mức `n = 12`
  (`(16/12)³ ≈ 2.4`).

Ước tính:

- Pilot RQ1 (ticket 16: validation subset 8–10 instance, biến pairwise vs
  order × pairwise vs seqcounter, một solver cố định, symmetry/warm start OFF)
  và pilot RQ2 (ticket 17: cố định encoding + AMO, đổi solver — kissat N/A)
  nằm trong khả năng máy dev: K-search đầy đủ tới `n = 12` chỉ chiếm một phần
  nhỏ của 15.58 s cho 422 test, và quy mô CNF ở `n = 16` chỉ tăng cỡ 2–3×.
- Kể cả chạy đủ dạng ma trận 8 cấu hình × bộ Tier 1 (`n ≤ 16`), tổng thời gian
  ước tính vẫn ở mức giây đến phút trên máy dev — không cần máy lớn.
- Chặn trên mỗi run: `Config.time_limit` là ngân sách cả chuỗi K (ticket 10:
  1800 s), nên run xấu nhất bị chặn cứng, không treo vô hạn.
- Pilot với glucose: đặt ngân sách rộng (budget không ổn định trong cùng
  process — `docs/sat_tooling.md`).

Không chắc chắn phải ghi rõ khi dùng ước tính này:

- Độ khó UNSAT ở ngưỡng cao **chưa đo** — `docs/sat_spec.md` §5 ghi "giả
  thuyết chưa đo: các ngưỡng cao là UNSAT khó nhất". Thời gian solve không
  ngoại suy tuyến tính từ quy mô CNF được; nếu pilot gặp ngưỡng UNSAT khó thì
  run đó trôi về sát ngân sách `time_limit`.
- Ticket 16 còn yêu cầu "vài instance lớn" ngoài validation subset — chưa có
  kích thước cụ thể trong repo, ước tính này không phủ phần đó.

## 4. Blocker còn mở: kết quả `--dry-run` của P3

Checklist ticket 15, mục 2: "Xem kết quả `--dry-run` của P3; ước tính compute."

Kiểm tra thực tế (2026-10-20, branch `p2/w2-sat`):

- `grep -i "dry"` trên `src/` (working tree) = **0 hit**.
- `git grep -i "dry"` trên HEAD: **0 hit trong src/ và tests/**; 3 dòng duy
  nhất nhắc "dry-run" là text của ticket 15 và README (docs), không phải code.
- Kết luận: runner của P3 (`src/runner`) **hiện không có cờ `--dry-run`** —
  mục "Xem kết quả `--dry-run`" **CHƯA thực hiện được**. Đây là blocker còn
  mở của ticket 15: cần P3 bổ sung cờ `--dry-run` (hoặc cung cấp dry-run
  output) trước khi gate M1 tick được đầy đủ checklist.
- Mục "ước tính compute" của ticket 15 được đáp ứng ở mục 3 bằng số liệu
  matrix của phía SAT, không nhờ dry-run của P3.
- Phạm vi: ticket này chỉ được thêm file docs (ràng buộc dispatch), không sửa
  `src/runner` — việc bổ sung cờ thuộc P3.

## 5. Hai phương án đặt ra cho gate M1

Doc không chốt. Hai phương án, lý do mỗi bên:

### Phương án A — GO Bonus (có điều kiện duyệt từng mục)

- **Nội dung**: làm Bonus trong đúng phạm vi W3 ticket 20 ("Staircase hoặc
  incremental ở mức prototype và test nhỏ"); duyệt từng mục (2.1–2.4) thay vì
  duyệt cả khối; mỗi mục phải qua dạng kiểm đúng của Core (OPT-oracle, mọi K,
  model counting, AMO closure) trước khi số liệu của nó được dùng cho RQ.
- **Lý do thuận**: Core xanh vững (mục 1: 8/8 cấu hình khớp oracle, 213 test
  matrix, 422 suite xanh); pilot W3 ước tính nhẹ trên máy dev (mục 3) nên có
  dư địa dev cho prototype; Bonus ở mức prototype + test nhỏ là rủi ro có
  chặn; từng mục có blocker riêng đã nêu rõ (mục 2) — incremental không bị
  chặn với cadical/glucose, symmetry/AMO phụ/commander không blocker kỹ thuật.
- **Rủi ro phải nhận**: mỗi mục Bonus thêm spec + code + test (commander/product
  không có sẵn trong pysat.card); nếu incremental dùng glucose phải cẩn thận
  budget (mục 2.2); bất kỳ mục Bonus nào làm Core đỏ lại đều phải rollback —
  Core là phần không được cắt theo WORK BREAKDOWN.

### Phương án B — NO-GO Bonus

- **Nội dung**: cắt toàn bộ Bonus W3; tài nguyên dồn cho pilot RQ1/RQ2
  (ticket 16, 17) và correctness suite cuối (ticket 19); ghi rõ Bonus bị cắt
  theo checklist mục 4 của ticket 15.
- **Lý do thuận**: quy tắc cắt của WORK BREAKDOWN đã định sẵn "khi chậm: cắt
  Bonus trước, không bao giờ cắt Core" (README; AGENTS.md) — NO-GO là cách áp
  dụng chủ động quy tắc đó; Core + pilot + RQ1/RQ2 là đường trực tiếp tới
  paper; giá trị kỳ vọng của mọi mục Bonus hiện chỉ là đánh giá định tính chưa
  có số đo (mục 2), trong khi pilot W3 đã đủ việc (2 pilot + correctness suite
  cuối) và ước tính mục 3 chỉ chắc chắn cho phạm vi `n ≤ 16`.
- **Hệ quả phải nhận**: paper chỉ báo cáo phạm vi Core: 2 encoding × 2 AMO ×
  2 solver (kissat đã loại) — RQ2 hẹp hơn kế hoạch gốc nêu Kissat; các mục
  Bonus trong WORK BREAKDOWN được ghi là bị cắt, muốn làm lại phải chờ gate
  sau.

### Bảng so sánh

| Tiêu chí | A — GO Bonus | B — NO-GO Bonus |
|---|---|---|
| Rủi ro cho Core | Có (thêm encoding/AMO phải giữ matrix xanh) | Không |
| Khối lượng W3 | Pilot + prototype Bonus (mỗi mục duyệt riêng) | Chỉ pilot + correctness suite |
| Giá trị RQ | Có thể thêm trục so sánh (nếu prototype ra số đo tốt) | Giữ nguyên phạm vi 2×2×2 |
| Điều kiện tiên quyết | Duyệt từng mục + kiểm đúng theo dạng ticket 12 | Không thêm |
| Quy tắc WORK BREAKDOWN | Không vi phạm (Bonus được làm khi không chậm) | Áp dụng chủ động quy tắc cắt |

Quyết định GO/NO-GO thuộc nhóm/customer tại gate M1. Doc này kết thúc ở đây,
không chốt phương án nào.

## Nguồn

- `docs/handoff/w2-sat/12-test-matrix.md` — kết quả matrix thật 2026-10-20.
- `docs/handoff/abp-sat-encoding/issues/W2/15-m1-gate-bonus-decision.md` —
  checklist của gate.
- `docs/handoff/abp-sat-encoding/issues/W2/08-amo-pairwise-seqcounter.md`,
  `09-glucose-kissat-backend.md`, `10-multi-run-k-search.md` — phạm vi Core,
  Kissat, ngân sách time_limit.
- `docs/handoff/abp-sat-encoding/issues/W3/16-pilot-rq1.md`, `17-pilot-rq2.md`,
  `20-bonus-sat-prototype.md` — phạm vi pilot và Bonus W3.
- `docs/handoff/abp-sat-encoding/README.md` — mốc M1, bậc cắt khi chậm.
- `docs/sat_spec.md` §5, `docs/sat_tooling.md` — K-search, tooling, kissat,
  glucose caveat.
- `src/sat/solve.py`, `src/sat/pairwise.py`, `src/sat/backend.py` —
  `IGNORED_CONFIG_FIELDS`, `SUPPORTED_AMO_ENCODINGS`, `PYSAT_KISSAT_FAMILIES`,
  blocking của kissat.
- Kiểm tra `--dry-run`: `grep -i "dry"` trên `src/` (working tree) và
  `git grep -i "dry"` trên HEAD, ngày 2026-10-20.
