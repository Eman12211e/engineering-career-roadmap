# ruff: noqa
# NON-PRODUCTION. Read-only on the repo: writes the DRAFT expectations file next to the contract (never into tests/).
# Run from the repo root at fa1555e:  python <this file> <output dir>
import os, sys, json, glob, hashlib, subprocess, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ".")
import sim_supported_v6 as X
import tests.test_stage4_scope as T4, tests.test_job_match as TJ

BASE = "fa1555e9999495cea9e1d4c1b64f3530cedc0daf"


def cause_of(rows, trig):
    """rows: [(state, cause, cues)] for the mentions behind one record."""
    c = {}
    cues = set().union(*(cu for _, _, cu in rows)) if rows else set()
    if cues: c["cue_line"] = sorted(cues)
    if trig: c["document_trigger"] = sorted(trig)
    if any(ca == "unsupported_form" for _, ca, _ in rows): c["unsupported_form"] = True
    return c


def permitted(c): return "cue_line" in c or "document_trigger" in c


fixtures, not_permitted, tally = {}, [], collections.Counter()
for d in ("tests/fixtures/postings", "tests/fixtures/regression_r6"):
    for f in sorted(glob.glob(d + "/*.json")):
        f = f.replace("\\", "/")
        fx = json.load(open(f, encoding="utf8")); fid = fx["id"]; e = fx["expected"]
        ments, trig, state, _ = X.analyse(fx["resume_text"])
        blob = subprocess.run(["git", "show", f"{BASE}:{f}"], capture_output=True, check=True).stdout
        rec = {"source_file": f, "source_sha256": hashlib.sha256(blob).hexdigest(), "doc_triggers": sorted(trig),
               "mention_labels": [], "skills": []}
        for lab in fx.get("mention_labels", []):
            if lab["doc"] != "resume": continue
            hit = [(st, ca, cu) for m, ln, st, ca, cu in ments if m.canonical == lab["canonical"] and lab["line_contains"] in ln.text]
            assert hit, ("label matches no mention", fid, lab)
            if not trig and all(st == "affirmed" for st, _, _ in hit):
                assert lab["status"] == "affirmed", ("CRITICAL", fid, lab)
                continue
            r = {"label": lab, "expected": "unresolved", "oracle_answer": lab["status"], "cause": cause_of(hit, trig)}
            if permitted(r["cause"]): rec["mention_labels"].append(r); tally["label:" + lab["status"]] += 1
            else: not_permitted.append({"fixture": fid, **r}); tally["not_permitted:label"] += 1
        gold = set(e.get("found", []))
        for s in sorted(set(e.get("required", [])) | set(e.get("preferred", [])) | set(e.get("unscored", []))):
            if state.get(s) != "unresolved": continue
            mine = [(st, ca, cu) for m, ln, st, ca, cu in ments if m.canonical == s]
            r = {"skill": s, "expected": "unresolved", "oracle_answer": "found" if s in gold else "not_found", "cause": cause_of(mine, trig)}
            if permitted(r["cause"]): rec["skills"].append(r); tally["skill:" + r["oracle_answer"]] += 1
            else: not_permitted.append({"fixture": fid, **r}); tally["not_permitted:skill"] += 1
        if rec["mention_labels"] or rec["skills"]: fixtures[fid] = rec


def params(fn): return fn.pytestmark[0].args[1]


S4, CB, JM = "tests/test_stage4_scope.py::", "tests/test_cue_binding.py::", "tests/test_job_match.py::"
CASES = [(S4 + "test_r31_minimal_pairs", t, e) for t, e in params(T4.test_r31_minimal_pairs)] + \
        [(S4 + "test_scope_ends_and_later_cues", t, e) for t, e in params(T4.test_scope_ends_and_later_cues)] + [
    (S4 + "test_scope_continues_across_a_joined_hard_wrap_but_not_a_blank_line", "- Currently learning PLC\nand root cause analysis", {T4.RCA: "hypothetical"}),
    (S4 + "test_scope_continues_across_a_joined_hard_wrap_but_not_a_blank_line", "- Currently learning PLC\n\nRoot cause analysis", {T4.RCA: "affirmed"}),
    (S4 + "test_cues_never_reach_back", "SolidWorks, then learning FEA", {T4.SW: "affirmed"}),
    (S4 + "test_negation_keeps_the_gap_rule_and_does_not_spread", "No experience with FEA or CFD", {T4.FEA: "negated"}),
    (S4 + "test_negation_keeps_the_gap_rule_and_does_not_spread", "No rework using SPC", {"Statistical Process Control": "affirmed"}),
    (S4 + "test_negation_keeps_the_gap_rule_and_does_not_spread", "Never missed a deadline in SolidWorks", {T4.SW: "affirmed"}),
    (CB + "test_negation_after_is_posting_only", "FEA is not required", {T4.FEA: "affirmed"}),
] + [(JM + "test_resume_negation_is_narrow", t, {T4.SW: "found"}) for t in params(TJ.test_resume_negation_is_narrow)]
cases = []
for src, text, oracle in CASES:
    ments, trig, state, _ = X.analyse(text)
    cause = {s: cause_of([(st, ca, cu) for m, _, st, ca, cu in ments if m.canonical == s], trig) for s in state if state[s] == "unresolved"}
    cases.append({"source_test": src, "doc": "resume", "input": text, "expected": state, "oracle_answer": oracle, "cause": cause})
    tally["case"] += 1; tally["case:every skill unresolved"] += all(v == "unresolved" for v in state.values())

out = {"schema": "expectations_line_rule/2", "status": "DRAFT - not approved; not read by any test",
       "rule": "CONTRACT_V4_LINE_RULE.md revision 3 (2026-11-13)", "base_commit": BASE,
       "generated_by": "sim/gen_expectations_v6.py (non-production simulation, not an implementation)",
       "permitted_causes": ["cue_line", "document_trigger"],
       "permitted_change": "a résumé label or skill may change to 'unresolved' only when a cue line or a document-level "
                           "trigger causes it; the cause is recorded per record; the original value is kept as oracle_answer; "
                           "source_sha256 is the sha256 of the file's blob at base_commit",
       "fixtures": fixtures, "not_permitted": not_permitted, "line_rule_cases": cases}
data = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
open(os.path.join(sys.argv[1], "EXPECTATIONS_LINE_RULE.DRAFT.json"), "w", encoding="utf8", newline="\n").write(data)
open(os.path.join(sys.argv[1], "EXPECTATIONS_LINE_RULE.DRAFT.sha256"), "w", newline="\n").write(
    hashlib.sha256(data.encode("utf8")).hexdigest() + "  EXPECTATIONS_LINE_RULE.DRAFT.json\n")
print(len(fixtures), "fixtures;", dict(sorted(tally.items())))
print("not permitted, by fixture:", dict(collections.Counter(r["fixture"] for r in not_permitted)))
c = collections.Counter()
for v in fixtures.values():
    for r in v["mention_labels"] + v["skills"]: c[("label" if "label" in r else "skill", "+".join(r["cause"]))] += 1
print("permitted records by cause:", dict(sorted(c.items())))
print("cases with an affirmed skill:", [(x["input"], x["expected"]) for x in cases if "affirmed" in x["expected"].values()])
