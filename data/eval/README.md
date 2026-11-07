# Owner labelling guide

The owner supplies the labeled data: 15 posting/resume pairs, 10 development (`"split": "tune"`)
and 5 holdout (`"split": "holdout"`). No pairs are included. Until they exist the script
reports "no evaluation pairs yet".

## Rules for the data

- **Consent.** Use another person's resume only with their written consent. Keep the consent
  with your own records, not in this repo. Your own resume, or one you wrote, needs none.
- **Remove personal data** before the text goes in a file: names, email, phone, street and home
  addresses, links to profiles, and employer-identifying details where they are not needed
  (replace with "Company A"). Keep skills, tools, duties and section headings as written.
  Delete anything else personal that the matching does not need (dates of birth, photos' alt text, references).
- **Postings** should be real. Keep the posting wording as published.
- **Label before you run.** A human labels each pair BEFORE running the engine, and must not see
  engine predictions while labelling (no `--fixtures` output, no result pages). Labels written
  after looking at predictions measure the labeller's agreement with the engine, not the engine.
- **Separate files for development and holdout** (for example `tune.json` and `holdout.json`).
  Tune rules only against the development files. Never tune against the holdout five; look at
  holdout results in aggregate only (the script prints no per-item holdout failures).

## File format

Each `*.json` file holds `{"pairs": [ ... ]}`. Files named `EXAMPLE.*` are ignored
(`EXAMPLE.schema.json` is fake). Each pair:

| field | meaning |
|---|---|
| `id` | unique short label |
| `split` | `"tune"` or `"holdout"` |
| `posting_text` | full posting text |
| `resume_text` | full resume text |
| `required_skills` | canonical names (as in `data/keywords.json`) the posting requires |
| `preferred_skills` | canonical names the posting lists as preferred / nice to have |
| `resume_has` | which of those required + preferred skills the resume actually shows |

`resume_has` is claimed experience only: a skill the resume negates ("No CFD experience") or
only mentions hypothetically ("currently studying CFD") is not in it.

### Optional stage labels

`line_labels`, `mention_labels` and `evidence_labels` (same shapes as `tests/fixtures/postings/*.json`)
are read by `check_fixture` for fixtures; the owner-pair report does not read them yet.

```json
"line_labels": [{"contains": "Nice to have", "section": "preferred"}],
"mention_labels": [
  {"doc": "resume", "line_contains": "No CFD experience", "canonical": "CFD", "status": "negated", "occurrence": 1},
  {"doc": "resume", "line_contains": "No CFD experience", "canonical": "CFD", "status": "hypothetical", "occurrence": 2}
],
"evidence_labels": [{"canonical": "CFD", "posting_line_contains": "- CFD", "requirement": "required"}]
```

- `doc` is `"posting"` or `"resume"`; `line_contains` finds the line; `canonical` is the skill.
- `status` is `affirmed`, `negated` or `hypothetical`.
- **Repeated mentions.** Every label resolves to exactly one mention, by canonical skill and
  position. When a line mentions the same skill more than once, label EACH mention and say which:
  `occurrence` (1-based, in text order among that skill's mentions on the line), or `span_text`
  (the exact text of the mention; combine with `occurrence` if the text repeats), or `span`
  (`[start, end]` absolute offsets). A label with none of these must match exactly one mention;
  otherwise it fails as an ambiguous label. Two labels for the same mention fail as duplicates,
  and a label with no mention fails as missing.
- `strict_mentions: true` (pair level) also reports mentions on labelled lines that you did not label.
- `required` / `preferred` are decided by the pair-level `required_skills` / `preferred_skills`
  lists; `evidence_labels[].requirement` (optional) states the expected group for that skill
  (`required`, `preferred`, `unscored`, `excluded`).
- `evidence_labels`: the engine's evidence for `canonical` must lie on the line containing
  `posting_line_contains` (checked by exact offset, not just by text).

## Running

`python scripts/evaluate_matching.py` (optionally `--dir <path>`) prints precision, recall,
sample size and example failures for posting required, posting preferred and resume matching,
for tune and holdout. Only skill names are printed, never posting or resume text. Holdout
results are aggregate only.

| result | exit | meaning |
|---|---|---|
| PENDING | 2 | fewer than 15 pairs, or fewer than 5 holdout pairs (including none at all) |
| FAIL | 1 | enough pairs, but holdout precision or recall is below the provisional 0.85 gate |
| PASS | 0 | enough pairs and holdout meets the gate (small sample, not a general accuracy claim) |

For the reviewer-written fixtures: `python scripts/evaluate_matching.py --fixtures tests/fixtures/postings tests/fixtures/regression_r6`.

Do not commit real resumes without consent and anonymization.
