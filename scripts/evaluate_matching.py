"""Evaluate posting extraction and resume matching against owner-labeled pairs.

Usage: python scripts/evaluate_matching.py [--dir data/eval]
Format: data/eval/README.md. Prints skill names only, never posting/resume text.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.job_match import match_posting  # noqa: E402

FIELDS = ("id", "split", "posting_text", "resume_text", "required_skills", "preferred_skills", "resume_has")


def load_pairs(eval_dir: Path) -> list[dict]:
    pairs = []
    for f in sorted(eval_dir.glob("*.json")):
        if f.name.startswith("EXAMPLE."):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for i, p in enumerate(data["pairs"]):
            missing = [k for k in FIELDS if k not in p]
            if missing or p["split"] not in ("tune", "holdout"):
                # name fields only, never values
                raise ValueError(f"{f.name} pair {i}: bad or missing fields {missing or ['split']}")
            pairs.append(p)
    return pairs


def _tally(stats, pred: set, truth: set, pid: str, failures: list) -> None:
    tp = len(pred & truth)
    stats[0] += tp
    stats[1] += len(pred)
    stats[2] += len(truth)
    for label, names in (("spurious", sorted(pred - truth)), ("missed", sorted(truth - pred))):
        if names:
            failures.append(f"{pid}: {label} {', '.join(names)}")


def _ratio(n: int, d: int) -> str:
    return f"{n / d:.2f}" if d else "n/a"


def evaluate(eval_dir: Path) -> str:
    pairs = load_pairs(eval_dir)
    if not pairs:
        return "no evaluation pairs yet (add labeled files to data/eval/, see data/eval/README.md)"
    out = []
    for split in ("tune", "holdout"):
        group = [p for p in pairs if p["split"] == split]
        out.append(f"== {split} (n={len(group)} pairs) ==")
        if not group:
            out.append("  no pairs")
            continue
        names = ("posting required", "posting preferred", "resume matching")
        stats = {n: [0, 0, 0] for n in names}
        fails = {n: [] for n in names}
        for p in group:
            r = match_posting(p["posting_text"], p["resume_text"])
            _tally(stats[names[0]], {m.skill for m in r.required}, set(p["required_skills"]), p["id"], fails[names[0]])
            _tally(stats[names[1]], {m.skill for m in r.preferred}, set(p["preferred_skills"]), p["id"], fails[names[1]])
            found = {m.skill for m in r.required + r.preferred if m.found}
            _tally(stats[names[2]], found, set(p["resume_has"]), p["id"], fails[names[2]])
        for n in names:
            tp, pred, truth = stats[n]
            out.append(f"  {n}: precision {_ratio(tp, pred)} ({tp}/{pred}), recall {_ratio(tp, truth)} ({tp}/{truth})")
            out += [f"    fail {f}" for f in fails[n][:5]]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path(__file__).resolve().parent.parent / "data" / "eval"))
    print(evaluate(Path(ap.parse_args(argv).dir)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
