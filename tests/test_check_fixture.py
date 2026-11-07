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


def test_duplicate_labels_reported():
    r = check(mention_labels=[lab("negated", occurrence=1), lab("negated", occurrence=1)])
    assert r["status"] == [True, False]
    assert any(f.startswith("duplicate label") for f in r["fails"])


def test_ambiguous_label_without_occurrence():
    r = check(mention_labels=[lab("negated")])
    assert r["status"] == [False]
    assert any(f.startswith("ambiguous label") for f in r["fails"])


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
