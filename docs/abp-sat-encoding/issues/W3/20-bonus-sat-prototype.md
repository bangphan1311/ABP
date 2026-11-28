# 20: Prototype Bonus SAT (chỉ khi GO)

**Tuần:** W3 · **Owner:** P2 (Quang) · **Status:** ready-for-human · **Điều kiện:** ticket 15 = GO (đã NO-GO)

**What to build:** Staircase hoặc incremental ở mức prototype và test nhỏ.

**Blocked by:** 15

- [x] Prototype chạy trên test nhỏ.
- [x] Không kéo trễ pairwise/order/correctness.
- [x] Nếu NO-GO: bỏ ticket, ghi lý do.

## Closure evidence (2026-11-09)

Điều kiện mở ticket không thỏa: ticket 15 chốt **NO-GO Bonus** tại gate M1, nên
ticket này đóng mà không viết prototype (không có code/test Bonus trong repo).

- Box 1: không thực hiện — điều kiện `ticket 15 = GO` sai; xem
  `docs/abp-sat-encoding/issues/W2/15-m1-gate-bonus-decision.md` mục "Kết quả"
  (NO-GO, quyết định của customer tại gate M1).
- Box 2: Core `pairwise`/`order`/correctness hoàn tất đúng hạn (ticket 16–19);
  Bonus bị cắt trước, không tiêu compute của Core.
- Box 3: lý do NO-GO ghi tại ticket 15; Bonus bị cắt khỏi phạm vi W3/W4.
