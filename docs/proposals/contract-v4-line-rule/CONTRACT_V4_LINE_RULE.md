# Contract v4: résumé line rule (DRAFT for owner sign-off, revision 3; no code)

| | |
|---|---|
| Date | 2026-11-13 (revision 2 was 2026-11-10) |
| Base | `upgrade/review-revisions` @ `fa1555e9999495cea9e1d4c1b64f3530cedc0daf`, unchanged |
| Status | DRAFT. Nothing is implemented. Every figure comes from an in-memory simulation. |
| Simulations | `sim/sim_supported_v6.py`, `sim/sim_supported_v6_pytest.py`, `sim/gen_expectations_v6.py` (non-production, read-only) |
| Migration draft | `EXPECTATIONS_LINE_RULE.DRAFT.json`, sha256 in `EXPECTATIONS_LINE_RULE.DRAFT.sha256` |

## 0. What changed from revision 2

- **Default reversed (owner ruling, 2026-11-13).** A résumé skill is `affirmed` only in a
  supported form (§1.4). Everything else is `unresolved`. In revision 2 a line without a cue
  was affirmed.
- **Unit stated (§1.1).** The rule runs on the whole bullet or paragraph after unwrapping,
  and merges when a boundary is in doubt.
- **No cue was added** for the 8 probe failures of revision 2. The cue set (§1.3) is the
  revision 2 set, word for word.
- **Migration (§6).** The permitted cause is a cue line or a document-level trigger, recorded
  per record. The inputs of the retired tests carry over as line-rule cases.
- **Round 9 (§8).** Probes are written fresh by a reviewer who has not seen the lists here.
- **Reconciliations (§9)** of 86 versus 85 pairs and 50 listed tests versus 49 failures.

## 1. The rule (résumé only; posting side byte-for-byte unchanged from `fa1555e`)

### 1.1 Unit

The rule runs on a **unit**: one whole bullet or one whole paragraph, after unwrapping.

- A unit **starts** at a line that begins with a list marker (the `bullets` data: `•`, `·`,
  `▪`, `◦`; `-`, `*`, `–`, `—`, `>` followed by a space; or a numbered or lettered item),
  at the first line after a heading that `segment` recognises at `fa1555e`, and at the first
  line after a blank line.
- **Every other physical line is merged into the unit before it.** Capital letters, digits,
  indentation and end punctuation do not start a unit. This is the "merge when the boundary
  is in doubt" rule: only a blank line, a list marker or a heading is a certain boundary.
- A unit's text is the source text from its first character to its last, newlines included.
  A newline counts as white space, so a two-word cue split by a wrap still matches.
- `fa1555e` joins a wrapped line only when it starts with a lower-case letter. That narrower
  join stays on the posting side. On the résumé side the unit replaces it.

### 1.2 Normalisation (unchanged from revision 2)

Before matching, apply these steps in order:
1. replace the curly apostrophes U+2019, U+2018 and U+02BC with `'`;
2. lowercase the text;
3. split it into tokens using `[a-z0-9]+(?:[-.,'][a-z0-9]+)*'?[a-z]*`.

A hyphenated word is one token ("no-code" is not the cue "no"). "0.5" is one token, so it is
not the cue "0". "haven't" is one token.

### 1.3 Cue set (unchanged from revision 2)

Cues match whole tokens. A multi-word cue matches a consecutive run of tokens.

- **The `fa1555e` lists** in `data/match_rules.json`:
  - `negation`: no, not, without, never, lack of, lacking, lacks, none;
  - `hypothetical`: learn, learning, currently learning, planning to take, planning to,
    plan to, plans to, preparing for, studying for, studying, hope to, hoping to, willing to
    learn, willingness to learn, aspire to, working toward, working towards.
- **Owner additions (2026-11-10):** `n't` (any token ending in "n't"), cannot, unable, zero,
  standalone 0, lack, unfamiliar, except, only, learning, studying, familiar, exposure,
  coursework, hobby.

A cue inside a skill name counts: "machine learning" contains the cue "learning".

### 1.4 Default and the two supported forms

**Default.** Every skill mention in a unit is `unresolved`, unless the unit has no cue (§1.5)
and is in one of the two supported forms below.

**Form A, Skills entry.** All of these hold:
- the unit is under a recognised Skills heading, and that Skills section is still open;
- the unit contains at least one known skill name;
- apart from known skill names, the unit contains only separators and approved level words.

Any other unit under a Skills heading **closes the section**. Units after it, up to the next
heading, can only qualify through Form B.

**Form B, Experience line.** All of these hold:
- the first word of the unit, after its list marker, is an approved action verb;
- the unit has no cue;
- the unit is not under an excluded heading (references, interests, hobbies).

**The lists.**

| List | Members |
|---|---|
| Recognised Skills headings (the `fa1555e` data) | skills, technical skills, key skills, core competencies, tools, technologies, skills and tools |
| Approved level words | basic, beginner, novice, intermediate, advanced, proficient, expert, working knowledge |
| Separators | space, tab, newline, carriage return, `,` `;` `\|` `/` `&` `(` `)` `[` `]` `:` `.` `-` `–` `—` `•` `·` `▪` `◦` `*` `>`, the word "and", and a leading list marker |
| Approved action verbs (past tense only) | designed, developed, built, led, managed, implemented, created, analyzed, analysed, tested, validated, verified, programmed, automated, modeled, modelled, simulated, fabricated, machined, assembled, installed, commissioned, calibrated, maintained, operated, performed, conducted, executed, delivered, produced, improved, reduced, increased, optimized, optimised, streamlined, integrated, deployed, configured, debugged, troubleshot, diagnosed, repaired, inspected, measured, documented, drafted, wrote, authored, reviewed, supervised, mentored, taught, coordinated, launched, engineered, prototyped, wired, welded, coded, scripted, migrated, upgraded, redesigned, refactored, established, generated, completed, achieved, applied, used, utilized, utilised, ran |
| Excluded headings (the `fa1555e` data) | references, interests, hobbies |

The verb list was written once, before any run, from general résumé convention. It was not
changed after the results were seen. The words familiar, exposure and coursework are cues
(§1.3), so they are not level words.

**Readings that need your confirmation** (each is the stricter of the readings I could see):

| # | Reading used | Effect if you rule the other way |
|---|---|---|
| M1 | Form B does not need an Experience heading. Your wording gave a heading requirement for Skills entries only. | Requiring one of the `fa1555e` Experience headings (experience, work experience, professional experience, employment history, projects, relevant experience, engineering experience) leaves all safety counts at 0 and drops pairs scored before confirmation from 4 to 2 of 85. |
| M2 | The cue test also applies to Skills entries, so "Machine Learning, Python" under Skills is unresolved for both skills. | Exempting cues inside a known skill name would affirm such lines. Not simulated. |
| M3 | A "Label:" prefix ("CAD: SolidWorks, Creo") is not a skill name, a separator or a level word, so the unit is not a Skills entry and closes the section. | See §5.3: 10 of 12 Skills units in the realistic sets fail Form A. |
| M4 | Only past-tense verbs are approved. "Design brackets in SolidWorks" (a current job) is unresolved. | Present-tense verbs also start aspirations ("Develop SolidWorks skills"), so I left them out. |

### 1.5 The cue test

The cue search runs on the whole normalised unit, before any comma, clause or list splitting.
If any cue occurs in the unit, **every** skill mention in that unit is `unresolved`, in either
form.

### 1.6 No scope resolution

Résumé text never produces `negated` or `hypothetical` findings. Only the user can produce
`denied` (§4).

### 1.7 Aggregation (S2, adopted in revision 2)

A skill's résumé finding is `affirmed` only if **all** of its résumé mentions are `affirmed`.
Any `unresolved` mention makes the skill `unresolved`.

### 1.8 Document-level triggers (unchanged from revision 2, now run on units)

If any one trigger fires, **every** résumé finding in the document is `unresolved`.

| Trigger | Fires when |
|---|---|
| `backref_negation` | A sentence contains no recognised skill name, has a negation cue, and either contains a back-reference word or has 4 tokens or fewer. Sentences are split inside a unit on `. ; ? !`; a wrap is not a sentence boundary. The negation cues for this trigger are the `negation` list plus `n't`, cannot, unable, zero, 0, lack, unfamiliar, nor, neither, nope. The back-reference words are it, them, this, that, these, those, either, neither, one, any of, the other, by me. |
| `unscoped_disclaimer` | A unit with no recognised skill has a negation cue (same list) and a possession word: experience, experienced, used, use, using, familiar, familiarity, knowledge, worked, exposure, proficient, proficiency, trained, skill, skills, background, hands-on. |
| `heading_cue_section` | A heading that `segment` recognises contains any cue from §1.3. |

Merging has one consequence here. A short negative sentence on a wrapped line now sits in the
same unit as the skill before it, so the cue test (§1.5) makes that unit unresolved and the
trigger does not need to fire. Example: `neg_resume_clause_breaks` fired `backref_negation`
in revision 2 and does not now; all its skills are unresolved through the cue test instead.

### 1.9 States, sources and reason codes

A finding is `(skill, state, source, evidence, reason)`:
- **state:** `affirmed`, `denied` or `unresolved`. The literal for the new résumé state is
  `unresolved`;
- **source:** `résumé` or `user-confirmed`;
- **résumé** findings can only be `affirmed` or `unresolved`;
- **user-confirmed** findings can only be `affirmed` or `denied`;
- **reason codes** are a fixed list: `skills_entry`, `experience_line`, `cue_line` (with the
  cue words), `unsupported_form`, and the three trigger names. They never hold user text.

## 2. Coverage score (unchanged from revision 2)

- **When computed:** only when no required or preferred skill is `unresolved`.
- **Absent skills:** a skill with no finding (no evidence), or a user-`denied` skill, counts
  as absent.
- **Unresolved never counts as absent.** The score calculation enforces this; it is not just
  a display label.

## 3. Retired résumé-side rules, and the tests that retire with them

### 3.1 Retired rules (résumé only; all still apply to postings)

- R2.3 lower-case-only hard-wrap joining, replaced on the résumé side by the unit (§1.1).
- R2.4/R3.1.3 negation gap rule (`neg_before` applied to résumé mentions).
- R3.1.2/R3.3 hypothetical scope (`_hyp_start` applied to résumé mentions).
- R2.8.15 comma-list exemption, and `_chains`/`_clause` use, in résumé qualification.
- R4.1, R4.2 and R4.7 on the résumé side. These live on `fix/comma-lists` and were never
  merged.

Drafts that lapse: the D1 level-word affirmation for familiar, exposure and coursework; the
Revision 5A Q1/Q2 and U1–U5 drafts; the supported-input S1/S2 definitions in
`SUPPORTED_INPUT_MVP.md`, which §1.4 replaces.

### 3.2 Tests (existing suite under revision 3, simulated in memory)

Result: **92 failed, 278 passed** of 370. Under revision 2 it was 49 failed, 321 passed.
The baseline at `fa1555e` is 370 passed.

| Test | Failing | Disposition |
|---|---|---|
| `test_stage4_scope.py::test_r31_minimal_pairs` | 9 cases | **Retire**; inputs carry over (§6.3) |
| `test_stage4_scope.py::test_scope_ends_and_later_cues` | 9 cases | **Retire**; inputs carry over |
| `test_stage4_scope.py::test_scope_continues_across_a_joined_hard_wrap_but_not_a_blank_line` | 1 | **Retire**; inputs carry over |
| `test_stage4_scope.py::test_negation_keeps_the_gap_rule_and_does_not_spread` | 1 | **Retire**; inputs carry over |
| `test_stage4_scope.py::test_cues_never_reach_back` | passes | **Retire**: its subject is retired. It calls the posting-side `qualify`, so the rule cannot fail it. Its input carries over. |
| `test_job_match.py::test_resume_negation_is_narrow` | 3 of 3 params | **Retire**; inputs carry over. The third ("Tools: no-code automation, SolidWorks") passed under revision 2 and fails now: the line is in no supported form. |
| `test_cue_binding.py::test_negation_after_is_posting_only` | 1 | **Split**: keep the posting assertion, drop the résumé `_qualify` assertion; that input carries over |
| `test_check_fixture.py` (per-occurrence, wrong second occurrence, duplicate labels, un-indexed every occurrence) | 4 | **Edit**, not retire. Proposed diff in `TEST_CHECK_FIXTURE_PROPOSED.diff` (§6.4). Not applied. |
| `test_fixtures.py::test_fixture` | 59 fixtures (45 postings + 14 regression_r6) | **Migrate** through the expectations file (§6). Under revision 2 it was 22. |
| `test_job_match.py`: `test_excluded_section_never_scores`, `test_headingless_posting_is_unscored_with_score_none`, `test_lines_and_spans_attributed`, `test_long_line_snippet_is_capped_and_span_exact`, `test_required_and_preferred_score` | 5 | **New in revision 3; needs your ruling.** These test the posting side. Their one-line synthetic résumés are in no supported form, so nothing is found. Each needs a supported-form résumé line. No diff drafted. |

Posting-side tests are unaffected. No test has been edited.

## 4. Confirmation (unchanged from revision 2; specification only)

4.1 **Answers.** The engine accepts one answer per skill: `yes`, `yes_with_evidence` or `no`.
    The answer produces a `user-confirmed` finding: `yes` and `yes_with_evidence` give
    `affirmed` (the latter with the user's evidence text); `no` gives `denied`.

4.2 **Prompts.** A prompt is offered for every `unresolved` skill that is required or
    preferred. Prompts for unresolved skills that aren't scored are optional.

4.3 **Overriding the résumé.** The user may override any résumé finding, including an
    `affirmed` one. A `user-confirmed` finding always replaces the `résumé` finding for that
    skill.

4.4 **When the score appears.** The score is computed as soon as no required or preferred
    skill is `unresolved`, with mode `scored_after_confirmation`. The number of
    user-confirmed findings is shown with it.

4.5 **Bullets.** Confirmed skills never feed bullets without evidence. `yes` and `no` never
    create `BulletEvidence`. `yes_with_evidence` text can be offered to the Bullet Builder
    only as the user's own words, through the unchanged
    `build_bullet`/`find_unsupported_claims` path. A bullet flagged by `split_claims(...)[0]`
    can't be added, copied or exported (D12).

4.6 **Privacy.** Answers and evidence text live in session state only. They are never logged,
    and never written to files or git.

## 5. Simulation results (original labels; read-only; `sim/sim_supported_v6.py`)

### 5.1 Critical false affirmations (a disclaimed skill counted affirmed without the user)

| Data | Result |
|---|---|
| Historical: postings 48, regression_r6 14, r7 12, r8 12 | **0**, at both mention and skill level |
| Independent minimal pairs (40 items, 51 labels; development data since 2026-11-10) | **0** |
| The 32 probes of revision 2 | **0** |
| 16 new hard-wrap probes (14 split a cue and a skill across a wrap, 2 are controls) | **0** |

- **The 8 revision 2 probe failures** are all unresolved now, with no cue added. Six fail
  Form A or Form B because of the extra words or the missing action verb; the two under
  unrecognised headings fail because a bare "- SolidWorks" has no action verb.
- **Check on the harness.** The same harness run with the revision 2 rule gives 9 failures on
  the 32 probes: the 8 reported on 2026-11-10 plus "Interests / - SolidWorks", which I now
  count as a failure and revision 2's report did not.
- **What the unit changes.** With the revision 2 rule and `fa1555e` line joining, 2 of the
  14 hard-wrap probes affirm a disclaimed skill ("…with no⏎Python", "…never opened⏎
  SolidWorks"). Both controls stay affirmed under revision 3.
- **What the history check covers.** At skill level, an affirmed skill is checked against
  the gold found-set only when the posting lists it as required, preferred or unscored. 33
  affirmed skills are in no tier (24 postings, 8 r6, 1 r8); they are checked only where a
  mention label covers them.
- **Who wrote the probes.** I wrote the 16 hard-wrap probes knowing the lists. They are
  development data and can't serve as round-9 evidence (§8).

### 5.2 Score availability and prompts

Pairs with at least one required or preferred skill: 85 of 86 (§9).

| Set | Scored before confirmation | Prompts per pair: median / max | Scored after confirmation (oracle answers) | Found-set mismatches vs gold after confirmation |
|---|---|---|---|---|
| postings (47) | 3 (6%) | 1 / 7 | 47 | 0 |
| regression_r6 (14) | 0 | 4.5 / 6 | 14 | 0 |
| r7 (12) | 1 (8%) | 4 / 7 | 12 | 0 |
| r8 (12) | 0 | 3 / 6 | 12 | 0 |
| **All (85)** | **4 (5%)** | **2 / 7** | **85 (100%)** | **0** |
| Realistic sets only, r6–r8 (38) | 1 (3%) | 4 / 7 | 38 | 0 |

- Revision 2 scored 42 of 85 before confirmation (median 1 prompt). The supported-form
  default costs 38 of those pairs. Nearly all of the loss is in the unit fixtures, whose
  résumés are bare lines without headings or action verbs.
- "Scored after confirmation" uses the original gold labels as the user's answers: yes if
  the skill is in the gold found-set, no otherwise. Every pair scores by construction once
  each prompt is answered, so 85 of 85 is not a finding. The check is the mismatch column.

### 5.3 Résumés that go fully unresolved, and why mentions are unresolved

| Set | Résumés | Fully unresolved from a document trigger | No affirmed skill for any reason |
|---|---|---|---|
| postings | 48 | 0 | 31 |
| regression_r6 | 14 | 2 | 3 |
| r7 | 12 | 0 | 1 |
| r8 | 12 | 0 | 4 |
| **Realistic sets (r6–r8)** | **38** | **2 (5%)** | **8 (21%)** |

The two are `u6_culture_benefits_heavy` and `u6_pdf_hardwrap`. Both fire `backref_negation`
on an achievement sentence, as in revision 2.

| Mentions (642 recognised) | postings | r6 | r7 | r8 |
|---|---|---|---|---|
| affirmed (supported form, no cue) | 116 | 38 | 24 | 32 |
| unresolved: cue in the unit | 43 | 76 | 74 | 41 |
| unresolved: no cue, but not in a supported form | 125 | 33 | 10 | 30 |

On the realistic sets, of 12 units under a Skills heading only 2 are in Form A. Two have a
cue; the rest carry a label prefix or other words (reading M3).

### 5.4 Independent minimal pairs

51 labels: 0 critical, 0 affirmed, 23 unresolved where the gold is negated, hypothetical or
ambiguous, 25 unresolved where the gold is affirmed, 3 skills not recognised. The items are
bare sentences. Only one (B08) starts with an approved verb and has no cue; its two skills
are unresolved because its second sentence fires `backref_negation`.

## 6. Migration (`EXPECTATIONS_LINE_RULE.DRAFT.json`)

### 6.1 Form

- **Status.** DRAFT. The file name and its `status` field both say so. No test reads it.
- **Scope.** The 62 fixtures in the repository (postings and regression_r6). The r7 and r8
  sets are outside the repository and stay sealed and untouched.
- **Each record** keeps the original label unchanged, and adds `expected: "unresolved"`,
  `oracle_answer` (the original status, or `found`/`not_found` for a skill), and `cause`.
- **`cause`** is recorded per record. It holds `cue_line` with the cue words, and/or
  `document_trigger` with the trigger names. `unsupported_form: true` is added when a mention
  behind the record also fails §1.4 without a cue.
- **`source_sha256`** is the hash of the fixture's blob at `fa1555e`, so it does not depend on
  the checkout's line endings. (The revision 2 draft hashed the working-tree file.)
- **Fixture files** are not touched.

### 6.2 What it holds

| | Records | Cause |
|---|---|---|
| Label → unresolved, permitted | 68 (34 affirmed, 21 negated, 13 hypothetical) | 62 cue line; 5 cue line and trigger; 1 trigger only |
| Skill → unresolved, permitted | 94 (62 gold-found, 32 gold-not-found) | 70 cue line; 11 cue line plus an unsupported-form mention; 9 cue line and trigger; 4 trigger only |
| **Not permitted: needs your ruling** | **88** (6 labels, 82 skills) in 46 fixtures | `unsupported_form` only: no cue line and no trigger |

- The permitted records are in 24 fixtures.
- Revision 2 listed 6 records as not permitted (trigger only, in
  `u6_culture_benefits_heavy` and `u6_pdf_hardwrap`). A document-level trigger is now a
  permitted cause, so 5 of them are the 5 "trigger only" records above.
- **Record scope changed.** The sixth, MATLAB in `u6_culture_benefits_heavy`, is no longer
  recorded. MATLAB is in no posting tier of that fixture, and this draft records skills only
  when they are required, preferred or unscored. The revision 2 draft recorded every skill.
- **The 88 are new.** They change only because of the supported-form default. Your ruling
  names two permitted causes and this is neither, so they are listed under `not_permitted`
  and left out of the migration. Without a ruling on them, 46 fixture tests cannot migrate.

### 6.3 Retired test inputs as line-rule cases

`line_rule_cases` holds 28 inputs taken from the retired tests in §3.2: 9 + 9 + 2 + 1 + 3
from `test_stage4_scope.py`, 1 from `test_negation_after_is_posting_only`, and 3 from
`test_resume_negation_is_narrow`. Each keeps the original assertion as `oracle_answer` and
records the cause per skill. Under revision 3 every skill in all 28 is `unresolved`: each
input either has a cue or is not in a supported form.

### 6.4 The four `test_check_fixture` edits (proposed, not applied)

The four tests need one résumé line whose two CFD mentions have different statuses. Under the
rule every skill in a unit has the same state, so no résumé line can provide that. The
proposal moves that line into the synthetic posting, where scope rules are unchanged. The
whole change is in `TEST_CHECK_FIXTURE_PROPOSED.diff`:

| Hunk | Serves |
|---|---|
| `POST` gains a "Notes:" line; `RESUME` becomes "Skills / CFD" | all four tests |
| `lab()` labels the posting line instead of the résumé line | `test_per_occurrence_labels_pass`, `test_wrong_second_occurrence_fails_even_though_first_is_right`, `test_duplicate_labels_reported` (no change to their bodies) |
| Two `resume_text=` overrides become `posting_text=` | `test_unindexed_label_asserts_every_occurrence` |

Checked on a scratch copy: the edited file passes 8 of 8 at `fa1555e` as it is today, and
8 of 8 under the simulated rule. The cost: these tests no longer exercise a résumé label
with two statuses, which the rule makes impossible.

## 7. PDF export: rendering both state and source (unchanged from revision 2)

1. **Input.** `generate_pdf` takes `findings` (skill, requirement, state, source, reason) and
   `score_mode` together with the score.
2. **Score line.** Print a number only in `scored` or `scored_after_confirmation` mode.
   Otherwise print "Score withheld" plus the fixed reason text.
3. **Findings table.** Columns are Skill, Requirement, State and Source. Labels:
   `affirmed` + `résumé` → "Shown in your resume"; `affirmed` + `user-confirmed` →
   "Confirmed by you"; `denied` → "You said you don't have this"; `unresolved` → "Needs your
   confirmation". `unresolved` never appears under "Skills to Develop".
4. **No résumé text.** Only skill names and fixed text are printed.
5. **Encoding.** Use latin-1-safe wording with the core Helvetica font, or embed a Unicode
   font.
6. **Bullets.** The bullets section holds only unflagged bullets. The findings table never
   feeds it.

## 8. Round-9 probes

- Round-9 probes must be **written fresh by a reviewer who has not seen** the cue list
  (§1.3), the verb list or the heading lists (§1.4), this file, the simulation scripts or the
  expectations file.
- That reviewer receives category names only: trailing qualifications, negation in headings,
  separate-line disclaimers, cross-line references, ambiguous comma lists, unsupported
  layouts, and a cue and a skill split across a hard wrap.
- **Disqualified:** the author of this contract, and the reviewer who checked this folder
  before the commit. Both have read the lists.
- The 32 probes and the 16 hard-wrap probes here are development data. They are not round-9
  evidence.
- `ROUND9_SPEC.md` in this folder is stale and is superseded by this section where they
  differ. Sealing round 9 is still not authorised.

## 9. Reconciliations

**86 versus 85 pairs.** There are 86 fixture pairs: 48 postings, 14 regression_r6, 12 r7,
12 r8. One of them, `email_no_cues` in postings, has no required or preferred skill, so it has
no coverage score to compute and its result is "unavailable". Every per-pair figure (scored,
prompts) therefore has 85 as its denominator, and the postings row has 47. Critical false
affirmations are counted on all 86.

**50 listed tests versus 49 failures (revision 2).** The revision 2 table listed 50 tests:
21 in `test_stage4_scope.py`, 2 params of `test_resume_negation_is_narrow`, 1 split, 4 in
`test_check_fixture.py` and 22 fixtures. Only 49 fail. The fiftieth is
`test_cues_never_reach_back`: it is listed because its subject retires, but it passes,
because it calls the posting-side `qualify`.

**Revision 3.** The same count gives 93 listed and 92 failing: 21 in `test_stage4_scope.py`
(20 failing), 3 params of `test_resume_negation_is_narrow`, 1 split, 4 in
`test_check_fixture.py`, 59 fixtures and 5 further `test_job_match.py` tests.

## 10. Open items for your ruling

- **R1.** Readings M1–M4 in §1.4.
- **R2.** The 88 not-permitted records (§6.2): add `unsupported_form` as a permitted cause, or
  keep those 46 fixtures out of the migration.
- **R3.** The 5 further `test_job_match.py` tests (§3.2).
- **R4.** The four `test_check_fixture` edits (§6.4).
- **R5.** Usefulness. Before confirmation, 4 of 85 pairs score, and 1 of 38 on the realistic
  sets, with a median of 4 prompts there. These sets are adversarial by design. The 15
  independently labelled owner pairs (10 development, 5 held out) have not been supplied
  (`data/eval/` holds only the README and the schema), so no figure here measures ordinary
  résumés.

## 11. Limits of this draft

- All figures come from an in-memory simulation, not an implementation.
- **Known ways a disclaimed skill is still affirmed under revision 3.** No probe in this
  folder covers them, and no cue or rule was added for them. Whether a round-9 hit on one of
  them blocks Gate 1 (the D9 proposal of the earlier documents) is your ruling; this contract
  does not assume it. All examples below were run and come out `affirmed`.
  1. **A disclaimer written as a Form B line.** Form B accepts any unit that starts with an
     approved verb and has no cue: "Used SolidWorks once in a class", "Managed a team that
     used SolidWorks".
  2. **A disclaimer in a different unit that fires no trigger.** A supported-form unit
     elsewhere stays affirmed when the disclaiming unit names no skill and either has no
     negation cue, or has one but no back-reference word, no possession word and more than
     4 tokens. These are risks RS2 and
     RS3 of `SUPPORTED_INPUT_MVP.md`, unchanged since revision 2:
     - Skills "Python, MATLAB", then after a blank line "Listed tools were not part of my
       job.";
     - Skills "SolidWorks", then "Never touched SW on the job, only in a single class.";
     - Skills "Python, SQL", then "All self-taught; nothing professional.";
     - "- Designed brackets in SolidWorks", then "The CAD work above was done by a
       teammate."
  3. **Punctuation that carries meaning.** Brackets, hyphens and asterisks are separators, so
     an unchecked checkbox passes Form A: "- [ ] MATLAB" under Skills is affirmed, while
     "- [x] Python" is unresolved. "MATLAB: -" and "MATLAB (*)" are affirmed too.
- The independent pairs, the 32 probes and the 16 hard-wrap probes have all been used for
  analysis.
