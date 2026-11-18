"""Evaluate the matching engine.

  python scripts/evaluate_matching.py [--dir data/eval]
      Owner-labeled pairs (format: data/eval/README.md). Exit codes: 2 PENDING (fewer than 15
      pairs or fewer than 5 holdout pairs), 1 FAIL (holdout precision or recall below the
      provisional 0.85 gate), 0 PASS. Holdout results are aggregate only.
  python scripts/evaluate_matching.py --fixtures tests/fixtures/postings tests/fixtures/regression_r6
      Per-stage report on the reviewer-written fixtures (exit 0, report only). Labels listed in
      tests/fixtures/DISPUTED.json (line_label, mention_label, expected_set) are reported separately.
  python scripts/evaluate_matching.py --update-docs
      Rewrite the generated evaluation section of docs/SCORING.md from a run over both folders.

Prints skill names and short descriptions only, never posting or resume text.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.job_match import match_posting  # noqa: E402
from engine.match_stages import _qualify, disambiguate, find_mentions, segment  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIRS = (ROOT / "tests" / "fixtures" / "postings", ROOT / "tests" / "fixtures" / "regression_r6")
DISPUTE_FILES = (ROOT / "tests" / "fixtures" / "DISPUTED.json",)
DOC = ROOT / "docs" / "SCORING.md"
MARK_START, MARK_END = "<!-- eval:start -->", "<!-- eval:end -->"
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


def load_disputed() -> list[dict]:
    """Disputed / conflicting labels, kept unchanged and reported separately."""
    out = []
    for f in DISPUTE_FILES:
        if f.exists():
            out += json.loads(f.read_text(encoding="utf-8"))["disputed"]
    return out


def _is_disputed(disputed, fid: str, label: dict, kind: str) -> dict | None:
    for rec in disputed:
        lab = rec["label"]
        if rec["fixture"] == fid and lab["kind"] == kind and all(lab[k] == label[k] for k in label):
            return rec
    return None


def _resolve(lab: dict, cands: list):
    """(mentions the label claims, None) or ([], error text).

    An indexed label (occurrence / span_text / span) claims exactly one mention; an un-indexed label
    claims every mention of its canonical on the line and asserts the status for all of them.
    """
    name = f"{lab['canonical']} in {lab['line_contains'][:30]!r}"
    if not cands:
        return [], f"missing mention: {name}"
    if "occurrence" in lab:  # 1-based among this canonical's mentions on the line, in text order
        i = lab["occurrence"]
        return ([cands[i - 1]], None) if 1 <= i <= len(cands) else ([], f"missing mention: {name} occurrence {i} of {len(cands)}")
    if "span_text" in lab or "span" in lab:
        want = lab.get("span_text")
        hits = [m for m in cands if (m.line.text[m.span[0] - m.line.start:m.span[1] - m.line.start] == want if want is not None
                                     else list(m.span) == list(lab["span"]))]
        if len(hits) != 1:
            return [], f"{'ambiguous span' if hits else 'missing mention'}: {name} span {want or lab['span']}"
        return hits, None
    return cands, None


def check_fixture(fx: dict, disputed=None) -> dict:
    """Return per-stage tallies, failure descriptions and disputed-label records for one fixture."""
    disputed = load_disputed() if disputed is None else disputed
    post, resume = fx["posting_text"], fx["resume_text"]
    res = match_posting(post, resume)
    got, exp = result_sets(res), fx["expected"]
    fails, t, disp, skip = [], {}, [], set()
    for g in (*GROUPS, "found"):
        have, want = got[g], sorted(exp.get(g, []))
        for rec in disputed:  # expected_set dispute: drop the canonical from both sides, report it
            lab = rec["label"]
            if rec["fixture"] == fx["id"] and lab["kind"] == "expected_set" and lab["group"] == g and (lab["canonical"] in want) == lab["present"]:
                present = lab["canonical"] in have
                disp.append({"fixture": fx["id"], "label": lab, "got": {"present": present}, "alternative": rec["alternative"],
                             "alt_ok": {"present": present} == rec["alternative"], "reason": rec["reason"]})
                skip.add((g, lab["canonical"]))
                have = [s for s in have if s != lab["canonical"]]
                want = [s for s in want if s != lab["canonical"]]
        if have != want:
            fails.append(f"{g}: got {have} expected {want}")
    t["doc_ok"] = not fails
    # stage 1: sections
    sec = []
    for lab in fx.get("line_labels", []):
        ln = _find_line(post, "posting", lab["contains"])
        pred = ln.section if ln else "missing"
        rec = _is_disputed(disputed, fx["id"], {"contains": lab["contains"], "section": lab["section"]}, "line_label")
        if rec:
            disp.append({"fixture": fx["id"], "label": rec["label"], "got": {"section": pred},
                         "alternative": rec["alternative"], "alt_ok": {"section": pred} == rec["alternative"],
                         "reason": rec["reason"]})
            continue
        sec.append(pred == lab["section"])
        if not sec[-1]:
            fails.append(f"section of line labelled {lab['contains'][:30]!r}: got {pred} expected {lab['section']}")
    t["section"] = sec
    # stages 2-3: skill mentions found in the posting vs. all skills the fixture accounts for
    lines = tuple(_lines(post, "posting"))
    kept = {m.canonical for m in disambiguate(find_mentions(lines))}
    truth = {s for g in GROUPS for s in exp.get(g, [])}
    truth |= {m["canonical"] for m in fx.get("mention_labels", []) if m["doc"] == "posting" and m["status"] != "affirmed"}
    t["mention"] = (len(kept & truth), len(kept), len(truth))
    # stage 4: status. Labels resolve one-to-one to actual mentions (canonical + exact span).
    stat, claimed, labelled = [], {}, {}
    for lab in fx.get("mention_labels", []):
        doc = lab["doc"]
        ln = _find_line(post if doc == "posting" else resume, doc, lab["line_contains"])
        cands = [m for m in disambiguate(find_mentions((ln,))) if m.canonical == lab["canonical"]] if ln else []
        tag = f"{lab['canonical']} in {lab['line_contains'][:30]!r}"
        picks, err = _resolve(lab, cands)
        preds = [_qualify(m, doc).status for m in picks]
        bad = next((i for i, x in enumerate(preds) if x != lab["status"]), None)
        pred = "absent" if err else preds[bad if bad is not None else 0]
        if ln:
            labelled[(doc, ln.start)] = ln
        if any(claimed.setdefault((doc, m.span), lab) is not lab for m in picks):
            pred, err = "duplicate", f"duplicate label for {tag}: resolves to a mention another label already claimed"
        elif bad is not None and len(cands) > 1:
            err = f"status of {tag} occurrence {cands.index(picks[bad]) + 1} of {len(cands)}: got {pred} expected {lab['status']}"
        key = {k: lab[k] for k in ("doc", "line_contains", "canonical", "status")}
        rec = _is_disputed(disputed, fx["id"], key, "mention_label")
        if rec:
            disp.append({"fixture": fx["id"], "label": rec["label"], "got": {"status": pred},
                         "alternative": rec["alternative"], "alt_ok": {"status": pred} == rec["alternative"],
                         "reason": rec["reason"]})
            continue
        stat.append(pred == lab["status"] and not err)
        if not stat[-1]:
            fails.append(err or f"status of {tag}: got {pred} expected {lab['status']}")
    t["status"] = stat
    if fx.get("strict_mentions"):  # opt-in: every mention on a labelled line must be labelled
        for (doc, _), ln in labelled.items():
            for m in disambiguate(find_mentions((ln,))):
                if (doc, m.span) not in claimed:
                    fails.append(f"unexpected unlabelled mention {m.canonical} on line {ln.text[:30]!r} ({doc})")
    # stage 5: importance and evidence
    t["importance"] = [s in got[g] for g in GROUPS for s in exp.get(g, []) if (g, s) not in skip]
    for lab in fx.get("evidence_labels", []):
        m = next((m for g in GROUPS for m in getattr(res, g) if m.skill == lab["canonical"]), None)
        if m is None or lab["posting_line_contains"] not in m.posting_line:
            fails.append(f"evidence for {lab['canonical']}: expected line containing {lab['posting_line_contains'][:30]!r}")
            continue
        sp = m.posting_span
        ln = next((x for x in _lines(post, "posting") if sp and x.start <= sp[0] and sp[1] <= x.end), None)
        if ln is None or lab["posting_line_contains"] not in ln.text:
            fails.append(f"evidence span for {lab['canonical']} is not on the line containing {lab['posting_line_contains'][:30]!r}")
        if "requirement" in lab and m.requirement != lab["requirement"]:
            fails.append(f"evidence for {lab['canonical']}: importance got {m.requirement} expected {lab['requirement']}")
    t["fails"], t["disputed"] = fails, disp
    return t


def run_fixtures(dirs, disputed=None) -> dict:
    """{folder name: [(fixture id, result)]} for every *.json in each directory."""
    disputed = load_disputed() if disputed is None else disputed
    out = {}
    for d in dirs:
        d = Path(d)
        out[d.name] = [(fx["id"], check_fixture(fx, disputed))
                       for fx in (json.loads(f.read_text(encoding="utf-8")) for f in sorted(d.glob("*.json")))]
    return out


def _summary(runs: dict) -> dict:
    rows = [r for rs in runs.values() for _, r in rs]
    pick = lambda k: [x for r in rows for x in r[k]]  # noqa: E731
    return {
        "section": pick("section"), "status": pick("status"), "importance": pick("importance"),
        "mention": tuple(sum(r["mention"][i] for r in rows) for i in range(3)),
        "disputed": [d for r in rows for d in r["disputed"]],
        "fixtures": len(rows), "ok": sum(1 for r in rows if r["doc_ok"] and not r["fails"]),
    }


def _metric_lines(sm: dict) -> list[str]:
    sec, stat, imp = sm["section"], sm["status"], sm["importance"]
    tp, pred, truth = sm["mention"]
    return [
        f"stage 1 section accuracy: {_ratio(sum(sec), len(sec))} ({sum(sec)}/{len(sec)})",
        f"stage 2-3 mention precision {_ratio(tp, pred)} ({tp}/{pred}), recall {_ratio(tp, truth)} ({tp}/{truth})",
        f"stage 4 status accuracy: {_ratio(sum(stat), len(stat))} ({sum(stat)}/{len(stat)})",
        f"stage 5 importance accuracy: {_ratio(sum(imp), len(imp))} ({sum(imp)}/{len(imp)})",
    ]


def _disputed_lines(sm: dict) -> list[str]:
    return [f"disputed label {d['fixture']}: {json.dumps(d['label'], ensure_ascii=False)} engine now "
            f"{json.dumps(d['got'])}, alternative {json.dumps(d['alternative'])} "
            f"({'engine matches the alternative' if d['alt_ok'] else 'engine matches neither'})" for d in sm["disputed"]]


def _original_line(dirs) -> str:
    """Totals with every disputed label counted as written (computed, not hard-coded)."""
    sm = _summary(run_fixtures(dirs, disputed=[]))
    sec, stat = sm["section"], sm["status"]
    return (f"with original labels (disputes counted as failures): fixtures passing {sm['ok']}/{sm['fixtures']}; "
            f"section accuracy {_ratio(sum(sec), len(sec))} ({sum(sec)}/{len(sec)}); "
            f"status accuracy {_ratio(sum(stat), len(stat))} ({sum(stat)}/{len(stat)})")


def report_fixtures(dirs) -> str:
    runs = run_fixtures(dirs)
    if not any(runs.values()):
        return "no fixtures found"
    sm = _summary(runs)
    out = [f"fixtures: {sm['fixtures']} ({', '.join(f'{k} {len(v)}' for k, v in runs.items())})"]
    out += _metric_lines(sm)
    out.append(f"document-level exact sets: {sm['ok']}/{sm['fixtures']} fixtures")
    out.append(_original_line(dirs))
    out.append(f"disputed labels reported separately: {len(sm['disputed'])}")
    out += _disputed_lines(sm)
    for folder, rows in runs.items():
        out.append(f"[{folder}]")
        for fid, r in rows:
            out.append(f"  {'PASS' if r['doc_ok'] and not r['fails'] else 'FAIL'} {fid}")
            out += [f"      {f}" for f in r["fails"]]
    return "\n".join(out)


def generated_section(dirs=FIXTURE_DIRS) -> str:
    """Markdown for the evaluation section of docs/SCORING.md (numbers come from a run, not by hand)."""
    runs = run_fixtures(dirs)
    sm = _summary(runs)
    out = [MARK_START, "<!-- generated by `python scripts/evaluate_matching.py --update-docs`; do not edit by hand -->", "",
           "Development and regression fixtures (written by the independent reviewer, not tuned on):", "",
           "| Folder | Fixtures | Exact-set pass |", "|---|---|---|"]
    for folder, rows in runs.items():
        out.append(f"| `{folder}` | {len(rows)} | {sum(1 for _, r in rows if r['doc_ok'] and not r['fails'])} |")
    out += [f"| total | {sm['fixtures']} | {sm['ok']} |", "", "Per-stage metrics over all fixtures:", ""]
    out += [f"- {m}" for m in _metric_lines(sm)]
    out += ["", f"With {_original_line(dirs)[5:]}"]
    out += ["", f"Disputed or conflicting labels, kept unchanged and excluded from the metrics above: {len(sm['disputed'])}", ""]
    out += [f"- `{d['fixture']}` {json.dumps(d['label'], ensure_ascii=False)}: engine now {json.dumps(d['got'])}, "
            f"alternative {json.dumps(d['alternative'])}; {d['reason']}" for d in sm["disputed"]]
    out += ["", "These are fixture results, not an accuracy estimate on unseen postings.", MARK_END]
    return "\n".join(out)


def update_docs() -> None:
    text = DOC.read_text(encoding="utf-8").replace("\r\n", "\n")
    a, b = text.index(MARK_START), text.index(MARK_END) + len(MARK_END)
    DOC.write_text(text[:a] + generated_section() + text[b:], encoding="utf-8", newline="\n")


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
        found = {m.skill for m in (*r.required, *r.preferred) if m.found}  # resume_has: scored skills only
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
    ap.add_argument("--fixtures", nargs="+", help="fixture directories for the per-stage report")
    ap.add_argument("--update-docs", action="store_true", help="rewrite the generated section of docs/SCORING.md")
    args = ap.parse_args(argv)
    if args.update_docs:
        update_docs()
        return 0
    if args.fixtures:
        print(report_fixtures(args.fixtures))
        return 0
    text, code = evaluate(Path(args.dir))
    print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
