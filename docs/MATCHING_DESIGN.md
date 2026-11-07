# Matching engine design (frozen contract)

Status: frozen by the coordinator on 2026-11-07. Agent C implements it. Any change to the
types, signatures, data schema, precedence rules or gates below needs a coordinator decision.

Interfaces live in `engine/match_stages.py`. All spans are absolute, half-open
`(start, end)` offsets into the original input: `source[start:end]` is the evidence.

## Pipeline

| Stage | Function | Input → output | Decides |
|---|---|---|---|
| 1 Segment | `segment`, `classify_heading` | text → `Section`s → `Line`s | Where a line sits |
| 2 Find | `find_mentions` | lines → candidate `Mention`s | Which alias appears where (longest alias first, no overlaps) |
| 3 Disambiguate | `disambiguate` | mentions → kept mentions | Skill or ordinary word |
| 4 Qualify | `clause_span`, `qualify` | mention → status | affirmed / negated / hypothetical |
| 5 Decide | `importance`, `match_posting` | mentions → `MatchResult` | Importance, found, evidence |

Each stage gets its own unit tests and its own numbers in the evaluation report.

## Stage rules

1. **Segment.** Section kinds: `required`, `preferred`, `responsibilities`, `skills`,
   `experience`, `excluded`, `unknown`. Heading labels map to kinds only through the heading
   vocabulary in `data/match_rules.json`. A heading candidate is a non-bullet line that
   ends with ":", or uses `#` / `**` / ALL CAPS styling, or matches a known heading.
   Title Case alone never makes a heading. Text before the first heading, text under an
   unrecognised heading, and headingless documents are `unknown`.
2. **Find.** Every alias of every skill, longest alias first, non-overlapping per line. Case
   folding applies unless the skill sets `case_sensitive`.
3. **Disambiguate.** One generic rule set, driven by optional per-skill fields in
   `data/keywords.json`:
   - `case_sensitive: bool`: the alias must match case exactly.
   - `needs_context: [words]`: at least one word must occur in the same line.
   - `exclude_phrases: [phrases]`: drop the mention if the line contains one of these
     phrases overlapping the mention span (e.g. `"excel at"`).
   Python code never names an individual skill.
4. **Qualify.** Cue lists live in `data/match_rules.json`: `negation`, `hypothetical`,
   `clause_breaks`. A cue applies only when it sits before the mention inside the same clause.
   "familiar with" is not a negation cue.
5. **Decide.**
   - **Posting importance.** It starts from the section kind: `required` → required,
     `preferred` → preferred, `excluded` → excluded, everything else → unscored. In any
     section that isn't `excluded`, an inline cue in the mention's clause overrides it:
     `preferred_cues` → preferred, `required_cues` → required.
   - **Negated or hypothetical posting mentions** don't create requirements.
   - **Precedence when a skill appears more than once:** required > preferred > unscored >
     excluded. The representative evidence is the earliest mention, lowest `start`, within
     the winning tier.
   - **Résumé.** A skill is found if any affirmed résumé mention exists, in any section. Its
     evidence is the earliest affirmed mention.

## Public contract (compatible with the planned UI)

`match_posting(posting, resume) -> MatchResult` keeps its signature. Fields are only added,
and every new field has a default.

```python
SkillMatch(skill, category, requirement, found, posting_line, resume_line,
           section="", posting_span=None, resume_span=None)
# requirement: "required" | "preferred" | "unscored" | "excluded"
MatchResult(required, preferred, score, unscored=(), excluded=())
```

- **Scored skills.** Only `required` and `preferred` skills are scored:
  `S = 100 × (0.8 × R_found/R_total + 0.2 × P_found/P_total)`. An empty group passes its
  weight to the other. If both are empty, `score is None`. A headingless posting with no
  inline cues therefore gets `score None`, and its skills appear in `unscored`.
- **Unscored and excluded skills.** `unscored` lists responsibility, skills-section and
  unknown-section skills, with `found` and evidence, so they can be displayed. `excluded`
  lists skills that appear only in excluded sections; this is for transparency and never
  counts toward the score.
- **Snippets.** `posting_line` and `resume_line` stay snippets of at most 200 characters. The
  spans are exact.

## Evaluation

- **Development fixtures.** `tests/fixtures/postings/*.json` are written by the independent
  reviewer, not the implementer. Each has expected `required`, `preferred`, `unscored`,
  `excluded` and `found` sets. Line labels (substring → section) and mention labels
  (line substring + canonical → status) are optional.
- **Report.** `python scripts/evaluate_matching.py --fixtures tests/fixtures/postings` prints
  per-stage accuracy for sections, mention precision/recall, status and importance, plus
  document-level exact-set results.
- **Owner set.** `data/eval/`: 15 pairs, 5 of them `"split": "holdout"`. Holdout pairs are
  never used for tuning, and the report gives only aggregate numbers for them.
- **Exit codes** for `python scripts/evaluate_matching.py`:
  - `2` with `PENDING`: fewer than 15 pairs, or fewer than 5 holdout pairs. An empty dataset
    always ends here.
  - `1` with `FAIL`: holdout precision or recall below the provisional 0.85.
  - `0` with `PASS`: only with a complete set that meets the gate.

## Acceptance criteria for this redesign

1. All six full-posting fixtures match exactly on the `required` and `preferred` sets, and no
   excluded-section skill is ever scored.
2. All targeted fixtures pass: acronyms, unknown headings, exclusion zones, negation, inline
   preferred cues, duplicate skills, lost bullet markers, benefits, culture and compensation.
3. No canonical skill name appears as a string literal in `engine/job_match.py` or
   `engine/match_stages.py`; a test enforces this.
4. Full suite and `ruff check .` pass; the empty owner dataset reports `PENDING` (exit 2).
5. No new dependencies.

If the redesign misses a criterion, the misses are documented in `docs/SCORING.md` and
reported to the owner for a decision. There is no further heuristic patching and no
threshold change.
