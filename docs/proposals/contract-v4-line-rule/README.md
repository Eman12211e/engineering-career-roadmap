# Contract v4 line rule: proposal folder (docs only)

Nothing here is production code or an approved contract. No engine, test, fixture or data
file is changed by this folder. Base: `upgrade/review-revisions` @ `fa1555e`.

## Current

| File | Status |
|---|---|
| `CONTRACT_V4_LINE_RULE.md` | **DRAFT**, revision 3 (2026-11-13). For owner sign-off. Open rulings are in its §10. |
| `EXPECTATIONS_LINE_RULE.DRAFT.json` | **DRAFT** migration expectations. Not approved. No test reads it. |
| `EXPECTATIONS_LINE_RULE.DRAFT.sha256` | Hash of the draft as committed (LF line endings). On a checkout that converts line endings, check the blob instead: `git show HEAD:docs/proposals/contract-v4-line-rule/EXPECTATIONS_LINE_RULE.DRAFT.json \| sha256sum`. |
| `TEST_CHECK_FIXTURE_PROPOSED.diff` | **PROPOSED, not applied.** The four `tests/test_check_fixture.py` edits. |

## Simulation material: non-production, and already used

Everything in `sim/` is **non-production**. It is read-only simulation code that patches the
engine in memory; none of it is imported by the app or the tests. All of it has been **used**
to produce figures in these documents, so none of the data in it is unseen.

| File | Used for |
|---|---|
| `sim/sim_supported_v6.py` | Revision 3 figures: history, independent pairs, the 32 probes, the 16 hard-wrap probes |
| `sim/sim_supported_v6_pytest.py` | Revision 3: the existing suite with the rule patched in memory |
| `sim/gen_expectations_v6.py` | Writes the draft expectations file |
| `sim/v6_output.txt`, `sim/v6_pytest_failures.txt` | Output of the two runs above, 2026-11-13 |
| `sim/sim_line_v5.py`, `sim/sim_line_v5_pytest.py` | Revision 2 figures (2026-11-10) |
| `sim/sim_line_rule.py` | First line-rule run (2026-11-10) |
| `sim/sim_restricted.py`, `sim/sim_restricted_b.py`, `sim/probe_restricted.py`, `sim/f_rules.py` | `SUPPORTED_INPUT_MVP.md` figures; `probe_restricted.py` also holds the 32 probes |
| `sim/minimal_pairs_zero_pronoun.json` | **Independent minimal pairs. Non-production. Used:** analysed on 2026-11-10 and 2026-11-13, so they are development data and can never be a held-out set. File unchanged from its author's version (sha256 starts `ee01dc02`). |

To re-run revision 3 from the repository root at `fa1555e`:

```
python docs/proposals/contract-v4-line-rule/sim/sim_supported_v6.py [dir holding sealed_r7/ and sealed_r8/]
python docs/proposals/contract-v4-line-rule/sim/sim_supported_v6_pytest.py
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
