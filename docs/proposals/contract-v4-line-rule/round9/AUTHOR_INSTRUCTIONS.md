# Instructions for the author of the sealed set

## Your role

- You are writing a sealed evaluation set of job-posting and résumé pairs.
- The set will test a tool that compares a job posting with a résumé.
- You have not seen, and must not look for, the tool's code, rules or documents.
- Work only inside the folder you were given. Do not read anything outside it. Do not use the web.

## What you produce

30 files named `u9_<short_name>.json`, one pair per file, in an `out/` subfolder. Each file has exactly this shape (see `SCHEMA_EXAMPLE.json`, which is fake):

```
{"pairs": [{"id", "split": "holdout", "category", "posting_text", "resume_text",
            "required_skills", "preferred_skills", "resume_has", "note"}]}
```

| Field | What to write |
|---|---|
| `id` | A unique short id, for example `u9_<short_name>` |
| `split` | Always `"holdout"` |
| `category` | One of the category names in the table below, exactly |
| `posting_text` | The job posting |
| `resume_text` | The résumé |
| `required_skills` | Skills from `SKILLS.json` (canonical names) that a careful human reader says the posting requires. Skills mentioned only in duties, benefits, the company blurb or legal text belong to neither list |
| `preferred_skills` | Skills from `SKILLS.json` (canonical names) that a careful human reader says the posting prefers |
| `resume_has` | The subset of required plus preferred skills that a careful human reader concludes the person genuinely has hands-on experience with, from the résumé text alone. A skill the résumé names but disclaims, plans to learn, only watched others use, or mentions in a way a careful reader would not accept as the person's own hands-on experience is NOT in `resume_has` |
| `note` | One or two sentences: what makes the pair hard, and why each doubtful skill is in or out |

Labels state what the text means to a careful human reader. They never state what a tool might do.

## Requirements for every pair

- Realistic length and formatting: postings 150 to 350 words, résumés 120 to 300 words.
- Invented names and companies.
- Engineering roles: mechanical, manufacturing, automation, robotics, aerospace, EV.
- As many required plus preferred skills as the posting naturally calls for, between 3 and 12.
- Skills written in the texts with a canonical name or a listed alias from `SKILLS.json`.
- Varied layouts.
- Do not reuse a phrasing across pairs.

## Composition: 30 pairs

| Category | Pairs |
|---|---|
| Disclaimer in a separate paragraph or section from the skill | 3 |
| Checkbox and form layouts | 3 |
| Meaningful punctuation or symbols next to a skill | 3 |
| Limited, classroom-only or second-hand use written like experience | 3 |
| Direct statements of not having a skill | 3 |
| Real achievements whose wording contains a negative word | 3 |
| Skills the person plans or wants to learn | 3 |
| Hard-wrapped or oddly formatted text (PDF copy-paste) | 3 |
| Ordinary realistic pairs with no traps | 6 |
| **Total** | **30** |

In each of the eight trap categories (every category except "Ordinary realistic pairs with no traps"), at least one pair must put the doubtful skill in the posting's required list.

## Sealing

When all 30 files are written, produce `out/SEALED_MANIFEST.txt`:
- one line per JSON file, in `sha256sum` format (`<hash>  <filename>`, two spaces), sorted by filename;
- a final line `combined  <hash>`, where the hash is the `sha256sum` of the per-file lines exactly as written (LF line endings).

Run this block from inside `out/`:

```
sha256sum u9_*.json | sed 's/ \*/  /' > SEALED_MANIFEST.txt
printf 'combined  %s\n' "$(sha256sum < SEALED_MANIFEST.txt | cut -d' ' -f1)" >> SEALED_MANIFEST.txt
```

The first command replaces the ` *` that Git Bash prints before each filename with a second space. `sha256sum -c SEALED_MANIFEST.txt` then reports every file OK and one warning for the `combined` line, which is expected.

## Validate before you finish

- Every file parses as JSON and has exactly the shape above.
- Every skill in `required_skills`, `preferred_skills` and `resume_has` is a canonical name in `SKILLS.json`.
- `resume_has` is a subset of `required_skills` plus `preferred_skills`.
- The category counts match the table.

## Final report

Give only:
- the file count;
- the count per category.

Do not include anything from the contents of the pairs.
