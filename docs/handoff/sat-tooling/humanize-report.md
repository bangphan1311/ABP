# Humanize report: docs/sat_tooling.md (issue #9)

Mode: humanizer, file mode. Prose only. Original saved at `docs/handoff/sat-tooling/sat_tooling.before.md`.

## Result

PASS. All numbers, code spans, and paths match. Line count is unchanged (149). Every `chưa kiểm` marker is kept (7 before, 7 after).

## Edits made

- Dash rule: `` `E0`–`E4` `` (en dash in prose) became `` `E0` đến `E4` ``. No em or en dashes remain in the file.
- Decorative bold removed from 14 prose spots: list labels (`Không dùng được`, `Binary Kissat ngoài`, `Upstream`, `PySAT Kissat không có`, `Không có asset Windows`, `Không hỗ trợ`, and similar), emphasis (`không` in the `SatBackend("kissat")` note, `chưa kiểm` in the intro, `chưa đo trong W1` in section 8), and the status line in section 7. Bold markers in the file: 0.
- No sentences, claims, or facts were added or removed. No chatbot residue, staged openers, closers, or forced triads were present.

## Remaining patterns (not changed)

- Repeated negative openers in the Kissat and assumptions lists (`Không ... không ...`). These state separate facts, one per bullet. Kept.
- `thay vì` contrast in section 6 (`native` encoding raises `ValueError` instead of dropping the constraint). It carries information. Kept.
- Repeated `chưa kiểm` and `(chưa kiểm)` markers. The task requires them. Kept.
- Parenthetical `Đây là suy luận, chưa kiểm.` in section 8. Required disclosure. Kept.
- Hyphenated compounds such as `wall-clock` and `pairwise`. Hyphens are not dashes under the rule. Kept.

## Verification

Method: extract from the before and after files with regex, compare sets.

- Numbers (`\d+(?:[.,]\d+)*`, with counts): identical sets. Includes `3.11.15`, `1.9.dev15`, `-1073741819`, `0.314`, `0.360`, `0.3`, `0.06`, `0.2`.
- Code spans (`` `...` ``, 288 total before and after): identical sets.
- Paths (`word/word` or `word\word` patterns): identical sets.
- Table rows, headings, and list structure: unchanged. Line count 149 before and after.
- Dashes: 0 em/en dashes after. Bold: 0 after.

Note: the Vietnamese text changed only in the places listed above. The `đến` replacement is the only new word added to the file.

## Verdict

PASS.
