# Scoring (engine/job_match.py)

The score is **skill coverage**: how many of the posting's recognized skills the
resume shows. It is not a hiring probability or a fit prediction.

## Formula

    S = 100 x (0.8 x R_matched/R_total + 0.2 x P_matched/P_total)

R = required skills, P = preferred skills. Weights 0.8 / 0.2.

- Only required skills recognized: `S = 100 x R_matched/R_total`.
- Only preferred skills recognized: `S = 100 x P_matched/P_total`.
- No skills recognized at all: `S` is `None` (not 0). Show "no skills recognized".

## Which skills, and which lines

Skills come from `data/keywords.json` (canonical name plus aliases), matched with
the regexes in `engine/keyword_extractor.py`.

Posting sections: only Preferred / Nice to have / Bonus (points) / Plus sections
are preferred. Every other line is required: intro, Responsibilities, Skills,
About you, Requirements, and unknown headings. Lines under clearly non-skill
sections (Benefits, Perks, Compensation, Salary, About us, About the company,
Equal opportunity) are dropped. A heading may carry text after a colon
("Requirements: SolidWorks"), and an inline "Preferred:" / "Nice to have:" label
mid-line starts a preferred segment ("Required: X. Preferred: Y."). A line that
starts with a bullet marker is never a heading. Heading lines are not
attributed to skills. A skill in both groups counts once, as required.

Attribution: each `SkillMatch` carries `posting_line`, the first posting line in
its group that mentions the skill, and (if found) `resume_line`, the first resume
line that mentions it. Lines are split on newlines and bullet characters and
capped at about 200 characters, centred on the match, with an ellipsis where
cut. Output order follows `keywords.json` order, so it is deterministic.

## Matching rules

- Aliases use the shared extractor's regexes: case-insensitive, word
  boundaries ("Solid Works" matches SolidWorks; "FEA" does not match
  "features"). `/` and `-` separators work ("FEA/CFD", "PLC-based"). All-caps
  aliases also match a plural ("PLCs").
- Ambiguous aliases (explicit set: `CAN`, `R`, `C`) match case-sensitively and
  not when attached to `& / + # - .` or word characters ("can", "R&D",
  "C-suite", "C/C++" do not match). The shipped keywords.json currently has no
  bare R, C or CAN alias.
- "excel at / excel in" does not match the Excel skill.

Negation:
- Posting: a mention is not a requirement if a negator (no, not, without,
  never, "don't need") is within 3 words before the skill with no comma,
  semicolon, sentence end, "but" or "and" between; hyphen compounds such as
  "no-code" are not negators. It is also negated if "not required / needed /
  necessary" follows within the same clause, up to 3 words later. "No prior PLC
  experience necessary but SolidWorks required" keeps only SolidWorks.
- Resume: only the literal phrases "no experience with X / in X" and "not
  familiar with X" negate. Anything else counts as having the skill, because a
  false "missing" is worse than a rare false "found" ("zero defects using FEA",
  "Not only PLC but also SolidWorks" are found).

## Known limits

- Regex matching only: no synonyms beyond the alias list, no sense of context,
  seniority or years of experience.
- Negation is a short-window heuristic. It can miss long-range or unusual
  negations ("FEA: none"), and a resume saying "no FEA experience" still counts
  as having FEA.
- Lines under an unrecognised heading are treated as required, so skills listed
  in company boilerplate may be counted.
- A mention anywhere on a resume counts as having the skill, regardless of depth.

## Evaluation status

The 0.85 threshold used by the evaluation is a **provisional engineering gate on
a small sample** (15 labeled pairs, 5 held out). It is not a general accuracy
claim. Measured results are **pending**: they exist only once the owner supplies
labeled data (format in `data/eval/README.md`; run `scripts/evaluate_matching.py`).
