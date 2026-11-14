# ruff: noqa
# NON-PRODUCTION. Read-only on the repo: writes the DRAFT expectations file and the migration ledger into <output dir>
# (never into tests/). Contract v4 revision 4: three permitted causes, every record listed, original values kept.
# Run from the repo root at fa1555e:  python <this file> <output dir>
import os, sys, json, glob, hashlib, subprocess, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ".")
import sim_confirm_v7  # patches X.analyse with the revision 4 rule ("affirmed" view of "suggested")
import sim_supported_v6 as X
import tests.test_stage4_scope as T4, tests.test_job_match as TJ

BASE = "fa1555e9999495cea9e1d4c1b64f3530cedc0daf"


def cause_of(rows, trig):
    c = {}
    cues = set().union(*(cu for _, _, cu in rows)) if rows else set()
    if cues: c["cue_line"] = sorted(cues)
    if trig: c["document_trigger"] = sorted(trig)
    if any(ca == "unsupported_form" for _, ca, _ in rows): c["unsupported_form"] = True
    return c


def classify(oracle): return "usefulness_loss" if oracle in ("affirmed", "found") else "conservative"


fixtures, tally = {}, collections.Counter()
for d in ("tests/fixtures/postings", "tests/fixtures/regression_r6"):
    for f in sorted(glob.glob(d + "/*.json")):
        f = f.replace("\\", "/")
        fx = json.load(open(f, encoding="utf8")); fid = fx["id"]; e = fx["expected"]
        ments, trig, state, _ = X.analyse(fx["resume_text"])
        blob = subprocess.run(["git", "show", f"{BASE}:{f}"], capture_output=True, check=True).stdout
        folder = "postings" if "/postings/" in f else "regression_r6"
        rec = {"source_file": f, "source_sha256": hashlib.sha256(blob).hexdigest(), "doc_triggers": sorted(trig),
               "source_test": f"tests/test_fixtures.py::test_fixture[{folder}-{fid}]",
               "mention_labels": [], "skills": []}
        for lab in fx.get("mention_labels", []):
            if lab["doc"] != "resume": continue
            hit = [(st, ca, cu) for m, ln, st, ca, cu in ments if m.canonical == lab["canonical"] and lab["line_contains"] in ln.text]
            assert hit, ("label matches no mention", fid, lab)
            if not trig and all(st == "affirmed" for st, _, _ in hit):
                assert lab["status"] == "affirmed", ("disclaimed mention in supported form", fid, lab)
                continue
            c = cause_of(hit, trig)
            rec["mention_labels"].append({"label": lab, "expected_status": "unresolved", "oracle_answer": lab["status"], "cause": c,
                                          "classification": classify(lab["status"])})
            tally["label:" + lab["status"]] += 1; tally["label cause:" + "+".join(c)] += 1
        gold = set(e.get("found", []))
        for s in sorted(set(e.get("required", [])) | set(e.get("preferred", [])) | set(e.get("unscored", []))):
            if state.get(s) != "unresolved": continue
            mine = [(st, ca, cu) for m, ln, st, ca, cu in ments if m.canonical == s]
            oracle = "found" if s in gold else "not_found"; c = cause_of(mine, trig)
            rec["skills"].append({"skill": s, "expected_suggestion": "unresolved", "oracle_answer": oracle, "cause": c, "classification": classify(oracle)})
            tally["skill:" + oracle] += 1; tally["skill cause:" + "+".join(c)] += 1
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
    assert all(v == "unresolved" for v in state.values()), text
    cases.append({"source_test": src, "doc": "resume", "input": text, "expected_suggestion": state, "oracle_answer": oracle, "cause": cause})

INPUT_CHANGES = [  # R3: the input half; the assertion half follows F1 (API_AND_MIGRATION_PLAN.md §3)
    {"test": JM + "test_headingless_posting_is_unscored_with_score_none", "argument": "resume",
     "original_input": "Python dev", "proposed_input": "Skills\nPython"},
    {"test": JM + "test_required_and_preferred_score", "argument": "resume",
     "original_input": "SolidWorks", "proposed_input": "Skills\nSolidWorks"},
    {"test": JM + "test_excluded_section_never_scores", "argument": "resume",
     "original_input": "Python, SolidWorks", "proposed_input": "Skills\nPython, SolidWorks"},
    {"test": JM + "test_lines_and_spans_attributed", "argument": "res",
     "original_input": "Intro\nDesigned parts in SolidWorks", "proposed_input": "Intro\n\nDesigned parts in SolidWorks"},
    {"test": JM + "test_long_line_snippet_is_capped_and_span_exact", "argument": "resume",
     "original_input": "<line> where line = 'word ' * 100 + 'SolidWorks ' + 'word ' * 100", "proposed_input": "'Used ' + <line>"},
]
CF = "tests/test_check_fixture.py::"
CHECKER = [
    {"test": CF + "test_per_occurrence_labels_pass", "change": "check/lab become pcheck/plab: the two-status line is labelled in the posting",
     "original_input": {"doc": "resume", "resume_text": "Skills\nNo CFD experience; currently studying CFD\n"}},
    {"test": CF + "test_wrong_second_occurrence_fails_even_though_first_is_right", "change": "same",
     "original_input": {"doc": "resume", "resume_text": "Skills\nNo CFD experience; currently studying CFD\n"}},
    {"test": CF + "test_duplicate_labels_reported", "change": "same",
     "original_input": {"doc": "resume", "resume_text": "Skills\nNo CFD experience; currently studying CFD\n"}},
    {"test": CF + "test_unindexed_label_asserts_every_occurrence", "change": "same; its two resume_text overrides become posting_text overrides",
     "original_input": {"doc": "resume", "resume_text_overrides": ["Skills\nNo CFD experience; no CFD training\n", "Skills\nNo CFD experience\n"]}},
    {"test": CF + "test_resume_labels_one_state_per_unit", "change": "NEW in the same migration: résumé-side occurrence regression", "original_input": None},
    {"test": CF + "(module constants POST, RESUME and helper lab; the other four tests)", "change": "UNCHANGED: they keep their résumé-side inputs",
     "original_input": {"POST": "Requirements:\n- Python\n- CFD\n\nNice to have:\n- CFD\n", "RESUME": "Skills\nNo CFD experience; currently studying CFD\n", "lab_doc": "resume"}},
]

out = {"schema": "expectations_line_rule/4", "status": "DRAFT - not approved; not read by any test",
       "rule": "CONTRACT_V4_LINE_RULE.md revision 4 (2026-11-13)", "base_commit": BASE,
       "generated_by": "sim/gen_expectations_v7.py (non-production simulation, not an implementation)",
       "permitted_causes": ["cue_line", "document_trigger", "unsupported_form"],
       "semantics": "expected_status (mention) and expected_suggestion (skill) are the résumé-side states under revision 4. They "
                    "are a separate measure of suggestion quality. They do not redefine the fixture's gold found-set, which stays "
                    "the record of what the person has and is kept unchanged as oracle_answer. 'unresolved' is never a passing "
                    "classification: the résumé alone decides nothing and the user is asked. source_test names the original test. classification 'usefulness_loss' marks a record whose original value was affirmed or "
                    "found; 'conservative' marks one whose original value was negated, hypothetical or not_found. source_sha256 is "
                    "the sha256 of the file's blob at base_commit.",
       "fixtures": fixtures, "line_rule_cases": cases, "test_input_changes": INPUT_CHANGES, "checker_test_changes": CHECKER}
data = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
dst = sys.argv[1]
open(os.path.join(dst, "EXPECTATIONS_LINE_RULE.DRAFT.json"), "w", encoding="utf8", newline="\n").write(data)
open(os.path.join(dst, "EXPECTATIONS_LINE_RULE.DRAFT.sha256"), "w", newline="\n").write(
    hashlib.sha256(data.encode("utf8")).hexdigest() + "  EXPECTATIONS_LINE_RULE.DRAFT.json\n")


# ---- ledger (Markdown view of the same records) ----
def esc(s): return str(s).replace("|", "\\|").replace("\n", "⏎")


def cause_txt(c):
    parts = []
    if "cue_line" in c: parts.append("cue line (" + ", ".join(c["cue_line"]) + ")")
    if "document_trigger" in c: parts.append("document trigger (" + ", ".join(c["document_trigger"]) + ")")
    if "unsupported_form" in c: parts.append("unsupported form")
    return "; ".join(parts)


rows = [(fid, v["source_file"], v["source_sha256"][:12], r) for fid, v in fixtures.items() for r in v["mention_labels"] + v["skills"]]
only_unsupported = [x for x in rows if list(x[3]["cause"]) == ["unsupported_form"]]
others = [x for x in rows if list(x[3]["cause"]) != ["unsupported_form"]]
HEAD = "| # | Fixture (original test: `tests/test_fixtures.py::test_fixture[<folder>-<id>]`) | Blob sha256 at fa1555e (first 12) | Record | Original value (kept) | Proposed | Cause | Classification |\n|---|---|---|---|---|---|---|---|"


def table(xs):
    out = [HEAD]
    for i, (fid, src, sha, r) in enumerate(xs, 1):
        rec = f"label: {r['label']['canonical']}, line_contains `{esc(r['label']['line_contains'])}`" if "label" in r else f"skill: {r['skill']}"
        out.append(f"| {i} | `{src}` | {sha} | {esc(rec)} | {r['oracle_answer']} | unresolved | {cause_txt(r['cause'])} | {r['classification'].replace('_', ' ')} |")
    return "\n".join(out)


cl = collections.Counter(r["classification"] for _, _, _, r in rows)
md = f"""# Migration ledger for contract v4 revision 4 (DRAFT, nothing applied)

Generated by `sim/gen_expectations_v7.py` from the fixtures at `fa1555e`. It is a readable view of
`EXPECTATIONS_LINE_RULE.DRAFT.json`. No fixture, label or test has been changed. Every original value is kept.

"Unresolved" is not a passing classification. It means the résumé alone decides nothing for that skill and the user is
asked. A record marked **usefulness loss** had an original value of affirmed or found.

## Summary

| | Count |
|---|---|
| Fixtures with at least one record | {len(fixtures)} of 62 |
| Records | {len(rows)}: {sum('label' in r for _, _, _, r in rows)} mention labels, {sum('skill' in r for _, _, _, r in rows)} skills |
| Usefulness losses (original affirmed or found) | {cl['usefulness_loss']} |
| Conservative (original negated, hypothetical or not found) | {cl['conservative']} |
| Part A: cause is unsupported form only (ruling R2) | {len(only_unsupported)}, all usefulness losses: {all(r['classification'] == 'usefulness_loss' for _, _, _, r in only_unsupported)} |
| Part B: cause includes a cue line or a document trigger | {len(others)} |
| Part C: retired test inputs carried over | {len(cases)} |
| Part D: test edits | {len(INPUT_CHANGES)} input changes, {len(CHECKER) - 2} checker tests, 1 new test; assertion and evaluator migration in `API_AND_MIGRATION_PLAN.md` |

## Part A. The {len(only_unsupported)} records migrated on "unsupported form" alone (R2)

{table(only_unsupported)}

## Part B. The {len(others)} records with a cue line or a document trigger

{table(others)}

## Part C. Retired test inputs carried over as line-rule cases

| # | Source test | Input | Original assertion (kept) | Revision 4 suggestion | Cause |
|---|---|---|---|---|---|
""" + "\n".join(
    f"| {i} | `{c['source_test']}` | `{esc(c['input'])}` | {esc(c['oracle_answer'])} | {esc(c['expected_suggestion'])} | "
    f"{esc('; '.join(k + ': ' + cause_txt(v) for k, v in c['cause'].items()))} |" for i, c in enumerate(cases, 1)) + """

## Part D. Test edits (proposed diffs: `TEST_JOB_MATCH_PROPOSED.diff`, `TEST_CHECK_FIXTURE_PROPOSED.diff`)

### D1. Five input changes in `tests/test_job_match.py` (R3). Their `score`/`found` assertions also move to the new interfaces (F1): see `API_AND_MIGRATION_PLAN.md` §3.

| Test | Argument | Original input (kept here) | Proposed input |
|---|---|---|---|
""" + "\n".join(f"| `{c['test']}` | {c['argument']} | `{esc(c['original_input'])}` | `{esc(c['proposed_input'])}` |" for c in INPUT_CHANGES) + """

### D2. Checker tests in `tests/test_check_fixture.py` (R4)

| Test | Change | Original résumé-side input (kept here) |
|---|---|---|
""" + "\n".join(f"| `{c['test']}` | {c['change']} | {esc(json.dumps(c['original_input'], ensure_ascii=False)) if c['original_input'] else 'none (new test)'} |" for c in CHECKER) + "\n"
open(os.path.join(dst, "MIGRATION_LEDGER.md"), "w", encoding="utf8", newline="\n").write(md)
print(len(fixtures), "fixtures;", len(rows), "records;", dict(sorted(tally.items())))
print("classification:", dict(cl), "| unsupported-form-only:", len(only_unsupported), "| cases:", len(cases))
