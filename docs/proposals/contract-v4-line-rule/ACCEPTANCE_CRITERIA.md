# Acceptance criteria for contract v4 (FROZEN; docs only, nothing implemented)

| | |
|---|---|
| Status | FROZEN 2026-11-13 by owner ruling; changes need a new owner ruling |
| Base | `upgrade/review-revisions` @ `fa1555e` (the code baseline) |
| Implementation branch | Starts from the commit on `docs/contract-v4-line-rule` that records the round-9 manifest hashes. That commit also holds this file and Part E of the ledger (§E). |
| Gate 1 | **Blocked** (§C) |

**Supersedes** `CONTRACT_V4_LINE_RULE.md` §10 (open decisions) and `API_AND_MIGRATION_PLAN.md` §7 (work packages) where they differ. The places where this file differs from the other text:

| Where | What changes |
|---|---|
| Plan §1.2 signature | `self_reported_coverage(targets, answers)`, not `(extraction, answers)`. A posting `Extraction` is one kind of target; the market top-N list is the other (§B). |
| Contract §2 and §7.2, coverage labels | The label "Self-reported skill coverage" is replaced by the two labels of §B (proposed wording, A2 item f). |
| Contract §7.2, withheld text | "Coverage not shown: N skills still need your answer" is replaced by the withheld message of §B (proposed wording, A2 item f). |
| Contract §8, budget scope | The budget was measured on the 15 owner-evaluation pairs. It now applies to résumé/job-posting pairs in general, and not to the market tabs (decision 3). |
| Contract §4.6, hint texts | Replaced by decision 2. The prompt text and choices of §4.6 are NOT approved by decision 2 (A2 item e). |
| Contract §5.2, "10 examples" | This file counts the 11 rows of the §11 table. |

**Corrections to the contract (flagged for the owner; the contract and Part C are not edited).**
- `tests/test_stage4_scope.py::test_cues_never_reach_back` calls `qualify(m)`, which applies the posting rules (docstring at `engine/match_stages.py:461-468`). It is a posting-side test. Contract §3.2 (the table row at line 226) and ledger Part C row 21 wrongly treat it as a résumé case and retire it. It is kept unchanged (ledger Part E, E1).

## A. Owner decisions (final)

Only what the owner ruled. Everything that is a proposed detail is in A2.

1. **Wrong hints.**
   - A wrong plain hint is a `suggested` hint for a skill whose gold answer is no (which skills count: A2 item d).
   - Provisional gate: at most 5% of all plain hints across the independent evaluation, and never more than one per pair.
   - Every wrong hint is reported: pair id and skill name only, no text.
   - All known misleading-hint examples (the 11 rows of contract §11) are kept as regression cases.
2. **Hint texts (approved).** These replace the hint texts of contract §4.6.

   | Suggestion | Hint text |
   |---|---|
   | `suggested` | "Mentioned in your résumé — please confirm." |
   | `unresolved` | "Mentioned in your résumé — please check the wording, then confirm." |
   | `none` | "Not mentioned in your résumé — please answer." |

   - The PDF uses a hyphen in place of the em dash when the core font is used (contract §7.7).
   - A suggestion is never described as verified, professional experience or proficiency.
3. **Prompt budget.** Median 6 or fewer and maximum 10 or fewer distinct confirmation prompts apply to résumé/job-posting pairs. The market Gap and Audit tabs may present more skills. They may never drop a skill from the denominator to meet a budget.
4. **Gap and Audit percentages.** Shown only after every skill in that screen's comparison group has an explicit answer. Market coverage is labelled separately from posting coverage.
5. **Evidence improvement.** A plain yes may start an invitation to describe relevant work. No achievement bullet is ever generated without evidence text typed by the user.
6. **Session-only confirmation model stays.** A confirmation is a self-reported skill claim. It is not proof of professional experience, proficiency level or measurable achievement, and no display says otherwise.

**Settled by the previous ruling (still in force).**
- Legacy scores are withheld until connected to confirmation.
- Historical extraction metrics and the 0.85 threshold are kept as diagnostics. On the résumé side they never set the evaluator's exit code. The "posting required" and "posting preferred" 0.85 gates are unchanged.
- Three gap kinds:

  | Kind | What the user gets |
  |---|---|
  | Confirmed, not shown in the résumé | An evidence-improvement invitation (decision 5) |
  | Denied | Learning paths |
  | Unanswered | Nothing personalised |

- Document triggers stay. They are reasons to suppress plain hints. They never establish absence and never authorise a score.

### A2. Proposed operationalisation (not ruled; needs the owner's confirmation)

| Item | Proposal | Note |
|---|---|---|
| a | If the pooled evaluation has fewer than 20 plain hints, the hint-quality result is INSUFFICIENT, which blocks. | With the no-remediation stopping rule (§F), an INSUFFICIENT result would end round 9. The owner should confirm this before the run. |
| b | Round 9 and the 15 owner pairs are pooled for the 5% rate ("across the independent evaluation" is the owner's wording, kept in A). | |
| c | The 5 closed rows of contract §11 are blocking regression cases and must stay closed. The 6 open rows are reported and must never be counted without a yes. | |
| d | A wrong hint is counted only for required and preferred skills. | Alternative: also count hints in the separate unscored list. |
| e | Prompt text "Do you have hands-on experience with {skill}?" with the choices "Yes", "Yes, and I'll describe it", "No". | **Still awaiting approval.** The owner approved the hint messages only. |
| f | Labels "Self-reported coverage of this posting" and "Self-reported coverage of the top N market skills"; withheld message "Coverage not shown until you confirm your skills". | Wording is mine. |
| g | Round 9 has 30 pairs in the composition of `round9/AUTHOR_INSTRUCTIONS.md`. | |

## B. One authoritative `Coverage` result

`engine/job_match.py::self_reported_coverage(targets, answers) -> Coverage` is:
- the only caller of `compute_coverage_score`;
- the only source of any user-facing coverage number, "have" list, learning-recommendation input or PDF coverage content.

Fields are as in plan §1.2, plus:
- `Coverage.target`: `"posting"` or `"market"`;
- `Coverage.denominator`: the skill names counted.

| | Posting | Market |
|---|---|---|
| Targets | Recognised required and preferred skills of the pasted posting (from `extract_match`) | The top-N market skills the screen shows, all in the required group. Gap tab: sidebar `top_n`. Audit tab: its slider, 5 to 30 in steps of 5, default 15 (`ui/tab_audit.py:161-168`) |
| Hints | From `extract_match` | Each market target skill carries a suggestion from the same résumé rule, applied to the résumé only (no posting) |
| Formula | `100 * (0.8R + 0.2P)`, unchanged | confirmed / N, as a percentage |
| Label (A2 item f) | "Self-reported coverage of this posting" | "Self-reported coverage of the top N market skills" |
| Count line | "N of M skills confirmed by you" | "N of M skills confirmed by you" |
| Mixing | Never mixed or averaged with market coverage | Never mixed or averaged with posting coverage |

Both targets:
- mode is `withheld` while any target skill is unanswered;
- one session-state answer map, keyed by skill, is shared by every screen and the PDF.

| Consumer | Reads |
|---|---|
| Gap tab | `Coverage` (market) |
| Audit tab | `Coverage` (market) |
| Donut chart | `Coverage` counts |
| Learning tab | `Coverage.denied` |
| PDF hand-off in `app.py` | `Coverage` objects |
| `generate_pdf` | `Coverage` objects |

No consumer may compute its own count, percentage or list.

## C. Release gates (four, each reported separately)

**Gate 1 stays blocked until all four pass on round 9, the 15 owner-labelled pairs are supplied and pass, and independent acceptance is given.**

**1. Confirmation safety (zero critical errors).** The safety table of contract §8, plus two rows:

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
| **New:** a legacy path (UI, session state, PDF) showing an unconfirmed score or "have" list | none |
| **New:** market and posting coverage shown under each other's label | never |

**2. Useful coverage.**
- Prompt budget on résumé/job-posting pairs per decision 3.
- No posting requirement omitted.
- Every usefulness loss listed and counted.
- With the gold answers as the user's answers, the confirmed set equals the gold set.

**3. Hint quality.** Decision 1, with the details of A2 once the owner confirms them.

**4. End-to-end displays.** The integration test of §D.

## D. Required integration test: `tests/test_no_unconfirmed_coverage.py`

Specification only. The file is not written yet.

1. **Structure.**
   - `compute_gap_score`, `_check_resume_gaps`, `analyze_gap`'s present/missing classification and `match_posting` no longer exist.
   - A source scan of `app.py`, `ui/`, `export/` and `engine/` finds exactly one call to `compute_coverage_score`, inside `self_reported_coverage`.
2. **App, no answers.** Run `app.py` with `streamlit.testing.v1.AppTest`, with a résumé naming every top skill.
   - No metric, progress bar or chart carries a coverage number.
   - No "Skills You Have" heading.
   - Session state has no `score`, `present` or `match_score` key, and no `gap_results` or `audit_results` carrying them.
   - The withheld message is shown.
3. **PDF, no answers.**
   - `generate_pdf` rejects the old `gap_results` dict.
   - With a withheld `Coverage`, the text extracted with PyMuPDF has no coverage percentage and no "Skills You Have".
4. **Partial answers.** All answered but one still withholds.
5. **Positive control.** With every skill answered, the number appears exactly once per target, under the correct label (posting and market), in the app and in the PDF, and equals the expected value.

Streamlit 1.55 (with `AppTest`) and PyMuPDF are installed.

## E. Work packages and sequence (not started; need explicit owner authorisation)

One new branch, started from the commit on `docs/contract-v4-line-rule` that records the round-9 manifest hashes. Each work package: the worker implements, an independent reviewer passes, then one commit.

| WP | Scope | Depends on | Acceptance |
|---|---|---|---|
| 1. Withhold all legacy unconfirmed coverage | Remove every number, "Skills You Have" list, donut and "raise your match score" line listed in plan §6, plus `ui/tab_audit.py:210-235, 296-299, 360`. Show "Coverage not shown until you confirm your skills". Drop score and present from session state and the PDF. | Nothing | Integration test parts 1-3, for the legacy paths |
| 2. Conservative evidence suggestions | The résumé rule (contract §1) | WP1 | The old plan WP1 acceptance: every list and table row of contract §1 as a test; the 28 line-rule cases; the 17 targeted checks; output equal to `sim_confirm_v7.py` on the 62 repository fixtures; posting output identical to `fa1555e` |
| 3. Separate extraction from confirmed scoring | Plan §1 | WP2 | The old plan WP2 acceptance: plan §3 assertions; no `score` or `found` attribute; nothing counted with no answers; unanswered withholds |
| 4. Approved test and evaluator migration | Plan §3-§5, ledger Parts A-E, including the posting-side scope re-run of ledger Part E (E1) | WP3 | Suite green, no skip or xfail; 250 records matched one to one; 184 usefulness losses reported; sealed manifests verify; no sealed fixture relabelled |
| 5. Confirmation UI | Prompts for every required and preferred skill, the approved hint texts (decision 2) and, once approved, the prompt text (A2 item e); unscored list display is in WP6 | WP3 | No pre-selected answer; no accept-all; no number while one skill is unanswered; nothing logged |
| 6. Connect Gap, Audit, learning and PDF to the authoritative coverage | §B; the three gap kinds; the PDF skill table, the separate unscored list and the block on flagged bullets (contract §7 items 3, 5 and 8, and §4.7 last bullet); the integration test in full | WP4, WP5 | `tests/test_no_unconfirmed_coverage.py` passes in full |

Then:
- freeze at a recorded commit;
- run round 9 once;
- the owner decides Gate 1.

**Rollback and limits.**
- `fa1555e` on `upgrade/review-revisions` is the green baseline (370 passed). It is not touched. A local tag is placed on it when implementation starts.
- No merge, push or PR without explicit owner approval.
- `fix/comma-lists` stays unmerged.

## F. Round 9

- **The kit.** `round9/` holds exactly what the author may see: `AUTHOR_INSTRUCTIONS.md`, `SCHEMA_EXAMPLE.json`, `SKILLS.json`. The procedure is in `ROUND9_KIT_README.md` (one level up, not part of the kit).
- **Isolation.**
  - The three kit files are copied to a new empty folder outside the repository and every worktree, before the author starts.
  - The author works only in that copy, reads nothing outside it and does not use the web.
  - The sealed `out/` files never enter the repository. Implementers' prompts forbid reading them.
- **Hashes.** Only the manifest hashes are committed, in `docs/UNSEEN_SET.md`, before any production change.
- **Stopping rule.** Any critical error, or any gate FAIL or INSUFFICIENT, goes back to the owner. There is no remediation round. The set becomes development data, and a new round needs a new author.
- `ROUND9_SPEC.md` stays stale.
