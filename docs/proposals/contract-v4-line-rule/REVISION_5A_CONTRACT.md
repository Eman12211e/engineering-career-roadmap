> **SUPERSEDED / STALE (2026-11-13).** Kept as the record behind `CONTRACT_V4_LINE_RULE.md` revision 3, which replaces it. See `README.md` in this folder.

# Revision 5A: safety abstention contract, v4 (PROPOSED, not frozen, not authorised)

Date: 2026-11-10.

**What changed since v3:**
- The owner's 2026-11-10 decisions D6, D8–D12 are applied.
- Metrics are split into four families.
- The residual-risk closures (N1–N6) are added.
- Skill-level interaction is fully specified.
- PDF export is now covered.
- The test-migration proposal is in `TEST_MIGRATION_5A.md`.

**Base:** `upgrade/review-revisions` @ `fa1555e` (370 passed). It remains unchanged.

**Out of scope here:** Revision 5B is specified in §5 only.

## 0. Principle
When the text does not settle whether the résumé claims a skill, the engine abstains with a
non-sensitive reason. An abstention:
- is never a found skill;
- is never a correct outcome;
- is never a pass;
- is never silently "missing" inside a numeric score.

## 1. Preservation
1.1 **Nothing historical changes.** No fixture file, gold label, `DISPUTED.json` entry,
    approved adjudication or sealed manifest changes. `sha256sum -c` passes for sealed
    r6/r7/r8 before and after.
1.2 **The adjudication tally is unchanged:** 2 engine-favoured, 0 engine-disfavoured. An
    abstention never justifies a dispute.
1.3 **Branches.**
    - `upgrade/review-revisions` stays at `fa1555e`.
    - `fix/comma-lists` stays isolated at `3a24d1b`.
    - 5A, if authorised, goes on `rev5a/abstention`.
1.4 **No blanket exemptions.** No xfail, skip, or blanket exemption. Historical abstentions
    are handled only by the exact, owner-approved migration in `TEST_MIGRATION_5A.md` (D6).
    No test assertion changes before the owner approves that file.

## 2. Mention qualification (résumé only; postings unchanged)

### 2.1 States
A résumé mention is `affirmed`, `negated`, `hypothetical` or `uncertain`. `uncertain` is never
merged with the other three, in the engine or in evaluation. It is set only by the U-rules
below, and only on a mention that R2–R3 would leave `affirmed`. A `negated` or `hypothetical`
result is never softened.

### 2.2 U-rules
Cue words live in `data/match_rules.json`. There is no exception or exclusion list.
- **Reused vocabulary:** the existing `negation` and `hypothetical` lists.
- **New vocabulary:**
  - `nor`, `neither`, and the `n't` forms;
  - `unfamiliar`, `unfamiliar with`;
  - the exclusion cues `except`, `except for`, `other than`, `apart from`, `excluding`,
    `everything but`, `anything but`, `all but`;
  - the trailing-state cues `in progress`, `enrolled`, `n/a`, `not used`.

  "zero" is deferred (D10).

Throughout, a cue never counts inside a recognised skill span (for example "machine
learning"), or inside a hyphenated word (for example "no-code").

| Rule | Fires when | Closes |
|---|---|---|
| **U1 negation reach** | A negation or exclusion cue appears earlier in the same logical line. Nothing between the last such cue and the skill's coordinated list ends its reach. **Reach is ended by** `. ; ? !` and by the contrast words `but`, `however`, `although`, `though`, `whereas`, `yet`. **Reach is not ended by** a comma or a colon. `except` is a cue, not an end. | Comma lists; "Not proficient in"; "Neither … nor"; "Haven't used"; "Unfamiliar with"; "every tool except X" (N4); "everything but X" (N4) |
| **U2 trailing state** | Directly after the last skill of the list comes an optional separator (`( , : ; - – — \| /`), an optional `currently` or `still`, then a cue from `hypothetical`, `negation` or the trailing-state list. The cue must close the item: it is followed only by an optional `)` and then a separator or the end of the line. | "Python (learning)", "SolidWorks: none", "FEA – in progress" |
| **U3 separated negation** | Directly after the list comes a separator (`( : - – —`), then a negation cue, followed by any words. | "SolidWorks — never touched it" (N6) |
| **U4 anaphoric negation** | A later sentence in the same logical line has no recognised skill and starts with a negation cue. It must also either be at most 2 words long, or contain `it`, `them` or `either` within its first 4 words. | "SolidWorks. Never used it." (N1); "MATLAB? Never." (N5) |
| **U5 negated heading** | The mention's section heading contains a negation or exclusion cue. | "Skills I have not used:" (N2) |

**Disclosure.** U4 first listed `this`, `that` and `those` as pronouns.
- They were removed after a simulation abstained on the locked fixture
  `u6_culture_benefits_heavy` ("…; never shipped a part that failed…").
- The grammatical reason given for removing them: in that position they usually start a
  relative clause or act as determiners.
- This is still a fixture-informed choice. "SolidWorks. Never used that." is therefore a
  residual risk. Independent minimal pairs must test it (D13).

**Level words (D1).** "SQL, basic" and "Creo (beginner)" stay `affirmed`. They count as claimed
proficiency only. Nothing about depth or achievement is inferred from them.

### 2.3 Remaining residual risks

| # | Pattern | Status under v4 |
|---|---|---|
| N3a | "Zero SolidWorks experience" | **Affirmed: a critical false affirmation.** Open until D10 is decided from independent minimal pairs. |
| N1b | "SolidWorks. Never used that." | Affirmed. See the disclosure under §2.2. |
| N7 | A "Hobbies" section counts as evidence | Affirmed. This is an evidence-quality gap, not a negation. It is not counted as a critical false affirmation unless the owner rules otherwise. |
| N8 | A contrast word that does not actually reverse polarity | Reach ends at the contrast. Probes are required. |
| — | Negation further away (an earlier line, or across bullets) | Not handled. Probes are required. |

**D9 consequence:** every residual probe that yields a critical false affirmation blocks
Gate 1. N3a will block Gate 1 unless D10 adds "zero" or a better rule.

## 3. Skill-level interaction (D11; exactly as below)
For each skill on the résumé, classify its mentions. "Decided" means affirmed, negated or
hypothetical. Apply the rows in order; the first match wins.

| # | Mentions | Skill state | Effect if required or preferred |
|---|---|---|---|
| 1 | Its document was refused (F1–F3) | `unsupported` | Score withheld |
| 2 | At least 1 `affirmed` **and** at least 1 `negated` | `contradicted`: an unresolved direct contradiction about possession | Score withheld (D11) |
| 3 | At least 1 `affirmed`, no `negated` | `found` (any `uncertain` or `hypothetical` mentions are listed but don't block) | Counted as found |
| 4 | At least 1 `uncertain`, no `affirmed` | `uncertain` (this includes `uncertain` together with `negated`; see D11a) | Score withheld |
| 5 | Only `negated` and/or `hypothetical` | `missing` | Counted as missing |
| 6 | No mention | `missing` | Counted as missing |

Notes:
- **"Independent, unambiguous" (row 3).** An `affirmed` mention can't share a logical line
  with an active cue, or U1–U4 would have fired on it. So any affirmed mention is
  independent of the uncertain ones by construction.
- **D11a (my reading, needs confirmation).** Row 4 follows "otherwise withhold" literally, so
  `uncertain` plus `negated` is withheld, not missing. In 5B, a skill in row 2 or row 4 can
  be confirmed only after the user resolves the contradiction explicitly. A confirmation
  never overrides a refused document (row 1).

## 4. Unsupported formats
F1–F3 refuse a document. F4 gives a reason without refusing. Rules are as in v3 §3
(prototype `f_rules.py`).
- F1 `paragraph_resume`
- F2 `fragmented_layout`
- F3 `non_english`
- F4 `no_scored_structure`

**Observable penalty for refusing a valid document (item 6).** A refusal is never silent.
For a refused document:
- every gold label in it counts as `abstained`, which lowers decision coverage and useful
  accuracy;
- its pair counts as not scored, which lowers availability;
- it is listed by name in the report;
- if its gold says it is supported, it also counts toward the look-alike gate.

Historical results: 0 of 172 documents refused. Synthetic results: 8 of 8 classified as
intended. I wrote those synthetic samples myself, so they are not independent evidence.

## 5. Score modes, reasons, and 5B

### 5.1 Score modes

| Mode | When | Score |
|---|---|---|
| `scored` | none of the conditions below | numeric |
| `withheld` | a required or preferred skill is in row 1, 2 or 4 of §3 | `None` |
| `unavailable` | F4 applies and the score is not withheld | `None` |
| `scored_after_confirmation` | 5B only | numeric |

Precedence: withheld, then unavailable, then scored. Uncertain skills that are not required
or preferred appear in `MatchResult.resume_uncertain` and do not withhold the score.

### 5.2 Reasons
A reason is `(code, skill | None, doc, span | None, message)`.
- **Message:** a fixed template, filled only with the canonical skill name and a cue word
  taken from the rules data.
- **Uncertain skills:** `resume_line` is `None`; only the span is kept.
- **No user text** appears in reasons, exceptions, or logs.

### 5.3 Revision 5B (specification only)
`confirm()` is pure:
- it never turns a refused document into a scored one;
- it applies the D11a constraint;
- it changes only coverage.

A confirmation is never evidence for a bullet. That is enforced in §5.4.

### 5.4 Unsupported-claim blocking (D12; Wave 2 / 5B implementation)
1. **Builder (`ui/tab_resume.py`).** A bullet with a non-empty `problems` list from
   `split_claims` is shown with an error. It is **not** added to `all_bullets`, the "Copy
   All Bullets" block, or `generated_bullets`. The informational ownership/impact words
   (`check`) do not block it.
2. **Session state.** It stores `(bullet, BulletEvidence)` pairs, not bare strings.
3. **PDF trust boundary (`app.py:178-185`).**
   - Before calling `generate_pdf`, the export calls a new pure helper
     `exportable_bullets(pairs)`.
   - The helper re-runs `find_unsupported_claims` on each pair and drops any bullet that is
     flagged.
   - If any bullet was dropped, the sidebar says how many were withheld from the PDF.
4. **Tests.**
   - `exportable_bullets` drops a bullet with an inserted metric or tool and keeps a clean
     bullet.
   - A static check shows `app.py` passes only `exportable_bullets(...)` output as
     `bullets=`.
   - A confirmed skill missing from the evidence never appears in an exported bullet.
5. **Out of scope.** The template example bullets in `tab_projects` and `tab_audit` are data,
   shown for reference only. The PDF doesn't export them; this was verified with grep.

## 6. Evaluation: four separate families
Results are always reported with the original labels. Adjudicated labels are reported
separately.

**Counting units.**
- **Unit:** one résumé mention label.
- **Ambiguous labels:** gold `ambiguous` labels are excluded from the useful-accuracy (UA)
  and decision-coverage (DC) denominators, and counted only in appropriate abstention (AA).
- **Posting labels:** reported separately. They can only abstain through a refusal.
- **Confusion matrix:** the full 4×4 matrix (gold × engine, including `uncertain`) is always
  shown.

### 6.1 Exact acceptance thresholds (proposed for freeze)

| Family | Metric | Numerator | Denominator | Historical gate (postings 48 + regression_r6 14 + r7 + r8 = 200 labels, 86 pairs) | Round-9 gate |
|---|---|---|---|---|---|
| **A. Safety** | Critical false affirmations (a negated or hypothetical skill counted present, or an invented claim) | count, on decided outputs and numeric scores | n/a | = 0 on the original labels that 5A decides | = 0 in the gate set **and** = 0 across all residual probes (D9) |
| A. Safety | Other R2.6 critical errors | count | n/a | = 0 | = 0 |
| **B. Classification correctness** | Useful accuracy (UA) | `correct` | non-ambiguous résumé labels | UA(5A) ≥ UA(pre) − 3.0 pts | UA(5A) ≥ UA(pre-5A baseline on r9) − 3.0 pts |
| B | Decided accuracy | `correct` | `correct` + `incorrect` | report only (rewards abstention, so never a gate) | report only |
| **C. Decision coverage** | Decision coverage (DC) | `correct` + `incorrect` | non-ambiguous résumé labels | ≥ 90% (D8b) | ≥ 90% |
| C | Appropriate abstention (AA) | abstentions whose gold is not affirmed, or is `ambiguous` | all abstentions | report only (n = 14 < 20) | ≥ 70% if n ≥ 20, otherwise report |
| C | Usefulness losses | each label that went from correct to abstained | listed | always listed | always listed |
| **D. Score availability** | Availability (SA) | pairs with gold `scored` and engine `scored` | pairs with gold `scored` | report only (no gold mode; the 86 pairs are treated as gold scored) | ≥ 90% |
| D | Look-alike refusals | count | n/a | = 0 of 172 documents | = 0 |

### 6.2 Semantics
- **All gates must pass.** Families are never averaged together.
- **Small denominators.** A gate with a denominator below 20 is INSUFFICIENT and cannot pass.
- **Abstention is never correct.** An incorrect → abstained change never raises UA. An
  engine that abstains on everything gets UA = DC = SA = 0, so it FAILS.

### 6.3 Statistical uncertainty (round 9)
- **Intervals.** Every rate is reported with a 95% Wilson interval.
- **UA difference.** It is paired, because the same labels are scored with and without 5A.
  It is reported with an exact McNemar test and a 95% interval on the paired difference.
- **Zero critical errors.** With 0 observed in n units, the 95% upper bound (rule of three)
  of about 3/n is reported.
- **Resolution.** With about 150 labels, the UA interval half-width is about ±4–5 pts.
  - A 3-point floor is therefore below what round 9 can resolve.
  - The gate uses the point estimate; the interval is shown next to it.
  - The owner should treat a point estimate within the interval of the floor as
    inconclusive, not as a clean pass (D8c).

### 6.4 Predicted historical values for v4
These come from an in-memory simulation (`sim_v5.py`, `hist_v3.py`, `hist_avail.py`). They
are regex approximations, not an implementation.

| Metric | Pre-5A | v4 | Gate | Result |
|---|---|---|---|---|
| A. Critical false affirmations decided | 8 (r8, negation counted present) + others | 0 of these 8; they are now abstentions, listed as "not a fix" | 0 | pass, by abstention |
| B. UA | 190/200 = 95.0% | 184/200 = **92.0%** | ≥ 92.0% | **pass at exactly the floor (zero margin)** |
| C. DC | 100% | 186/200 = **93.0%** | ≥ 90% | pass |
| C. AA | — | 8/14 = 57% | report | — |
| C. Usefulness losses | — | 6 labels (1 locked, 5 retrospective) | listed | — |
| D. SA | 86/86 | 77/86 = **89.5%** (9 pairs withheld, 1 of them from a D11 contradiction) | report | below the round-9 bar |
| D. Look-alikes | — | 0/172 | 0 | pass |

**Honest summary.**
- v4 clears the historical gates only narrowly.
- UA sits exactly on the floor.
- SA would fail a 90% bar if one were applied to history.
- Round 9 can't resolve a 3-point UA difference.

## 7. Q1/Q2 simplification analysis (item 4)
I simulated each variant in memory against the existing suite and the 200 historical labels.

| Variant | Description | Tests failing | Historical UA | DC |
|---|---|---|---|---|
| v3 | Q1 (closing trailing cue) + Q2 (reach) | 3 | 92.0% | 93.0% |
| L | One rule: any negation cue anywhere in the line, plus heading cues | 19 | 71.0% | 72.0% |
| LH | L + hypothetical cues anywhere | 27 | 67.0% | 68.0% |
| S | Negation cue anywhere in the same sentence, either side | 12 | 82.0% | 83.0% |
| **v4** | U1–U5, reusing the existing lists | **3** | **92.0%** | **93.0%** |

**Conclusion.**
- Broader single rules are simpler but fail usefulness: they abstain on ordinary
  achievements ("no rework", "never missed").
- v4's only simplification is reuse: U2 takes its vocabulary from the existing
  `hypothetical` and `negation` lists instead of v3's separate Q1 list.
- Neither v4 nor v3 has any exception list.
- The U3–U5 closures cost 0 additional historical labels.

## 8. Risk register (carried forward)
- **R4.8 three-word cap.** PROPOSED, UNAPPROVED. It exists only on `fix/comma-lists` and is
  not used by 5A.
  - Fixtures: `u6_duty_lines_as_required`, `u6_gov_defense_clearance`.
  - Limitation: "…or any other parametric CAD package preferred".
- **R4 branch.** It has a known locked failure.
- **N3a "zero".** A critical false affirmation that blocks Gate 1 (D10).
- **N1b, N7, N8.** Open, per §2.3.
- **UA zero margin; round-9 resolution.** See §6.4 and §6.3.
- **Usefulness losses.** 6 historical labels.

## 9. Acceptance matrix
These are coordinator-written unit tests, committed before any code. Rows marked † use novel
phrasing.

| # | Text (résumé) | Expected |
|---|---|---|
| 1 | "Never used Creo" | `negated` |
| 2 | "No SolidWorks experience" | `negated` |
| 3 | "Without SolidWorks experience" | `negated` |
| 4† | "Not proficient in MATLAB" | `uncertain` (U1) |
| 5† | "Never let a GD&T callout slip past review" | GD&T `uncertain`; the skill is `uncertain` |
| 6† | Row 5 plus "Applied GD&T to drawing packages" | the skill is `found` (§3 row 3) |
| 7† | "Cut scrap 12% without new equipment by applying SPC" | `uncertain` |
| 8† | "Reduced rework by applying SPC" | `affirmed` |
| 9 | "Never improved yield by applying SPC" | `uncertain` |
| 10 | "No PLC experience, proficient in SQL" | PLC `negated`; SQL `uncertain` |
| 11† | "Python (learning)" / "FEA - in progress" / "Creo: still studying" | `uncertain` (U2) |
| 12† | "SolidWorks: none" / "Creo (not used)" / "SolidWorks — none" | `uncertain` (U2) |
| 13 | "SQL, basic" / "Creo (beginner)" | `affirmed` (D1) |
| 14 | "Used SolidWorks; currently learning FEA" | SolidWorks `affirmed`; FEA `hypothetical` |
| 15 | "Never used Creo, Foobar, SQL" | Creo `negated`; SQL `uncertain` |
| 16 | "Proficient in SolidWorks, Foobar, Python" | both `affirmed` |
| 17 | Metamorphic: rows 10, 15 and 16 with Foobar placed at the start, middle and end | no change |
| 18 | "No CAD certification, but daily SolidWorks use" | `affirmed` |
| 19 | "Never used MATLAB; built models in Python" | Python `affirmed` |
| 20 | "No SolidWorks, but strong in Creo" | SolidWorks `negated`; Creo `affirmed` |
| 21 | "Tools: no-code automation, SolidWorks" | `affirmed` |
| 22† | "Neither SolidWorks nor Creo" / "Haven't used SolidWorks" / "Unfamiliar with SQL" | `uncertain` |
| 23† | "Used every CAD tool except SolidWorks" / "Everything but SQL" | `uncertain` (U1, N4) |
| 24† | "SolidWorks — never touched it" | `uncertain` (U3) |
| 25† | "SolidWorks. Never used it." / "MATLAB? Never." | `uncertain` (U4) |
| 26† | Heading "Skills I have not used:" over "- SolidWorks" | `uncertain` (U5) |
| 27† | "Designed brackets in SolidWorks. No rework was needed." / "Ran FEA on frames; never shipped a part that failed drop testing" | `affirmed` (usefulness guards) |
| 28 | "No SolidWorks experience" plus a separate "Designed parts in SolidWorks" | `contradicted`; score withheld if required (§3 row 2) |
| 29 | "No SolidWorks experience" plus "SolidWorks: none" | `uncertain`, withheld (D11a) |
| 30 | Score withheld / score kept / `resume_uncertain` (v3 rows 23–24) | as in v3 |
| 31 | F1 / F2 / F3 refusals; look-alikes pass; F4 `unavailable` | as in v3 rows 25, 26 and 28 |
| 32 | Privacy: every reason is template words only; `resume_line` is `None` for uncertain skills; nothing is logged | — |
| 33 | Bullet blocking: a flagged bullet is absent from `generated_bullets` and from the PDF (§5.4) | — |
| 34 | Never softened: rows 1–3 and 20 (SolidWorks) | stay `negated` |

## 10. Implementation scope (not authorised)
- **Files:** `engine/match_stages.py`, `engine/job_match.py`, `data/match_rules.json`,
  `scripts/evaluate_matching.py` (four families, intervals, McNemar),
  `tests/test_rev5a.py`, and the approved migrations only.
- **Docs:** an R5A section and an R3.1.3 amendment.
- **Bullet blocking (§5.4):** `ui/tab_resume.py`, `app.py`, plus a helper. This is UI work,
  so the owner decides whether it ships with 5A or with Wave 2 (D14).
- **Size:** about 150 lines of engine code, about 90 in the eval script, about 50 tests.
- **Process:** round 9 is sealed first, then the worker implements, then an independent
  review. One round only.
- **Stopping rule:** stop on any of these:
  - a critical error, including in any probe;
  - a look-alike refusal;
  - any gate that FAILS or is INSUFFICIENT;
  - any test change not in the approved migration.

## 11. Owner decisions outstanding
- **D6-migration:** approve `TEST_MIGRATION_5A.md`, all three items.
- **D8b:** confirm DC ≥ 90% for both historical and round 9. The earlier 97% is unreachable
  under D2: 93.0% is predicted.
- **D8c:** confirm reading the UA gate on the point estimate plus its interval, with
  "inconclusive" when the floor falls inside the interval.
- **D10:** independent minimal pairs for "zero" are being prepared, and results will follow.
  Until it is decided, N3a blocks Gate 1.
- **D11a:** confirm that `uncertain` plus `negated` is withheld rather than missing.
- **D13:** independent minimal pairs for the U4 pronoun set ("Never used that.").
- **D14:** ship bullet blocking with 5A, or with Wave 2.
- Sealing round 9 and implementing 5A each still need separate authorisation.

Gate 1 remains blocked.

## 12. Status after independent review of v4 (2026-11-10): NOT READY TO FREEZE

**Review verdict:** NEEDS REVISION. Findings are in `REVIEW_5A_v4.md`.

**Structural finding (coordinator).** The cue-rule approach cannot satisfy D9 and D8
together.
- **D9 versus D8:** D9 requires zero critical false affirmations across every residual probe.
  D8 sets a useful-accuracy floor of 3 points below the pre-5A baseline.
- **Holes remain:** the reviewer found more than 25 common phrasings that v4 still affirms.
  Examples are "not yet used", "Python was not used", curly apostrophes, "Learning: PLC" and
  "MATLAB certification in progress".
- **Each closure costs usefulness:**
  - "zero" moves historical UA from 92.0% to 90.5%;
  - broad back-reference detection moves it to 86.5%.

  Both fall below the floor.
- **The baseline already fails:** with every occurrence counted, v4's own historical UA is
  about 91.5%, below the floor.
- **Why the cycle repeats:** each round of cue additions either leaves critical holes or
  converts ordinary achievement bullets into abstentions. This is the same limit as the
  "never" preflight stop.

**Options for the owner (see the reply). No further contract revision until one is chosen.**
- **(A) Keep cue rules.** Accept that Gate 1 stays blocked until a phrase-structure
  qualifier (post-Gate-1 architecture) exists.
- **(B) Confirmation-first, recommended.**
  - The engine never asserts possession of a required or preferred skill on its own.
  - Each matched résumé mention is shown as "suggested", with its span, and counts only once
    the user confirms it.
  - With no confirmations, the mode is `awaiting_confirmation` and there is no score.
  - Critical false affirmation by the engine becomes impossible by construction.
  - Abstention rules (U1–U5, F-codes) only order and explain the suggestions.
  - D12 bullet blocking still applies, so a confirmation is never evidence.
  - Cost: 5B UI becomes required for any score, so Gate 1 depends on Wave 2 UI.
- **(C) Lower the bar.** Relax D8 or D9. Not recommended, since it gives up the safety rule.
