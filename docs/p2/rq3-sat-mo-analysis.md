# P2 - Vì sao 12/24 run SAT (RQ3) trả `MO`

**Ngày:** 2026-11-28 · **Owner:** P2 · **Trạng thái:** phân tích dữ liệu, không chạy lại solver.

Cấu hình SAT được phân tích: `abp_encoding=order`, `amo_encoding=pairwise`, `solver=glucose4`,
`time_limit=1800.0`, `memory_limit=12.0` GiB, `seed=0`, `symmetry=false`, `warm_start=false`
(`ABP-rq3/results/runs.csv`, cột tương ứng; 24/24 run SAT có cùng bộ giá trị).

**Nguồn số liệu (chỉ đọc, không sửa):**

| Ký hiệu | Đường dẫn (gốc `C:\Users\ducqu\workspace\ABP-rq3`) |
|---|---|
| `[runs]` | `results/runs.csv` (120 run = 24 instance × 5 method) |
| `[raw]` | `results/rq3_official/<run_id>.json` (120 file) |
| `[att]` | `results/rq3_official/attempt_history/` (5 file) |
| `[ckpt]` | `results/rq3_official/checkpoints/` (16 file) |
| `[manifest]` | `benchmark/hb/MANIFEST.csv` (`n_reference`, `m_reference`, `delta_max`) |
| `[inst]` | `benchmark/hb/instances.csv` |

Số liệu dự kiến (clause/biến) tính bằng công thức `project_cnf_growth` trong
`experiments/w5_final_analysis.py:345-352` (repo chính), áp dụng cho `k` tương ứng:
`order`: `variables = n(n-1)`, `clauses = n(n-2) + n·C(n,2) + 2m·Σ_{d=1..k-1}(n-d)`.
Công thức này được kiểm chứng lại trên 12 run không `MO`: **12/12 khớp chính xác** số clause
đo được tại probe cuối (xem Bảng 3). Không có số nào trong tài liệu này được sinh bằng cách
chạy solver.

---

## 1. Bảng 24 run SAT

`n`, `m` lấy từ `[manifest]`; `status`, `lb`, `ub`, `wall_time` (s), `peak_memory` (MB),
`variables`, `clauses` lấy từ `[runs]`; số probe = `len(metadata.probes)` trong `[raw]`;
"checkpoint" = có file `<run_id>.json` trong `[ckpt]`.

| # | Instance | n | m | Status | lb | ub | wall_time | peak_memory | variables | clauses | #probe | Checkpoint |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | pores_1 | 30 | 103 | OPT | 6 | 6 | 9.41 | 53.00 | 870 | 46 644 | 7 | có |
| 2 | ibm32 | 32 | 90 | OPT | 9 | 9 | 2.36 | 50.17 | 992 | 60 572 | 10 | có |
| 3 | bcspwr01 | 39 | 46 | OPT | 17 | 17 | 2.70 | 57.02 | 1 482 | 77 262 | 18 | có |
| 4 | bcsstk01 | 48 | 176 | OPT | 9 | 9 | 3.15 | 98.11 | 2 256 | 192 576 | 10 | có |
| 5 | bcspwr02 | 49 | 59 | OPT | 21 | 21 | 5.73 | 88.92 | 2 352 | 154 091 | 22 | có |
| 6 | curtis54 | 54 | 124 | OPT | 13 | 13 | 6.93 | 114.27 | 2 862 | 231 610 | 14 | có |
| 7 | will57 | 57 | 127 | OPT | 13 | 13 | 6.96 | 126.21 | 3 192 | 259 207 | 14 | có |
| 8 | impcol_b | 59 | 281 | OPT | 8 | 8 | 4.36 | 158.24 | 3 422 | 349 344 | 9 | có |
| 9 | ash85 | 85 | 219 | FEAS | 21 | 84 | 1800.65 | 468.95 | 7 140 | 991 157 | 22 | có |
| 10 | nos4 | 100 | 247 | FEAS | 33 | 99 | 1800.30 | 912.96 | 9 900 | 1 857 866 | 34 | có |
| 11 | dwt_234 | 117 | 162 | FEAS | 45 | 116 | 1800.35 | 1114.39 | 13 572 | 2 177 937 | 46 | có |
| 12 | bcspwr03 | 118 | 179 | OPT | 39 | 39 | 416.46 | 892.49 | 13 806 | 2 196 518 | 40 | có |
| 13 | bcsstk06 | 420 | 3720 | **MO** | — | — | 802.38 | — | — | — | 0 | có (hỏng, §3.3) |
| 14 | bcsstk07 | 420 | 3720 | **MO** | — | — | 802.89 | — | — | — | 0 | có (hỏng, §3.3) |
| 15 | impcol_d | 425 | 1267 | **MO** | — | — | 815.88 | — | — | — | 0 | có (hỏng, §3.3) |
| 16 | can_445 | 445 | 1682 | **MO** | — | — | 247.18 | — | — | — | 0 | có (hỏng, §3.3) |
| 17 | 494_bus | 494 | 586 | **MO** | — | — | 237.55 | — | — | — | 0 | không |
| 18 | dwt__503 | 503 | 2762 | **MO** | — | — | 80.82 | — | — | — | 0 | không |
| 19 | sherman4 | 546 | 1341 | **MO** | — | — | 79.08 | — | — | — | 0 | không |
| 20 | dwt__592 | 592 | 2256 | **MO** | — | — | 80.42 | — | — | — | 0 | không |
| 21 | 662_bus | 662 | 906 | **MO** | — | — | 72.61 | — | — | — | 0 | không |
| 22 | nos6 | 675 | 1290 | **MO** | — | — | 87.69 | — | — | — | 0 | không |
| 23 | 685_bus | 685 | 1282 | **MO** | — | — | 77.44 | — | — | — | 0 | không |
| 24 | can_715 | 715 | 2975 | **MO** | — | — | 86.56 | — | — | — | 0 | không |

Tổng hợp: **9 OPT, 3 FEAS (đều hết giờ ở 1800 s), 12 MO**
(`[runs]`, `status` của 24 dòng `method=sat`).

Hai quan sát định vị ranh giới:

- **Ranh giới sạch theo `n`:** toàn bộ instance `n ≤ 118` không `MO`; toàn bộ `n ≥ 420` `MO`
  (12/12). Không có ngoại lệ nào trong 24 run (`[runs]`, `[manifest]`).
- **`MO` không phải hết giờ:** wall_time của 12 run `MO` là 72.61–815.88 s, đều dưới
  `time_limit=1800` rất xa (`[runs]`). Run `MO` dài nhất (impcol_d, 815.88 s) vẫn chưa bằng
  nửa ngân sách.
- **`MO` lặp lại được:** 5/12 instance `MO` có bản ghi attempt cũ hơn trong `[att]`
  (494_bus 80.53 s, bcsstk06 104.12 s, bcsstk07 89.17 s, can_445 93.42 s, impcol_d 87.71 s),
  cùng `status=MO`, cùng `error=MemoryError`. Đây không phải sự cố nhất thời.

---

## 2. `MO` do bùng nổ CNF hay do search thật sự?

### 2.1 Kích thước CNF `order` dự kiến cho 12 instance `MO`

`k=1` là probe đầu tiên (rẻ nhất) của chuỗi K; `k=lb_ref` là mốc mà chuỗi K **buộc phải đi qua**
để có incumbent, với `lb_ref` = cận dưới tốt nhất đã được chứng minh bởi 4 method còn lại trong
`[runs]` (662_bus và 685_bus có `OPT` nên `B` biết chính xác = 220 và 136); `k=n-1` là worst case
(`B ≤ n-1`). Cột GiB là **ước lượng tuyến tính**, không phải đo: hai đầu
100 byte/clause và 491 byte/clause là biên dưới/biên trên của tỉ lệ quan sát được trong chính
bộ dữ liệu này (491 B/clause = slope fit bình phương tối thiểu trên 12 run không `MO`; 100 B/clause
= tỉ lệ thấp nhất ghi trong `[ckpt]`, xem §3.3 về độ tin cậy của file này).

| Instance | n | m | `lb_ref` (nguồn `[runs]`, method) | clauses @k=1 | clauses @k=`lb_ref` | GiB @`lb_ref` (100–491 B) | clauses @k=n−1 |
|---|---|---|---|---|---|---|---|
| bcsstk06 | 420 | 3720 | 29 (cplex_cp) | 37 131 360 | 121 605 120 | 11.3 – 55.6 | 691 769 520 |
| bcsstk07 | 420 | 3720 | 29 (cplex_cp) | 37 131 360 | 121 605 120 | 11.3 – 55.6 | 691 769 520 |
| impcol_d | 425 | 1267 | 122 (cplex_cp) | 38 472 275 | 150 079 771 | 14.0 – 68.6 | 266 783 141 |
| can_445 | 445 | 1682 | 79 (cplex_cp) | 44 158 685 | 150 558 641 | 14.0 – 68.9 | 376 484 881 |
| 494_bus | 494 | 586 | 226 (cplex_cp) | 60 397 922 | 160 867 622 | 15.0 – 73.6 | 203 112 362 |
| dwt__503 | 503 | 2762 | 59 (cplex_cp) | 63 757 262 | 215 462 874 | 20.1 – 98.5 | 761 173 310 |
| sherman4 | 546 | 1341 | 231 (cplex_cp) | 81 533 634 | 347 091 864 | 32.3 – 158.8 | 480 572 322 |
| dwt__592 | 592 | 2256 | 104 (cplex_cp) | 103 911 392 | 354 868 832 | 33.0 – 162.3 | 893 218 112 |
| 662_bus | 662 | 906 | 220 (cp_sat/cplex_cp, **OPT**) | 145 276 562 | 364 325 618 | 33.9 – 166.6 | 541 724 042 |
| nos6 | 675 | 1290 | 278 (cplex_cp) | 153 999 900 | 537 057 660 | 50.0 – 245.6 | 740 882 820 |
| 685_bus | 685 | 1282 | 136 (cp_sat/cplex_cp, **OPT**) | 160 942 805 | 374 511 185 | 34.9 – 171.3 | 761 608 521 |
| can_715 | 715 | 2975 | 118 (cplex_cp) | 183 017 120 | 639 691 520 | 59.6 – 292.6 | 1 701 778 420 |

`variables` của `order` = `n(n-1)`: 175 980 (bcsstk06/07) … 510 510 (can_715); con số này khớp
`variables` trong 4 file `[ckpt]` của instance `MO` (§3.3).

### 2.2 So với 12 instance không `MO`

| Instance | n | m | #probe | k cuối | clauses đo được | clauses theo công thức | khớp | peak_memory (MB) |
|---|---|---|---|---|---|---|---|---|
| pores_1 | 30 | 103 | 7 | 7 | 46 644 | 46 644 | ✓ | 53.00 |
| ibm32 | 32 | 90 | 10 | 10 | 60 572 | 60 572 | ✓ | 50.17 |
| bcspwr01 | 39 | 46 | 18 | 18 | 77 262 | 77 262 | ✓ | 57.02 |
| bcsstk01 | 48 | 176 | 10 | 10 | 192 576 | 192 576 | ✓ | 98.11 |
| bcspwr02 | 49 | 59 | 22 | 22 | 154 091 | 154 091 | ✓ | 88.92 |
| curtis54 | 54 | 124 | 14 | 14 | 231 610 | 231 610 | ✓ | 114.27 |
| will57 | 57 | 127 | 14 | 14 | 259 207 | 259 207 | ✓ | 126.21 |
| impcol_b | 59 | 281 | 9 | 9 | 349 344 | 349 344 | ✓ | 158.24 |
| ash85 | 85 | 219 | 22 | 22 | 991 157 | 991 157 | ✓ | 468.95 |
| nos4 | 100 | 247 | 34 | 34 | 1 857 866 | 1 857 866 | ✓ | 912.96 |
| dwt_234 | 117 | 162 | 46 | 46 | 2 177 937 | 2 177 937 | ✓ | 1114.39 |
| bcspwr03 | 118 | 179 | 40 | 40 | 2 196 518 | 2 196 518 | ✓ | 892.49 |

(`clauses đo được` = `clauses` của dòng `[runs]` = probe cuối trong `metadata.probes` của `[raw]`;
`peak_memory` = `[runs]`.)

Trần thực đo của nhóm "vừa được 12 GiB": **2 196 518 clause / 892.49 MB**
(bcspwr03, `[runs]`), cao nhất cả nhóm là **2 177 937 clause / 1114.39 MB** (dwt_234).

### 2.3 Trả lời

**`MO` do bùng nổ CNF, không do search thật sự.** Ba dòng bằng chứng:

1. **Kích thước CNF tăng bậc ba theo `n`, bậc một theo `m·k`.**
   `clauses = n(n-2) + n·C(n,2) + 2m·Σ(n-d)`, tức `Θ(n³ + mkn)`. Ở `k=1` (chưa có clause
   distance nào) mỗi instance `MO` đã cần 37.1M–183.0M clause, gấp **17×–83×** mức lớn nhất mà
   một run còn sống đã chạm (2.20M clause, bcspwr03). Riêng số hạng hoán vị `n·C(n,2)` đã là
   36.96M clause cho `n=420` và 182.5M cho `n=715`.
2. **Chuỗi K buộc phải đi qua mốc vượt cap, kể cả khi tính rất rẻ.** Với từng instance `MO`,
   CNF tại `k=lb_ref` cần 11.3–59.6 GiB ở tỉ lệ lạc quan nhất (100 B/clause) và 55.6–292.6 GiB
   ở tỉ lệ đo được (491 B/clause) — đều vượt cap 12.0 GiB (trừ bcsstk06/07 ở mức lạc quan nhất:
   11.3 GiB, tức chỉ còn 6% margin, trước khi tính overhead của solver). Với 662_bus và 685_bus
   thì `B` đã biết chính xác (220 và 136, hai method `OPT`), nên đây không phải giả định về `B`.
3. **Thời điểm chết khớp với pha encode/nạp clause, không khớp với "search lâu".**
   662_bus cần 221 probe (vì `B=220`) nhưng chết ở 72.61 s; 685_bus cần 137 probe (vì `B=136`)
   nhưng chết ở 77.44 s. Với `t_encode` của các run sống cùng cỡ (dwt_234: 52.7 s cho 2.15M clause,
   `[ckpt]`), 72–87 s chỉ đủ cho 1–2 probe đầu — tức chết ngay khi dựng/nạp CNF, không phải sau
   khi đã search. Trần thời gian không phải nguyên nhân: mọi run `MO` dừng ở 4–45% của 1800 s.

**Giới hạn của kết luận này:** record **không** phân biệt được chết ở `build_cnf` (Python dựng
list clause), ở `add_clauses` (nạp vào Glucose), hay ở bước `solve` của probe đầu — vì cả
`t_encode` và `metadata.probes` đều rỗng (§3). Câu đúng để viết trong paper là: *"CNF tại ngưỡng
mà chuỗi K buộc phải đi qua đã vượt ngân sách bộ nhớ, nên `MO` xảy ra trong pha dựng/nạp CNF hoặc
ngay đầu solve, không phải do solver search lâu."* Không được viết *"solver hết bộ nhớ khi search"*.

**Encoding khác trong codebase không cứu được.** `pairwise` (ABP) tại `k=1` cần
73.9M–365.0M clause cho chính 12 instance đó (tính theo cùng công thức, nhánh `pairwise`:
`n²` biến, `2n + 2n·C(n,2) + 2m·Σ(n-d)` clause), tức **tệ hơn `order`**, và `order` vốn đã bỏ
hẳn nhóm AMO (`docs/canonical_sat_config.md:113-114`) nên `amo_encoding` không đổi được gì. Nguyên nhân là
ràng buộc hoán vị `n·C(n,2)`, không phải AMO.

---

## 3. Tính nhất quán của record `MO`

### 3.1 Trạng thái field (12/12 run)

Kiểm tra trên 12 file `[raw]` có `status=MO`:

| Field | Giá trị | Ý nghĩa |
|---|---|---|
| `status` | `"MO"` | do runner gán, không do solver |
| `error` | `"MemoryError"` | chuỗi duy nhất mô tả nguyên nhân |
| `peak_memory` | `null` | **không có phép đo bộ nhớ nào** |
| `lb`, `ub` | `null` | không có incumbent, không có cận |
| `t_encode`, `t_solve`, `t_total` | `null` | mất cả thời gian encode lẫn solve |
| `variables`, `clauses` | `null` | mất luôn kích thước CNF thực tế |
| `solution` | không có key | không có labeling |
| `metadata` | `{}` | mất toàn bộ `probes`, `k_best`, `k_unsat` |

`[runs]` giữ nguyên khoảng trống đó (12 dòng: `lb`, `ub`, `t_encode`, `peak_memory`,
`variables`, `clauses` đều rỗng; `wall_time` và `error` thì có).

### 3.2 Vì sao rỗng — đúng đường code

- `src/runner/worker.py:34-35`: `except MemoryError` → `{"ok": True, "result": {"status": "MO"},
  "note": "MemoryError"}`. Worker **không** ghi `Result`, không ghi metric.
- `src/runner/runner.py:286-288`: nhận `status == "MO"` và thiếu `t_total` → `build_record(...,
  status_override="MO", error="MemoryError")`. Không có nhánh nào đọc lại `peak_memory`.
- `src/sat/solve.py:243-249`: vòng probe chỉ bắt `BackendError`; `MemoryError` thoát khỏi `_probe`
  nên `Result` (dòng 346-359, nơi dựng `metadata` gồm `probes`) **không bao giờ được tạo**. Vì vậy
  `metadata={}` chứ không phải `{"probes": [...]}`, dù đã có probe chạy xong trước đó.
- `src/sat/solve.py:356` còn có `peak_memory=None if error is not None else peak_ws`, tức kể cả
  khi `Result` được tạo với `error`, `peak_memory` vẫn bị xoá.

Hệ quả: **không có mẫu số** cho bất kỳ khẳng định nào về bộ nhớ.

### 3.3 Checkpoint của 4 instance `MO` không dùng được

`[ckpt]` có 4 file ứng với instance `MO` (bcsstk06, bcsstk07, can_445, impcol_d) và chứa số liệu
trông hấp dẫn (clauses 37.1M–44.2M, `peak_memory` 2249.7–3543.0 MB, `t_encode` 70.0–150.8 s).
Nhưng chúng **không hợp lệ**:

- `objective = 1` cho cả 4 file, kèm labeling identity (`"0":1, "1":2, ...`). Bandwidth thật của
  labeling identity, tính trực tiếp trên cạnh trong `benchmark/hb/raw/*.mtx.rnd`: bcsstk06 = 417,
  bcsstk07 = 417, impcol_d = 411, can_445 = 436. Vậy `objective=1` mâu thuẫn với chính `solution`
  trong cùng file.
- 2 file bcsstk06/bcsstk07 có `solution` và `objective` trùng nhau dù là 2 file dữ liệu khác SHA-256
  trong `[manifest]`.
- `status` của run là `MO` (không có nghiệm), nhưng checkpoint lại ghi một "incumbent".

Theo `docs/experimental_protocol.md:149`, checkpoint hỏng/không hợp lệ là lỗi validation và không
được dùng làm nghiệm. Ở đây **không** dùng làm nghiệm và **không** dùng làm số đo bộ nhớ.
Giá trị duy nhất còn kiểm chứng được là `clauses`/`variables`: 37 131 360 = đúng công thức tại
`k=1` cho (420, 3720); 44 158 685 = đúng cho (445, 1682); 38 472 275 = đúng cho (425, 1267).
Nghĩa là CNF **đã được dựng tới probe đầu** trước khi chết — nhưng file không nói chết ở probe nào.

### 3.4 Điều này giới hạn kết luận gì

- **Chứng minh được:** run kết thúc bằng `MemoryError`; CNF của instance đó lớn hơn mọi CNF đã
  chạy thành công trong cùng bộ dữ liệu (mục 2); run dừng rất lâu trước `time_limit`.
- **KHÔNG chứng minh được:** rằng run đã chạm cap 12.0 GiB. `MemoryError` có thể đến từ
  (a) Job Object `JOB_OBJECT_LIMIT_JOB_MEMORY` do `src/runner/memory_limit.py` áp cho process tree
  — đây là cơ chế *được thiết kế* để sinh `MemoryError` khi vượt cap, nhưng nó không để lại dấu vết
  nào trong record; (b) cạn commit của OS; (c) một cấp phát đơn lẻ quá lớn. Không có `peak_memory`
  thì ba khả năng này không phân biệt được.
- **KHÔNG chứng minh được** `lb`/`ub` cho 12 instance đó, kể cả dạng "đã có incumbent".

Đối chiếu chuẩn: `docs/experimental_protocol.md:158` định nghĩa `MO` = "vượt memory limit đã cấu
hình", và dòng 139-141 yêu cầu "chỉ ghi `MO` khi có bằng chứng run vượt giới hạn; lỗi không rõ
nguyên nhân phải điều tra, không tự gán `MO`". Với record hiện tại, **12 dòng `MO` chưa đạt chuẩn
này** — chúng là "MemoryError chưa xác định nguyên nhân", không phải "vượt 12 GiB".

### 3.5 P1 được/không được viết gì trong paper

| Được viết | Không được viết |
|---|---|
| "12/24 instance (`n ≥ 420`) kết thúc bằng `MemoryError` ở 72.6–815.9 s, dưới `time_limit=1800 s`." | "12 run đã vượt memory cap 12 GiB." |
| "Kích thước CNF `order` tại `k=1` của 12 instance đó là 37.1M–183.0M clause, gấp 17–83 lần mức lớn nhất còn chạy được (2.20M clause)." | "SAT solver cần > 12 GiB để giải các instance lớn." |
| "Do mất `peak_memory`, không xác định được run chạm cap cấu hình hay cạn bộ nhớ OS; đây là hạn chế của instrumentation." | "`MO` = out-of-memory do cap; PAR2/so sánh bộ nhớ với các method khác là hợp lệ cho 12 dòng này." |
| "Bảng RQ3 báo cáo 12/24 cho SAT, kèm ghi chú 12 dòng `MO` không có phép đo." | Bất kỳ trung bình/median `peak_memory` nào tính trên 24 dòng SAT (mẫu số thật là 12). |
| "checkpoint của 4 instance `MO` tồn tại nhưng không hợp lệ (objective không khớp nghiệm); không dùng." | Trích `peak_memory` từ `[ckpt]` như số đo của run `MO`. |

Nếu P1 cần một câu ngắn cho phần Limitations: *"12 dòng `MO` chỉ có `error=MemoryError`; không có
`peak_memory` nên không khẳng định được việc chạm cap 12 GiB — xem P2/rq3-sat-mo-analysis."*

---

## 4. `search_mode = null` trong cả 24 run SAT

**Hiện trạng đo được:**

- `[runs]`: cột `search_mode` của 24 dòng `method=sat` chỉ nhận **một** giá trị: chuỗi rỗng `""`.
- `[raw]`: `search_mode: null` ở cả cấp record và cấp `config`, 24/24 file.
- Cấu hình chuẩn lại khai `search_mode="multi"`: `experiments/w5_final_analysis.py:651`
  (`CANONICAL_SAT_CONFIG`), và `docs/experimental_protocol.md:23` ghi "search multi-run,
  non-incremental".

**Chuỗi K có thật sự chạy không?** Có — nhưng chỉ chứng minh được ở 12 run không `MO`:
`metadata.probes` dài 7–46 phần tử, `k` tăng 1,2,3,… tới `k_unsat` (Bảng 3). Với 12 run `MO`,
`metadata={}` nên **không có phần tử nào** chứng minh chuỗi K đã chạy; ta chỉ biết
`src/sat/solve.py:239-303` là vòng `while lo + 1 < hi` và không có nhánh nào tắt nó.

**Hệ quả cho filter `search_mode ∈ {"", "multi"}`:**

1. **Filter này luôn vacuous (không loại dòng nào).** Trên `[runs]`, mọi dòng SAT có `""` → lọt.
   Trên `[raw]`, `experiments/analyze_rq1_rq2.py:76-80` gán `null` → `"multi"` nếu `run_id` chứa
   `__multi__`, và dòng 112 ghi đè lần nữa bằng `str(raw.get("search_mode") or "multi")` — vì
   dict literal có **hai key `search_mode`** (dòng 98 và 112), giá trị dòng 112 thắng, nên `null`
   luôn thành `"multi"`. `run_id` của 24 run SAT **không** chứa `__multi__`
   (`<inst>__sat__order__pairwise__glucose4__na__sym0__ws0__s0__tl1800.0__ml12.0`), nên nếu không
   có dòng 112 thì chúng sẽ thành `""`.
2. **Vì luôn vacuous, filter không thể dùng làm bằng chứng.** Câu "chúng tôi chỉ phân tích các run
   `search_mode ∈ {"", "multi"}`" trong paper là đúng nhưng **rỗng nghĩa**: nó không loại được gì,
   và không phát hiện được 12 run đã chết trước khi sinh probe đầu tiên.
3. **Hai đường đọc dữ liệu cho kết quả khác nhau.** Cùng một run: CSV cho `""`, JSON đã chuẩn hoá
   cho `"multi"`. Ai filter `search_mode == "multi"` trên `[runs]` sẽ **mất toàn bộ 24 dòng SAT**;
   ai filter `search_mode in ("", "multi")` thì giữ tất cả. Đây là bẫy im lặng.
4. **Không tái lập được cấu hình từ record.** `config.search_mode = null` nghĩa là raw record không
   tự nó nói run dùng multi-run. Giá trị `"multi"` chỉ đến từ `CANONICAL_SAT_CONFIG` và từ suy luận
   qua `probes`. Người đọc lại raw JSON sau này không dựng lại được cấu hình.

**Cách viết an toàn cho P1:** nêu `search_mode` là "multi-run K-search (giá trị `multi` theo
`CANONICAL_SAT_CONFIG`; field `search_mode` trong raw record bị ghi `null` — lỗi exporter, xem
P2/rq3-sat-mo-analysis §4)"; không dùng cột này để lọc, và không trích nó như bằng chế độ chạy.

---

## 5. Kết luận P2

### 5.1 Canonical config còn đúng không?

**Đúng với tư cách cấu hình, không đủ với tư cách độ phủ.**

- Không có bằng chứng nào cho thấy `order`/`pairwise`/`glucose4` sai: 12 instance chạy được vẫn
  cho 9 `OPT` + 3 `FEAS`, và mọi `OPT` đều nằm trong `[ab_lb_ref, ab_ub_ref]` của
  `benchmark/hb/instances.csv`; 8/9 bằng đúng `ab_lb_ref` (pores_1 6=6, bcspwr03 39=39,
  impcol_b 8=8), riêng bcsstk01 chứng minh được 9 > `ab_lb_ref=8` (vẫn ≤ `ab_ub_ref=22`).
- Nhưng độ phủ là **12/24**, và ranh giới là cấu trúc chứ không ngẫu nhiên: `n ≥ 420` ⟹ `MO`
  12/12. Nguyên nhân là số hạng `n·C(n,2)` (ràng buộc hoán vị) cộng `2m·Σ(n-d)`, tức `Θ(n³ + mkn)`
  — không phải tham số chọn được.
- Vì vậy **giữ nguyên config là quyết định đúng**, miễn là paper viết đúng phạm vi và đúng bản chất
  `MO`. Đổi `amo_encoding` không có tác dụng (order bỏ AMO); đổi sang `pairwise` (ABP) làm CNF to
  hơn.

### 5.2 Hai phương án

**Phương án A — Giữ config, ghi limitation (khuyến nghị).**

- Nội dung: RQ3 báo cáo SAT trên 12/24 instance (`n ≤ 118`); 12 instance `n ≥ 420` ghi `MO` +
  `error=MemoryError`, kèm (i) kích thước CNF dự kiến tại `k=1` và `k=lb_ref`, (ii) tuyên bố rõ
  không có `peak_memory` nên không khẳng định chạm cap, (iii) so sánh chéo với 4 method còn lại
  (đã có đủ 24/24 run cho `cp_sat`, `cplex_cp`, `cplex_mip`, `gurobi_mip` trong `[runs]`).
- Chi phí: **0 giờ máy, 0 dòng code.** Chỉ sửa văn bản (P1).
- Rủi ro: reviewer có thể nói baseline SAT thiếu nửa bộ dữ liệu. Nhưng đó là sự thật đã đo, và
  thiếu minh bạch sẽ tệ hơn.
- Điều kiện đi kèm: phải viết đúng §3.5, nếu không phần Limitations sẽ tự mâu thuẫn với cột
  `status=MO`.

**Phương án B — Chạy lại 12 instance `MO` với cấu hình khác.**

- Bắt buộc làm trước: sửa exporter để `MemoryError` vẫn giữ `metadata.probes` + `peak_memory` tạm
  tính (`src/sat/solve.py`, `src/runner/worker.py`, `src/runner/runner.py`), và ghi `search_mode`.
  Không sửa trước thì run mới lặp lại đúng record không dùng được — tức chi phí máy bỏ đi.
- Sau đó mới chọn cấu hình. Các lựa chọn trong phạm vi codebase hiện tại **đều không cứu được**:
  tăng `memory_limit` bị chặn bởi host (protocol §6.3: 15.0 GiB vật lý, cap 12.0 GiB để chừa
  3.21 GiB); `pairwise` nhiều clause hơn `order`; `seqcounter` vô hiệu với `order`. Muốn khác thật
  thì phải thêm một formulation mới (ví dụ bỏ nhóm hoán vị `n·C(n,2)` bằng cách encode assignment
  khác) — việc này là thay đổi methodology, cần spec + test + review chéo + freeze lại.
- Chi phí tối thiểu: 12 run × 1800 s = **6.0 giờ máy** (chưa kể encode có thể chiếm phần lớn), cộng
  công implement/validate formulation mới, cộng một vòng freeze mới. Rủi ro: vẫn `MO`, vì trần
  là `Θ(n³)` của chính ràng buộc hoán vị, không phải hằng số cấu hình.
- Rủi ro học thuật: đổi formulation ở thời điểm này làm lệch bộ kết quả đã có (120 run) và có thể
  buộc chạy lại cả 4 method còn lại nếu muốn so sánh công bằng.

**Khuyến nghị:** chọn A. Chỉ cân nhắc B nếu paper bị yêu cầu baseline SAT đủ 24 instance — và khi
đó, B phải bắt đầu bằng việc sửa exporter, không phải bằng việc chạy lại.

### 5.3 Việc không thuộc P2

- Sửa exporter (`peak_memory` trước khi raise, `search_mode`, giữ `metadata` khi lỗi): P3.
- Chốt budget pilot 60 s vs 1800 s và review protocol: P1.
- Quyết định có mở issue dữ liệu cho 12 dòng `MO` hay chấp nhận limitation: P1 + P3.
