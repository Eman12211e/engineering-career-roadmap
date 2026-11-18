> **SUPERSEDED / STALE (2026-11-13).** Kept as the record behind `CONTRACT_V4_LINE_RULE.md` revision 3, which replaces it. See `README.md` in this folder.

# Test-migration proposal for Revision 5A (needs owner approval; nothing changed yet)

Status: PROPOSED, 2026-11-10.

## Scope
- **No test file is edited until the owner approves each item below.**
- No gold label, fixture, or `DISPUTED.json` entry changes.
- No xfail, skip or blanket exemption is added.

## Why tests fail
In the in-memory simulation of v4 on the current suite, 3 tests fail: 367 passed, 3 failed.
Every failure comes from a historical case where the engine now abstains (`uncertain`), not
from a wrong decision.

## M1. `tests/test_fixtures.py::test_fixture[regression_r6-u6_bigco_basic_desired]` (locked fixture)
- **Why it fails.** The fixture has two résumé mentions that become `uncertain`:
  - SPC, on "without added headcount by applying statistical process control";
  - APQP, on "never missed a customer PPAP date".

  SPC therefore leaves the `found` set. APQP stays found through an earlier, independent
  mention. `check_fixture` reports 3 failures: the found set and 2 mention labels.
- **Current assertion.** `r["fails"] == []`.
- **Proposed change.**
  1. `check_fixture` gains a third result list, `abstained`, alongside `fails`.
     - A label whose engine state is `uncertain` goes to `abstained`, never to `fails` and
       never to a pass count.
     - A gold-`found` skill that resolves to `uncertain` or `contradicted` is recorded in
       `abstained`. It is not counted as a found-set mismatch.
     - Every other mismatch still goes to `fails`.
  2. A new coordinator-owned file, `tests/fixtures/ABSTENTIONS_5A.json`, lists every
     approved historical abstention, one entry per label. Each entry has the fixture, doc,
     canonical name, `line_contains`, original gold status, the U-rule that fired, and
     `"approved": "<owner, date>"`.
  3. The test asserts all of the following:
     - `r["fails"] == []`;
     - `r["abstained"]` equals exactly the entries for this fixture in
       `ABSTENTIONS_5A.json`. An extra abstention fails, and so does a missing one;
     - every listed entry's gold status is unchanged in the fixture.
  4. A new test prints the full abstention list with "usefulness loss" counts on every run,
     and asserts that the count equals the file's length.
- **Why this is not an exemption.**
  - The fixture still fails on any wrong decision, and on any abstention that is not listed.
  - The file is an exact, reported list of usefulness losses, approved one entry at a time.
  - It is never a pass.
- **Initial `ABSTENTIONS_5A.json` content (2 entries, both in `u6_bigco_basic_desired`):**
  - SPC, gold `affirmed`, rule U1 ("without");
  - APQP, gold `affirmed`, rule U1 ("never").

  Retrospective rounds r7 and r8 are not pytest fixtures. Their 5 losses are reported by the
  evaluation script, not listed here.

## M2. `tests/test_stage4_scope.py::test_r31_minimal_pairs[Without rework by applying SPC]`
- **Current assertion.** `{"Statistical Process Control": "affirmed"}`. This encodes R3.1.3,
  which was owner-frozen.
- **Proposed change.** Make the expected value `{"Statistical Process Control":
  "uncertain"}` and add an inline comment: "R5A amendment of R3.1.3 (owner-approved
  <date>): a non-binding negation cue makes the mention uncertain, never affirmed or
  negated."
- **Companion guard (new, same file).** "Reduced rework by applying SPC" is `affirmed`. This
  checks that removing the cue restores the decision.

## M3. `tests/test_stage4_scope.py::test_negation_keeps_the_gap_rule_and_does_not_spread`
- **Current assertions.**
  1. "No experience with FEA or CFD": FEA `negated`. Still passes.
  2. "No rework using SPC": SPC `affirmed`. **Fails** (now `uncertain`).
  3. "Never missed a deadline in SolidWorks": SolidWorks `affirmed`. **Fails** (now
     `uncertain`).
- **Proposed change.**
  - Keep assertion 1 unchanged.
  - Change assertions 2 and 3 to `== "uncertain"`.
  - Add `!= "negated"` alongside them, to keep the original intent: negation still does not
    *spread* as a decided negation.
  - Rename the test to `test_negation_gap_rule_and_non_binding_cues_abstain`.

## What the owner approves
Each item is approved or rejected separately: M1 with its 2 abstention entries, M2, and M3.
- If **M1 is rejected:** U1 cannot follow D2 without a locked failure, and 5A stops.
- If **M2 or M3 is rejected:** R3.1.3 stays in force, and U1 must not fire on non-binding
  "no", "never" or "without". That conflicts with D2.
