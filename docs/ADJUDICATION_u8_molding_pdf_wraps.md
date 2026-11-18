# Adjudication record: `u8_molding_pdf_wraps` (APPROVED by owner, 2026-11-07)

**Direction:** engine-favoured. The ruling agrees with the engine's output.

## The original label

Evidence label: `canonical: Lean Manufacturing`,
`posting_line_contains: "supports injection molding cells"`, `requirement: unscored`.

## Approved interpretation

The label is an erroneous evidence-line label. The supported evidence line is
"3. Lead 5S and kaizen activities on second shift.", which is the engine's output.

## Objective evidence

- The aliases of Lean Manufacturing are `lean manufacturing`, `lean principles`, `kaizen` and
  `5S` (`data/keywords.json`, unchanged since the round-8 seal).
- The labelled line, "The Associate Process Engineer supports injection molding cells",
  contains none of them. No span on that line can satisfy the R2.3 offset invariant, so no
  engine could satisfy the label.
- The fixture's own mention labels mark occurrences 1 and 2 on the "Lead 5S and kaizen" line
  as affirmed.
- Coordinator check, run after the review: there is exactly one posting line with a Lean
  alias, and it is the 5S/kaizen line.

## Impact on reported results

Round 8 (now retrospective) is reported twice:
- with the original labels: 11/12 exact, with 1 critical-class evidence miss;
- with the adjudicated label: 12/12 exact and 0 critical.

The sealed file is unchanged; the round-8 combined hash `5b30627c…8c27` is intact.
