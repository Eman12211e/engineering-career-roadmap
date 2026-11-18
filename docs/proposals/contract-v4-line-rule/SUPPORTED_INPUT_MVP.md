> **SUPERSEDED / STALE (2026-11-13).** Kept as the record behind `CONTRACT_V4_LINE_RULE.md` revision 3, which replaces it. See `README.md` in this folder.

# Supported-input MVP: contract proposal and feasibility study

- **Date:** 2026-11-10.
- **Status:** PROPOSED, read-only study. Nothing has been implemented, and no labels or sets
  have changed.
- **Branches:** `upgrade/review-revisions` @ `fa1555e` (green), unchanged. `fix/comma-lists`
  @ `3a24d1b`, unmerged.
- **Supersedes:** the general-negation-heuristic track of Revision 5A, which the owner stopped
  on 2026-11-10.
- **Simulation scripts (scratchpad):** `sim_restricted.py`, `sim_restricted_b.py` and
  `probe_restricted.py`. They are in-memory approximations, not an implementation.

## 1. Principle

The engine counts a résumé skill as present only when it appears in a **supported form**.
Everything else is **unresolved**:
- never counted as present;
- never counted as absent;
- never folded into an ordinary numeric score.

A score is produced only when every required or preferred skill is decided from supported
evidence, or is missing outright.

## 2. Supported résumé evidence

### 2.1 Recognised sections
These come from the existing `data/match_rules.json` résumé headings:
- **Skills:** `skills`, `technical skills`, `key skills`, `core competencies`, `tools`,
  `technologies`, `skills and tools`.
- **Experience:** `experience`, `work experience`, `professional experience`,
  `employment history`, `projects`, `relevant experience`, `engineering experience`.
- **Excluded:** `references`, `interests`, `hobbies`. These never give evidence.

**Entry lines.** An unrecognised heading-like line inside a Skills or Experience section
doesn't end that section if it looks like a job or education entry: it contains a year, a
`|`, a "City, ST" pattern, or a "Title, Company" pattern. Any other unrecognised heading
starts an unknown section. Unknown sections include Summary, Education, Certifications and
Training.

### 2.2 Cue vocabulary
Text is normalised first: curly apostrophes become straight ones.

A cue is any of:
- a word from the `negation` or `hypothetical` data lists;
- one of these words: nor, neither, unfamiliar, except, other than, apart from, excluding,
  everything/anything/all but, in progress, enrolled, n/a, not used, zero, cannot, unable,
  yet to, lack, missing, gaps, pending, planned, expected, self-study, self-taught,
  pursuing, studying, learning, nope;
- any word ending in "n't";
- the digit "0" standing alone.

Cues inside a recognised skill's own span ("machine learning") or inside a hyphenated word
("no-code") don't count.

### 2.3 The two supported forms
A mention that the existing Stages 1–4 leave `affirmed` is **supported** only if one of these
forms holds.

**S1, Skills entry.** All of these must be true:
- the line is in a Skills section;
- the section heading contains no cue;
- the line contains no cue anywhere;
- the list item holding the skill, after an optional "Label:" prefix, is only the skill name
  plus optional level words (D1: basic, beginner, intermediate, advanced, proficient,
  expert, familiar, working knowledge, coursework, exposure, novice) and punctuation.

Items are split on `, ; | • ·`, " / ", "and" and "&". Anything else in the item makes it
unresolved, for example "GD&T (ASME Y14.5)" or "SolidWorks (academic only)".

**S2, Experience statement.** All of these must be true:
- the line is in an Experience or Projects section;
- the section heading contains no cue;
- the line contains no cue anywhere.

**Everything else** (another section, a cue anywhere on the line, or extra words in a Skills
item) is `unresolved`, with one of these reason codes:
- `section_unknown`
- `cue_in_line`
- `heading_cue`
- `skills_item_extra`

The existing `negated` and `hypothetical` results stay decided wherever they occur.

### 2.4 Document-level safeguards (condition 3)
Each flag withholds the numeric score for the whole pair when at least one required or
preferred skill exists. The flags are listed by name in the result.

| Flag | Fires when | Example |
|---|---|---|
| `backref_negation` | A sentence with no recognised skill contains a negation cue, and either points back (it, them, this, that, these, those, either, neither, one, any of, the other, by me) or is 4 words or fewer. | "Skills: SolidWorks" … "Never used it professionally." / "Not yet used professionally" / "Nope." |
| `unscoped_disclaimer` | A line with no recognised skill contains a negation cue and a possession word (experience, used, familiar, knowledge, worked, exposure, proficient, trained, skills, background, hands-on). | Summary "No professional CAD experience yet" + Skills "SolidWorks" |
| `heading_cue_section` | Any section heading contains a cue. | "Skills I lack", "Currently learning", "Missing skills", "Areas for growth" |
| `refused_F1/F2/F3` | Format refusal: paragraph-only résumé, fragmented layout, or non-English (the v3 rules). | — |

**A pronoun is never resolved to a skill.** Its effect is to withhold the whole score, so a
cross-line disclaimer can't produce a confident number.

## 3. Supported job-posting structures

- **Unchanged from `fa1555e`:** required and preferred come only from a recognised Required
  or Preferred section, or from an explicitly bound inline cue (R2.4/R4.4 as on the
  integration branch).
- **Unavailable:** a posting with no required or preferred skill gives `unavailable` (F4)
  with a reason.
- **Refusal:** a posting refused by F1–F3 gives `withheld`.
- **Known posting-side risk:** a postfix cue across an unknown list item ("SolidWorks, Creo
  or any other parametric CAD package preferred") keeps the section's importance. R4.8
  remains proposed and unapproved, and isn't adopted here. This is an importance error,
  not a résumé false affirmation.

## 4. Result schema and score behaviour (condition 2)

### 4.1 Skill state
Each skill gets a state per pair. The first matching row applies.

| Order | Mentions of the skill | State |
|---|---|---|
| 1 | The document is refused or carries a document-level flag | `withheld_document` (the skill itself keeps its row below, for display) |
| 2 | At least one supported `affirmed` mention and at least one `negated` mention | `contradicted` |
| 3 | At least one supported `affirmed` mention | `found` |
| 4 | At least one `unresolved` mention, and no supported `affirmed` mention | `unresolved` (never `missing`) |
| 5 | Only `negated` mentions | `negated` |
| 6 | Only `hypothetical` mentions (plus any `negated`) | `hypothetical` |
| 7 | No mention | `no_evidence` |

### 4.2 Score
- **Coverage score:** computed only when no required or preferred skill is `contradicted`
  or `unresolved`, no document is flagged or refused, and the posting is not
  `unavailable`.
- **What counts as absent:** `negated`, `hypothetical` and `no_evidence` count as not
  covered. `unresolved` never enters the numerator or the denominator; it withholds the
  score instead. This is enforced in `compute_coverage_score`'s caller, not only in labels.
- **Modes:** `scored`, `withheld` (with a list of reasons), `unavailable`.
- **Reasons:** fixed templates with the skill name and the code only, no résumé text.
  Unresolved skills carry spans, not line snippets.

### 4.3 Bullet contract (unchanged, plus D12)
- **Unchanged:** `BulletEvidence` comes only from text the user types.
- **Flagged bullets are blocked:** a bullet with a non-empty `split_claims(...)[0]` can't be
  added, copied or exported. The PDF export re-checks with the same function at
  `app.py:178`.
- **Confirmation is not evidence:** a skill state never becomes bullet evidence.

## 5. Acceptance matrix (coordinator-written; committed before code if authorised)

| # | Input | Expected |
|---|---|---|
| 1 | Skills "SolidWorks, Python" | both `found` (S1) |
| 2 | Skills "SQL (basic), Python" | both `found` (D1) |
| 3 | Skills "SolidWorks (learning), Python" | SolidWorks `unresolved`; Python not `found` |
| 4 | Skills "SolidWorks (in progress)" / "(planned)" / "(expected 2027)" / "- none" / "(academic only)" | `unresolved` |
| 5 | Skills "Tools I want to learn: SolidWorks" | `unresolved` |
| 6 | Experience "- Designed brackets in SolidWorks" | `found` (S2) |
| 7 | Experience "- Have not yet used SolidWorks" / "Python was not used" / "Haven’t used SolidWorks" (curly apostrophe) / "Cannot use Python" / "Have yet to use MATLAB" / "Unable to use Python" / "0 years of SQL experience" | `unresolved` or `negated`, never `found` |
| 8 | Experience "- Learning: PLC" / "MATLAB certification in progress" | `unresolved` |
| 9 | Experience "- Never used Creo, Foobar, SQL" | Creo `negated`; SQL `unresolved` |
| 10 | Experience "- Used every CAD tool except SolidWorks" | `unresolved` |
| 11 | Headings "Skills I lack" / "Areas for growth" / "Currently learning" / "Missing skills" | `unresolved` plus `heading_cue_section` |
| 12 | Skills "SolidWorks" + Experience "- Never used it professionally." | `withheld` (`backref_negation`) |
| 13 | Experience "- Designed brackets in SolidWorks" + "- Never touched it since 2019" | `withheld` (`backref_negation`) |
| 14 | Summary "No professional CAD experience yet" + Skills "SolidWorks" | `withheld` (`unscoped_disclaimer`) |
| 15 | Interests "- SolidWorks" | `unresolved`, never `found` |
| 16 | Posting requires PLC; résumé PLC only in Summary prose | `withheld`; PLC `unresolved` (never `no_evidence`) |
| 17 | Posting requires PLC; résumé never mentions PLC | `scored`; PLC `no_evidence` |
| 18 | Skills "SolidWorks" + Experience "- No SolidWorks certification" | `contradicted`, `withheld` |
| 19 | Posting without required or preferred structure | `unavailable` |
| 20 | Paragraph-only, table-fragment or non-English résumé | `withheld` (refused) |
| 21 | Look-alikes: skill-per-line, contact block, terse list, accented names, stacked job-entry lines | not refused |
| 22 | Metamorphic: rows 1, 6 and 9 with "Foobar" at the start, middle or end | never `found` where row is unresolved/negated |
| 23 | Privacy: every reason | template words only; no résumé text; nothing logged |
| 24 | PDF: a flagged bullet | absent from Copy-All, session state and PDF |

## 6. Coverage analysis (read-only simulation)

### 6.1 Historical fixtures (original gold labels; 200 résumé mention labels, 86 pairs)

| Set | Pairs | Pairs scored | Labels correct / incorrect / unresolved (loss) / unresolved (safe) | Critical false affirmations |
|---|---|---|---|---|
| postings (unit fixtures; 39 of 48 résumés have no headings) | 48 | 8 (17%) | 21 / 0 / 9 / 0 of 30 | 0 |
| regression_r6 (locked) | 14 | 4 (29%) | 24 / 0 / 28 / 0 of 52 | 0 |
| r7 (retrospective) | 12 | 4 (33%) | 42 / 2* / 24 / 0 of 68 | 0 |
| r8 (retrospective) | 12 | 3 (25%) | 26 / 0 / 16 / 8 of 50 | 0 |
| **Total** | **86** | **19 (22%)** | **113 / 2 / 77 / 8 of 200** | **0** |

\* Both r7 "incorrect" labels are the pre-existing `u7_gov_later_cue_state` CFD labels. The
owner adjudicated them engine-favoured on 2026-11-07. They are reported here with the
original labels, as required. With the adjudicated labels they are correct.

**Mention level (all sets).** Of 642 recognised résumé mentions:
- 281 supported `affirmed`;
- 261 `unresolved`;
- 48 `negated`;
- 52 `hypothetical`.

So of the mentions that Stages 1–4 would affirm, 51.8% are supported. On the realistic r6–r8
sets alone the figure is 54.6% (149 of 273).

**Why mentions are unresolved:**

| Cause | postings | r6 | r7 | r8 |
|---|---|---|---|---|
| `section_unknown` (no or unrecognised heading) | 129 | 11 | 5 | 1 |
| `cue_in_line` | 3 | 47 | 28 | 22 |
| `skills_item_extra` | 5 | 6 | 0 | 4 |

**Cue words behind `cue_in_line` (realistic sets).** These are mostly achievement phrasing
such as "zero defects", "no rework" and "without added headcount":
- "no": 35
- "zero": 19
- "never": 17
- "without": 17
- "not": 4
- "learning" / "studying": 5

**Comparison with the pre-5A engine on the same 200 labels:**
- correct falls from 190 to 113 (−77 useful labels);
- incorrect falls from 10 to 2;
- critical-class errors fall from 8 to 0;
- scored pairs fall from 86 to 19.

**Caveat on representativeness.** The historical sets are adversarial by design: almost
every résumé carries at least one deliberate trap line next to a required skill. So these
availability figures are probably a floor for real résumés, but this study can't measure
real-world availability. The owner's 15 realistic pairs are the first data that can.

### 6.2 Independent minimal pairs

40 items with 51 labels, written by an independent author. They have since been used for
analysis, so they are now development data. Each line was wrapped as an Experience bullet.

| Group | Correct | Unresolved (loss) | Unresolved (safe) | Incorrect | Critical | Not recognised |
|---|---|---|---|---|---|---|
| "zero" (30 labels) | 4 | 14 | 10 | 0 | **0** | 2 |
| back-reference (21 labels) | 1 | 9 | 9 + 1 ambiguous | 0 | **0** | 1 |

**Safety comes from conservatism.** Almost every line in these groups contains a cue, so
nearly everything is unresolved.

### 6.3 Safety probes (D9; 32 probes)

- **Probe set:** every v4-review leak (B2 list) plus the owner's cross-line examples.
- **Result:** no probe yields `found` for a disclaimed skill in a pair that would be scored.
- **Where "found" still appears, the pair is always withheld:** in 4 probes the skill state
  is still "found", but the document-level flag withholds the whole pair. These are the
  cross-line "Never used it professionally", "Not yet used professionally", the
  separate-line "Never touched it since 2019" and the Summary disclaimer.
- **One probe ("Familiar with: SolidWorks")** is `found` under D1, as intended.

## 7. Residual risks (how the restricted system could still count a disclaimed skill)

| # | Path | Status |
|---|---|---|
| RS1 | Cue vocabulary gaps: a disclaimer without any listed cue ("SolidWorks — only read about it", "SolidWorks (theory)", "SolidWorks: my teammate handled it") | **Open.** S1 catches extra words in a Skills item. S2 doesn't: an Experience line with no cue is supported. This is the main remaining critical path, and it needs probes in round 9. |
| RS2 | A cross-line disclaimer more than 4 words long, without a back-reference word and without a possession word ("Haven't touched CAD since school.") | `unscoped_disclaimer` needs a possession word, so this case is **open**. |
| RS3 | A disclaimer in another document section with no negation cue ("Interested in learning CAD tools" uses "learning", so it is caught; "Want to pick up CAD" is not) | **Open.** It is a vocabulary gap, as in RS1. |
| RS4 | Postings: a cue boundary across unknown items keeps the section's importance (R4.8 limitation) | **Open**, posting side. Importance is wrong, but no false possession results. |
| RS5 | Entry-line inheritance treats a real heading that has a year or comma ("Training, 2023") as Experience | **Open.** Probes are needed. |
| RS6 | Format detectors refuse valid terse or stacked résumés (v4 review M6) | The refusal is visible, but it costs usefulness. Look-alike probes are needed. |
| RS7 | The simulation's regexes differ from a real implementation | It needs the implementation, plus an independent review and round 9. |

**Consequence under D9.** RS1–RS3 are critical paths. Round 9 must probe them (D9), and any
hit blocks Gate 1. Unlike the general heuristics, the restriction narrows each of them to a
**cue-free sentence that still disclaims**, which is a much smaller target. But it doesn't
eliminate them.

## 8. Proposed minimum useful-coverage thresholds (set before any realistic data is seen)

These are measured on realistic data only: the owner's 15 pairs and the realistic part of
round 9. The adversarial historical sets are report-only. Safety gates are never relaxed.

| Family | Metric (numerator / denominator) | Proposed minimum |
|---|---|---|
| Safety | Critical false affirmations on scored output, across all probes | **= 0** (unchanged) |
| Supported share | Supported `affirmed` mentions / mentions that Stages 1–4 would affirm | ≥ 60% |
| Document eligibility | Résumés neither refused nor document-flagged / all résumés | ≥ 85% |
| Score availability | Pairs `scored` / pairs whose gold says scorable | ≥ 50% |
| Useful label coverage | `correct` / non-ambiguous résumé labels (unresolved counts as not correct) | ≥ 70% |
| Losses | Each correct → unresolved change | always listed |

**Rationale.** If the tool can't score at least half of ordinary, realistic pairs, it is
mostly a "can't score" screen. In that case the owner should decide whether the MVP is worth
shipping, rather than lower the bar.

**Feasibility verdict.** Safety looks achievable within the supported forms, apart from the
RS1–RS3 vocabulary gaps. Usefulness is **unproven**: the historical sets show 22% (all) or
29% (realistic sets) availability, but they are adversarial. The decisive measurement is the
owner's 15 realistic pairs.

## 9. Implementation estimate (not authorised)

**Five-stage engine: no interface changes.**
- The restriction is a new post-Stage-4 pass, a new module `engine/supported_input.py`
  (about 150 lines). It takes `(Section, Mention, status)` tuples and returns per-mention
  support and reason, plus document flags.
- `segment` keeps its signature. Entry-line inheritance is about 20 lines, either in that
  module or as a small `segment` post-pass.
- `_qualify` and `importance` are unchanged.

**`engine/job_match.py`**
- `SkillMatch` gets an additive field: `state`.
- `MatchResult` gets additive fields: `score_mode`, `reasons`, `doc_flags`.
- The score is computed only in `scored` mode, about 40 lines. Existing fields keep their
  meaning: `found` is `True` only for state `found`.

**Data and evaluation**
- `data/match_rules.json`: new `supported_input` keys (the cue additions, level words,
  back-reference and possession words, entry-line patterns).
- `scripts/evaluate_matching.py`: the four metric families plus the supported-share
  metrics, with intervals (about 100 lines).

**Tests**
- Existing tests: the in-memory simulation shows many current fixture assertions would
  change. Most labels that were `affirmed` become `unresolved` under S1/S2, about
  77 historical labels. These are **not** gold changes. A test migration in the
  `TEST_MIGRATION_5A` style would be required, and it is much larger: it is per-entry and
  listed, with 77 labels. It needs separate owner approval, which hasn't been requested.
- New tests: the acceptance matrix, about 60 tests.

**Bullet generator.** No change to `build_bullet` or `find_unsupported_claims`. D12 blocking
touches `ui/tab_resume.py` and `app.py`, about 30 lines.

**Total:** about 350 lines of code and about 60 tests, plus a large, listed test migration.
These are moderate changes, isolated to a new pass. The five-stage contracts and bullet
contracts stay intact.

## 10. Owner decisions requested

| # | Decision |
|---|---|
| SI-1 | Approve the supported-form definitions (§2) and document safeguards (§2.4) as the MVP scope. |
| SI-2 | Approve the thresholds in §8 before any realistic data is evaluated. |
| SI-3 | Should Education and Certifications be added as supported sections (S1-style lists only)? They are excluded now, which costs some coverage. |
| SI-4 | Accept the RS1–RS3 residual paths as mandatory round-9 probes (D9: any hit blocks Gate 1). |
| SI-5 | The feasibility gate: evaluate the MVP read-only on the owner's 15 realistic pairs once they are labelled, before authorising implementation, test migration or round 9. |
