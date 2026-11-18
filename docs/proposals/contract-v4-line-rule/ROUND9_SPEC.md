> **SUPERSEDED / STALE (2026-11-13).** Kept as the record behind `CONTRACT_V4_LINE_RULE.md` revision 3, which replaces it. See `README.md` in this folder.

# Round 9 sealed evaluation set: specification v2 (PROPOSED; sealing not authorised)

## Purpose
Round 9 measures Revision 5A on text unseen by the rules author, the implementer and the
reviewer. Safety (critical errors) and usefulness (useful accuracy, coverage, availability,
appropriate abstention) are reported separately (contract §6).

## Isolation (M9)
- **Author.**
  - A new independent agent writes the set: not the coordinator, the implementer, either
    reviewer, or an earlier sealed-set author.
  - The author has **no repository access**. It receives only:
    - the label schema, pasted in;
    - the category names below, without example phrasings;
    - the R2.6 severity table;
    - the D1 ruling.
  - It never sees cue lists, thresholds, engine code or engine output.
- **Labels.** Labels state what the text means to a careful human reader. `ambiguous: true`
  is set before sealing, only where a careful reader genuinely cannot tell.
- **Storage.**
  - Files are written outside the repository and the implementer's working tree, in
    `scratchpad/sealed_r9/`, with `SEALED_MANIFEST.txt` (SHA-256 per file plus a combined
    hash).
  - The coordinator verifies the manifest with `sha256sum -c` without opening any file, and
    records the hash in `docs/UNSEEN_SET.md` on the 5A branch before any 5A code exists.
  - The implementer's prompt forbids reading `sealed_r*`, and the reviewer checks this in the
    transcript. *Shortcut: this is enforced by instruction and review, not by file
    permissions. Move the set to an access-controlled location if stronger isolation is
    needed.*
- **Runs.**
  - Nothing is run on round 9 until the implementation is frozen.
  - Two runs then happen back to back: first the baseline from a `fa1555e` worktree, then
    5A.
  - Results are not used to tune anything, and no remediation round follows.

## Composition

### Gate set: 48 pairs, plus 12 format documents
The gate set is sized so that each gate's denominator is expected to reach at least 20
(B5).

| Category | Pairs | Requirement |
|---|---|---|
| Positive achievements written with a negation word | 8 | At least 3 with the same skill clearly affirmed elsewhere in the résumé, at least 3 without. |
| Direct skill negations | 8 | Varied wording; at least 4 with the skill required or preferred in the posting. |
| Genuinely ambiguous qualification | 8 | At least 1 `ambiguous` mention per pair in a required or preferred position. |
| Trailing qualifiers (pending, negating, level) | 8 | At least 2 level qualifiers (D1). |
| Comma lists with unknown items after a cue | 6 | Unknown items at the start, middle and end. |
| Contrasting clauses | 4 | Both cases: contrasts that reverse polarity and contrasts that don't. |
| Ordinary realistic pairs, no traps | 6 | These form the availability baseline. |

The format documents:
- **6 genuinely unsupported:** 2 paragraph-only résumés, 2 column/table fragments, 1
  non-English posting, 1 non-English résumé.
- **6 look-alikes that must not be refused:** skill-per-line résumé, long contact block,
  long certification block, terse list-only skills résumé, accented-name English résumé,
  three-line bio résumé with bullets.

Each format document is paired with an ordinary counterpart.

### Expected denominators
- Résumé labels: about 150 or more.
- Abstained units: about 25 or more. That comes from 8 ambiguous pairs, 8 achievement pairs
  and trailing qualifiers, so it is not guaranteed; if it falls below 20, appropriate
  abstention is INSUFFICIENT.
- Gold-scored pairs: about 35 or more.

### Probe set: 12 pairs, report-only (owner decision D9)
- **Content:** residual patterns N1–N8: another sentence, heading negation, words outside the
  cue list, except/but-exclusion, question form, trailing negation followed by more words,
  hobbies section.
- **Why separate:** 5A doesn't claim to handle these patterns. Putting them in the gate set
  would make the stopping rule fire by design (B5).
- **Reporting:** probe results are reported in full. Every critical error found there is
  added to the risk register and blocks any claim that 5A handles that pattern.
- **D9 ruling needed:** if the owner instead rules that probe critical errors count against
  the release gate, then 5A is expected to stop. N1–N8 would then have to be closed before
  round 9.

## Labels (added to the existing fixture schema)
- **`mention_labels[].ambiguous`** (bool): no gold status is required when true.
- **`expected.score_mode`**: `scored`, `withheld` or `unavailable`.
  - `withheld` only when a required or preferred skill is genuinely ambiguous, or a document
    is unsupported.
- **`unsupported`** (per document): a bool and a reason.
- **`critical_traps`**: as in rounds 6–8.
- **`set`**: `gate` or `probe`.

## Reporting (after the implementation is frozen)
- The 4×4 confusion matrix.
- Every §6.2 metric, each with its numerator and denominator.
- A per-code hit count (Q1, Q2, F1–F4).
- Every abstention, with its gold status and `ambiguous` flag.
- The conversion lists: correct → abstained, and incorrect → abstained (not a fix).
- Gate set and probe set reported separately.
- Original labels only. A dispute is recorded with its direction, and nothing is
  relabelled.

## Stopping rule
The work goes back to the owner, with no remediation round, on any of these in the gate set:
- a critical error;
- a refused look-alike;
- any gate FAIL or INSUFFICIENT.
