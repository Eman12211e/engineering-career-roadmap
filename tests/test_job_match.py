import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.job_match import compute_coverage_score, match_posting, split_posting_requirements

ROOT = Path(__file__).resolve().parent.parent
SHORT = [  # skills the shipped keyword file lacks, to exercise short-acronym guards
    {"canonical": "R", "aliases": ["R"], "category": "programming"},
    {"canonical": "C", "aliases": ["C"], "category": "programming"},
    {"canonical": "CAN", "aliases": ["CAN"], "category": "controls"},
    {"canonical": "Excel", "aliases": ["Excel"], "category": "tools"},
]


def names(matches):
    return [m.skill for m in matches]


# ---- score ----
def test_score_required_only():
    assert compute_coverage_score(1, 4, 0, 0) == 25


def test_score_preferred_only():
    assert compute_coverage_score(0, 0, 1, 2) == 50


def test_score_both():
    assert compute_coverage_score(1, 2, 1, 2) == pytest.approx(50)
    assert compute_coverage_score(2, 2, 0, 2) == pytest.approx(80)


def test_score_neither_is_none_not_zero():
    assert compute_coverage_score(0, 0, 0, 0) is None
    assert match_posting("We are a friendly team.", "I like cats.").score is None


# ---- sections ----
def test_split_sections():
    p = "About us:\nGreat place, uses Python\nRequirements:\n- SolidWorks\nNice to have:\n- ANSYS\n"
    assert split_posting_requirements(p) == (["- SolidWorks"], ["- ANSYS"])


def test_no_sections_all_required():
    r = match_posting("Need SolidWorks and Python.", "Python dev")
    assert names(r.required) == ["SolidWorks", "Python"] and not r.preferred


def test_heading_with_inline_text_and_both_sections_count_once():
    r = match_posting("Requirements: SolidWorks\nPreferred: SolidWorks, Python", "SolidWorks")
    assert names(r.required) == ["SolidWorks"] and names(r.preferred) == ["Python"]


def test_required_and_preferred_score():
    r = match_posting("Requirements:\nSolidWorks\nPreferred:\nPython", "SolidWorks")
    assert r.score == pytest.approx(80)


# ---- negation ----
@pytest.mark.parametrize("line", ["No FEA experience required", "no FEA experience", "FEA is not required"])
def test_negated_posting_not_a_requirement(line):
    r = match_posting(f"Requirements:\n{line}\nSolidWorks", "SolidWorks")
    assert names(r.required) == ["SolidWorks"]


def test_negated_resume_not_a_match():
    r = match_posting("Requirements:\nFEA", "No experience with FEA")
    assert not r.required[0].found and r.required[0].resume_line is None


# ---- false matches ----
@pytest.mark.parametrize("text", ["We can do it", "R&D team", "C-suite access", "Core cable carrier", "a can of paint"])
def test_short_acronyms_do_not_false_match(text):
    assert match_posting(text, "x", _skills=SHORT).score is None


def test_short_acronyms_match_when_real():
    r = match_posting("Know R, C and CAN.", "x", _skills=SHORT)
    assert names(r.required) == ["R", "C", "CAN"]


def test_excel_at_is_not_excel():
    assert match_posting("Candidates excel at teamwork", "x", _skills=SHORT).score is None
    assert names(match_posting("Proficient in Excel", "x", _skills=SHORT).required) == ["Excel"]


def test_solid_works_variant_and_plc_acronym():
    r = match_posting("Experience with Solid Works and PLC.", "Used SOLIDWORKS daily; plc programming")
    assert [(m.skill, m.found) for m in r.required] == [("SolidWorks", True), ("PLC Programming", True)]


# ---- attribution, order, errors ----
def test_lines_attributed():
    r = match_posting("Requirements:\nSolidWorks expert\nANSYS", "Intro\nDesigned parts in SolidWorks")
    a, b = r.required
    assert a.posting_line == "SolidWorks expert" and a.resume_line == "Designed parts in SolidWorks"
    assert not b.found and b.posting_line == "ANSYS" and b.resume_line is None


def test_deterministic_order():
    p, res = "Python, SolidWorks, SQL", "SQL"
    assert match_posting(p, res) == match_posting(p, res)
    assert names(match_posting(p, res).required) == ["SolidWorks", "Python", "SQL"]


@pytest.mark.parametrize("posting,resume", [("", "x"), ("   \n", "x"), ("x", ""), ("x", " \t")])
def test_empty_inputs_raise_without_echo(posting, resume):
    with pytest.raises(ValueError) as e:
        match_posting(posting, resume)
    assert "text is empty" in str(e.value)


def test_error_does_not_echo_text():
    with pytest.raises(ValueError) as e:
        match_posting("SECRETPOSTING", "  ")
    assert "SECRETPOSTING" not in str(e.value)


# ---- evaluation script ----
def _run(d):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "evaluate_matching.py"), "--dir", str(d)],
                          capture_output=True, text=True, cwd=ROOT)


def test_eval_script_no_pairs(tmp_path):
    (tmp_path / "EXAMPLE.schema.json").write_text("not even json")
    p = _run(tmp_path)
    assert p.returncode == 0 and "no evaluation pairs yet" in p.stdout


def test_eval_script_synthetic_pair(tmp_path):
    pair = {"id": "t1", "split": "tune", "posting_text": "Requirements:\nSolidWorks\nANSYS",
            "resume_text": "I know SecretResumeWord and SolidWorks.", "required_skills": ["SolidWorks"],
            "preferred_skills": [], "resume_has": ["SolidWorks"]}
    (tmp_path / "a.json").write_text(json.dumps({"pairs": [pair]}))
    p = _run(tmp_path)
    assert p.returncode == 0, p.stderr
    assert "tune (n=1" in p.stdout and "holdout (n=0" in p.stdout
    assert "precision 0.50" in p.stdout and "recall 1.00" in p.stdout
    assert "SecretResumeWord" not in p.stdout


# ---- review fixes: real keywords, sections, negation, snippets ----
def req(posting, resume="x"):
    return names(match_posting(posting, resume).required)


def test_real_acronyms_with_separators_case_and_plurals():
    assert set(req("FEA/CFD experience; PLC/HMI programming; SQL/Python")) == {
        "Finite Element Analysis", "CFD", "PLC Programming", "Python", "SQL"}
    assert set(req("plc, fea, cfd, sql")) == {"Finite Element Analysis", "CFD", "PLC Programming", "SQL"}
    assert req("PLC-based control systems") == ["PLC Programming"]
    assert req("Experience programming PLCs") == ["PLC Programming"]
    assert req("Strong sql skills; Sql Server") == ["SQL"]
    r = match_posting("PLC and SQL", "plc and sql databases, fea")
    assert all(m.found for m in r.required)


def test_unlabeled_and_unknown_sections_are_required():
    p = ("About us\nWe build robots.\nResponsibilities\n- Design parts in SolidWorks\n- Run FEA on brackets\n"
         "- Program PLC logic\nRequirements\n- BS in Mechanical Engineering\n- 3+ years experience")
    assert set(req(p)) == {"SolidWorks", "Finite Element Analysis", "PLC Programming"}


def test_skills_then_preferred():
    r = match_posting("Skills\n- SolidWorks\n- FEA\nPreferred\n- PLC", "x")
    assert len(r.required) == 2 and names(r.preferred) == ["PLC Programming"]


def test_about_you_is_kept_benefits_dropped():
    assert set(req("Requirements\n- SolidWorks\nAbout you\n- FEA expert")) == {"SolidWorks", "Finite Element Analysis"}
    assert req("Benefits\n- Free Python lessons\nRequirements\n- SolidWorks") == ["SolidWorks"]


def test_negation_scope():
    r = match_posting("No prior PLC experience necessary but SolidWorks required", "x")
    assert names(r.required) == ["SolidWorks"]
    assert req("PLC experience not required") == []


@pytest.mark.parametrize("resume", ["Achieved zero defects using FEA and SolidWorks",
                                    "Tools: no-code automation, SolidWorks", "Not only PLC but also SolidWorks"])
def test_resume_negation_is_narrow(resume):
    r = match_posting("SolidWorks, FEA, PLC", resume)
    got = {m.skill: m.found for m in r.required}
    assert got["SolidWorks"]
    if "FEA" in resume:
        assert got["Finite Element Analysis"]
    if "PLC" in resume:
        assert got["PLC Programming"]


def test_resume_not_familiar():
    assert not match_posting("PLC", "Not familiar with PLC").required[0].found


def test_inline_preferred_and_bullet_plus():
    r = match_posting("Required: SolidWorks. Preferred: Python", "x")
    assert names(r.required) == ["SolidWorks"] and names(r.preferred) == ["Python"]
    assert req("Requirements\n- Plus\n- SolidWorks") == ["SolidWorks"]
    assert names(match_posting("Bonus points\n- Python", "x").preferred) == ["Python"]


def test_long_line_is_capped_around_match():
    line = "word " * 100 + "SolidWorks " + "word " * 100
    m = match_posting(line, line).required[0]
    assert len(m.posting_line) <= 202 and "SolidWorks" in m.posting_line
    assert m.posting_line.startswith("…") and m.posting_line.endswith("…")
