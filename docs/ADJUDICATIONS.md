# Adjudication tally

Each owner ruling on a disputed label is recorded here with its direction:
- **engine-favoured:** the ruling agrees with the engine;
- **engine-disfavoured:** the ruling agrees with the original label against the engine.

A dispute is never approved just because the alternative reading makes the engine pass.
Original sealed files and their hashes are never changed. Results are always reported with the
original labels and with the adjudicated labels, separately.

| Date | Fixture | Ruling | Direction | Record |
|---|---|---|---|---|
| 2026-11-07 | `u7_gov_later_cue_state` | Occurrence-specific labels: 1st CFD negated, 2nd ("flow simulation") hypothetical | engine-favoured | `ADJUDICATION_u7_gov_later_cue_state.md` |
| 2026-11-07 | `u8_molding_pdf_wraps` | Erroneous evidence-line label; the 5S/kaizen line is supported | engine-favoured | `ADJUDICATION_u8_molding_pdf_wraps.md` |

**Running tally:** 2 engine-favoured, 0 engine-disfavoured.

**Recorded but not ruled** (`tests/fixtures/DISPUTED.json`; the original labels are kept unchanged, excluded from the headline metrics, and reported alongside as original-label totals):
- `u6_linkedin_lost_bullets`: line section;
- `r5_linkedin_bonus_if`: MATLAB status;
- `u6_bigco_basic_desired`: Statistical Process Control status and found set (R2.4 vs R4.7.1).

Every ruling so far has favoured the engine. Weigh the next dispute with that in mind.
