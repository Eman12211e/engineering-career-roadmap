import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("evaluate_matching", ROOT / "scripts" / "evaluate_matching.py")
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)

POST = "Requirements:\n- Python\n- CFD\n\nNice to have:\n- CFD\n"
RESUME = "Skills\nNo CFD experience; currently studying CFD\n"  # engine: 1st negated, 2nd hypothetical


def check(**kw):
    fx = {"id": "t", "posting_text": POST, "resume_text": RESUME, "expected": {}, **kw}
    return ev.check_fixture(fx, disputed=[])


def lab(status, **kw):
    return {"doc": "resume", "line_contains": "No CFD", "canonical": "CFD", "status": status, **kw}


def test_per_occurrence_labels_pass():
    r = check(mention_labels=[lab("negated", occurrence=1), lab("hypothetical", occurrence=2)])
    assert r["status"] == [True, True]
    assert check(mention_labels=[lab("negated", span_text="CFD", occurrence=1)])["status"] == [True]


def test_wrong_second_occurrence_fails_even_though_first_is_right():
    # the old checker compared every label to the first mention, so "negated" for occurrence 2 passed
    r = check(mention_labels=[lab("negated", occurrence=1), lab("negated", occurrence=2)])
    assert r["status"] == [True, False]
    assert any(f.startswith("status of CFD") and "got hypothetical" in f for f in r["fails"])


def test_expected_set_dispute_is_removed_and_reported():
    rec = {"fixture": "t", "label": {"kind": "expected_set", "group": "found", "canonical": "CFD", "present": True},
           "alternative": {"present": False}, "reason": "r"}
    fx = {"id": "t", "posting_text": POST, "resume_text": RESUME, "expected": {"found": ["CFD"]}}
    found = lambda r: [f for f in r["fails"] if f.startswith("found:")]  # noqa: E731
    assert found(ev.check_fixture(fx, disputed=[])) == ["found: got [] expected ['CFD']"]
    r = ev.check_fixture(fx, disputed=[rec])
    assert found(r) == [] and r["disputed"][0]["got"] == {"present": False} and r["disputed"][0]["alt_ok"]
    fx["expected"] = {"found": ["CFD", "Python"]}  # a non-disputed mismatch still fails
    assert found(ev.check_fixture(fx, disputed=[rec])) == ["found: got [] expected ['Python']"]


def test_duplicate_labels_reported():
    r = check(mention_labels=[lab("negated", occurrence=1), lab("negated", occurrence=1)])
    assert r["status"] == [True, False]
    assert any(f.startswith("duplicate label") for f in r["fails"])


def test_unindexed_label_asserts_every_occurrence():
    r = check(mention_labels=[lab("negated")])  # occurrence 2 is hypothetical
    assert r["status"] == [False]
    assert any("occurrence 2 of 2" in f and "got hypothetical" in f for f in r["fails"])
    assert check(mention_labels=[lab("negated", occurrence=1)])["status"] == [True]
    both = check(mention_labels=[lab("negated")], resume_text="Skills\nNo CFD experience; no CFD training\n")
    assert both["status"] == [True]
    one = check(mention_labels=[lab("negated")], resume_text="Skills\nNo CFD experience\n")
    assert one["status"] == [True]


def test_indexed_and_unindexed_label_on_same_mention_is_duplicate():
    r = check(mention_labels=[lab("negated", occurrence=1), lab("negated")])
    assert any(f.startswith("duplicate label") for f in r["fails"])


def test_missing_mention():
    r = check(mention_labels=[lab("negated", occurrence=3)])
    assert r["status"] == [False] and any(f.startswith("missing mention") for f in r["fails"])
    r = check(mention_labels=[lab("affirmed", canonical="Python", occurrence=1)])
    assert any(f.startswith("missing mention") for f in r["fails"])


def test_strict_mentions_flags_unlabelled_only_when_opted_in():
    labels = [lab("negated", occurrence=1)]
    assert not any("unexpected" in f for f in check(mention_labels=labels)["fails"])
    assert any("unexpected unlabelled mention CFD" in f for f in check(mention_labels=labels, strict_mentions=True)["fails"])


def test_same_skill_in_requirements_and_nice_to_have():
    ev_ok = [{"canonical": "CFD", "posting_line_contains": "- CFD", "requirement": "required"}]
    assert not [f for f in check(evidence_labels=ev_ok)["fails"] if f.startswith("evidence")]
    wrong_line = [{"canonical": "CFD", "posting_line_contains": "- Python"}]
    assert any(f.startswith("evidence") for f in check(evidence_labels=wrong_line)["fails"])
    wrong_imp = [{"canonical": "CFD", "posting_line_contains": "- CFD", "requirement": "preferred"}]
    assert any("importance" in f for f in check(evidence_labels=wrong_imp)["fails"])


def test_expected_set_dispute_on_scored_group_keeps_importance():
    rec = {"fixture": "t", "label": {"kind": "expected_set", "group": "required", "canonical": "Python", "present": True},
           "alternative": {"present": False}, "reason": "r"}
    fx = {"id": "t", "posting_text": POST, "resume_text": RESUME, "expected": {"required": ["CFD", "Python"]}}
    r = ev.check_fixture(fx, disputed=[rec])
    assert r["importance"] == [True] and r["disputed"][0]["got"] == {"present": True}
    assert not r["disputed"][0]["alt_ok"]


def test_expected_set_dispute_with_mismatched_present_is_not_applied():
    rec = {"fixture": "t", "label": {"kind": "expected_set", "group": "found", "canonical": "CFD", "present": False},
           "alternative": {"present": True}, "reason": "r"}
    fx = {"id": "t", "posting_text": POST, "resume_text": RESUME, "expected": {"found": ["CFD"]}}
    r = ev.check_fixture(fx, disputed=[rec])
    assert r["disputed"] == [] and "found: got [] expected ['CFD']" in r["fails"]
