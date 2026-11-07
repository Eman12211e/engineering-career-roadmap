import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.job_match import compute_coverage_score, match_posting, split_posting_requirements

ROOT = Path(__file__).resolve().parent.parent


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


def test_score_rejects_bad_counts():
    with pytest.raises(ValueError):
        compute_coverage_score(3, 2, 0, 0)


# ---- sections and the extended contract ----
def test_split_wrapper():
    p = "About us:\nGreat place, uses Python\nRequirements:\n- SolidWorks\nNice to have:\n- ANSYS\n"
    assert split_posting_requirements(p) == (["- SolidWorks"], ["- ANSYS"])


def test_headingless_posting_is_unscored_with_score_none():
    r = match_posting("Need SolidWorks and Python.", "Python dev")
    assert not r.required and not r.preferred and r.score is None
    assert names(r.unscored) == ["SolidWorks", "Python"]
    assert [m.found for m in r.unscored] == [False, True]
    assert all(m.requirement == "unscored" for m in r.unscored)


def test_skill_in_both_sections_counts_once_as_required():
    r = match_posting("Requirements:\n- SolidWorks\nPreferred:\n- SolidWorks\n- Python", "SolidWorks")
    assert names(r.required) == ["SolidWorks"] and names(r.preferred) == ["Python"]


def test_required_and_preferred_score():
    r = match_posting("Requirements:\n- SolidWorks\nPreferred:\n- Python", "SolidWorks")
    assert r.score == pytest.approx(80)


def test_excluded_section_never_scores():
    r = match_posting("Requirements:\n- SolidWorks\nBenefits:\n- Python training", "Python, SolidWorks")
    assert names(r.excluded) == ["Python"] and r.excluded[0].requirement == "excluded"
    assert names(r.required) == ["SolidWorks"] and r.score == 100


def test_new_fields_have_defaults():
    r = match_posting("Requirements:\n- SolidWorks", "SolidWorks")
    assert r.unscored == () and r.excluded == ()
    m = r.required[0]
    assert m.section == "required" and m.requirement == "required"


# ---- negation ----
@pytest.mark.parametrize("line", ["No FEA experience required", "no FEA experience", "FEA is not required"])
def test_negated_posting_not_a_requirement(line):
    r = match_posting(f"Requirements:\n- {line}\n- SolidWorks", "SolidWorks")
    assert names(r.required) == ["SolidWorks"] and not r.unscored


def test_negated_resume_not_a_match():
    r = match_posting("Requirements:\n- FEA", "No experience with FEA")
    assert not r.required[0].found and r.required[0].resume_line is None


@pytest.mark.parametrize("resume", ["Achieved zero defects using FEA and SolidWorks",
                                    "Tools: no-code automation, SolidWorks", "Not only PLC but also SolidWorks"])
def test_resume_negation_is_narrow(resume):
    r = match_posting("Requirements:\n- SolidWorks", resume)
    assert r.required[0].found


# ---- false matches, with the real keyword data ----
@pytest.mark.parametrize("text", ["We can do it", "R&D team", "C-suite access", "Core cable carrier",
                                  "a can of paint", "MLS listings", "Measure 500 ml of coolant"])
def test_ordinary_words_do_not_match(text):
    assert match_posting(f"Requirements:\n- {text}", "x").score is None


def test_case_sensitive_skill_from_data():
    assert names(match_posting("Requirements:\n- ROS", "x").required) == ["ROS"]
    assert match_posting("Requirements:\n- ros", "x").score is None


def test_solid_works_variant_and_plc_acronym():
    r = match_posting("Requirements:\n- Experience with Solid Works and PLC.",
                      "Used SOLIDWORKS daily; plc programming")
    assert [(m.skill, m.found) for m in r.required] == [("SolidWorks", True), ("PLC Programming", True)]


# ---- attribution, order, errors ----
def test_lines_and_spans_attributed():
    post = "Requirements:\nSolidWorks expert\nANSYS"
    res = "Intro\nDesigned parts in SolidWorks"
    a, b = match_posting(post, res).required
    assert a.posting_line == "SolidWorks expert" and a.resume_line == "Designed parts in SolidWorks"
    assert post[slice(*a.posting_span)] == "SolidWorks" and res[slice(*a.resume_span)] == "SolidWorks"
    assert not b.found and b.posting_line == "ANSYS" and b.resume_line is None and b.resume_span is None


def test_deterministic_order():
    p, res = "Requirements:\n- Python, SolidWorks, SQL", "SQL"
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
    with pytest.raises(ValueError) as e:
        split_posting_requirements(" ")
    assert "text is empty" in str(e.value)


def test_long_line_snippet_is_capped_and_span_exact():
    line = "word " * 100 + "SolidWorks " + "word " * 100
    post = "Requirements:\n" + line
    m = match_posting(post, line).required[0]
    assert len(m.posting_line) <= 200 and len(m.resume_line) <= 200
    assert "SolidWorks" in m.posting_line and m.posting_line.startswith("…")
    assert post[slice(*m.posting_span)] == "SolidWorks"


# ---- evaluation script ----
def _run(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "evaluate_matching.py"), *args],
                          capture_output=True, text=True, cwd=ROOT)


def _pair(pid, split, required=("SolidWorks",)):
    return {"id": pid, "split": split, "posting_text": "Requirements:\n- SolidWorks\nPreferred:\n- ANSYS",
            "resume_text": "I know SecretResumeWord, SolidWorks and ANSYS.", "required_skills": list(required),
            "preferred_skills": ["ANSYS"], "resume_has": ["SolidWorks", "ANSYS"]}


def _write(tmp_path, pairs):
    (tmp_path / "a.json").write_text(json.dumps({"pairs": pairs}))


def test_eval_empty_owner_dir_is_pending_exit_2(tmp_path):
    (tmp_path / "EXAMPLE.schema.json").write_text("not even json")
    p = _run("--dir", str(tmp_path))
    assert p.returncode == 2 and "PENDING" in p.stdout and "no evaluation pairs yet" in p.stdout


def test_eval_default_dir_is_pending():
    p = _run()
    assert p.returncode == 2 and "PENDING" in p.stdout


def test_eval_too_few_pairs_pending_and_no_text_leak(tmp_path):
    _write(tmp_path, [_pair("t1", "tune", required=("SolidWorks", "Creo"))])
    p = _run("--dir", str(tmp_path))
    assert p.returncode == 2 and "PENDING" in p.stdout
    assert "tune: n=1" in p.stdout and "holdout (aggregate only): n=0" in p.stdout
    assert "missed Creo" in p.stdout and "SecretResumeWord" not in p.stdout


def test_eval_pass_exit_0(tmp_path):
    _write(tmp_path, [_pair(f"t{i}", "tune") for i in range(10)] + [_pair(f"h{i}", "holdout") for i in range(5)])
    p = _run("--dir", str(tmp_path))
    assert p.returncode == 0 and "PASS" in p.stdout


def test_eval_fail_exit_1_holdout_aggregate_only(tmp_path):
    pairs = [_pair(f"t{i}", "tune") for i in range(10)]
    pairs += [_pair(f"h{i}", "holdout", required=("SolidWorks", "Creo")) for i in range(5)]
    _write(tmp_path, pairs)
    p = _run("--dir", str(tmp_path))
    assert p.returncode == 1 and "FAIL" in p.stdout
    assert "h0" not in p.stdout and "Creo" not in p.stdout  # no per-item holdout detail


def test_eval_fixtures_report():
    p = _run("--fixtures", str(ROOT / "tests" / "fixtures" / "postings"))
    assert p.returncode == 0 and "document-level exact sets" in p.stdout and "section accuracy" in p.stdout
