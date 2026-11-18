"""Tests for the evidence-based bullet builder."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.bullet_generator import (
    BulletEvidence,
    build_bullet,
    find_unsupported_claims,
    generate_bullets,
    skill_mentioned,
    split_claims,
    suggest_prompts,
    suggest_verbs,
)

META = [{"canonical": "SolidWorks", "category": "cad"}]


def test_verb_kept_never_upgraded():
    b = build_bullet(BulletEvidence("PLC Programming", "helped test a controller"))
    assert b.startswith("Helped test a controller")
    assert "led" not in b.lower().split() and "optimized" not in b.lower()


def test_result_blank_means_no_result():
    b = build_bullet(BulletEvidence("SolidWorks", "drew brackets in SolidWorks"))
    assert b == "Drew brackets in SolidWorks."


def test_result_and_context_used_verbatim():
    b = build_bullet(BulletEvidence("SolidWorks", "modeled", "a bracket", "passed review"))
    assert b == "Modeled a bracket, passed review."


def test_deterministic():
    e = BulletEvidence("FEA", "ran", "a beam study", "matched hand calcs")
    assert build_bullet(e) == build_bullet(e)


@pytest.mark.parametrize("skill,action", [("", "did"), ("  ", "did"), ("FEA", ""), ("FEA", " \t\n")])
def test_blank_raises_without_echo(skill, action):
    with pytest.raises(ValueError) as exc:
        build_bullet(BulletEvidence(skill, action))
    assert "FEA" not in str(exc.value) and "did" not in str(exc.value).split("blank")[0].split()[-1:]


def test_flags_invented_numbers():
    e = BulletEvidence("SolidWorks", "modeled a bracket")
    bad = "Modeled a bracket, saving $50K and cutting time 40% across 3 production lines."
    flagged = find_unsupported_claims(bad, e)
    assert {"$50K", "40%", "3"} <= set(flagged)


def test_flags_inflation_and_tools():
    e = BulletEvidence("CAD", "helped draw parts")
    flagged = find_unsupported_claims("Led drawing of parts in CATIA, PMP certified", e)
    assert {"led", "catia", "pmp"} <= set(flagged)


def test_evidence_numbers_and_versions_pass():
    e = BulletEvidence("SolidWorks", "modeled 12 brackets", "in SolidWorks 2024", "cut 15%")
    b = build_bullet(e)
    assert find_unsupported_claims(b, e) == []


def test_built_bullet_has_no_unsupported_claims():
    e = BulletEvidence("PLC Programming", "helped test a controller", "on a bench rig")
    assert find_unsupported_claims(build_bullet(e), e) == []


def test_suggestions_only():
    verbs = suggest_verbs("cad")
    assert verbs and "Designed" in verbs
    assert suggest_verbs("unknown")
    prompts = suggest_prompts("FEA", "analysis")
    assert prompts and any("FEA" in p for p in prompts)


def test_generate_bullets_invents_nothing():
    out = generate_bullets(["SolidWorks"], "EV/Automotive", "Current ME Student", META)
    assert out[0]["bullets"] == [] and out[0]["prompts"]
    assert out == generate_bullets(["SolidWorks"], "EV/Automotive", "Current ME Student", META)


def test_skill_never_inserted_nor_evidence():
    e = BulletEvidence("GD&T", "helped test a controller")
    b = build_bullet(e)
    assert "GD&T" not in b and not skill_mentioned(b, "GD&T")
    assert "gd&t" in find_unsupported_claims("Helped test a controller using GD&T.", e)


def test_number_words_and_verbs():
    e = BulletEvidence("X", "helped test", "a controller")
    for text, term in [
        ("Helped test three controllers", "three"),
        ("Helped test, cut time forty percent", "forty"),
        ("Helped test, doubled output", "doubled"),
        ("Optimized a controller", "optimized"),
        ("Drove the test", "drove"),
        ("Helped test as owner of the rig", "owner of"),
        ("Helped test, responsible for the rig", "responsible for"),
    ]:
        assert term in find_unsupported_claims(text, e), text


def test_tools_from_keywords_json_and_word_boundary():
    e = BulletEvidence("X", "helped test", "a controller")
    flagged = find_unsupported_claims("Helped test with Minitab, CSWP and Siemens TIA Portal", e)
    assert {"minitab", "cswp"} <= set(flagged)
    assert "ros" not in find_unsupported_claims("Helped test across rigs", e)
    ok = BulletEvidence("X", "helped test", "with Minitab")
    assert "minitab" not in find_unsupported_claims("Helped test with Minitab.", ok)


def test_number_commas_and_units():
    e = BulletEvidence("X", "processed 2,000 parts in 3 days")
    assert find_unsupported_claims("Processed 2000 parts in 3 days.", e) == []
    assert "3" in find_unsupported_claims("Processed 2000 parts in 3 weeks.", e)


def test_verb_must_be_in_action_not_context():
    e = BulletEvidence("X", "helped the team", "we were led by a manager")
    assert "led" in find_unsupported_claims("Led the team", e)
    e2 = BulletEvidence("X", "led a bench test")
    assert find_unsupported_claims(build_bullet(e2), e2) == []


def test_session_bullets_cleared_when_deselected():
    at_mod = pytest.importorskip("streamlit.testing.v1")

    def app():
        import pandas as pd
        from ui.tab_resume import render_resume_tab
        df = pd.DataFrame({"canonical": ["GD&T", "FEA"], "priority_score": [50.0, 40.0]})
        render_resume_tab(df, {"industries": [], "background": ""}, [])

    at = at_mod.AppTest.from_function(app).run()
    at.text_input(key="action_GD&T").set_value("checked drawings").run()
    assert at.session_state["generated_bullets"]
    at.multiselect[0].set_value([]).run()
    assert at.session_state["generated_bullets"] == []


def test_user_typed_words_not_called_unsupported():
    e = BulletEvidence("PLC", "helped lead the PLC test")
    assert find_unsupported_claims(build_bullet(e), e) == []
    e = BulletEvidence("X", "helped the team", "we were led by a manager")
    assert split_claims("Helped the team, we were led by a manager.", e) == ([], ["led"])
    e = BulletEvidence("X", "tracked downtime", "", "improved uptime")
    assert split_claims(build_bullet(e), e) == ([], ["improved"])
    assert split_claims("Drove the test", e)[0] == ["drove"]
