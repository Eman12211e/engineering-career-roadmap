import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = sorted((ROOT / "tests" / "fixtures" / "postings").glob("*.json"))

_spec = importlib.util.spec_from_file_location("evaluate_matching", ROOT / "scripts" / "evaluate_matching.py")
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)


def test_there_are_48_fixtures():
    assert len(FIXTURES) == 48


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_fixture(path):
    fx = json.loads(path.read_text(encoding="utf-8"))
    r = ev.check_fixture(fx)
    # check_fixture compares the five expected sets, line labels, mention labels and evidence labels
    assert r["fails"] == [], fx.get("note")
    assert r["doc_ok"]
