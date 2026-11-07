import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DIRS = {
    "postings": ROOT / "tests" / "fixtures" / "postings",
    "regression_r6": ROOT / "tests" / "fixtures" / "regression_r6",
}
FIXTURES = [(name, p) for name, d in DIRS.items() for p in sorted(d.glob("*.json"))]

_spec = importlib.util.spec_from_file_location("evaluate_matching", ROOT / "scripts" / "evaluate_matching.py")
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)


def test_fixture_counts():
    assert {n: len(list(d.glob("*.json"))) for n, d in DIRS.items()} == {"postings": 48, "regression_r6": 14}


# Locked historical labels with no `occurrence`/`span_text` on a line holding several mentions of the
# skill. Not edited and not in DISPUTED.json; the coordinator decides. They must fail ONLY as ambiguous.
AMBIGUOUS = {"full_indeed_dash", "r5_bigco_basic_preferred", "r5_desired_characteristics", "r5_pdf_wrapped",
             "r5_staffing_agency", "u6_bigco_basic_desired", "u6_mfg_technician", "u6_numbered_lists", "u6_pdf_hardwrap"}


@pytest.mark.parametrize("folder,path", FIXTURES, ids=lambda x: x.stem if isinstance(x, Path) else x)
def test_fixture(folder, path):
    fx = json.loads(path.read_text(encoding="utf-8"))
    r = ev.check_fixture(fx)  # disputed labels are excluded from `fails` and reported separately
    if fx["id"] in AMBIGUOUS:
        assert r["fails"] and all(f.startswith("ambiguous label") for f in r["fails"])
        pytest.xfail("historical label is ambiguous under one-to-one matching")
    # check_fixture compares the five expected sets, line labels, mention labels and evidence labels
    assert r["fails"] == [], fx.get("note")
    assert r["doc_ok"]


def test_disputed_labels_are_reported_and_match_their_alternative(capsys):
    """Disputed labels never fail the fixture test, but the engine's value must be the recorded alternative."""
    records = []
    for _, path in FIXTURES:
        r = ev.check_fixture(json.loads(path.read_text(encoding="utf-8")))
        records += r["disputed"]
    disputed = ev.load_disputed()
    assert len(records) == len(disputed) >= 2
    for rec in records:
        print("DISPUTED", json.dumps(rec, ensure_ascii=False))
        assert rec["alt_ok"], rec
    assert "DISPUTED" in capsys.readouterr().out
