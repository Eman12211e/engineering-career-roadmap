# Scoring and matching (engine/job_match.py, engine/match_stages.py)

The score is **skill coverage**: how many of the posting's *scored* skills the resume shows.
It is not a hiring probability or a fit prediction. The contract is `docs/MATCHING_DESIGN.md`;
this page describes what the code does.

## Formula

    S = 100 x (0.8 x R_found/R_total + 0.2 x P_found/P_total)

R = required skills, P = preferred skills.

- Only required skills: `S = 100 x R_found/R_total`. Only preferred: `S = 100 x P_found/P_total`.
- Neither: `S` is `None` (not 0). A posting with no headings and no inline cues therefore has
  `score None`; its skills are listed as `unscored`.
- Only required and preferred skills are scored. `unscored` (responsibilities, skills sections,
  unknown sections, headingless text) and `excluded` (benefits, compensation, about us, EEO)
  are shown for transparency and never change the score.

## The five stages

All vocabulary is data: `data/match_rules.json` (headings, cue lists, clause breaks, bullet
markers) and `data/keywords.json` (skills, aliases, optional per-skill fields). Code names no skill.

1. **Segment.** Text is split into lines (spans are absolute offsets) and typed sections:
   required, preferred, responsibilities, skills, experience, excluded, unknown.
   Structural heading test (thresholds in `data/match_rules.json` -> `heading_test`): a
   non-bullet line is a heading when, after stripping leading emoji/symbols/`#`/`*`/`_`, it has
   at most 6 words, does not end with `.`, `!` or `?`, is styled (ends with ":", Title Case,
   ALL CAPS or in the vocabulary), and has context (the next non-blank line is a bullet, a
   blank line follows, it ends with ":", or it is in the vocabulary). Extra safety: an
   unknown line that mentions a skill and has no colon stays body text. Every heading ends
   the previous section, including excluded ones; a heading outside the vocabulary opens an
   `unknown` section. A plain Title Case or ALL CAPS line inside a list without blank lines
   or bullets is body text (so a hard-wrapped "HOW TO APPLY" line is not detected).
   Text before the first heading and headingless text are `unknown`. Bullets: `-`, `*`,
   en/em dash, `>` followed by a space, or a bullet character (U+2022, U+00B7, U+25AA, U+25E6).
2. **Find.** Every alias of every skill, longest alias first, no overlaps within a line
   (ties go to the earlier skill in keywords.json). Word-bounded and case-folded; an all-caps
   alias matched in exact case may take a trailing lowercase "s" ("PLCs").
3. **Disambiguate.** Optional per-skill fields in keywords.json: `case_sensitive` (alias must
   match case exactly), `needs_context` (one of these words must be in the same line),
   `exclude_phrases` (drop a mention overlapping one of these phrases, e.g. "ml of").
4. **Qualify.** A cue applies only inside the mention's clause (clause breaks: comma,
   semicolon, sentence end, "but", "however", "except", "although", spaced dashes, "|"; "or"
   and "and" are not breaks, a period inside "Y14.5" is not a break).
   Cues before the mention: `negation` (no, not, without, never, lack of, ...) gives
   *negated*; `hypothetical` (learn, learning, planning to, willingness to, ...) gives
   *hypothetical*. "familiar with" is not a cue; "not familiar with" is. Hyphen compounds
   such as "no-code" are not cues. A cue that sits inside another skill's mention ("Machine
   Learning and FEA") is ignored. In postings only, `negation_after` ("not required", "not
   needed", ...) after the mention in the same clause also negates. Mentions in excluded
   posting sections are not qualified (they cannot create requirements anyway).
5. **Decide.** Positive evidence only: importance is required or preferred only from a known
   required/preferred heading or an inline cue (decided in one function, `_importance_cue`);
   everything else is unscored and nothing inherits importance from a previous line or
   section. Excluded needs a known excluded heading. In any non-excluded section an inline cue in the mention's
   clause overrides it: `preferred_cues` (a plus, nice to have, preferred, ...) or
   `required_cues` (required, must, mandatory, essential, ...); when both occur the nearer
   one wins, required on a tie. Negated and hypothetical posting mentions appear in no
   group. With several mentions of a skill the tier precedence is required > preferred >
   unscored > excluded, and the evidence is the earliest mention in the winning tier. A
   resume skill is *found* if any affirmed resume mention exists, in any section; its
   evidence is the earliest one.

## Attribution

Each `SkillMatch` carries `posting_line` and `resume_line` (the line, capped at 200
characters around the match with an ellipsis where cut), the exact `posting_span` and
`resume_span` of the matched text in the original input, and `section` (kind of the posting
section holding the evidence). Output order follows keywords.json order within each group.

## Known limits

- Regex matching only: no synonyms beyond the alias list, no sense of seniority or years.
- Skills that are ordinary words need data fields to be safe; only a few have them. Skills
  with several meanings, and an alias shared by two skills, resolve to the first skill in
  keywords.json.
- Heading vocabulary is finite. A real heading that is not in the vocabulary starts an
  `unknown` section, so its skills are unscored; an unrecognised heading inside an excluded
  section stays excluded. A line ending in ":" or in ALL CAPS is a heading even if it is
  really a sentence.
- Clause breaks include commas, so "No experience with FEA, CFD" negates only the first
  skill; "and" is not a break, so "Not familiar with PLC and fluent in SQL" negates both.
  "Without X, ..." negates X. Cue lists are English-only.
- A hypothetical cue such as "learn" also drops postings like "Opportunities to learn X".
- Inline bullet characters in the middle of a line do not split the line.
- A resume mention anywhere counts as having the skill, regardless of depth or recency.
- "X or Y" alternatives count as separate skills.

## Evaluation status

The 0.85 threshold is a **provisional engineering gate on a small sample** (15 owner-labeled
pairs, 5 held out); it is not a general accuracy claim. Measured owner-set results are
**pending**: `python scripts/evaluate_matching.py` exits 2 (`PENDING`) until the owner
supplies at least 15 pairs with at least 5 holdout (format in `data/eval/README.md`).
`--fixtures tests/fixtures/postings` reports per-stage numbers on 38 reviewer-written
development fixtures; those are development checks, not accuracy estimates.
