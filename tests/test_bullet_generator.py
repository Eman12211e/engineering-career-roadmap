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
    assert b == "Modeled a bracket using SolidWorks, passed review."


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
    e = BulletEvidence("SolidWorks 2024", "modeled 12 brackets", "in SolidWorks 2024", "cut 15%")
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
