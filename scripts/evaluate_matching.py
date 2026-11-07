"""Evaluate the matching engine.

  python scripts/evaluate_matching.py [--dir data/eval]
      Owner-labeled pairs (format: data/eval/README.md). Exit codes: 2 PENDING (fewer than 15
      pairs or fewer than 5 holdout pairs), 1 FAIL (holdout precision or recall below the
      provisional 0.85 gate), 0 PASS. Holdout results are aggregate only.
  python scripts/evaluate_matching.py --fixtures tests/fixtures/postings
      Per-stage report on the reviewer-written development fixtures (exit 0, report only).

Prints skill names and short descriptions only, never posting or resume text.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.job_match import match_posting  # noqa: E402
from engine.match_stages import _qualify, disambiguate, find_mentions, segment  # noqa: E402

GATE = 0.85
MIN_PAIRS, MIN_HOLDOUT = 15, 5
FIELDS = ("id", "split", "posting_text", "resume_text", "required_skills", "preferred_skills", "resume_has")
GROUPS = ("required", "preferred", "unscored", "excluded")


def _ratio(n: int, d: int) -> str:
    return f"{n / d:.2f}" if d else "n/a"


# ---- fixtures (per-stage) ---------------------------------------------------------------------
def _lines(text: str, doc: str):
    return [ln for sec in segment(text, doc) for ln in sec.lines]


def _find_line(text: str, doc: str, needle: str):
    return next((ln for ln in _lines(text, doc) if needle in ln.text), None)


def result_sets(res) -> dict:
    """Group name -> sorted skill names, plus the found set (scored + unscored skills only)."""
    sets = {g: sorted(m.skill for m in getattr(res, g)) for g in GROUPS}
    sets["found"] = sorted(m.skill for g in ("required", "preferred", "unscored") for m in getattr(res, g) if m.found)
    return sets


def check_fixture(fx: dict) -> dict:
    """Return per-stage tallies and failure descriptions for one fixture."""
    post, resume = fx["posting_text"], fx["resume_text"]
    res = match_posting(post, resume)
    got, exp = result_sets(res), fx["expected"]
    fails, t = [], {}
    for g in (*GROUPS, "found"):
        if got[g] != sorted(exp.get(g, [])):
            fails.append(f"{g}: got {got[g]} expected {sorted(exp.get(g, []))}")
    t["doc_ok"] = not fails
    # stage 1: sections
    sec = []
    for lab in fx.get("line_labels", []):
        ln = _find_line(post, "posting", lab["contains"])
        sec.append(ln is not None and ln.section == lab["section"])
        if not sec[-1]:
            fails.append(f"section of line labelled {lab['contains'][:30]!r}: got {ln.section if ln else 'missing'} expected {lab['section']}")
    t["section"] = sec
    # stages 2-3: skill mentions found in the posting vs. all skills the fixture accounts for
    lines = tuple(_lines(post, "posting"))
    kept = {m.canonical for m in disambiguate(find_mentions(lines))}
    truth = {s for g in GROUPS for s in exp.get(g, [])}
    truth |= {m["canonical"] for m in fx.get("mention_labels", []) if m["doc"] == "posting" and m["status"] != "affirmed"}
    t["mention"] = (len(kept & truth), len(kept), len(truth))
    # stage 4: status
    stat = []
    for lab in fx.get("mention_labels", []):
        txt = post if lab["doc"] == "posting" else resume
        ln = _find_line(txt, lab["doc"], lab["line_contains"])
        ms = [m for m in disambiguate(find_mentions((ln,))) if m.canonical == lab["canonical"]] if ln else []
        pred = _qualify(ms[0], lab["doc"]).status if ms else "absent"
        stat.append(pred == lab["status"])
        if not stat[-1]:
            fails.append(f"status of {lab['canonical']} in {lab['line_contains'][:30]!r}: got {pred} expected {lab['status']}")
    t["status"] = stat
    # stage 5: importance and evidence
    imp = []
    for g in GROUPS:
        for s in exp.get(g, []):
            imp.append(s in got[g])
    t["importance"] = imp
    for lab in fx.get("evidence_labels", []):
        m = next((m for g in GROUPS for m in getattr(res, g) if m.skill == lab["canonical"]), None)
        ok = m is not None and lab["posting_line_contains"] in m.posting_line
        if not ok:
            fails.append(f"evidence for {lab['canonical']}: expected line containing {lab['posting_line_contains'][:30]!r}")
    t["fails"] = fails
    return t


def report_fixtures(fx_dir: Path) -> str:
    fixtures = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(fx_dir.glob("*.json"))]
    if not fixtures:
        return "no fixtures found"
    rows = [(fx["id"], check_fixture(fx)) for fx in fixtures]
    sec = [x for _, r in rows for x in r["section"]]
    stat = [x for _, r in rows for x in r["status"]]
    imp = [x for _, r in rows for x in r["importance"]]
    tp, pred, truth = (sum(r["mention"][i] for _, r in rows) for i in range(3))
    ok = sum(r["doc_ok"] for _, r in rows)
    out = [
        f"fixtures: {len(rows)}",
        f"stage 1 section accuracy:   {_ratio(sum(sec), len(sec))} ({sum(sec)}/{len(sec)})",
        f"stage 2-3 mention precision {_ratio(tp, pred)} ({tp}/{pred}), recall {_ratio(tp, truth)} ({tp}/{truth})",
        f"stage 4 status accuracy:    {_ratio(sum(stat), len(stat))} ({sum(stat)}/{len(stat)})",
        f"stage 5 importance accuracy: {_ratio(sum(imp), len(imp))} ({sum(imp)}/{len(imp)})",
        f"document-level exact sets:  {ok}/{len(rows)} fixtures",
    ]
    for fid, r in rows:
        out.append(f"  {'PASS' if r['doc_ok'] and not r['fails'] else 'FAIL'} {fid}")
        out += [f"      {f}" for f in r["fails"]]
    return "\n".join(out)


# ---- owner-labeled pairs ----------------------------------------------------------------------
def load_pairs(eval_dir: Path) -> list[dict]:
    pairs = []
    for f in sorted(eval_dir.glob("*.json")):
        if f.name.startswith("EXAMPLE."):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for i, p in enumerate(data["pairs"]):
            missing = [k for k in FIELDS if k not in p]
            if missing or p["split"] not in ("tune", "holdout"):
                raise ValueError(f"{f.name} pair {i}: bad or missing fields {missing or ['split']}")  # names only
            pairs.append(p)
    return pairs


def _tally(stats: list, pred: set, truth: set, pid: str, failures: list | None) -> None:
    stats[0] += len(pred & truth)
    stats[1] += len(pred)
    stats[2] += len(truth)
    if failures is not None:
        for label, names in (("spurious", sorted(pred - truth)), ("missed", sorted(truth - pred))):
            if names:
                failures.append(f"{pid}: {label} {', '.join(names)}")


METRICS = ("posting required", "posting preferred", "resume matching")


def _measure(group: list[dict], detail: bool) -> tuple[dict, dict]:
    stats = {n: [0, 0, 0] for n in METRICS}
    fails = {n: [] for n in METRICS}
    for p in group:
        r = match_posting(p["posting_text"], p["resume_text"])
        found = {m.skill for m in (*r.required, *r.preferred, *r.unscored) if m.found}
        for n, pred, truth in (
            (METRICS[0], {m.skill for m in r.required}, set(p["required_skills"])),
            (METRICS[1], {m.skill for m in r.preferred}, set(p["preferred_skills"])),
            (METRICS[2], found, set(p["resume_has"])),
        ):
            _tally(stats[n], pred, truth, p["id"], fails[n] if detail else None)
    return stats, fails


def evaluate(eval_dir: Path) -> tuple[str, int]:
    pairs = load_pairs(eval_dir)
    holdout = [p for p in pairs if p["split"] == "holdout"]
    tune = [p for p in pairs if p["split"] == "tune"]
    out, gate_fail = [], False
    for name, group, detail in (("tune", tune, True), ("holdout (aggregate only)", holdout, False)):
        out.append(f"== {name}: n={len(group)} pairs ==")
        if not group:
            out.append("  no pairs")
            continue
        stats, fails = _measure(group, detail)
        for n in METRICS:
            tp, pred, truth = stats[n]
            out.append(f"  {n}: precision {_ratio(tp, pred)} ({tp}/{pred}), recall {_ratio(tp, truth)} ({tp}/{truth})")
            out += [f"    fail {f}" for f in fails[n][:5]]
            if detail is False and ((pred and tp / pred < GATE) or (truth and tp / truth < GATE)):
                gate_fail = True
    if len(pairs) < MIN_PAIRS or len(holdout) < MIN_HOLDOUT:
        if not pairs:
            out.append("no evaluation pairs yet (add labeled files to data/eval/, see data/eval/README.md)")
        out.append(f"PENDING: {len(pairs)} pairs ({len(holdout)} holdout); "
                   f"need {MIN_PAIRS} pairs with {MIN_HOLDOUT} holdout")
        return "\n".join(out), 2
    out.append(f"FAIL: holdout precision or recall below the provisional {GATE} gate" if gate_fail
               else f"PASS: holdout meets the provisional {GATE} gate (small sample, not a general accuracy claim)")
    return "\n".join(out), 1 if gate_fail else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path(__file__).resolve().parent.parent / "data" / "eval"))
    ap.add_argument("--fixtures", help="directory of development fixtures for the per-stage report")
    args = ap.parse_args(argv)
    if args.fixtures:
        print(report_fixtures(Path(args.fixtures)))
        return 0
    text, code = evaluate(Path(args.dir))
    print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
