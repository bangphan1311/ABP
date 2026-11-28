# 01: Đặc tả ABP cho SAT (`docs/sat_spec.md`)

**Tuần:** W1 · **Owner:** P2 (Quang) · **Status:** ready-for-human

**What to build:** Tài liệu đặc tả đủ rõ để code encoding và kiểm chứng. Không code.

**Blocked by:** None (can start immediately)

- [x] Định nghĩa decision problem: với K, tồn tại hoán vị nhãn f sao cho mọi cạnh (u,v) có |f(u) − f(v)| ≥ K. (evidence: `docs/sat_spec.md`)
- [x] Liệt kê biến SAT và ý nghĩa; ràng buộc assignment/permutation; ràng buộc khoảng cách; ngưỡng K. (evidence: `docs/sat_spec.md`)
- [x] Định nghĩa SAT / UNSAT và cách decode model thành labeling. (evidence: `src/sat/pairwise.py`)
- [x] Chiến lược K-search: cận dưới tầm thường hoặc heuristic; SAT → decode, verify, B thực tế, K ← B+1; UNSAT → B tối ưu; ub do P1/P2 tính. (evidence: `src/sat/solve.py`)
- [x] Ghi rõ không bê hướng tìm kiếm của 2DBMP. (evidence: `docs/sat_spec.md`)
- [x] Độ dài 1–2 trang. (evidence: `docs/sat_spec.md`)
