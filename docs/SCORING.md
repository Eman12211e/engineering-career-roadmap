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

All vocabulary is data: `data/match_rules.json` (headings, bullet markers, clause breaks, cue
lists, fillers, connectors, heading-test thresholds) and `data/keywords.json` (skills, aliases,
optional per-skill fields). Code names no skill.

1. **Segment.** Text is split into physical lines, joined into logical `Line`s, and grouped
   into typed sections: required, preferred, responsibilities, skills, experience, excluded,
   unknown. Spans are absolute offsets; `Line.text == source[start:end]` always.
   - *Heading test* (thresholds in `heading_test`): a non-bullet line is a heading when, after
     stripping leading emoji/symbols/`#`/`*`/`_`, it has at most 6 words, does not end with
     `.`, `!` or `?`, is styled (ends with ":", Title Case, ALL CAPS, or in the vocabulary), and
     has context (next non-blank line is a list item, a blank line follows, it ends with ":", or
     it is in the vocabulary). The end of the text is not a blank line. A vocabulary match
     satisfies the style and context rules. An unknown line that mentions a skill and has no
     colon stays body text. Every heading ends the previous section, including excluded
     ones; a heading outside the vocabulary opens an `unknown` section. Heading lines carry no
     skill mentions.
   - *Vocabulary lookup* strips leading symbols, case-folds, turns "&" into "and" and
     hyphens into spaces. "About the job" and "About the role" are known headings of kind
     `unknown` (R2.8.17): their text is unscored, not excluded.
   - *List items:* `-`, `*`, en/em dash, `>` followed by a space; bullet characters (U+2022,
     U+00B7, U+25AA, U+25E6); numbered and lettered items ("1.", "2)", "a.", "b)"). They are
     never headings and never wrap continuations.
   - *Hard-wrap joining:* a physical line continues the previous body line when that line does
     not end with `.` `:` `;` `!` `?`, and the line is not a list item or heading and starts
     with a lower-case letter. A blank line or a heading breaks the join.
2. **Find.** Every alias of every skill, longest alias first, no overlaps within a line (ties go
   to the earlier skill in keywords.json). Word-bounded and case-folded. Whitespace runs,
   including a hard-wrap newline, match as one space; the span is mapped back to the original
   text, so a span may contain the newline. An all-caps alias in exact case may take a
   trailing lowercase "s" ("PLCs"). Property test: for every mention,
   `norm(source[start:end]) == norm(alias)` (or `+ "s"`), with `norm` = case fold + whitespace
   collapse only.
3. **Disambiguate.** Optional per-skill fields in keywords.json: `case_sensitive`,
   `needs_context` (one of these words must be in the same line), `exclude_phrases`.
4. **Qualify** (R3.1, same rules for postings and resumes). A mention is affirmed by default.
   - A hypothetical cue (learn, learning, planning to take, preparing for, studying for,
     willing to learn, ...) opens a scope that runs across ordinary words, coordinators, commas and
     slashes. Every later mention inside it is hypothetical. The scope ends at a contrast ("but",
     "however", "although", "whereas") or a hard stop (period, semicolon, colon, end of the
     logical line, so it continues across a joined hard wrap). A cue inside another skill's own
     span ("machine learning") never opens one.
   - A negator (no, not, without, never, lack of, ...) keeps the gap rule: it applies to a skill
     directly after it, separated only by `negation_fillers` ("prior", "experience with",
     "used", "the", ...), and to every skill in that skill's coordinated list. It does not spread
     across ordinary words, so achievement bullets ("without rework by applying SPC", "never
     missed a deadline in X") stay affirmed. "familiar with" is affirmed; "not familiar with" is
     negated.
   - A later cue sets a new state from that point; a cue never reaches back to a mention before it.
   - Postings only: a `negation_after` cue ("not required", "not needed", ...) after the skill
     negates when only `cue_fillers` sit between; "X is not required, but is a plus" is not
     negated (and is preferred).
   - Clause breaks (comma, semicolon, sentence end, "but", "however", "although", "whereas",
     spaced dashes, ...) still bound cue binding and negation, but commas do not end a
     hypothetical scope. Mentions in excluded posting sections are not qualified.
5. **Decide.** Positive evidence only: a posting skill is required or preferred only from a known
   required/preferred heading or a bound cue; everything else is unscored and nothing inherits
   importance from a previous line or section. Cue binding is grammatical (`_importance_cue`):
   - prefix label at the start of the clause ("Preferred: X", "Required: X", "Nice to have: X",
     "Bonus: X") binds every skill of the clause;
   - postfix phrase right after the last skill of a list ("X (preferred)", "X is a plus",
     "X and Y a plus", "X is required", "X is a must") binds the whole list; only `cue_fillers`
     ("experience", "skills", "knowledge", "programming", "is", "are", "highly", ...) may sit
     between;
   - modal or preference prefix directly before the first skill: "must have X", "preferably X",
     "ideally X";
   - "Must be able to <verb> X", "as required" and "desired tolerances" bind nothing.
   Negated and hypothetical posting mentions appear in no group. With several mentions of a skill
   the precedence is required > preferred > unscored > excluded; the evidence is the earliest
   mention in the winning tier. A resume skill is *found* if any affirmed resume mention exists
   (résumés use negation and hypothetical rules but not `negation_after`); its evidence is the
   earliest one.

## Attribution

Each `SkillMatch` carries `posting_line` and `resume_line` (the line with whitespace collapsed, capped at 200
characters around the match with an ellipsis where cut), the exact `posting_span` and
`resume_span` of the matched text in the original input, and `section` (kind of the posting
section holding the evidence). Output order follows keywords.json order within each group.

## Known limits

- Regex matching only: no synonyms beyond the alias list, no sense of seniority or years.
- Skills that are ordinary words need data fields to be safe; only a few have them. An alias
  shared by two skills resolves to the first skill in keywords.json.
- The heading vocabulary is finite. A real heading that is not in the vocabulary and fails the
  structural test stays body text of the previous section; if it passes, it opens an `unknown`
  section (its skills are unscored). Hard-wrapped postings with no bullets or blank lines
  lose headings that are not in the vocabulary ("HOW TO APPLY" is, "Our Culture" is not).
  A line ending in ":" or in Title Case followed by a list is a heading even if it is
  really a sentence.
- "About the job" / "About the role" are vocabulary headings of kind `unknown` (R2.8.17), so
  their text is unscored, not excluded.
- Cue lists and fillers are English-only and finite. A skill separated from a cue by a word
  that is not a filler ("FEA coursework is not necessary") is neither negated nor bound.
- A hypothetical cue such as "learn" also drops postings like "Opportunities to learn X".
- A hypothetical scope has no way to tell an assertion from the cue's object: in "Learning PLC and
  already proficient in root cause analysis" both skills are hypothetical, although the second
  is claimed outright. Ambiguous claims are never counted as confirmed experience (R3.1.8).
- "X or Y" alternatives count as separate skills; commas end a clause outside a coordinated
  list ("No experience with FEA, CFD" negates both only because they form a list).
- Hard-wrap joining needs the next line to start with a lower-case letter; wrapped lines that
  start with an upper-case word (a product name) or a digit do not join, and an alias split
  across them is missed.
- Inline bullet characters in the middle of a line do not split the line.
- A resume mention anywhere counts as having the skill, regardless of depth or recency.

## Known critical-risk patterns

- **Postfix qualifiers.** "Python (learning)", "Python (in progress)", "SolidWorks (beginner, studying)" and
  similar trailing parentheticals are not recognised as hypothetical: the skill comes out
  `affirmed`. On a resume that is an invented claim, so the skill would count as confirmed
  experience the person does not have. Until the engine handles postfix qualifiers, treat a
  resume match on such a line as unverified.
- **A negation or prefix-label cue followed by a comma list whose first item is not a known
  skill.** "Never used LabVIEW, SQL" and "No experience with LabVIEW, SQL" leave SQL affirmed, so a
  negated skill is counted as present. "Nice to have: LabVIEW, SQL" or "Preferred: LabVIEW, SQL" give
  SQL the section's importance instead of the label's. Root cause: the R2.8.15 comma exemption in
  `_clause()` applies only when every list item is a known skill. Status: not fixed; a
  correction needs a separately reviewed contract change.

## Technical debt

- Two separate rules overlap and are not unified: the hypothetical scope rule (R3.1.2, a cue such
  as "learn" opens a scope over the rest of the clause) and the negation gap rule (R3.1.3, how far
  a negation cue reaches over fillers). They differ in reach and in how coordinated lists are
  handled, so the same phrase can be treated differently depending on which cue it contains.
  Merging them is deferred.
- The UI wiring of match results and the bullet-punctuation issues (inline bullet characters
  mid-line) belong to Wave 2, not to this engine work.

## Evaluation status

The 0.85 threshold is a **provisional engineering gate on a small sample** (15 owner-labeled
pairs, 5 held out); it is not a general accuracy claim. Measured owner-set results are
**pending**: `python scripts/evaluate_matching.py` exits 2 (`PENDING`) until the owner
supplies at least 15 pairs with at least 5 holdout (format in `data/eval/README.md`).

The numbers below are generated by `python scripts/evaluate_matching.py --update-docs`.

<!-- eval:start -->
<!-- generated by `python scripts/evaluate_matching.py --update-docs`; do not edit by hand -->

Development and regression fixtures (written by the independent reviewer, not tuned on):

| Folder | Fixtures | Exact-set pass |
|---|---|---|
| `postings` | 48 | 48 |
| `regression_r6` | 14 | 14 |
| total | 62 | 62 |

Per-stage metrics over all fixtures:

- stage 1 section accuracy: 1.00 (200/200)
- stage 2-3 mention precision 1.00 (377/377), recall 1.00 (377/377)
- stage 4 status accuracy: 1.00 (132/132)
- stage 5 importance accuracy: 1.00 (368/368)

Disputed or conflicting labels, kept unchanged and excluded from the metrics above: 2

- `r5_linkedin_bonus_if` {"kind": "mention_label", "doc": "posting", "line_contains": "Learning stipend for MATLAB", "canonical": "MATLAB", "status": "affirmed"}: engine now {"status": "hypothetical"}, alternative {"status": "hypothetical"}; Labelled under R2. Read literally, R3.1.2 makes 'Learning' open a hypothetical scope, so MATLAB is hypothetical. The line is in an excluded (benefits) section, so no result set or score changes. Coordinator-recorded; the owner decides any relabel.
- `u6_linkedin_lost_bullets` {"kind": "line_label", "contains": "Northfield Robotics is hiring", "section": "excluded"}: engine now {"section": "unknown"}, alternative {"section": "unknown"}; Sealed under R2.8.12 (About the job = excluded). R2.8.17, committed after the seal, makes About the job a known heading of kind unknown. The line has no skills, so neither the score nor the found set changes.

These are fixture results, not an accuracy estimate on unseen postings.
<!-- eval:end -->
