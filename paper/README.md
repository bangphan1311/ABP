# Paper workspace — P1 section handoff

**Repository review date:** 2026-11-17  
**Reviewed refs:** `p1/w3-experimental-protocol-rc` at current head; P2 SAT handoff reviewed from `p2/w4-sat`.

## Manuscript inventory

The repository still has no integrated master manuscript (no master `main.tex`/document root was found). It now contains modular P1 and P2 section drafts. The team may have a separate manuscript outside this repository; it was not available in the reviewed Git tree.

Do not describe those sections as reviewed or complete. When the master manuscript is added, integrate the modular sections below and check terminology, notation, citation style, section numbering, and cross-references against it.

## Modular material prepared

- `p1_intro_background_related_work.tex`: modular P1 contributions for Introduction, Problem Background, and Related Work; integrate with the full manuscript and team-wide research framing.
- `p1_exact_methodology.tex`: paper-ready description of the four implemented Exact backends, common model semantics, verification, bounds, and result statuses.
- `p1_exact_experimental_setup.tex`: Exact-only experimental setup plus the P1 candidate environment snapshot and unresolved environment/host confirmations.
- `docs/p1/exact-methodology-review.md`: code/documentation audit with open Exact status, extraction, configuration-warning, environment, and license items; no solver experiment was run for this review.
- `p1_references.bib`: bibliographic entries cited by the P1 sections.
- `p2_sat_methodology.tex`: SAT decision formulation, pairwise/order encodings, AMO variants, K-search, verification, and explicitly labelled W3 pilot results.
- `p2_sat_appendix.tex`: proof sketches for encoding equivalence and K-search completeness; no independent UNSAT certificate is claimed.

These files are modular section drafts, not a complete paper. The SAT pilot table uses the committed 10-instance synthetic W3 pilot (60 s/run); it is not the official 24-instance Harwell–Boeing RQ3 result. No official RQ3 outcome is asserted. The Exact Experimental Setup covers only P1-owned Exact methods and candidate environment details; P3 must confirm official queue/host/resource operations. **No W5/W6 final analysis, integrated manuscript, or sign-off is claimed**; official data validation, final figures, captions, cross-review, and final reporting remain open.

## Ownership boundary

P1 owns the Exact formulations and their correctness review, the Exact-side environment/solver entitlement record, the Exact portion of Experimental Setup, the predeclared Exact spot-check, and technical interpretation of RQ3.

P3 remains responsible for the official benchmark queue, official host/resource enforcement and run accounting, raw-result export, and production of the official figures/tables. The Exact environment values below are P1's candidate snapshot and must be reconciled with P3 before the protocol is frozen.
