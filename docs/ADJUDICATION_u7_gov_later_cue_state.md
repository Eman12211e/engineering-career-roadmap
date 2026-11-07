# Adjudication record: `u7_gov_later_cue_state` (APPROVED by owner, 2026-11-07)

**Status:** approved by the owner on 2026-11-07. **Direction: engine-favoured** (the ruling
agrees with the engine's output). The sealed file is unchanged; its round-7 hash
(`3e34b01a…f12d`) still matches `docs/UNSEEN_SET.md`.

## The original labels

There are two un-indexed résumé mention labels for the canonical skill `CFD` on the same
résumé line, which contains two CFD mentions:
1. `line_contains: "No CFD experience yet"`, `status: negated`
2. `line_contains: "currently studying flow simula"`, `status: hypothetical`

## The two evaluation results

| Checker | Result |
|---|---|
| Before the fix: first mention only (`ea497f2`) | Label 1 is checked against the 1st mention (negated, which passes). Label 2 is also checked against the 1st mention and reported as negated (a false failure). |
| After the fix: un-indexed means every occurrence (`fa1555e`) | Label 1 claims both mentions: the 2nd is hypothetical, so it fails. Label 2 resolves to a mention already claimed, so it is a duplicate. |

## What the engine actually returns

Checked directly with the engine:
- 1st mention, `"CFD"`: **negated**
- 2nd mention, `"flow simulation"`: **hypothetical**
- CFD is not found, which matches the expected `found` set.

No critical error.

## Proposed interpretation

The author wrote one label per mention but had no `occurrence` field to say which, because
it did not exist at sealing time. The proposed reading is:
- label 1 = occurrence 1, negated;
- label 2 = occurrence 2 (span text "flow simulation"), hypothetical.

**Rationale:** each label's `line_contains` text sits next to a different mention, and the
author's `critical_traps` require only that CFD is never found. Under this reading the
engine matches both labels, and the pair has no failure other than its unrelated status
counts.

## Approved interpretation

- Occurrence 1, `"CFD"`: **negated**
- Occurrence 2, `"flow simulation"`: **hypothetical**

## Objective evidence

Each label's `line_contains` text sits next to a different mention. The `occurrence` field
did not exist when the set was sealed. The author's `critical_traps` require only that CFD is
never found, and the engine meets that.

## Impact on reported results

The round-7 retrospective is reported twice: with the original labels (10/12 exact), and with
the adjudicated labels. With the adjudicated labels this pair passes, and
`u7_cue_bound_preferred` is the remaining miss, now fixed on `fix/comma-lists`.

The sealed file is unchanged; its hash `3e34b01a…f12d` is intact.
