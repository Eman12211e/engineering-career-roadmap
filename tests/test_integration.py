"""Gate 1 integration: job-match gaps feed evidence-only bullets."""

import re

import pytest

from engine.bullet_generator import (
    BulletEvidence,
    build_bullet,
    find_unsupported_claims,
    skill_mentioned,
)


def test_fea_evidence_gives_supported_bullet():
    e = BulletEvidence(skill="FEA", action="Performed FEA on a mounting bracket",
                       context="Senior design project", result="")
    bullet = build_bullet(e)
    assert bullet == build_bullet(e)  # deterministic
    assert "FEA" in bullet
    assert find_unsupported_claims(bullet, e) == []
    assert not re.search(r"\d", bullet)  # no invented metric


def test_unmentioned_skill_is_not_inserted():
    e = BulletEvidence(skill="GD&T", action="Helped test a controller", context="", result="")
    bullet = build_bullet(e)
    assert "GD&T" not in bullet
    assert skill_mentioned(bullet, "GD&T") is False
    assert find_unsupported_claims(bullet, e) == []


def test_match_gap_flows_into_bullet_evidence():
    job_match = pytest.importorskip("engine.job_match")
    r = job_match.match_posting("Requirements:\n- SolidWorks\n- FEA", "Designed brackets in SolidWorks.")
    gaps = [m.skill for m in r.required if not m.found]
    assert gaps == ["Finite Element Analysis"]
    e = BulletEvidence(skill=gaps[0], action="ran finite element analysis on a bracket")
    bullet = build_bullet(e)
    assert skill_mentioned(bullet, gaps[0])
    assert find_unsupported_claims(bullet, e) == []
