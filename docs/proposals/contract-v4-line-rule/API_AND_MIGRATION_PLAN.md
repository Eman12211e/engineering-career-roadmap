# API separation and implementation migration plan (DRAFT; nothing implemented)

- **Belongs to:** `CONTRACT_V4_LINE_RULE.md` revision 4, final owner rulings F1–F5 (2026-11-13).
- **Base:** `fa1555e`. Every file and line reference below is to that commit.
- **Status:** plan only. No engine, interface, test, evaluator or fixture has been changed.
  The new assertions below have **not been run**, because the interfaces they call do not
  exist. Names are proposals. **Gate 1 is blocked.**

## 1. The two interfaces (F1)

### 1.1 Extraction: `extract_match(posting, resume) -> Extraction`

| Field | Meaning |
|---|---|
| `required`, `preferred`, `unscored`, `excluded` | Tuples of `SkillSuggestion`, in `keywords.json` order, as the four groups are today |
| `SkillSuggestion.skill`, `.category`, `.requirement`, `.section` | As `SkillMatch` today |
| `SkillSuggestion.posting_line`, `.posting_span` | The posting evidence, as today |
| `SkillSuggestion.suggestion` | `"suggested"`, `"unresolved"` or `"none"` (contract §1.9) |
| `SkillSuggestion.resume_line`, `.resume_span` | The first résumé mention of the skill, whatever its status; `None` when the suggestion is `"none"` |
| `SkillSuggestion.reasons` | Reason codes from the fixed list; never résumé text |
| `Extraction.doc_triggers` | Names of the document triggers that fired |

`Extraction` has **no `score` and no `found`**. `SkillMatch.found` and `MatchResult.score` are
removed from the production schema, not renamed.

### 1.2 Scoring: `self_reported_coverage(extraction, answers) -> Coverage`

`answers` maps a skill name to `"yes"`, `"yes_with_evidence"` or `"no"`. A skill absent from the
map is unanswered.

| Field | Meaning |
|---|---|
| `Coverage.mode` | `"scored"`, `"withheld"` (a required or preferred skill is unanswered) or `"unavailable"` (the posting has no required or preferred skill) |
| `Coverage.score` | A number only in mode `"scored"`; otherwise `None` |
| `Coverage.confirmed`, `.denied`, `.unanswered` | Skill names, required and preferred only |
| `Coverage.confirmed_count` | Shown with the score |
| `Coverage.answers` | The answer given for each required and preferred skill, so "yes" and "yes with evidence" stay distinguishable |

- An answer for a skill that is not required or preferred is ignored by the score.
- An answer value outside the three allowed ones raises `ValueError` without echoing input.
- `compute_coverage_score` (the arithmetic) is unchanged and is called only from here.

### 1.3 What goes away

`match_posting` is removed. Keeping it as an alias for extraction would keep a function whose
name promises a match; keeping it with `found` and `score` is what F1 forbids.
`split_posting_requirements` is posting-only and stays as it is.

## 2. Every consumer of the legacy `score` and `found`

Found by searching the repository at `fa1555e` for `match_posting`, `MatchResult`, `SkillMatch`,
`.found`, `.score`, `resume_line` and `gap_results`.

| Consumer | Uses | Plan |
|---|---|---|
| `engine/job_match.py` | Defines `SkillMatch.found`, `MatchResult.score`, `match_posting` | Replaced by §1 |
| `tests/test_job_match.py` | 11 `assert` lines on `.found` or `.score`; other calls for posting groups and evidence | §3 |
| `tests/test_job_match.py`, the seven `test_eval_*` tests (lines 172–217) | Run `scripts/evaluate_matching.py` in a separate process | §5.3. Two of them, `test_eval_pass_exit_0` and `test_eval_duty_only_skill_in_resume_is_not_spurious`, fail under the rule while "resume matching" is a gate; the in-memory simulation does not reach them |
| `tests/test_integration.py:33-41` | Bullet gaps from `not m.found` | §4 |
| `tests/test_cue_binding.py:58` | Posting groups only | Call `extract_match`; assertion unchanged |
| `tests/test_fixtures.py`, `tests/test_check_fixture.py` | Through `scripts/evaluate_matching.py::check_fixture` | §5 |
| `scripts/evaluate_matching.py` | `result_sets` found-set (line 53); `check_fixture` (line 100); `_measure` "resume matching" precision and recall (lines 287–299) and the 0.85 holdout gate (lines 317–326) | §5 |
| `docs/SCORING.md` generated section | Written by `--update-docs` from the evaluator | Regenerated after §5 |
| `app.py`, `ui/*`, `export/pdf_export.py` | **None of them calls `match_posting`.** They use the separate legacy keyword path of §6. | §6 |

## 3. The 11 `score`/`found` assertions in `tests/test_job_match.py`

`x` stands for `extract_match(...)` with the same posting, and `cov(answers)` for
`self_reported_coverage(x, answers)`. Inputs follow `TEST_JOB_MATCH_PROPOSED.diff` where that
diff changes them; original inputs are in the ledger, Part D1.

| Line | Test | Assertion today | Proposed assertion | Meaning kept |
|---|---|---|---|---|
| 33 | `test_score_neither_is_none_not_zero` | `match_posting(...).score is None` | `cov({}).score is None and cov({}).mode == "unavailable"` | No scored skill gives no number, not zero |
| 49 | `test_headingless_posting_is_unscored_with_score_none` | `not r.required and not r.preferred and r.score is None` | `not x.required and not x.preferred and cov({}).mode == "unavailable"` | Same |
| 51 | same test | `[m.found for m in r.unscored] == [False, True]` | `[s.suggestion for s in x.unscored] == ["none", "suggested"]` | Unscored skills carry a hint and no answer |
| 62 | `test_required_and_preferred_score` | `r.score == pytest.approx(80)` | `cov({"SolidWorks": "yes", "Python": "no"}).score == pytest.approx(80)`; and new: `cov({}).score is None and cov({}).mode == "withheld"`; `cov({"SolidWorks": "yes"}).mode == "withheld"` | The 0.8/0.2 weighting; plus R6 and R7 |
| 68 | `test_excluded_section_never_scores` | `names(r.required) == ["SolidWorks"] and r.score == 100` | `names(x.required) == ["SolidWorks"] and cov({"SolidWorks": "yes"}).score == 100`; and new: an answer for the excluded skill changes nothing | Excluded skills never score |
| 87 | `test_negated_resume_not_a_match` | `not r.required[0].found and r.required[0].resume_line is None` | `x.required[0].suggestion == "unresolved" and cov({}).score is None and cov({"Finite Element Analysis": "no"}).score == 0` | A disclaimed skill is never counted. The résumé line is now reported as evidence for the hint, so the `resume_line is None` half is dropped and recorded here |
| 94 | `test_resume_negation_is_narrow` (3 params) | `r.required[0].found` | **Retired with its test** (contract §3.2); inputs are line-rule cases in the ledger, Part C | — |
| 101 | `test_ordinary_words_do_not_match` (7 params) | `match_posting(...).score is None` | `x.required == () and cov({}).mode == "unavailable"` | Ordinary words are not skills |
| 106 | `test_case_sensitive_skill_from_data` | `match_posting(...).score is None` | `x.required == () and cov({}).mode == "unavailable"` | Same |
| 112 | `test_solid_works_variant_and_plc_acronym` | `[(m.skill, m.found) ...] == [("SolidWorks", True), ("PLC Programming", True)]` | `[(s.skill, s.suggestion) ...] == [("SolidWorks", "suggested"), ("PLC Programming", "suggested")]` | Alias and acronym recognition on the résumé side |
| 122 | `test_lines_and_spans_attributed` | `not b.found and ... b.resume_line is None and b.resume_span is None` | `b.suggestion == "none" and ... b.resume_line is None and b.resume_span is None` | A skill the résumé never mentions has no résumé evidence |

- Ten assertions migrate; one retires with its already-retired test.
- Lines 120, 121 and 151 use `resume_line` and `resume_span` without `found`; they stay, on
  `SkillSuggestion`.
- Every other `match_posting(...)` call in this file checks posting groups, order or errors.
  Each becomes `extract_match(...)` with its assertion unchanged.
- `test_new_fields_have_defaults` (line 71) asserts on `SkillMatch` fields that remain.
- New tests to add with this migration: no `score` or `found` attribute exists on
  `Extraction` or `SkillSuggestion`; `self_reported_coverage` with every suggestion
  `"suggested"` and no answers returns no number.

## 4. The missing-skill-to-bullet integration test

`tests/test_integration.py::test_match_gap_flows_into_bullet_evidence` today:

```python
r = job_match.match_posting("Requirements:\n- SolidWorks\n- FEA", "Designed brackets in SolidWorks.")
gaps = [m.skill for m in r.required if not m.found]
assert gaps == ["Finite Element Analysis"]
e = BulletEvidence(skill=gaps[0], action="ran finite element analysis on a bracket")
```

The gap list is built from the résumé alone. Under F1 there is no `found`.

**Proposed meaning of a gap (decision D3 in the contract):** a skill the user has
**confirmed** that the résumé does not clearly show, that is, one whose suggestion is
`"unresolved"` or `"none"`. The user then writes the bullet in their own words.

```python
x = job_match.extract_match("Requirements:\n- SolidWorks\n- FEA", "Designed brackets in SolidWorks.")
cov = job_match.self_reported_coverage(x, {"SolidWorks": "yes", "Finite Element Analysis": "yes"})
gaps = [s.skill for s in x.required if s.skill in cov.confirmed and s.suggestion != "suggested"]
assert gaps == ["Finite Element Analysis"]
e = BulletEvidence(skill=gaps[0], action="ran finite element analysis on a bracket")
```

- The rest of the test (the bullet mentions the skill; no unsupported claim) is unchanged.
- **A gap is an invitation, not a bullet.** The contract (§4.7) lets a bullet come only from
  "yes with evidence", that is, from words the user types. The gap list above includes skills
  answered with a plain yes; for those the interface may ask the user to describe the work,
  and nothing is generated unless they do. `Coverage.answers` keeps the two kinds of yes
  apart. Whether a plain yes should appear in the gap list at all is part of decision D3.
- Added assertions: with no answers, `gaps == []`; a denied skill is never a gap; nothing in
  `Coverage` or `Extraction` can construct a `BulletEvidence`.
- This keeps the contract's rule that confirmation alone never creates a bullet: the action
  text is still typed by the user and still passes `find_unsupported_claims`.

## 5. The fixture evaluator (`scripts/evaluate_matching.py`)

### 5.1 `result_sets` and `check_fixture`

| Today | After |
|---|---|
| `result_sets(res)["found"]`: skills with `m.found`, over required, preferred and unscored | Removed. Replaced by two **diagnostic** sets, `suggested` and `unresolved`, and by `confirmed_under_gold_answers` |
| `check_fixture` compares `got["found"]` with `expected["found"]` | The three checks of contract §6.6: posting side as today; gold found-set through confirmation; suggestion quality per migration record |
| Résumé mention labels compared with `_qualify(m, "resume").status` | Same comparison. A difference must match a migration record by fixture, label and cause, and is tallied as a usefulness loss or a conservative record |
| `t["doc_ok"]` true when all five sets match | True when the four posting sets match and check 2 holds |

- The gold `expected.found` in every fixture is read, never rewritten.
- `EXPECTATIONS_LINE_RULE.DRAFT.json` becomes the per-record expectation file the checker
  reads, once approved. There is no skip list and no xfail.
- `DISPUTED.json` handling is unchanged.

### 5.2 Report and generated documentation

The per-stage report keeps its posting-side lines. The résumé side reports, separately:

| Diagnostic (never a user-facing score) | Definition | Historical meaning it preserves |
|---|---|---|
| `suggestion_precision` | suggested skills that are in the reference set / suggested skills | Precision of the old "resume matching" metric |
| `suggestion_recall` | suggested skills that are in the reference set / reference set | Recall of the old "resume matching" metric |
| `wrong_suggestions` | suggested skills outside the gold found-set, each listed | The old "spurious" list |
| `usefulness_losses` | records whose original value was affirmed or found, each counted | New; required by R2 and F3 |
| `confirmations_per_pair` | median and maximum of required plus preferred skills | New; R5 |

**Scope of the two ratios.** On fixtures the reference set is the gold found-set, over
required, preferred and unscored skills. On owner-labelled pairs it is `resume_has`, over
required and preferred skills only, which is exactly what "resume matching" measures today.
The two are reported separately and never pooled.

### 5.3 Owner-labelled pairs (`_measure`, `evaluate`)

- "posting required" and "posting preferred" are unchanged, including their 0.85 gate.
- "resume matching", computed today from `m.found` against `resume_has`, is renamed to the
  two suggestion diagnostics above. **Proposed (decision D4):** it stops being a pass/fail
  gate, because a suggestion is no longer a result. Gate 1 uses the contract's §8 instead.
- Two existing tests depend on that ruling: `test_eval_pass_exit_0` and
  `test_eval_duty_only_skill_in_resume_is_not_spurious` expect exit code 0 from pairs whose
  synthetic résumés ("I know SecretResumeWord, SolidWorks and ANSYS.", "SolidWorks and
  Python") give no `suggested` skill under the rule. They pass unchanged if the gate is dropped,
  and need supported-form résumés if it is kept.
- New for owner pairs: with `resume_has` as the answers, the scoring interface must count
  exactly `resume_has` among required and preferred skills; and confirmations per pair are
  reported against the R5 budget.

## 6. Other production consumers: the legacy keyword path

These screens do not use the five-stage engine. They compute coverage from keyword matches in
the résumé text, with no negation handling and no confirmation.

| Where | What the user sees | Source |
|---|---|---|
| `ui/tab_gap.py:46-74` | "Skills Coverage N%", "Skills You Have", "Skills to Develop" | `engine/gap_analysis.py`: `analyze_gap`, `compute_gap_score` |
| `ui/tab_audit.py:40-75, 185-361` | "Industry Match N%", found and missing lists, "could raise your match score from N% to M%" | Its own keyword check |
| `export/pdf_export.py:90-110` | "Coverage Score: N%", "Skills You Have", "Skills to Develop" | `st.session_state["gap_results"]` |
| `ui/tab_learning.py:34-37` | Learning paths for `gap["missing"]` | Same session key |
| `ui/charts.py:43-51` | Donut chart labelled "Skills You Have" / "Skills to Develop" | Counts from the Gap tab |
| `app.py:176-185` | Passes `gap_results` to `generate_pdf` | Same session key |
| `app.py:66` | Subtitle "Skill coverage from your posting and résumé" | Fixed text |

By R6's wording these are skills counted as demonstrated without confirmation. Whether Path B
covers them is contract decision D2. If it does, they need their own work package: route them
through the confirmation flow, or relabel them as keyword presence and remove the percentage.
This plan does not design that.

## 7. Work packages (replaces the earlier WP list; not started)

| WP | Scope | Depends on | Acceptance |
|---|---|---|---|
| 1. Résumé rule | Units, cue test with skill names blanked, the two forms with the F4 safeguards, triggers, aggregation. Pure functions; lists in `data/match_rules.json`. | Contract approved | Every list and table row of contract §1 as a test; the 28 line-rule cases; the 17 targeted checks; output equal to `sim_confirm_v7.py` on the 62 repository fixtures; posting output identical to `fa1555e` |
| 2. Two interfaces | §1 of this plan. Remove `match_posting`, `found`, `score`. | WP1 | §3 assertions; no `score`/`found` attribute; nothing counted with no answers; unanswered withholds |
| 3. Test and evaluator migration | §3, §4, §5; the checker diff; retire and split the listed tests; per-record expectations. | WP2; decisions D3, D4 | Suite green with no skip or xfail; all 250 records matched one to one; sealed manifests verify; report shows 184 usefulness losses |
| 4. Confirmation interface | Prompts for every required and preferred skill, neutral texts, unscored list, session-only answers. | WP2; decision D1 | No pre-selected answer; no accept-all; no number while one skill is unanswered; nothing logged |
| 5. PDF and bullet guard | Contract §7; gaps per §4. | WP2, WP4 | No number when withheld; no suggestion under "Skills You Have"; a yes creates no bullet |
| 6. Legacy keyword screens | §6. | Decision D2 | Set when D2 is ruled |
| 7. Independent evaluation | Round 9, written fresh, every known misleading-hint pattern a named category; the 15 owner pairs. Frozen build, run once. | WP1–WP6 frozen; owner pairs | Contract §8 |

**Integration sequence.** One branch from `fa1555e`. WP1, WP2, WP3 in that order, each
implemented by the worker and passed by the reviewer before its commit; the suite must be
green after WP3. Then WP4 and WP5; WP6 if ruled in. Freeze. WP7 once. You decide Gate 1.
Only then a merge. `fix/comma-lists` stays unmerged.

## 8. What this plan does not establish

- None of the new assertions has been run.
- The in-memory simulation does not reach tests that start the evaluator in a separate
  process. Two such failures were found by hand in the final review; there may be other
  effects of that kind that only an implementation will show.
- The interface names are proposals.
- §6 is an inventory, not a design.
- The size of WP3 is larger than under the earlier plan: every `match_posting` call site in
  the tests and the evaluator changes.
