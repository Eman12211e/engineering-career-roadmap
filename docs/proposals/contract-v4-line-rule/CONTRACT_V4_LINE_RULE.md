# Contract v4: confirmation-first matching (DRAFT, revision 4; no code)

| | |
|---|---|
| Date | 2026-11-13 |
| Base | `upgrade/review-revisions` @ `fa1555e9999495cea9e1d4c1b64f3530cedc0daf`, unchanged |
| Previous | Revision 3, committed as `d49574a` on `docs/contract-v4-line-rule` |
| Status | DRAFT. Nothing is implemented. Every figure comes from an in-memory simulation. **Gate 1 is blocked.** |
| Simulations | `sim/sim_confirm_v7.py`, `sim/sim_confirm_v7_pytest.py`, `sim/gen_expectations_v7.py` (non-production, read-only) |
| Migration | `API_AND_MIGRATION_PLAN.md`, `MIGRATION_LEDGER.md`, `EXPECTATIONS_LINE_RULE.DRAFT.json` (hash in `.sha256`), `TEST_JOB_MATCH_PROPOSED.diff`, `TEST_CHECK_FIXTURE_PROPOSED.diff` |

## 0. Owner rulings applied (2026-11-13)

**Direction.** Confirmation-first matching. Automatic résumé extraction may suggest skills.
No skill counts toward the self-reported coverage score without the user's explicit
affirmative confirmation.

| Ruling | What it decides | Where |
|---|---|---|
| R1 | Experience heading stays optional. Only supported category prefixes are accepted in a Skills entry. Action verbs stay past tense. A cue is not detected inside a recognised skill alias. | §1.3, §1.4 |
| R2 | "Unsupported form" is a permitted migration cause. Original labels are preserved. The 88 such records are listed one by one as usefulness losses. | §6 |
| R3 | Five test input changes, originals preserved. Final ruling F1 overrides "assertions unchanged": the assertions move to the new interfaces. | §6.4, plan §3 |
| R4 | Four checker-test changes, with a replacement résumé-side occurrence regression in the same migration. | §6.5 |
| R5 | Provisional budget: median 6 or fewer and at most 10 distinct skill confirmations per owner-evaluation pair. Posting requirements are never omitted to meet it. | §8 |
| R6 | Any skill counted as demonstrated or confirmed without explicit affirmative user confirmation is a critical error. | §2, §8 |
| R7 | Suggestions, confirmations, denials and unanswered skills stay distinct. An unanswered required or preferred skill withholds the score. A completed result is labelled self-reported skill coverage. Confirmation never generates unsupported résumé achievements. | §1.9, §2, §4, §7 |
| **F1** | **Option B.** Extraction and confirmation-aware scoring are separate interfaces. The production result schema holds no unconfirmed coverage score and no `found` flag. Historical evaluation meaning is kept in separately named diagnostic fields that never become user-facing scores. | §2, plan §1–§4 |
| **F2** | Every recognised required and preferred posting skill is prompted, including skills the résumé never mentions. Unscored posting skills are shown separately and are not mandatory prompts. | §4 |
| **F3** | Gold labels and sealed hashes are preserved. The 250 records stay traceable to their original test, expected value and cause. The gold found-set is not redefined as the suggestion set; suggestion quality is a separate measure. No blanket exemptions, skips or xfails. | §6 |
| **F4** | Suggestions are never treated as confirmed. Interface wording is neutral; no affirmative answer is pre-ticked. The two structural safeguards (unchecked checkboxes, unclean Skills sections) are approved. Known misleading-hint patterns are documented and independently tested. Confirmation never authorises fabricated achievements, professional experience or proficiency levels. | §1.4, §4, §7, §11 |
| **F5** | This checkpoint: incorporate the rulings, review, commit locally, stop before implementation. | — |

## 1. The résumé rule (résumé only; posting side byte-for-byte unchanged from `fa1555e`)

### 1.1 Unit (unchanged from revision 3)

The rule runs on a **unit**: one whole bullet or one whole paragraph, after unwrapping.

- A unit **starts** at a line that begins with a list marker (the `bullets` data: `•`, `·`,
  `▪`, `◦`; `-`, `*`, `–`, `—`, `>` followed by a space; or a numbered or lettered item),
  at the first line after a heading that `segment` recognises at `fa1555e`, and at the first
  line after a blank line.
- **Every other physical line is merged into the unit before it.** Capital letters, digits,
  indentation and end punctuation do not start a unit. Only a blank line, a list marker or a
  heading is a certain boundary; when in doubt, merge.
- A unit's text is the source text from its first character to its last, newlines included.
  A newline counts as white space, so a two-word cue split by a wrap still matches.
- The `fa1555e` lower-case-only join stays on the posting side.

### 1.2 Normalisation (unchanged)

Before matching, apply these steps in order:
1. replace the curly apostrophes U+2019, U+2018 and U+02BC with `'`;
2. lowercase the text;
3. split it into tokens using `[a-z0-9]+(?:[-.,'][a-z0-9]+)*'?[a-z]*`.

A hyphenated word is one token ("no-code" is not the cue "no"). "0.5" is one token. "haven't"
is one token.

### 1.3 Cue set

Cues match whole tokens. A multi-word cue matches a consecutive run of tokens. The set is
unchanged from revision 3; no cue has been added.

- **The `fa1555e` lists** in `data/match_rules.json`:
  - `negation`: no, not, without, never, lack of, lacking, lacks, none;
  - `hypothetical`: learn, learning, currently learning, planning to take, planning to,
    plan to, plans to, preparing for, studying for, studying, hope to, hoping to, willing to
    learn, willingness to learn, aspire to, working toward, working towards.
- **Owner additions (2026-11-10):** `n't` (any token ending in "n't"), cannot, unable, zero,
  standalone 0, lack, unfamiliar, except, only, learning, studying, familiar, exposure,
  coursework, hobby.

**R1: a cue inside a recognised skill alias is not a cue.** Every cue test that uses this
set, the unit cue test (§1.5) and the heading test of `heading_cue_section` (§1.8), runs on
text with every recognised skill mention blanked out. A heading "Machine Learning:" fires no
trigger; "Currently Learning:" still does. The other two triggers use the negation list only,
and no skill name contains one of those words.

In a unit: "Machine Learning, Python" has no cue.
"Learning Machine Learning, Python" still has one, the first word. Revision 3 counted the
word inside the name. One of the 53 skills is affected, Machine Learning.

### 1.4 The two supported forms

A skill mention is `affirmed` only if its unit has no cue (§1.5) and is in one of the two
forms. Otherwise it is `unresolved`. `affirmed` means only "in a supported form with no cue".

**Form A, Skills entry.** All of these hold:
- the unit is under a recognised Skills heading;
- the unit contains at least one known skill name;
- apart from known skill names, the unit contains only separators, approved level words and
  supported category labels;
- **the Skills section is clean (F4):** every unit under that heading, up to the next
  heading, is itself a Skills entry. If one unit is not, no unit in that section qualifies
  through Form A. Revision 3 only closed the section from that unit onward.

**Form B, Experience line.** All of these hold:
- the first word of the unit, after its list marker, is an approved action verb;
- the unit has no cue;
- the unit is not under an excluded heading.

**R1: no Experience heading is required** for Form B. A unit under a Skills heading can still
qualify through Form B.

**The lists.**

| List | Members |
|---|---|
| Recognised Skills headings (the `fa1555e` data) | skills, technical skills, key skills, core competencies, tools, technologies, skills and tools |
| Approved level words | basic, beginner, novice, intermediate, advanced, proficient, expert, working knowledge |
| Supported category labels (R1; the `category` values in `data/keywords.json`) | analysis, cad, certifications, controls, manufacturing, programming, quality, soft skills, standards. A label counts only when a colon follows it with nothing in between: "CAD: SolidWorks, Creo" counts, "CAD : SolidWorks" does not. "soft_skills:" is read as "soft skills:". A label may appear anywhere in the unit and more than once, so a merged block of labelled lines is one Skills entry. |
| Separators | space, tab, newline, carriage return, `,` `;` `\|` `/` `&` `(` `)` `:` `.` `-` `–` `—` `•` `·` `▪` `◦`, the word "and", and a leading list marker. **F4:** `[`, `]`, `*` and `>` are no longer separators, so "- [ ] MATLAB" and "MATLAB (*)" are not Skills entries. |
| Approved action verbs (R1: past tense only) | designed, developed, built, led, managed, implemented, created, analyzed, analysed, tested, validated, verified, programmed, automated, modeled, modelled, simulated, fabricated, machined, assembled, installed, commissioned, calibrated, maintained, operated, performed, conducted, executed, delivered, produced, improved, reduced, increased, optimized, optimised, streamlined, integrated, deployed, configured, debugged, troubleshot, diagnosed, repaired, inspected, measured, documented, drafted, wrote, authored, reviewed, supervised, mentored, taught, coordinated, launched, engineered, prototyped, wired, welded, coded, scripted, migrated, upgraded, redesigned, refactored, established, generated, completed, achieved, applied, used, utilized, utilised, ran |
| Excluded headings (the `fa1555e` data) | references, interests, hobbies |

- **Unsupported prefixes stay unresolved (R1).** "Planned: SolidWorks" and "Wishlist:
  SolidWorks, Creo" are not category labels, so the unit is not a Skills entry, and under F4
  the whole section is then unresolved.
- An unknown tool name or a parenthetical detail on a Skills line makes that section
  unresolved. That follows from "only known skill names".
- The verb list was written once, before any run, and has not been changed since.

### 1.5 The cue test

The cue search runs on the whole normalised unit, with skill names blanked (§1.3), before any
comma, clause or list splitting. If any cue occurs, **every** skill mention in that unit is
`unresolved`, in either form.

### 1.6 No scope resolution

Résumé text never produces `negated` or `hypothetical`. Only the user can deny a skill (§4).

### 1.7 Aggregation

A skill is `suggested` only if **all** of its résumé mentions are `affirmed`. Any `unresolved`
mention makes the skill's suggestion `unresolved`.

### 1.8 Document-level triggers (as revision 3, except the heading test now skips skill names)

If any one trigger fires, **every** résumé suggestion in the document is `unresolved`.

| Trigger | Fires when |
|---|---|
| `backref_negation` | A sentence contains no recognised skill name, has a negation cue, and either contains a back-reference word or has 4 tokens or fewer. Sentences are split inside a unit on `. ; ? !`; a wrap is not a sentence boundary. The negation cues for this trigger are the `negation` list plus `n't`, cannot, unable, zero, 0, lack, unfamiliar, nor, neither, nope. The back-reference words are it, them, this, that, these, those, either, neither, one, any of, the other, by me. |
| `unscoped_disclaimer` | A unit with no recognised skill has a negation cue (same list) and a possession word: experience, experienced, used, use, using, familiar, familiarity, knowledge, worked, exposure, proficient, proficiency, trained, skill, skills, background, hands-on. |
| `heading_cue_section` | A heading that `segment` recognises contains any cue from §1.3, with skill names blanked (R1). |

### 1.9 Four distinct things (R7)

| Thing | Values | Who produces it |
|---|---|---|
| **Mention status** | `affirmed`, `unresolved` | The résumé rule, per mention (§1.4–§1.5). These are the literals the fixture labels use. |
| **Suggestion** | `suggested`, `unresolved`, `none` (the résumé never mentions the skill) | The résumé rule, per skill (§1.7–§1.8) |
| **Answer** | `confirmed`, `denied`, `unanswered` | The user only |
| **Counted** | yes only when the answer is `confirmed` | The scoring interface (§2) |

- `affirmed` never means demonstrated. It is kept because the fixture labels and the posting
  side already use that literal.
- A suggestion is never an answer. Nothing converts `suggested` into `confirmed` except the
  user choosing yes for that skill.
- Reason codes are a fixed list: `skills_entry`, `experience_line`, `cue_line` (with the cue
  words), `unsupported_form`, and the three trigger names. They never hold user text.

## 2. Two interfaces, one score (F1, R6, R7)

**Extraction interface.** It takes the posting and the résumé. For each recognised posting
skill it returns the requirement tier, the posting evidence, the suggestion, the résumé
evidence span if any, mention statuses and reason codes. It returns **no coverage score and
no `found` flag**. Nothing in its output represents confirmed possession.

**Scoring interface.** It takes the extraction result and the user's answers. It is the only
code that produces the user-facing number.

- **What counts.** A required or preferred skill is covered only when its answer is
  `confirmed`. `denied` counts as not covered.
- **When it is computed.** Only when every required and preferred skill has an answer. One
  `unanswered` required or preferred skill withholds the complete numeric score.
- **What never counts.** A suggestion of any kind, and any résumé evidence on its own.
- **Name.** The completed result is labelled **"Self-reported skill coverage"** wherever it is
  shown or exported, with the number of skills the user confirmed.
- **Formula.** Unchanged: `100 * (0.8 * R + 0.2 * P)`, with R and P the confirmed shares.

**Critical error (R6).** Any skill counted as demonstrated or confirmed without the user's
explicit affirmative confirmation: in the self-reported score, in any "you have this" list, in
the PDF, or as a stored answer the user did not give. The production result schema carries no
field that could be shown as an unconfirmed score.

**Diagnostics (F1).** Evaluation keeps its historical meaning through separately named
diagnostic values: suggestion precision, suggestion recall, wrong suggestions and usefulness
losses. They live in the evaluation script and its report. They are not fields of the
production result and are never shown to a user. The names, the old-to-new mapping and every
consumer are in `API_AND_MIGRATION_PLAN.md`.

## 3. Retired résumé-side rules, and the tests that change

### 3.1 Retired rules (résumé only; all still apply to postings)

- R2.3 lower-case-only hard-wrap joining, replaced on the résumé side by the unit (§1.1).
- R2.4/R3.1.3 negation gap rule, R3.1.2/R3.3 hypothetical scope, R2.8.15 comma-list
  exemption and `_chains`/`_clause` use, in résumé qualification.
- R4.1, R4.2 and R4.7 on the résumé side (on `fix/comma-lists`, never merged).

Drafts that lapse: D1 level words familiar, exposure and coursework; the Revision 5A drafts;
the S1/S2 forms of `SUPPORTED_INPUT_MVP.md`.

### 3.2 Tests (existing suite under revision 4, simulated in memory)

Result in the simulation: **92 failed, 278 passed** of 370, the same 92 tests as revision 3.
The baseline at `fa1555e` is 370 passed.

**Two more tests would fail, so the real count is 94.** The simulation patches the engine
inside the test process. The `test_eval_*` tests in `test_job_match.py` run
`scripts/evaluate_matching.py` in a separate process, which the patch does not reach. Run in
process with the rule patched, two of them fail: their synthetic résumés give no `suggested` skill,
"resume matching" recall is 0.00, and the 0.85 holdout gate reports FAIL. This blind spot has
existed since revision 3 and was found in the final review.

The simulation also still patches the `fa1555e` interface, where `match_posting().found`
stands in for "suggested". It does not simulate the two interfaces of §2, so tests that pass
in the simulation only because of that stand-in also migrate (plan §3).

| Test | Failing in the simulation | Disposition |
|---|---|---|
| `test_stage4_scope.py`: `test_r31_minimal_pairs` (9), `test_scope_ends_and_later_cues` (9), `test_scope_continues_across_a_joined_hard_wrap_but_not_a_blank_line` (1), `test_negation_keeps_the_gap_rule_and_does_not_spread` (1) | 20 | **Retire**; inputs carry over (§6.3) |
| `test_stage4_scope.py::test_cues_never_reach_back` | passes | **Retire**: its subject is retired. Its input carries over. |
| `test_job_match.py::test_resume_negation_is_narrow` | 3 of 3 params | **Retire**; inputs carry over |
| `test_cue_binding.py::test_negation_after_is_posting_only` | 1 | **Split**: keep the posting assertion; the résumé input carries over |
| `test_check_fixture.py`, four tests | 4 | **Edit** (R4), with one new test (§6.5) |
| `test_job_match.py`, five tests | 5 | **Edit inputs** (R3) **and assertions** (F1; §6.4) |
| `test_fixtures.py::test_fixture` | 59 (45 postings, 14 regression_r6) | **Migrate** per record (§6.6) |
| Every other use of `.found`, `.score` or `match_posting` in tests and in `scripts/evaluate_matching.py` | passes in the simulation | **Migrate to the two interfaces** (F1; plan §3–§5) |
| `test_job_match.py::test_eval_pass_exit_0`, `::test_eval_duty_only_skill_in_resume_is_not_spurious` | not reached by the simulation; **fail** when run in process | **Depends on decision D4.** If the "resume matching" gate becomes a diagnostic, they pass unchanged. If it stays a gate, their synthetic résumés need a supported form. |

Listed as failing or retiring: 95. Failing: 94 (92 in the simulation plus these two). The
listed-but-passing test is `test_cues_never_reach_back`. No test has been edited.

## 4. Confirmation (R7, F2, F4)

4.1 **One explicit answer per skill:** yes, yes with evidence, or no. Yes and yes with evidence
    give `confirmed`; no gives `denied`. **No answer is pre-selected, and no affirmative
    answer is ever pre-ticked.** There is no accept-all.

4.2 **Who is asked (F2).** Every recognised required and every recognised preferred skill of the
    posting, including skills the résumé never mentions. No requirement is dropped, merged or
    hidden to shorten the list (R5).

4.3 **Unscored posting skills (F2)** are shown in a separate list with their résumé hint. They
    are not mandatory prompts and never enter the coverage calculation.

4.4 **Answers replace suggestions in both directions.** The user can confirm a skill the résumé
    never mentions, and deny one it suggests.

4.5 **The score** appears only when every required and preferred skill is answered (§2).

4.6 **Neutral wording (F4).** Fixed text plus the skill name. It never quotes the résumé and
    never asserts that the user has the skill. Proposed texts, for your approval:
    - prompt: "Do you have hands-on experience with {skill}?" with the choices "Yes", "Yes, and
      I'll describe it", "No";
    - hint for `suggested`: "Your résumé mentions this.";
    - hint for `unresolved`: "Your résumé mentions this. Please check the wording.";
    - hint for `none`: "Your résumé does not mention this."

4.7 **Confirmation never authorises invented content (R7, F4).**
- Yes and no never create `BulletEvidence`, a bullet, or any résumé text.
- A yes never produces or implies an achievement, a job, a period of professional experience
  or a proficiency level. No level word, duration or employer is attached to a confirmed
  skill.
- Yes with evidence passes the user's own typed words through the unchanged
  `build_bullet`/`find_unsupported_claims` path.
- A bullet flagged by `split_claims(...)[0]` can't be added, copied or exported. (This block
  was proposed in the earlier documents as "D12" and is not implemented.)

4.8 **Privacy.** Answers and evidence text live in session state only. They are never logged,
    and never written to files or git.

## 5. Simulation results (original labels; read-only; `sim/sim_confirm_v7.py`)

### 5.1 Skills counted without confirmation

**0, by construction.** In the simulated design nothing counts until the user answers, so
this is a property of the design, not a measurement. An implementation has to be tested for
it (§8).

### 5.2 Wrong suggestions (the résumé suggests a skill it disclaims)

A wrong suggestion is not a counted skill. It is a misleading hint, and each one is reported.

| Data | Wrong suggestions |
|---|---|
| Historical: postings 48, regression_r6 14, r7 12, r8 12 | 0, at mention and skill level |
| Independent minimal pairs (40 items, 51 labels) | 0 |
| The 32 probes of revision 2 | 0 |
| The 16 hard-wrap probes (14 probes, 2 controls) | 0 |
| The 10 known-pattern examples of §11 | **5 of 10** (10 of 10 before the F4 safeguards) |

The history check covers a skill at skill level only when the posting lists it as required,
preferred or unscored; others are covered only where a mention label exists.

### 5.3 Confirmations per pair

Pairs with at least one required or preferred skill: 85 of 86 (§9). One prompt per required
or preferred skill (F2).

| Set | Prompts per pair: median / max | Prompts by suggestion: suggested / unresolved / none |
|---|---|---|
| postings (47) | 2 / 8 | 24 / 76 / 41 |
| regression_r6 (14) | 5.5 / 8 | 10 / 59 / 7 |
| r7 (12) | 5 / 7 | 12 / 48 / 2 |
| r8 (12) | 4 / 6 | 14 / 38 / 2 |
| **All (85)** | **4 / 8** | **60 / 221 / 52** (333 prompts) |
| Realistic sets only, r6–r8 (38) | 5 / 8 | 36 / 145 / 11 |

- Both figures are inside the provisional budget of R5 (median 6, maximum 10) on these sets.
- All 60 `suggested` prompts have a gold answer of yes. Of the 221 `unresolved` prompts, 142
  have a gold answer of yes and 79 of no. All 52 `none` prompts have a gold answer of no.
- So the résumé gives a "mentions this" hint without a caution for 60 of 333 prompts (18%).
  No answer is pre-selected for any prompt.
- With the gold labels as the user's answers, the confirmed set equals the gold found-set
  among required and preferred skills for every pair. That is true by construction and is a
  check on plumbing only.

### 5.4 What R1 and F4 changed

Nothing on the historical sets: mention counts are identical to revision 3 (210 affirmed, 234
with a cue, 198 in an unsupported form, of 642), and the 250 migration records are the same.
Seventeen targeted checks behave as ruled:
- "CAD: SolidWorks, Creo", a two-line labelled block and "Soft skills:" are suggested;
- "Planned:", "Wishlist:", "CAD (planned):" and "CAD : SolidWorks" stay unresolved;
- "Machine Learning, Python" is suggested and a "Machine Learning:" heading fires no trigger;
  "Learning Machine Learning" and a "Currently Learning:" heading stay unresolved;
- a present-tense line stays unresolved;
- F4: "- [ ] MATLAB / - [x] Python" is unresolved for both; one unsupported unit in a Skills
  section ("- Python (in progress)", or a trailing paragraph) makes every skill in that
  section unresolved; a clean Skills section followed by an Experience line stays suggested.

### 5.5 Documents and mentions (unchanged from revision 3)

| Set | Résumés | All suggestions unresolved by a document trigger | No suggested skill for any reason |
|---|---|---|---|
| postings | 48 | 0 | 31 |
| regression_r6 | 14 | 2 | 3 |
| r7 | 12 | 0 | 1 |
| r8 | 12 | 0 | 4 |

Independent pairs: 51 labels; 0 suggested; 25 unresolved where the gold is affirmed; 23
unresolved where it is not; 3 skills not recognised.

## 6. Migration (R2–R4, F3)

### 6.1 Form

- **Status.** DRAFT. No test reads the file. No fixture, label or test has been changed, and
  the sealed manifests are untouched.
- **Scope.** The 62 fixtures in the repository. The r7 and r8 sets stay sealed.
- **The gold found-set is not redefined (F3).** `expected.found` in a fixture stays the record
  of what the person has. The migration records describe a separate thing: the résumé-side
  suggestion state.
- **Permitted causes (R2):** `cue_line`, `document_trigger`, `unsupported_form`.
- **Each record is individually traceable (F3).** It carries:
  - `source_test`, the original test id, and `source_file` with `source_sha256`, the hash of
    the fixture's blob at `fa1555e`;
  - the original label unchanged, or the skill, with `oracle_answer`, the original value;
  - `expected_status` (mention) or `expected_suggestion` (skill), always `unresolved`;
  - `cause` and `classification`.
- **`classification`** is `usefulness_loss` when the original value was affirmed or found, and
  `conservative` when it was negated, hypothetical or not found.
- **`unresolved` is not a passing classification.** Every record whose original value was
  correct is reported as a usefulness loss in every evaluation report.

### 6.2 What it holds (`MIGRATION_LEDGER.md` lists every row)

| | Records |
|---|---|
| All | 250 in 59 fixtures: 74 mention labels, 176 skills |
| Usefulness losses | 184 |
| Conservative | 66 |
| **Cause is unsupported form only (R2)** | **88** (6 labels, 82 skills) in 46 fixtures; **all 88 are usefulness losses** |
| Cause includes a cue line or a document trigger | 162 (68 labels, 94 skills) in 24 fixtures |

The 59 fixtures are exactly the 59 failing fixture tests: 13 have only cue or trigger records,
35 have only unsupported-form records, 11 have both.

### 6.3 Retired test inputs as line-rule cases

`line_rule_cases` holds 28 inputs from the retired tests: 24 from `test_stage4_scope.py`
(9 + 9 + 2 + 1 + 3), 1 from `test_negation_after_is_posting_only` and 3 from
`test_resume_negation_is_narrow`. The ledger's Part C lists each. Each
keeps the original assertion as `oracle_answer`. Every skill in all 28 is `unresolved`.

### 6.4 The five `test_job_match.py` tests (R3, F1)

- **Inputs.** `TEST_JOB_MATCH_PROPOSED.diff` replaces each synthetic résumé with one in a
  supported form. The originals are kept in the ledger (Part D1) and in the expectations
  file. Checked on a scratch copy against the `fa1555e` interface: the five pass today and
  under the simulated rule.
- **Assertions.** Under F1 the assertions on `score` and `found` in these tests move to the
  two interfaces. So the diff is the input half only. The assertion half is specified line
  by line in `API_AND_MIGRATION_PLAN.md` §3 and cannot be written as a runnable diff until
  the interfaces exist.

### 6.5 Checker tests in `test_check_fixture.py` (R4)

`TEST_CHECK_FIXTURE_PROPOSED.diff`, one migration. It touches exactly the four failing
tests and adds one:
- a new constant `POST_NOTES` and two small helpers, `pcheck` and `plab`, label the
  two-status line in a synthetic posting, because a résumé unit gives every skill on it one
  status;
- the four tests call `pcheck`/`plab` in place of `check`/`lab`; in
  `test_unindexed_label_asserts_every_occurrence` the two `resume_text` overrides become
  `posting_text` overrides;
- the module constants `POST` and `RESUME`, the helper `lab`, and the other four tests are
  **not changed** and keep their résumé-side inputs. (The first draft of this diff rewrote
  the shared constants and so moved those four tests to the posting side as well. That is
  withdrawn.)
- **new** `test_resume_labels_one_state_per_unit` keeps résumé-side coverage: labels on two
  units resolve to different statuses, two occurrence-indexed labels on one unit both pass,
  and a wrong status is reported.

Checked on a scratch copy: under the simulated rule all 9 pass. At `fa1555e` the 8 existing
tests pass and the new test fails, as it must, because `unresolved` does not exist there yet.
So this diff can only be applied together with the engine change.

### 6.6 How fixture tests read after migration (F3)

A migrated fixture test makes three separate checks. None is skipped, exempted or marked as
an expected failure.

1. **Posting side.** The required, preferred, unscored and excluded sets, line labels, posting
   mention labels and evidence labels are asserted exactly as today.
2. **Gold found-set, through confirmation.** The gold found-set is turned into answers: yes
   for each required or preferred skill in it, no for the others. The scoring interface must
   then count exactly the gold-found required and preferred skills. With no answers it must
   count nothing and return no number.
3. **Suggestion quality, as its own measure.**
   - **Scope.** This check covers the skills the gold found-set covers: those the posting
     lists as required, preferred or unscored. Excluded-tier skills carry a suggestion but
     are outside the gold found-set, as they are today; 7 of them are `suggested` in 3
     fixtures. Skills the résumé mentions that the posting does not list have no entry in
     the extraction result at all.
   - Within that scope, no skill outside the gold found-set may be `suggested`. One such
     skill fails the test.
   - Every gold-found skill that is not `suggested`, and every résumé mention label whose
     status differs from its gold status, must match one migration record with its recorded
     cause. A difference with no record fails the test.
   - Every recorded skill must have its recorded suggestion. This also pins the 32
     conservative records whose original value was not found, so all 250 records are matched
     one to one.
   - Each matched record is counted in the report as a usefulness loss or a conservative
     record. A green test is not a passing classification.

Gold-found skills in the unscored tier are never prompted (F2), so check 2 does not cover
them. They are covered by check 3 only.

## 7. Display and PDF export (R7, F4)

1. **Input.** `generate_pdf` takes, per skill: requirement, suggestion, answer; and the result
   of the scoring interface.
2. **Score line.** A number is printed only when every required and preferred skill is
   answered, under the heading "Self-reported skill coverage", with "N skills confirmed by
   you". Otherwise: "Coverage not shown: N skills still need your answer".
3. **Skill table.** Columns are Skill, Requirement, Your answer, Résumé hint.
   - Your answer: "Confirmed by you", "You said no", "Not answered".
   - Résumé hint: the neutral texts of §4.6.
4. A suggestion never appears as confirmed, and never under "Skills You Have".
5. **Unscored posting skills** are listed separately, with their hint and no answer column.
6. **No résumé text.** Only skill names and fixed text are printed.
7. **Encoding.** Latin-1-safe wording with the core Helvetica font, or an embedded font.
8. **Bullets.** Only unflagged bullets built from the user's own words (§4.7).

## 8. Gate 1 thresholds and round 9

**Safety (each blocks Gate 1).**

| Gate | Threshold |
|---|---|
| R6: a skill counted as demonstrated or confirmed without explicit affirmative user confirmation, in the self-reported score, any list, the PDF or stored answers | 0, on round 9 and on every existing set |
| The production result schema exposing an unconfirmed coverage score or `found` flag (F1) | none |
| A coverage number shown while a required or preferred skill is unanswered | never |
| A pre-selected answer, a pre-ticked yes or an accept-all control | none |
| A recognised required or preferred skill left unprompted (F2) | none |
| A confirmation producing a bullet, an achievement, professional experience or a proficiency level (F4) | never |
| A skip, xfail or blanket exemption in the migrated tests (F3) | none |
| Posting-side output against `fa1555e` on the 62 repository fixtures | identical |
| Résumé text in reason codes, logs or the PDF | none |

**Usefulness (provisional, R5), measured on the 15 owner-evaluation pairs.**

| Metric | Threshold |
|---|---|
| Distinct skill confirmations per pair, median | 6 or fewer |
| Distinct skill confirmations per pair, maximum | 10 or fewer |
| Posting requirements omitted to meet the budget | none, ever. A pair over budget is reported as over budget. |
| Wrong suggestions | each one listed; the threshold is decision D1 |
| Usefulness losses | each one listed and counted |

**Round 9 and independent testing (F4).**
- Probes are written fresh by a reviewer who has not seen the cue, verb, heading or category
  lists, this file, the scripts or the expectations file. The author gets category names
  only. No category is excluded.
- **Every known misleading-hint pattern of §11 is a named category** for that author:
  separate-paragraph disclaimers, checkbox and form layouts, meaningful punctuation, and
  limited, classroom-only or second-hand use written as experience. For each, the test is
  that the skill is never counted without the user's yes; the hint shown is recorded.
- Disqualified: the author of this contract and every reviewer who has read these lists.
- All probes and examples in this folder are development data.
- `ROUND9_SPEC.md` is stale. Sealing round 9 is not authorised.

## 9. Reconciliations

- **86 versus 85 pairs.** `email_no_cues` has no required or preferred skill, so it has no
  coverage to compute. Per-pair figures use 85; wrong-suggestion checks use all 86.
- **Tests.** 370 in the suite. Revision 2: 50 listed, 49 failing in the simulation.
  Revisions 3 and 4: 93 listed, 92 failing in the simulation. The listed-but-passing test is
  `test_cues_never_reach_back`. Two `test_eval_*` tests run the evaluator in a separate
  process that the simulation does not patch; they fail under the rule, which makes 95
  listed and 94 failing (§3.2).
- **Records.** 250 = 162 with a cue line or trigger + 88 with unsupported form only.
  250 = 184 usefulness losses + 66 conservative. 250 = 74 labels + 176 skills.
- **Fixtures.** 62 in the repository; 59 fail and have records; 3 pass
  (`acr_can_word`, `acr_plc_forms`, `full_indeed_dash`).

## 10. Decisions still open

Settled by the final rulings: the interface split (F1), who is prompted and unscored skills
(F2), the migrated fixture assertion (F3), and the structural safeguards (F4).

| # | Decision | What this draft assumes |
|---|---|---|
| D1 | A threshold for wrong suggestions, and your approval of the hint and prompt texts in §4.6. | No threshold. 0 on history; 5 of 10 on the known patterns. |
| D2 | **The live app already shows unconfirmed coverage, outside this engine.** The Gap tab, the Audit tab and the PDF compute "Skills Coverage", "Industry Match", "Skills You Have" and "Coverage Score" from keyword matches in the résumé text, through `engine/gap_analysis.py` and `ui/tab_audit.py`. `match_posting` has no interface consumer at `fa1555e`. Does R6 apply to those screens? | Yes, by R6's wording. The plan (§6) lists them as a work package but does not design it. |
| D3 | What a "gap" is for the bullet builder, now that there is no `found` flag. | A skill the user confirmed that the résumé does not clearly show (suggestion `unresolved` or `none`). The user then describes it in their own words. Plan §4. |
| D4 | The evaluation script's provisional 0.85 holdout gate on "resume matching". | It becomes two diagnostics, suggestion precision and recall, and stops being a pass/fail gate; Gate 1 uses §8. Two `test_eval_*` tests pass or fail on this ruling (§3.2). Plan §5. |
| D5 | Do the document triggers stay? | Yes, unchanged. They only turn hints to "please check the wording". |
| D6 | The 15 owner-evaluation pairs (10 development, 5 held out). | Not supplied; `data/eval/` holds only the README and the schema. |

## 11. Limits of this draft

- All figures come from an in-memory simulation, not an implementation. The simulation does
  not model the two interfaces of §2.
- **Known misleading hints (F4).** After the two safeguards, the résumé rule still gives a
  plain "mentions this" hint in the rows marked open. None of them counts without the user's yes.
  All examples were run.

| Pattern | Example | Hint after F4 |
|---|---|---|
| Disclaimer in a separate unit inside the Skills section | Skills "Python, MATLAB", then "Listed tools were not part of my job." | Closed within the Skills section: unresolved |
| Same | Skills "SolidWorks", then "Never touched SW on the job, only in a single class." | Closed within the Skills section: unresolved |
| Same | Skills "Python, SQL", then "All self-taught; nothing professional." | Closed within the Skills section: unresolved |
| The same disclaimer after another heading | Skills "Python, MATLAB", then an Experience section, then "Listed tools were not part of my job." | **Open: suggested** |
| Disclaimer in a separate unit, after an Experience line | "- Designed brackets in SolidWorks", then "The CAD work above was done by a teammate." | **Open: suggested** |
| Unchecked checkbox | Skills "- [ ] MATLAB" / "- [x] Python" | Closed: both unresolved |
| Meaningful punctuation | Skills "MATLAB (*)" | Closed: unresolved |
| Meaningful punctuation | Skills "MATLAB: -" | **Open: suggested** |
| Limited use as a Form B line | "- Used SolidWorks once in a class" | **Open: suggested** |
| Second-hand use | "- Managed a team that used SolidWorks" | **Open: suggested** |
| Tutorial | "- Completed a SolidWorks tutorial" | **Open: suggested** |

- **What confirmation does not solve.** A user can answer yes to a skill they barely used.
  The result is then their own statement, labelled self-reported. The contract does not
  verify it.
- A hint may bias the answer. Nothing here measures that.
- The prompt counts come from adversarial history sets, not ordinary résumés.
- The independent pairs, the 32 probes, the 16 hard-wrap probes and the 10 examples have all
  been used for analysis.
- The assertion changes in `API_AND_MIGRATION_PLAN.md` have not been run; the interfaces they
  call do not exist yet.
