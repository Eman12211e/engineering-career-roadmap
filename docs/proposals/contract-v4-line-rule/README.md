# Contract v4 line rule: proposal folder (docs only)

Nothing here is production code or an approved contract. No engine, test, fixture or data
file is changed by this folder. Base: `upgrade/review-revisions` @ `fa1555e`.

## Current

| File | Status |
|---|---|
| `CONTRACT_V4_LINE_RULE.md` | **DRAFT**, revision 4 (2026-11-13): confirmation-first, owner rulings R1–R7 and final rulings F1–F5 applied. Open decisions are in its §10. Revision 3 is commit `d49574a`. |
| `API_AND_MIGRATION_PLAN.md` | **DRAFT plan, nothing implemented.** The two interfaces, every consumer of the legacy `score`/`found`, the 11 assertions, the evaluator, the bullet integration test, the legacy keyword screens, and the work packages. Its new assertions have not been run. |
| `EXPECTATIONS_LINE_RULE.DRAFT.json` | **DRAFT** migration expectations for revision 4 (250 records, three permitted causes). Not approved. No test reads it. |
| `MIGRATION_LEDGER.md` | **DRAFT.** Every migration record, retired test input and test edit, with original values. Generated from the same data. |
| `EXPECTATIONS_LINE_RULE.DRAFT.sha256` | Hash of the draft file with LF line endings. On a checkout that converts line endings, check the blob instead: `git show HEAD:docs/proposals/contract-v4-line-rule/EXPECTATIONS_LINE_RULE.DRAFT.json \| sha256sum`. |
| `TEST_CHECK_FIXTURE_PROPOSED.diff` | **PROPOSED, not applied.** The four `tests/test_check_fixture.py` edits plus the new résumé-side regression. Applies only together with the engine change. |
| `TEST_JOB_MATCH_PROPOSED.diff` | **PROPOSED, not applied.** The input half of five `tests/test_job_match.py` changes. The assertion half is in `API_AND_MIGRATION_PLAN.md` §3 and cannot be a runnable diff until the interfaces exist. |

## Simulation material: non-production, and already used

Everything in `sim/` is **non-production**. It is read-only simulation code that patches the
engine in memory; none of it is imported by the app or the tests. All of it has been **used**
to produce figures in these documents, so none of the data in it is unseen.

| File | Used for |
|---|---|
| `sim/sim_confirm_v7.py` | Revision 4 figures: confirmations per pair, wrong suggestions, the 10 known-pattern examples, 17 targeted checks. It patches the `fa1555e` interface and does not model the two interfaces of the plan. |
| `sim/sim_confirm_v7_pytest.py` | Revision 4: the existing suite with the rule patched in memory. It does not reach tests that run the evaluator in a separate process (two more failures; contract §3.2). |
| `sim/gen_expectations_v7.py` | Writes the revision 4 draft expectations file and `MIGRATION_LEDGER.md` |
| `sim/v7_output.txt`, `sim/v7_pytest_failures.txt` | Output of the two revision 4 runs, 2026-11-13 |
| `sim/sim_supported_v6.py` | Revision 3 figures: history, independent pairs, the 32 probes, the 16 hard-wrap probes |
| `sim/sim_supported_v6_pytest.py` | Revision 3: the existing suite with the rule patched in memory |
| `sim/gen_expectations_v6.py` | Wrote the revision 3 draft expectations file (superseded by v7) |
| `sim/v6_output.txt`, `sim/v6_pytest_failures.txt` | Output of the two runs above, 2026-11-13 |
| `sim/sim_line_v5.py`, `sim/sim_line_v5_pytest.py` | Revision 2 figures (2026-11-10) |
| `sim/sim_line_rule.py` | First line-rule run (2026-11-10) |
| `sim/sim_restricted.py`, `sim/sim_restricted_b.py`, `sim/probe_restricted.py`, `sim/f_rules.py` | `SUPPORTED_INPUT_MVP.md` figures; `probe_restricted.py` also holds the 32 probes |
| `sim/minimal_pairs_zero_pronoun.json` | **Independent minimal pairs. Non-production. Used:** analysed on 2026-11-10 and 2026-11-13, so they are development data and can never be a held-out set. File unchanged from its author's version (sha256 starts `ee01dc02`). |

To re-run revision 4 from the repository root at `fa1555e` (the v6 scripts run the same way for revision 3):

```
python docs/proposals/contract-v4-line-rule/sim/sim_confirm_v7.py [dir holding sealed_r7/ and sealed_r8/]
python docs/proposals/contract-v4-line-rule/sim/sim_confirm_v7_pytest.py
```

The r7 and r8 sets are not in the repository. Without that directory the first script reports
the postings and regression_r6 sets only. The 2026-11-10 scripts are kept as they were run
and expect that directory as their first argument.

Not included: the scripts of the stopped Revision 5A heuristic track (`sim_variants.py`,
`sim_v5.py` and related), and the sealed r6–r8 files.

## Superseded or stale (kept as the record)

| File | Why it is kept |
|---|---|
| `SUPPORTED_INPUT_MVP.md` | The supported-input feasibility study. Its S1/S2 forms are replaced by §1.4 of the contract; its three document triggers survive in §1.8. |
| `REVISION_5A_CONTRACT.md`, `REVIEW_5A_v2.md`, `REVIEW_5A_v4.md`, `TEST_MIGRATION_5A.md` | The general-negation-heuristic track, stopped by the owner on 2026-11-10. |
| `ROUND9_SPEC.md` | Stale. The contract's §8 governs who may write round-9 probes. |
