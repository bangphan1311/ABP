# Paper workspace — P1 section handoff

**Repository review date:** 2026-11-06  
**Reviewed refs:** `main` at `276c6c0`; P1 branch at `ec211ab`

## Manuscript inventory

At the review snapshot, the repository contains no manuscript source: `paper/` contains only `.gitkeep` on both `main` and the P1 branch. In particular, no existing Introduction, Background, or Related Work sections were found to review or edit. The team may have a separate manuscript outside this repository; it was not available in the reviewed Git tree.

Do not describe those sections as reviewed or complete. When the master manuscript is added, integrate the P1 sections below and check terminology, notation, citation style, and section numbering against it.

## P1 material prepared

- `p1_intro_background_related_work.tex`: modular P1 contributions for Introduction, Problem Background, and Related Work; integrate with the full manuscript and team-wide research framing.
- `p1_exact_methodology.tex`: paper-ready description of the four implemented Exact backends, common model semantics, verification, bounds, and result statuses.
- `p1_exact_experimental_setup.tex`: Exact-only experimental setup plus the P1 candidate environment snapshot and unresolved environment/host confirmations.
- `docs/p1/exact-methodology-review.md`: code/documentation audit with open Exact status, extraction, configuration-warning, environment, and license items; no solver experiment was run for this review.
- `p1_references.bib`: bibliographic entries cited by the P1 sections.

These files are modular section drafts, not a complete paper. The Introduction/Background/Related Work file contains only P1-supported passages and does not complete the team-wide sections. The Exact Experimental Setup covers only P1-owned Exact methods and candidate environment details; P3 must confirm official queue/host/resource operations. The RQ3 analysis-plan document is planning material only. **No W5 or W6 execution or completion is claimed**; result validation, official analysis, figures, and final reporting remain future work.

## Ownership boundary

P1 owns the Exact formulations and their correctness review, the Exact-side environment/solver entitlement record, the Exact portion of Experimental Setup, the predeclared Exact spot-check, and technical interpretation of RQ3.

P3 remains responsible for the official benchmark queue, official host/resource enforcement and run accounting, raw-result export, and production of the official figures/tables. The Exact environment values below are P1's candidate snapshot and must be reconciled with P3 before the protocol is frozen.
