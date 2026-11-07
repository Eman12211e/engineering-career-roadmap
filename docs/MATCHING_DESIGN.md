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
   unrecognised heading, and headingless documents are `unknown`. Inside an `excluded`
   section, only a *known* heading ends the section; an unrecognised heading candidate, such
   as an ALL CAPS perk line, stays excluded.
2. **Find.** Every alias of every skill, longest alias first, non-overlapping per line. Case
   folding applies unless the skill sets `case_sensitive`. Generic plural rule: an all-caps
   alias matched case-exactly may take a trailing lowercase "s" ("PLCs").
3. **Disambiguate.** One generic rule set, driven by optional per-skill fields in
   `data/keywords.json`:
   - `case_sensitive: bool`: the alias must match case exactly.
   - `needs_context: [words]`: at least one word must occur in the same line.
   - `exclude_phrases: [phrases]`: drop the mention if the line contains one of these
     phrases overlapping the mention span (e.g. `"excel at"`).
   Python code never names an individual skill.
4. **Qualify.** Cue lists live in `data/match_rules.json`: `negation`, `hypothetical`,
   `clause_breaks`. A cue applies only when it sits before the mention inside the same clause.
   The one exception is `negation_after` (e.g. "not required", "not needed"), which applies
   after the mention within the same clause, and only in postings. "familiar with" is not a
   negation cue; "not familiar with" is. "or" is not a clause break.
5. **Decide.**
   - **Posting importance.** It starts from the section kind: `required` → required,
     `preferred` → preferred, `excluded` → excluded, everything else → unscored. In any
     section that isn't `excluded`, an inline cue in the mention's clause overrides it:
     `preferred_cues` → preferred, `required_cues` → required.
   - **Negated or hypothetical posting mentions** don't create requirements and appear in no
     result group, not even `unscored`.
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
  `excluded` and `found` sets. Line labels (substring → section), mention labels
  (line substring + canonical → status) and evidence labels (canonical → posting line
  substring) are optional. The implementer may not edit fixture expectations; a disputed
  fixture goes to the coordinator.
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

---

# Revision 2: bounded remediation round (frozen 2026-11-07)

The owner approved Option A. Where this revision conflicts with anything above, this
revision wins. It is frozen before any code is written, so the rules, the severity table and
the unseen-set protocol can't move after results come in.

## R2.1 Positive evidence for importance

A posting skill is `required` or `preferred` only with positive evidence:
- it sits in a section whose heading matches the `required` or `preferred` vocabulary; or
- a bound cue (R2.4) ties it to `required` or `preferred`.

Everything else is `unscored`. That covers text before the first heading, text after an
unknown heading, responsibilities, skills sections and headingless text. A skill never takes
its importance from the line or section before it. Unscored skills are still reported as
"also mentioned in the posting" and never count toward the score. `excluded` still needs a
known excluded heading.

## R2.2 Structural heading test (thresholds in `data/match_rules.json` → `heading_test`)

A non-bullet line is a heading if all of these hold:
1. After stripping leading emoji, symbols, `#`, `*` and `_`, it has at most `max_words`
   words (default 6).
2. It does not end with sentence punctuation (`.`, `!`, `?`).
3. It either ends with ":", or is Title Case (every word not in `small_words` starts with an
   upper-case letter), or is ALL CAPS, or matches the heading vocabulary.
4. The next non-blank line is a list item, or the line is followed by a blank line, or it
   ends with ":", or it matches the vocabulary.

Lines that look like headings but fail the test stay body text: "Our team uses Python." fails
rule 2, and "Python lunch-and-learns" fails rules 3 and 4. Tests must cover such near-misses.
Every heading ends the previous section, including unknown and excluded ones. A heading
outside the vocabulary opens an `unknown` section; this supersedes the earlier "only a known
heading ends an excluded section" ruling. Emoji and symbols are stripped before vocabulary
lookup. The vocabulary is data only.

## R2.3 Hard-wrapped lines

A physical line continues the previous one when the previous line does not end with
`.`, `:`, `;`, `!` or `?`, and the line itself is not a bullet or a heading and starts with a
lower-case letter. Segment builds logical `Line`s from physical lines, and
`Line.text == source[Line.start:Line.end]` still holds, newlines included. Find matches
aliases across a joined line through an offset map back to the original text.

**Offset invariant**, checked by a property test over every fixture and every mention:
`norm(source[start:end]) == norm(alias)`, or `norm(alias) + "s"` under the plural rule.
`norm` does case folding and collapses runs of whitespace (spaces, tabs, newlines) to one
space. It removes nothing else. A span that contains any other word or character fails.

## R2.4 Cue binding: grammatical, not distance-based

A cue binds to a skill only inside the same list item or clause, and only in these forms
(templates and filler words live in data):
- **Prefix label** at the start of the clause: "Preferred: X", "Required: X",
  "Nice to have: X", "Bonus: X". All skills in the clause are bound.
- **Postfix phrase** after the last skill of a skill list: "X (preferred)", "X preferred",
  "X is a plus", "X and Y a plus", "X required", "X is required". Only words from
  `cue_fillers` (e.g. "experience", "skills", "knowledge", "is", "are", "highly", "strongly")
  may sit between the last skill and the cue.
- **Modal prefix:** "must have X", "X is a must".

So "as required" and "desired tolerances" never bind.

**Negation and hypothetical cues use the same gap rule.** A negator ("no", "not", "without",
"never", "not familiar with") or a hypothetical cue ("learning", "willing to learn") applies
only when it sits directly before the skill, or is separated from it only by
`negation_fillers` (e.g. "prior", "experience with", "knowledge of"). This means:
- "without added headcount by applying lean" is not negated;
- "Zero escapes with no rework using SPC" is not negated;
- "willing to travel 20% and have AutoCAD skills" is not hypothetical.

"X is not required, but is a plus" or "not required but nice to have" is `preferred`.

## R2.5 Evaluation

- **Metric bug.** The résumé metric is fixed before anything else: it covers required and
  preferred skills only, as `data/eval/README.md` defines. All earlier numbers, including
  38/38, are re-run and reported.
- **Development and regression fixtures.** The 38 existing fixtures, plus the 10 postings
  from review 5. Their expected results change only with coordinator approval. Agent C may
  read them.
- **Unseen set.** Written by an independent reviewer before implementation and stored
  outside the repository. Only its SHA-256 hashes and creation date go in
  `docs/UNSEEN_SET.md`. Agent C must never read it. Nobody runs it before session 3.
  Filesystem isolation is by instruction only; the hashes prove the set was fixed in
  advance, not that it stayed secret.
- **Not accuracy evidence.** Integration and unit test counts show the wiring works, not
  that the answers are correct.

## R2.6 Pass criteria on the unseen set (fixed in advance)

| Error | Severity | Allowed |
|---|---|---|
| Skill marked required/preferred from culture, benefits or company text | Critical | 0 |
| Negated or hypothetical mention counted as present | Critical | 0 |
| Résumé claim invented in a bullet | Critical | 0 |
| Wrong offset or evidence line | Critical | 0 |
| Required and preferred swapped | Major | Count reported |
| Common alias missed (SolidWorks, FEA, GD&T, ...) | Major | Count reported |
| Uncommon alias or odd formatting missed | Minor | Documented |

If any critical error remains, the round stops, Gate 1 stays blocked, and the owner makes a
scope decision. A critical error is never documented away as a limitation.

## R2.7 Time box: three sessions

A session is one bounded implementation-and-validation cycle.

| Session | Work |
|---|---|
| 1 | Fix the eval metric and re-run; freeze the regression fixtures and the unseen set; implement R2.1 and R2.2 |
| 2 | Implement R2.3 and R2.4, plus the offset property test |
| 3 | Integration checks, then the independent review on the unseen set, then the evidence report |

There is no fourth session. Whatever fails after session 3 goes to the owner.

## R2.8 Clarifications (coordinator rulings, session 1, before any results)

1. **Vocabulary match.** A line that matches the heading vocabulary satisfies rules 3 and 4
   of R2.2. Excluded vocabulary covers process and company text, including "How to Apply".
   ALL CAPS alone does not waive rule 4.
2. **Lookup normalisation.** Leading emoji and symbols are stripped. Inside the label, "&"
   becomes "and", hyphens become spaces, and the text is case folded. Other characters
   inside the label are kept.
3. **End of text** does not count as a blank line under R2.2 rule 4.
4. **Mentions in heading lines** are ignored. A heading carries no skill mentions.
5. **Negators and hypothetical cues span coordinated lists.** A negator or hypothetical cue
   that binds to the first skill of a coordinated skill list ("X, Y or Z", "X and Y") binds
   to every skill in that list, as postfix cues do. So "No experience with FEA or CFD"
   negates both.
6. **Multi-word cues are data.** Hypothetical cues may be multi-word phrases, e.g.
   "planning to take", "preparing for", "studying for". The cue and filler examples in R2.4
   are the minimum contents of their data lists.
7. **Lines that mention a skill.** Accepted implementer addition (`heading_test.skill_text_is_body`):
   an unrecognised line that mentions a skill and has no trailing colon is body text, not a
   heading. This keeps a résumé line such as "SQL, PYTHON" from becoming a heading. A known
   vocabulary heading is unaffected.
8. **Numbered and lettered items.** "1.", "1)" and "a." / "a)" at line start are list items.
   They are never heading candidates or wrap continuations.
9. **`cue_fillers` is open-ended data.** It holds words that describe the skill rather than
   assert something new: "experience", "skills", "knowledge", "proficiency", "programming",
   "design", "development", "is", "are", "highly", "strongly". It never holds verbs of
   ability or duty.
10. **No ability phrases.** "Must be able to <verb> X" binds nothing; only "must have X" and
    "X is a must" are modal cues. The skill falls back to unscored, which is the safe
    direction.
11. **Order of the two heading rules.** R2.8.7 is applied first. R2.8.4 (mentions in heading
    lines are ignored) applies only to lines that end up as headings.
12. **Excluded vocabulary also covers** "About the job" and "About the role".
13. **`negation_fillers` is open-ended data,** with the same intent as R2.8.9. It may hold
    usage and exposure phrases such as "used", "worked with", "had", "exposure to" and
    "prior", so "Never used MATLAB" is negated.
14. **`negation_after` follows the `cue_fillers` gap rule.** "X coursework is not necessary"
    binds only if every word between X and the cue is a filler.
15. **Commas inside a coordinated skill list are not clause breaks** for cue binding.
    "SolidWorks, Creo, or CATIA preferred" binds all three.
16. **"preferably X" and "ideally X" are prefix cue forms** for `preferred`.
17. **Amends R2.8.12.** "About the job" and "About the role" are known headings of kind
    `unknown`, not `excluded`. On LinkedIn, "About the job" often introduces the whole
    posting, so treating it as excluded would hide real requirements. As `unknown`, it still
    ends the previous section, and its skills are unscored. Four independent fixtures expect
    exactly this.

---

# Revision 3: Stage 4 remediation (frozen 2026-11-07)

The owner approved a final, simplified Stage 4 contract after the round-6 sealed review found
one critical error: in "Currently learning PLC troubleshooting and root cause analysis", the
second skill was affirmed. The five-stage architecture is unchanged. There are no assertion
cues and no skill-specific exceptions. Where this revision conflicts with anything above, it
wins.

## R3.1 Qualification by scope

Applies to Stage 4 (`qualify`) on both documents.
1. A mention is `affirmed` by default.
2. A **hypothetical cue** (data list `hypothetical`) starts a hypothetical scope. The scope
   continues across ordinary words, coordinators ("and", "or"), commas and slashes. Every
   following mention inside it is `hypothetical`.
3. A **negation cue** keeps the R2.4 gap rule. It applies to a skill directly after it, or
   separated only by `negation_fillers`, and to every skill in that skill's coordinated list
   (R2.8.5). It does not spread across ordinary words, so achievement bullets ("without rework
   by applying SPC") stay affirmed. This split is the owner's decision; it keeps the locked
   round-6 labels valid.
4. A scope ends at a **contrast** ("but", "however", "although", "whereas") or a **hard
   stop** (period, semicolon, colon, line end). After it, mentions are affirmed by default
   again.
5. A later negation or hypothetical cue in the same clause sets a new state from that point.
6. A cue affects only mentions after it, never mentions before it. `negation_after` remains
   the only exception, for postings only, as defined in R2.8.14.
7. "familiar with" is affirmed; "not familiar with" is negated.
8. An ambiguous claim is never counted as confirmed résumé experience. When in doubt, the
   conservative state (hypothetical or negated) wins.

**Required minimal pairs**, as parametrized Stage 4 tests:

| Text | Expected |
|---|---|
| "Currently learning PLC troubleshooting and root cause analysis" | PLC hypothetical, RCA hypothetical |
| "Never used PLC, but interested in learning root cause analysis" | PLC negated, RCA hypothetical |
| "Learning PLC and already proficient in root cause analysis" | both hypothetical; a documented known limitation |
| "Used SolidWorks; currently learning FEA" | SolidWorks affirmed, FEA hypothetical |
| "Learning FEA. Expert in SolidWorks" | FEA hypothetical, SolidWorks affirmed |
| "SolidWorks and learning FEA" | SolidWorks affirmed (a cue never reaches back), FEA hypothetical |
| "Familiar with GD&T" / "Not familiar with GD&T" | affirmed / negated |
| "Without rework by applying SPC" | SPC affirmed (the negation gap rule) |

## R3.2 Evaluation controls

- **Round-6 sealed set.** It is now locked regression data in `tests/fixtures/regression_r6/`,
  copied byte-for-byte; its combined hash still matches `docs/UNSEEN_SET.md`. Its expectations
  are locked.
- **Disputed labels.** Listed in `tests/fixtures/DISPUTED.json`. They are kept unchanged and
  reported separately, never silently relabelled.
- **New sealed set (round 7).** Written by a new independent author and sealed BEFORE any
  Stage 4 code changes. It is recorded in `docs/UNSEEN_SET.md` and run only in the final
  review.
- **Generated numbers.** The evaluation counts and metrics in `docs/SCORING.md` are
  generated by `scripts/evaluate_matching.py`, between markers, not written by hand.
- **Gate 1 integration tests.**
  - FEA evidence produces a deterministic bullet that contains FEA, with no unsupported
    claims and no invented metric.
  - GD&T evidence whose text never mentions GD&T produces a bullet without GD&T, and
    `skill_mentioned` is False. That is the actual Agent A behaviour, which uses no warning
    interface.
  - A `MatchResult` gap flows into `BulletEvidence`.
- **Session limit.** One working session. Pass requires zero critical errors on the round-7
  set (R2.6 table). If any critical error remains, the round stops and the owner decides.

## R3.3 Clarifications (coordinator, before any Stage 4 code change)

Where `data/match_rules.json` disagrees with Revision 3, the contract wins, and the data must
be updated to match it.
1. **Scope ends.** A hypothetical scope ends at the R3.1.4 contrasts ("but", "however",
   "although", "whereas") and hard stops (period, semicolon, colon, end of line). Commas and
   slashes do NOT end it. Other `clause_breaks` entries keep their R2 role in cue binding and
   negation, but do not end a hypothetical scope.
2. **End of line** means the end of the logical line built by R2.3, not a physical newline. A
   scope therefore continues across a joined hard wrap.
3. **Cues inside skill names.** A cue word inside another skill's matched span (e.g.
   "learning" in "machine learning") never starts a scope. This restates existing behaviour.

---

# Revision 4: coordinated lists (frozen 2026-11-07, final bounded correction)

The owner approved this as the final correction before a product-scope decision. It
replaces R2.8.15's "commas inside a coordinated *skill* list" exemption. That exemption made
list boundaries depend on whether neighbouring words were recognised skills, which broke
"Never used LabVIEW, SQL" (a critical-class error) and "Nice to have: LabVIEW, SQL".

## R4.1 What a coordinated list is

- A comma, "and", "or", "/", ", and" and ", or" are coordinators by default.
- A **coordinated list** is the run of items joined by coordinators inside one clause. It is
  one grammatical unit.
- An item is any text between coordinators: a skill, an unknown word ("LabVIEW",
  "Foobar") or a phrase ("PLC experience", "proficient in SQL").
- Whether an item is a recognised skill **never** decides where the list starts or ends.
- A list ends at a hard stop (`.` `;` `:` `!` `?` `|` `–` `—`, end of the logical line), a
  contrast ("but", "however", "although", "whereas", "except"), or a new qualification
  cue (negation, hypothetical, or a posting importance cue).

## R4.2 Negation

- **Inside a list:** the R2 gap rule is kept, but the gap is measured from the cue to the
  **start of the list**. If the list starts within the permitted gap (only
  `negation_fillers` between them), the negation applies to every skill in the list.
- **Outside a list:** a single skill with no coordinator uses the R2 gap rule unchanged.
- Expected results:

  | Text | Expected |
  |---|---|
  | "Never used LabVIEW, SQL" | SQL negated |
  | "Without rework by applying SPC" | SPC affirmed (gap rule, no list) |
  | "No PLC experience, but proficient in SQL" | PLC negated, SQL affirmed (the contrast ends it) |
  | "No PLC experience, proficient in SQL" | PLC negated, SQL **negated** |

  The last row is the conservative model. It is a documented **major** known limitation,
  because a real skill is reported missing.

## R4.3 Hypothetical scope

Unchanged from R3.1.2 and R3.3. Coordinators and ordinary words don't end it; contrasts,
new cues and hard stops do.

## R4.4 Posting importance cues

- A prefix label ("Nice to have:", "Preferred:", "Required:", "Bonus:") or a modal or
  adverb prefix ("must have", "preferably", "ideally") binds every skill in the
  coordinated list that follows it, up to the end of that list.
- A postfix cue binds every skill in the coordinated list just before it.
- Unknown items anywhere in the list do not break the binding.

## R4.5 Metamorphic invariant

For every list-bearing minimal pair, inserting one whole unrecognised item ("Foobar") at
the start, middle or end of the list must not change any recognised skill's status or
importance. Unknown words are never inserted inside an alias.

## R4.6 Evaluation controls

- **Tests come first.** The regression and metamorphic tests are coordinator-written
  (`tests/test_comma_lists.py`) and committed before any implementation. The implementer
  may not edit them, exempt them, or edit any fixture.
- **Round 8.** A new sealed set, written by a new independent author, is sealed before the
  implementation and recorded in `docs/UNSEEN_SET.md`.
- **Round 7.** Its sealed files are unchanged. It is retrospective regression data: run by
  the script and reported, not counted as unseen accuracy evidence.
- **Disputed labels.** The `u7_gov_later_cue_state` adjudication
  (`docs/ADJUDICATION_u7_gov_later_cue_state.md`) is a PROPOSAL and is not authoritative
  until the owner approves it.
- **Stopping rule.** Any critical error on round 8 stops implementation. A scope-narrowing
  proposal then goes to the owner. There is no further remediation cycle.

## R4.7 Clarifications (coordinator, after the round-8 seal and before implementation)

The sealed set avoids all of these phrasings, so the rulings don't affect its labels.
1. **Where the first item starts.** After a negation cue, the first item starts after the
   cue and any `negation_fillers`, and runs to the first coordinator. This is the
   conservative model, and it matches R4.2's "No PLC experience, proficient in SQL". So
   "without new tooling by applying kaizen and 5S" negates the whole list. With no
   coordinator, there is no list, and the R2 gap rule applies.
2. **Postfix cues.** A postfix cue binds every skill in the list just before it in the same
   clause. Items may contain non-skill words ("MoveIt exposure is a must", "Python
   scripting, preferred").
3. **`negation_after`** binds the whole list just before it in the same clause
   ("X, Y or Z is not required").
4. **More coordinators.** "&", "and/or" and "as well as" are coordinators too, as in the
   existing `list_connectors` data.
5. **"except"** remains a contrast that ends a list. It is not a negation cue.

## R4.8 PROPOSED addendum, 2026-11-07: list-item word cap (needs owner approval)

R4.1 and R4.4 did not authorise this rule; the implementer added it in `13cda7b` as
`max_item_words` = 3 in `data/match_rules.json`. It is recorded here so it isn't silently
retained, and Revision 3 and Revision 4 above are left unchanged.

- **What it does:** for posting importance cues, a non-skill list item longer than 3 words
  ends the coordinated list.
- **Why it exists:** without it, a postfix cue binds across long duty phrases. "technical
  reports and engineering change proposals as required" would bind earlier skills. That
  contradicts R2.4 and R2.8.10, under which "as required" binds nothing.
- **Locked tests that need it:** removing it (setting it to 99) breaks
  `u6_duty_lines_as_required` and `u6_gov_defense_clearance` (regression_r6). Round 8 gives
  the same result for any value from 2 to 99.
- **Limitation:** a long unknown alternative ends the binding. In "SolidWorks, Creo or any
  other parametric CAD package preferred", the skills stay at the section's importance (for
  example required), a major-class swap. It fails toward the section kind, never toward an
  invented claim.
- **Coordinator recommendation:** retain it as a defensible temporary product rule, list the
  limitation in `docs/SCORING.md`, and replace it with real phrase structure in the
  post-Gate-1 architecture work.

## Post-Gate-1 architecture issue (high priority, not fixed in this round)

Trailing qualification cues on résumé and posting text ("Python (learning)",
"FEA (in progress)", "SQL, basic") come after the skill, and R3.1.6 says a cue never reaches
back. Fixing it needs phrase-level structure, not another cue rule.
