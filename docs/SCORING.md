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

Posting sections: headings such as Requirements / Required / Qualifications /
Must have mark required lines; Preferred / Nice to have / Bonus / Plus mark
preferred lines. A heading may carry text after a colon ("Requirements: SolidWorks").
Other headings (Responsibilities, Benefits, About...) end a section, and their
lines are ignored when the posting has any requirement/preferred section. A
posting with no such sections treats every recognized skill as required. A skill
in both groups counts once, as required.

Attribution: each `SkillMatch` carries `posting_line`, the first posting line in
its group that mentions the skill, and (if found) `resume_line`, the first resume
line that mentions it. Lines are split on newlines and bullet characters. Output
order follows `keywords.json` order, so it is deterministic.

## Matching rules

- Aliases match case-insensitively on word boundaries ("Solid Works" matches
  SolidWorks; "FEA" does not match "features").
- Short all-caps acronyms (3 letters or fewer, e.g. CAN, PLC, R, C) match
  case-sensitively and not when attached to `&`, `/`, `+`, `#`, `-`, `.` or word
  characters ("can", "R&D", "C-suite" do not match).
- "excel at / excel in" does not match the Excel skill.
- Negation: a mention preceded within 6 words (same sentence) by no / not /
  without / never / none / lack(ing) / zero, or followed by "not required /
  needed / necessary", is ignored. "No FEA experience required" is not a
  requirement; a resume saying "no experience with X" does not show X.

## Known limits

- Regex matching only: no synonyms beyond the alias list, no sense of context,
  seniority or years of experience.
- Negation is a short-window heuristic. It can miss long-range or unusual
  negations ("FEA: none") and can wrongly suppress ("not only SolidWorks").
- Postings with unusual headings are treated as unsectioned or lose lines.
- A mention anywhere on a resume counts as having the skill, regardless of depth.

## Evaluation status

The 0.85 threshold used by the evaluation is a **provisional engineering gate on
a small sample** (15 labeled pairs, 5 held out). It is not a general accuracy
claim. Measured results are **pending**: they exist only once the owner supplies
labeled data (format in `data/eval/README.md`; run `scripts/evaluate_matching.py`).
