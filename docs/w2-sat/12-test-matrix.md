# 12 — Test matrix correctness (encoding × AMO × backend)

Ticket 12 (GH #19) + ticket 08 closure (GH #15) · Ngày chạy: 2026-10-20
· Branch `p2/w2-sat` · File test: `tests/sat/test_matrix.py` (213 test).

Lệnh chạy đã dùng (kết quả dưới đây lấy từ lần chạy thật này, không viết tay):

```
.\.venv\Scripts\python.exe -m pytest tests\sat\test_matrix.py -v --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp
213 passed in 3.48s

.\.venv\Scripts\python.exe -m pytest tests -q --basetemp=C:\Users\ducqu\AppData\Local\Temp\opencode\pytest-tmp
422 passed in 15.58s
```

## Ma trận 2 × 2 × 2 + cột kissat N/A

Mỗi ô là kết quả thật của 26 test cho cấu hình đó (10 OPT-oracle
+ 10 SAT/UNSAT-từng-K + 6 model counting). Nhóm kiểm "verify() mọi nghiệm" không
cột riêng: nó được assert bên trong 2 nhóm đầu (mọi nghiệm SAT đều qua
`verify()` với đúng giá trị trước khi so oracle).

| abp_encoding | amo_encoding | cadical195 | glucose4 | kissat |
|---|---|---|---|---|
| pairwise | pairwise | PASS (10/10) · PASS (10/10) · PASS (6/6) | PASS (10/10) · PASS (10/10) · PASS (6/6) | N/A (1) |
| pairwise | seqcounter | PASS (10/10) · PASS (10/10) · PASS (6/6) | PASS (10/10) · PASS (10/10) · PASS (6/6) | N/A (1) |
| order | pairwise | PASS (10/10) · PASS (10/10) · PASS (6/6) | PASS (10/10) · PASS (10/10) · PASS (6/6) | N/A (1) |
| order | seqcounter | PASS (10/10) · PASS (10/10) · PASS (6/6) | PASS (10/10) · PASS (10/10) · PASS (6/6) | N/A (1) |

(1) Kissat N/A vĩnh viễn W2: qua PySAT family `kissat404` cho model sai, bỏ qua
assumptions (kết quả sai im lặng) và `add_clause` sau solve làm process abort;
không có binary kissat ngoài trên PATH. Bị chặn ở khởi tạo backend
(`PYSAT_KISSAT_FAMILIES`) và ở pipeline (`_validate_solver`) —
`tests/sat/test_backend.py`, `tests/sat/test_solve.py`. Cột ghi N/A, không chạy.

## Ghi chú AMO no-op của order encoding

Order encoding không có ràng buộc at-most-one nào (chuỗi đơn điệu `o[v][p] →
o[v][p+1]` thay ALO + AMO của pairwise) nên `amo_encoding` được chấp nhận + ghi
nhận trong `CNF` nhưng không đổi clause, không đổi kết quả
(`tests/sat/test_order.py::test_order_change_amo_encoding_does_not_change_cnf`).
Matrix vẫn chạy đủ 2 giá trị AMO cho order — khẳng định đường config hoạt động;
trục AMO chỉ có ý nghĩa thật với pairwise (dòng 1–2 bảng trên).

## Nhóm kiểm từng cấu hình

- **OPT khớp oracle** (`test_matrix_solve_sat_matches_oracle`): `solve_sat` trả
  status OPT, `lb == ub ==` B của oracle brute-force, nghiệm qua `verify()` đúng
  bằng B — trên 10 instance.
- **SAT/UNSAT tại mọi K ∈ 1..n** (`test_matrix_decision_matches_oracle_at_every_k`):
  `solve_decision` khớp oracle tại từng K; mọi nghiệm SAT verify được ≥ K.
- **Model counting** (`test_matrix_model_count_by_blocking_matches_permutations`):
  6 cặp (instance, K) cực nhỏ, đếm blocking-clause == đếm `itertools.permutations`.

## Model counting: blocking clause vs đếm hoán vị (n ≤ 6)

Đếm bằng blocking clause qua `SatBackend` như pipeline (giải, chặn model trên các
biến chính, giải lại — không enumerate trong solver), so với đếm
`itertools.permutations` kèm điều kiện |f(u)−f(v)| ≥ K. Chạy ở cả pairwise và
order trên cả 8 cấu hình: không thừa, không thiếu nghiệm.

| Instance | K | # hoán vị thỏa (itertools) | Blocking-clause |
|---|---|---|---|
| path4 | 2 | 2 | bằng đúng, 8/8 cấu hình |
| path4 | 3 | 0 | bằng đúng, 8/8 cấu hình |
| cycle5 | 2 | 10 | bằng đúng, 8/8 cấu hình |
| cycle5 | 3 | 0 | bằng đúng, 8/8 cấu hình |
| disconnected | 3 | 8 | bằng đúng, 8/8 cấu hình |
| isolated | 3 | 2 | bằng đúng, 8/8 cấu hình |

Hai dòng K = 3 là UNSAT (0 nghiệm) — chặn cả hướng "không thừa nghiệm".

## Ticket 08 closure — AMO exhaustive

Contract `amo(literals, encoding)` kiểm exhaustive: mọi tập con của 6 literal
(64 tập con, gồm cả tập 0/1 literal — clause rỗng), mọi assignment
(729 lần kiểm mỗi encoding): assignment có ≤ 1 literal true phải
thỏa toàn bộ clause AMO; assignment > 1 true phải bị chặn. Kiểm qua backend vì
`seqcounter` sinh biến phụ: "thỏa toàn bộ clause" = tồn tại cách gán biến phụ thỏa
mọi clause đồng thời (semantics chuẩn của encoding AMO).

| amo_encoding | Kết quả |
|---|---|
| pairwise | PASS (1 test, 729 lần kiểm: 64 tập con × mọi assignment) |
| seqcounter | PASS (1 test, 729 lần kiểm: 64 tập con × mọi assignment) |

AMO closure là contract mức clause nên không phụ thuộc solver — chạy trên
`cadical195` mặc định; 2 test tương ứng (1 mỗi encoding).

## Instance set + B tối ưu theo oracle

10 instance của ma trận (toy W1 + tier0 họ T3 + edge case + random có seed,
toàn bộ n ≤ 9 để chạy được oracle; grid3x3 là toy W1 với n = 9 = giới hạn oracle):

| Instance | n | B (oracle) |
|---|---|---|
| path4 | 4 | 2 |
| cycle5 | 5 | 2 |
| grid3x3 | 9 | 3 |
| complete5 | 5 | 1 |
| star6 | 7 | 1 |
| bintree3 | 7 | 3 |
| grid2x3 | 6 | 2 |
| disconnected | 6 | 3 |
| isolated | 5 | 3 |
| random8-seed42 | 8 | 2 |

## Tier 1 (n ≤ 12) — cấu hình mặc định

Oracle brute-force giới hạn n ≤ 9 nên tier1 không so brute-force: OPT được
chứng minh bằng UNSAT của solver tại K = B + 1, nghiệm qua `verify()`, và order
encoding phải cho cùng B (hai encoding cùng giải một bài toán quyết định).
3/3 test PASS.

| Instance | n | B (mặc định, tự chứng minh) |
|---|---|---|
| path10 | 10 | 5 |
| grid3x4 | 12 | 5 |
| random12-seed42 | 12 | 3 |

## Ghi chú

- Ma trận 8 cấu hình × 213 test trong `test_matrix.py`, toàn suite
  xanh trong ~16 giây (giới hạn brief < ~60s).
- Model counting chặn trên các biến chính (`var_of`) nên biến phụ của seqcounter
  không làm một hoán vị bị đếm nhiều lần.
- Bảng trên sinh từ lần chạy thật ngày 2026-10-20 bằng script đọc output
  `pytest -v` (mọi ô PASS/FAIL khớp từng dòng PASSED/FAILED).
