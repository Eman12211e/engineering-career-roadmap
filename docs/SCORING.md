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

Posting sections: only Preferred / Nice to have / Bonus points (or Bonus skills) /
Plus sections are preferred. A bare "Bonus" is not (it usually means pay). Every
other line is required: intro, Responsibilities, Skills, About you, Requirements,
and lines under unknown headings. Lines under these skip sections are dropped:
Benefits, Perks, Compensation, Salary, About us, About the company, Who we are,
Equal opportunity (employer), EEO.

Headings: a heading-like line has no bullet marker, is 45 characters or fewer
once markdown (`#`, `**`, `__`, trailing colon) is stripped, has no sentence
punctuation, no digits, `$` or `%`, and mentions no recognized skill. Every
heading-like line ends the current section, except inside a skip section, where
only a known heading, a line ending in ":", a markdown-marked line, or a
Title Case line ("The Position") ends it; a plain line such as "Free lunch"
stays in the skip section and is dropped. A known required/preferred/skip
heading sets the section type; an unknown heading ("The Position", "Your
Toolbox") starts a required section, so a skip section never swallows the rest
of the posting. A bullet marker is `-`, an en/em dash, `>`, a bullet character (U+2022, U+00B7,
U+25AA, U+25E6) with or without a space, or `*` followed by a space
("**Requirements**" is a heading). For an inline "Label: text" line, a
required/preferred label applies to the text; a skip label ("Salary: ...")
drops only that line and leaves the current section unchanged. An inline
"Preferred:" / "Nice to have:" label mid-line starts a preferred segment
("Required: X. Preferred: Y."). Heading lines are not attributed to skills. A
skill in both groups counts once, as required. A non-heading line inside a
required section that ends with "a plus", "(is) a plus", "preferred", "nice to
have" or "is a bonus" counts as preferred.

Attribution: each `SkillMatch` carries `posting_line`, the first posting line in
its group that mentions the skill, and (if found) `resume_line`, the first resume
line that mentions it. Lines are split on newlines and bullet characters and
capped at about 200 characters, centred on the match, with an ellipsis where
cut. Output order follows `keywords.json` order, so it is deterministic.

## Matching rules

- Aliases use the shared extractor's regexes: case-insensitive, word
  boundaries ("Solid Works" matches SolidWorks; "FEA" does not match
  "features"). `/` and `-` separators work ("FEA/CFD", "PLC-based"). All-caps
  aliases also match an upper-case-plus-lowercase-s plural ("PLCs", "SAPs");
  "MLS listings" and "500 mls" do not match Machine Learning.
- Ambiguous aliases (explicit set: `CAN`, `R`, `C`) match case-sensitively and
  not when attached to `& / + # - .` or word characters ("can", "R&D",
  "C-suite", "C/C++" do not match). The shipped keywords.json currently has no
  bare R, C or CAN alias.
- "excel at / excel in" does not match the Excel skill.

Negation (a clause break is a comma, semicolon, sentence end, "and" or "but"):
- Posting, before: a mention is not a requirement if a negator (no, not,
  without, never, "don't need") is within 3 words before the skill with no
  clause break between; hyphen compounds such as "no-code" are not negators.
  "No prior PLC experience necessary but SolidWorks required" keeps only
  SolidWorks. Side effect: "Without SolidWorks, you will struggle" is also
  treated as negated (accepted).
- Posting, after: "not required / needed / necessary" within up to 3 words
  after the skill, with no clause break in between, negates it. "SolidWorks
  skills and degree not required" keeps SolidWorks.
- Resume: only the literal phrases "no experience with / in X", "no prior
  experience with / in X" and "not familiar with X" negate. Anything else counts
  as having the skill, because a false "missing" is worse than a rare false
  "found" ("zero defects using FEA", "Not only PLC but also SolidWorks" are
  found).

## Known limits

- Regex matching only: no synonyms beyond the alias list, no sense of context,
  seniority or years of experience.
- Negation is a short-window heuristic. It can miss long-range or unusual
  negations ("FEA: none"), and a resume saying "no FEA experience" still counts
  as having FEA.
- Section detection is heuristic. A short plain line with no skill under a
  Preferred heading (for example "3 plus years") may end that section, and
  company boilerplate under an unrecognised heading counts as required.
- "X or Y" alternatives are counted as separate requirements.
- Plain-line skill lists directly after a skip section (no bullets, no heading)
  are dropped, since they look like benefits text.
- A mention anywhere on a resume counts as having the skill, regardless of depth.

## Evaluation status

The 0.85 threshold used by the evaluation is a **provisional engineering gate on
a small sample** (15 labeled pairs, 5 held out). It is not a general accuracy
claim. Measured results are **pending**: they exist only once the owner supplies
labeled data (format in `data/eval/README.md`; run `scripts/evaluate_matching.py`).
