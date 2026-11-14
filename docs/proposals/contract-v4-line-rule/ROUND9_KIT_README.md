# Round 9 author kit: procedure

This file is NOT part of the kit. The author never sees it. The kit is the folder `round9/`, which holds exactly three files:

| File | Purpose |
|---|---|
| `round9/AUTHOR_INSTRUCTIONS.md` | What to write, the composition, how to seal |
| `round9/SCHEMA_EXAMPLE.json` | One fake pair showing the file shape. Not evaluation data |
| `round9/SKILLS.json` | The skill names the author may use: canonical name and aliases |

## Isolation

1. The three kit files are COPIED to a new, empty folder outside the repository and outside every worktree, before the author starts.
2. The author works only in that copy.
3. The sealed `out/` files never enter the repository. Implementers' prompts forbid reading them.
4. Only the manifest hashes are committed, in `docs/UNSEEN_SET.md`, before any production change.

## Who may do what

| Who | May |
|---|---|
| Anyone | Read the three kit files |
| Only a fresh author who has not read this proposal folder, `data/match_rules.json`, the engine, the simulations or the expectations file | Write the probes |
| Implementers and their prompts | Never read the sealed files |

## How `SKILLS.json` was made

One-off command, run from the repository root:

```
python -c "import json; d=json.load(open('data/keywords.json',encoding='utf-8'))['skills']; json.dump([{'canonical':s['canonical'],'aliases':s['aliases']} for s in d], open('docs/proposals/contract-v4-line-rule/round9/SKILLS.json','w',encoding='utf-8'), indent=2, ensure_ascii=False)"
```

It keeps only `canonical` and `aliases`. The `category`, `industries` and every other field are dropped.
