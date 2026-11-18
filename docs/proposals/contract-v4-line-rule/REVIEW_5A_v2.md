> **SUPERSEDED / STALE (2026-11-13).** Kept as the record behind `CONTRACT_V4_LINE_RULE.md` revision 3, which replaces it. See `README.md` in this folder.

# Independent review of the Revision 5A contract v2

- **Reviewer:** Opus, read-only.
- **Date:** 2026-11-09.
- **Verdict:** NEEDS REVISION.
- **Repo state:** stayed at `fa1555e` with a clean tree; 370 tests passed. Sealed r7 and r8
  were not opened by the reviewer.

The v3 response to each finding is in the contract's review log.

## Blocking
- **B1. Q2 misses the documented comma-list risk.**
  - The engine's `_clause` ends at commas outside a fully known chain.
  - So "Never used X, Foobar, SQL" and "No PLC experience, proficient in SQL" leave SQL
    `affirmed`.
  - Q2 needs to reach across commas and end only at contrasts or `. ; ? !`.
  - It must not reuse `hypothetical_scope_ends`, because that ends at `:`.
- **B2. Rows 4 and 29 contradict the rules.** "Not proficient in MATLAB" is `affirmed` today,
  so Q2 would make it `uncertain`, not `negated`.
- **B3. LabVIEW isn't a recognised skill.** Rows 1, 12, 14 and 16 tested nothing.
- **B4. The locked impact was understated.** Three tests fail: the u6_bigco fixture,
  the stage-4 minimal pair "Without rework by applying SPC", and
  `test_negation_keeps_the_gap_rule_and_does_not_spread`.
  - These encode the owner-frozen rule R3.1.3.
  - D6 didn't cover unit tests or set-level assertions.
  - `check_fixture` doesn't assert the score.
- **B5. Round 9 as specified can only stop.**
  - The gate denominators fall below 20, so the gates come out INSUFFICIENT.
  - The deliberate residual-risk probes become critical errors.
  - Historical appropriate abstention was 0 of 6.

## Major
- **M1. Decided accuracy rewards abstention.** Moving a result from incorrect to abstained
  shrinks the denominator. The gate should be correct divided by all labels.
- **M2. Score availability** can exceed 100%, and is undefined on the historical sets.
- **M3. The coverage denominator** was ambiguous (posting labels can't abstain). The 97%
  claim was unverified. Ambiguous labels with no gold status didn't fit the matrix.
- **M4. The Q2 cue list omitted engine negation words:** lack of, lacking, lacks, neither,
  and n't forms.
- **M5. Q1 gaps:**
  - missing separators: em dash, `;`, `|`;
  - missing cues: "no", "still learning";
  - no separator at all;
  - "same item" undefined;
  - cues inside an alias.
- **M6. Skill-level resolution had gaps:**
  - hypothetical-only skills weren't covered;
  - negated plus uncertain gave `uncertain`, which would ask the user to confirm a skill the
    résumé denies.
- **M7. Score modes were underspecified:**
  - a refused document reads as "missing";
  - no precedence between modes;
  - a posting with no recognised required skills;
  - `scored_after_confirmation` wasn't listed;
  - `resume_line` exposed text unnecessarily.
- **M8. §5.3 only partly held:**
  - 5B test 2 tested a code path that doesn't exist;
  - the "imports" test misses session-state flow;
  - flagged bullets are only warnings and can still be exported (`ui/tab_resume.py:77-90`).
- **M9. Round-9 isolation:**
  - the baseline ran before the implementation was frozen;
  - the author had repo access;
  - the categories leaked cue phrasings.

## Minor
- **Wrong row reference:** the privacy row was mis-cited.
- **Scan provenance:** `r5a_scan2.py` still contained exclusions.
- **Row 21:** there was no channel to report a non-posting uncertain skill.
- **Row 17:** "CAD" isn't a recognised skill.
- **Unlisted residual risks:** except/but-exclusions, question form, trailing negation with
  no separator.
- **R1–R5 naming:** clashes with the design doc's rule names.
- **Hobbies sections:** they still count as evidence.
