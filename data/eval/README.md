# Evaluation data format

The owner supplies the labeled data. No pairs are included yet; the evaluation
script reports "no evaluation pairs yet" until they exist.

Target: 15 pairs, 5 of them `"split": "holdout"` (never used to tune rules), the
other 10 `"split": "tune"`.

Resumes must be real and anonymized with the person's written consent, or written
by the owner. Postings should be real.

Each `*.json` file here holds `{"pairs": [ ... ]}`. Files named `EXAMPLE.*` are
ignored (see `EXAMPLE.schema.json`, which is fake). Each pair:

| field | meaning |
|---|---|
| `id` | unique short label |
| `split` | `"tune"` or `"holdout"` |
| `posting_text` | full posting text |
| `resume_text` | full resume text |
| `required_skills` | canonical skill names (as in `data/keywords.json`) the posting requires |
| `preferred_skills` | canonical skill names the posting lists as preferred / nice to have |
| `resume_has` | which of those required + preferred skills the resume actually shows |

Run: `python scripts/evaluate_matching.py` (optionally `--dir <path>`).
Output: precision, recall, sample size and example failures, separately for
posting extraction (required, preferred) and resume matching, for tune and holdout.
Only skill names are printed, never posting or resume text.

Do not commit real resumes without consent and anonymization.
