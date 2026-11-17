# Humanize report v2: docs/sat_tooling.md

Skill: humanizer, file mode. Language: Vietnamese.

Backup of the input: `docs/handoff/sat-tooling/sat_tooling.v2.before.md`.

## Result

PASS. One edit, prose only. All numbers, code spans, file names, solver names, headings, table rows and the "chưa kiểm" items are unchanged.

## Edit made

- Line 71: "AMO thực sự là bound=1." → "AMO là bound=1." The word "thực sự" was emphasis only. The claim is the same.

## Patterns checked

Scanned the full text (108 lines, 9 tables) against the humanizer catalog.

- §1 Not X but Y: none found.
- §2 Closers and fragments: none found. Section endings state a conclusion or a limit.
- §3 Deep-sounding sayings: none found.
- §4 Staged run-up: none found. The opening line is a scope statement, kept because it sets what the reader can trust.
- §5 Arguing with no one: none found.
- §6 Forced triads: none found. Lists match the number of items in the source.
- §7 Repeated openings: none found.
- §8 Em or en dashes: none in prose (checked). Hyphens remain only in code and paths.
- §9 Stacked qualifiers: none found. The "chưa kiểm" markers are verification status and are kept.
- §10 to §11: none found in prose.
- §12 to §18 (AI words, inflation, sales language, borrowed authority): none found.
- §19 Bold decoration: none found in prose.
- §20 Decorative headings and rules: none found. Headings are sentence-style and descriptive.
- §21 Curly quotes: none found. Straight quotes are used.
- §22 Chatbot residue: none found.
- §23 Knowledge-limit guesses: none found. Unverified items are stated as "chưa kiểm" with the reason.
- §24 to §26: none found.
- §25 Writing about the document: the line pointing to `docs/handoff/sat-tooling/evidence.md` is a source credit, kept. The line stating how each claim was verified is a caveat about trust, kept.

## Remaining patterns

None that justify an edit. Two notes for the author, not changed:

- The "Kết luận về Kissat" section repeats the "Không đưa Kissat vào W1" decision from the Kissat section. This is a deliberate summary, so it is kept.
- Several sentences are terse fragments ("Không cần đưa vào W1."). They are technical status lines, not AI rhythm, so they are kept.

## Verification

Method: regex extraction from the before file and the after file, then set comparison.

| Item | Before | After | Match |
|---|---|---|---|
| Numbers (incl. versions, timings, counts) | 184 | 184 | yes |
| Code spans (backtick) | 171 | 171 | yes |
| File names (`.md`, `.py`, `.txt`, `.json`) | evidence.md, requirements.txt | same | yes |
| Solver names | same set | same set | yes |
| Heading lines | same | same | yes |
| Table separators | 9 | 9 | yes |
| Line count | 108 | 108 | yes |
| Em or en dashes in output | n/a | 0 | yes |

Result: ALL PRESERVED.
