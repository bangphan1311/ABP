# ABP – Phần SAT & Encoding (P2 – Quang)

Nguồn: `Tong quat.md`, `WORK BREAKDOWN.md`, `Quang.md`.
Trạng thái: **DRAFT – chờ duyệt granularity và blocking edges trước khi làm.**

Quy ước:
- Mỗi ticket = một file trong `issues/`, đánh số theo thứ tự phụ thuộc (blocker trước).
- Status `ready-for-human` = Quang làm. Owner cố định: P2.
- Ticket external (cần P1/P3) ghi rõ trong "Blocked by".

## Mốc

| Mốc | Thời điểm | Ý nghĩa với P2 |
|---|---|---|
| G1 | Cuối W1 | Một encoding chạy CaDiCaL, verify, khớp oracle |
| M1 | Cuối W2 | Core SAT xong; GO/NO-GO Bonus |
| G2 | Cuối W3 | Pilot xong; đề xuất canonical config |
| M2 | Giữa W4 | Freeze `v1.0` |
| G3 | Cuối W4 | ≥ 80% run Core, RQ1/RQ2 nháp |
| G4 | Cuối W5 | RQ1/RQ2 final; paper v0.9 |
| M3 | Cuối W6 | Technical sign-off; nộp trước deadline 2 ngày |

## Bảng ticket

| # | Tuần | Ticket | Blocked by |
|---|---|---|---|
| 01 | W1 | SAT spec (decision problem, biến, K-search) | None |
| 02 | W1 | Kiểm chứng tooling PySAT/Kissat | None |
| 03 | W1 | SatBackend + CaDiCaL | 01 |
| 04 | W1 | Pairwise encoding | 01, 03 |
| 05 | W1 | Order encoding (stretch → W2) | 01, 03 |
| 06 | W1 | Loader + generator toy tối thiểu | 01 |
| 07 | W1 | G1 – prototype khớp oracle | 02, 04, 06 |
| 08 | W2 | AMO pairwise + sequential counter | 04 |
| 09 | W2 | Glucose + Kissat qua SatBackend | 02, 03 |
| 10 | W2 | Multi-run K search | 04, 08, 09 |
| 11 | W2 | Loader + generator hoàn chỉnh (Tier 0/1) | 06 |
| 12 | W2 | Test matrix encoding × AMO × backend | 05, 08, 09, 10, 11 |
| 13 | W2 | Review formulation exact (P1) | 12 (ext: P1 formulation) |
| 14 | W2 | Nháp SAT methodology (paper §3) | 10 |
| 15 | W2 | M1 – GO/NO-GO Bonus + review dry-run | 12, 13 |
| 16 | W3 | Pilot RQ1 | 11, 12 |
| 17 | W3 | Pilot RQ2 | 12 |
| 18 | W3 | Đề xuất canonical SAT config | 16, 17 |
| 19 | W3 | Correctness suite cuối + appendix nháp | 12, 18 |
| 20 | W3 | Prototype Bonus SAT (chỉ khi GO) | 15 |
| 21 | W4 | M2 – Freeze v1.0 SAT | 18, 19 |
| 22 | W4 | Trực lỗi SAT khi official run | 21 |
| 23 | W4 | Nháp phân tích RQ1/RQ2 + G3 | 21 |
| 24 | W5 | RQ1 final | 23 (ext: data-final P3) |
| 25 | W5 | RQ2 final | 23 |
| 26 | W5 | Cross-review P1 + nhất quán code ↔ spec ↔ paper | 24, 25 |
| 27 | W5 | Paper v0.9 phần SAT | 24, 25, 26 |
| 28 | W6 | Proofread kỹ thuật thuật ngữ SAT | 27 |
| 29 | W6 | Claim verification + appendix final | 28 |
| 30 | W6 | Đọc chéo phần P3 + final LaTeX review | 28 |
| 31 | W6 | M3 – technical sign-off | 29, 30 |

## Frontier W1

Bắt đầu ngay: **01, 02**. Sau 01: **03, 06**. Sau 03: **04, 05, 09**.

## Cắt khi chậm (theo WORK BREAKDOWN)

Staircase → commander/product AMO → binary search theo K → Bonus. Không cắt: pairwise, order, correctness, RQ1/RQ2, tái lập.
