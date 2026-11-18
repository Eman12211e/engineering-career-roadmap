> **SUPERSEDED / STALE (2026-11-13).** Kept as the record behind `CONTRACT_V4_LINE_RULE.md` revision 3, which replaces it. See `README.md` in this folder.

# Independent review of the Revision 5A contract v4, plus independent minimal-pair results

- **Date:** 2026-11-10.
- **Reviewer:** Opus, strictly read-only. It created no files, did not open the sealed sets or
  the minimal pairs, and left the repository at `fa1555e` with a clean working tree.
- **Verdict:** NEEDS REVISION.

## Blocking findings
- **B1. "yet" ends negation reach.**
  - "Have not yet used SolidWorks" and "Not yet proficient in MATLAB" both come out
    `affirmed`.
  - "however" and "though" written as asides leak the same way.
  - Removing "yet" costs nothing on the current test suite.
- **B2. Many critical false affirmations are left unlisted.**
  - **Negation after the skill:**
    - "Python was not used"
    - "SolidWorks, never touched it"
    - "SolidWorks experience: none"
  - **Curly apostrophes:** "Haven’t used SolidWorks"
  - **Cues missing from the lists:**
    - "Cannot use"
    - "Unable to use"
    - "Have yet to use"
    - "Skills I lack:"
    - gap headings such as "Missing skills:" and "Areas for growth:"
  - **Hypothetical cases come out as present:**
    - "Learning: PLC" (a frozen test asserts `affirmed` here)
    - "Currently learning: MATLAB"
    - "Python (learning) and MATLAB"
    - "MATLAB certification in progress"
  - **Back-reference (U4) gaps:** "I've never used it.", "Unfamiliar with it.", "Nope."
- **B3. §6.4 counts one occurrence per un-indexed label, while `check_fixture` counts
  every occurrence.**
  - The locked fixture loses 2 labels, not 1.
  - Corrected UA is about **91.5%, below the 92.0% floor**.
  - DC is about 92.5%, with 7 losses.

## Major findings
- **M1. The U4 disclosure is inaccurate.** The 4-word window already excluded "that".
  Restoring this/that/those costs nothing. The real fixture-informed parameters, the
  ≤2-word cap and the 4-word window, were not disclosed.
- **M2. Every historical gate is in-sample, and each was set after its prediction was
  known.**
  - UA sits exactly on the floor.
  - DC was lowered from 97% to 90% after 93% was predicted.
  - SA (89.5%) and AA (57%) would fail their round-9 bars, and both are report-only.
- **M3. Over-confidence goes unmeasured.** No metric penalises scoring a pair whose gold is
  `withheld`, or deciding a gold-`ambiguous` label. A "withheld recall" metric is needed.
- **M4. The uncertainty rules are inexact.**
  - It is unclear which interval applies.
  - The paired CI is about ±3 pts, not ±4–5.
  - McNemar is not a non-inferiority test.
  - The rule-of-three n is undefined.
  - "Inconclusive" is missing from the stopping rule.

  Gate on the lower bound of the paired difference against −3.
- **M5. The PDF helper uses `find_unsupported_claims`.** That flags informational
  ownership words ("led", "improved"), so clean bullets would be dropped from the PDF.
  Use `split_claims(...)[0]`. Builder-side problems are always empty today, and the flagged
  preview stays copyable.
- **M6. The F-rules refuse valid documents.**
  - terse English bullets → F3;
  - a terse English posting → F3;
  - stacked title/company/date lines plus a one-per-line skills list → F2.
  - v4 does not inline F1–F4.
- **M7. §3's claim that "affirmed is independent by construction" is false.** "SolidWorks:
  none" plus "Have not yet used SolidWorks" resolves to `found`.
- **M8. N7 (hobbies) is exempt by default,** which conflicts with D9.

## Minor findings
- **Row 17 (metamorphic) is false as written.**
- **U2–U4 are underspecified:** the separator sets, cue sets, sentence definition and "n't"
  are not pinned down.
- **Refused-document mode** has edge cases.
- **Where contradicted non-required skills are reported** is not stated.
- **TEST_MIGRATION M1 matching** for found-set records and contradictions is undefined.
- **M2/M3 losses are unreported.**
- **§6.1 header** mixes pairs and labels.
- **"Invented claim"** has no data source.

## ROUND9_SPEC inconsistencies with v4 (10 found)
- The probe set is still described as report-only, which contradicts D9.
- The stopping rule doesn't cover probes or "inconclusive".
- Reporting uses the old code names (Q1/Q2 instead of U1–U5).
- The statistics are missing.
- The probe list includes patterns v4 claims to close, and omits N3a, N1b, N8 and the B2
  patterns.
- The gold `score_mode` rule ignores §3 rows 2 and 4.
- There are only 6 look-alikes, so n < 20.
- The terse-bullet, stacked-header and terse-posting look-alikes are missing.
- `set` granularity (per pair or per label) is undefined.

## TEST_MIGRATION_5A.md
- It is not a blanket exemption. Each entry is approved one at a time, asserted by equality,
  and gold labels are untouched.
- Its failure claims are accurate.

## Independent minimal pairs (`minimal_pairs_zero_pronoun.json`)
- **Authorship:** 40 items with 51 labels, written by an independent agent that saw no rules
  or code.
- **Scoring:** coordinator, read-only, with the v4 simulation.
- **Status:** these pairs have now been used for analysis. They are development data, not
  unseen evidence.

| Variant | "zero" group: critical false affirmations / usefulness losses | Back-reference group: critical / losses | Suite failures | Historical UA (first-occurrence count) |
|---|---|---|---|---|
| v4 | 10 / 0 | 7 / 0 | 3 | 92.0% |
| v4 + "zero" | 2 / 4 | 7 / 0 | 7 | 90.5% |
| v4 + "zero" + broad U4 (any short skill-less negative sentence later in the line) | 2 / 5 | 0 / 9 | 14 | 86.5% |

**D10 evidence.**
- "zero" as a cue removes 8 of the 10 critical false affirmations. What remains:
  - "0 years of SQL experience" (a digit);
  - "FEA background: zero" (trailing, after other words).
- Its cost is that achievement phrasings ("zero defects using X") abstain.
- It drops historical UA below the floor.

**D13 evidence.** The narrow U4 misses 7 of 9 negated back-references. Every broader form
abstains on nearly every affirmed back-reference (9 of 10).
