import re
from pathlib import Path

import pytest

from engine.keyword_extractor import load_keywords
from engine.match_stages import (
    Line,
    classify_heading,
    clause_span,
    disambiguate,
    find_mentions,
    importance,
    qualify,
    segment,
)

ROOT = Path(__file__).resolve().parent.parent


def line(text, section="unknown", start=0):
    return Line(text, start, start + len(text), section, None, False)


def mentions(text, section="unknown", doc="posting"):
    return disambiguate(find_mentions((line(text, section),)))


def one(text, canonical, section="unknown"):
    return next(m for m in mentions(text, section) if m.canonical == canonical)


# ---- stage 1 ----
def test_classify_heading_vocabulary():
    assert classify_heading("**What We're Looking For:**", "posting") == "required"
    assert classify_heading("Nice to Have", "posting") == "preferred"
    assert classify_heading("Compensation & Benefits:", "posting") == "excluded"
    assert classify_heading("Skills", "resume") == "skills"
    assert classify_heading("Physical Requirements", "posting") is None
    assert classify_heading("Free lunch", "posting") is None


def test_segment_headingless_is_one_unknown_section():
    (s,) = segment("We use things.\nMore text.", "posting")
    assert s.kind == "unknown" and s.heading is None and len(s.lines) == 2


def test_segment_spans_are_absolute_and_exact():
    text = "Requirements:\r\n  - A thing  \nPreferred\n\n* Another"
    secs = segment(text, "posting")
    assert [s.kind for s in secs] == ["required", "preferred"]
    for sec in secs:
        assert text[slice(*sec.heading_span)] and all(text[ln.start:ln.end] == ln.text for ln in sec.lines)
    assert secs[0].lines[0].text == "- A thing" and secs[0].lines[0].is_bullet
    assert secs[1].lines[0].is_bullet and secs[1].lines[0].section == "preferred"


def test_title_case_is_not_a_heading_but_styling_is():
    secs = segment("Requirements\nTeam Player\n**Our Culture**\nTeam Player", "posting")
    assert [s.kind for s in secs] == ["required", "unknown"]
    assert secs[0].lines[0].text == "Team Player"


def test_heading_candidates_colon_caps_markdown_are_unknown():
    for h in ("Why Join Us:", "HOW TO APPLY", "## Heading", "**Heading**"):
        secs = segment(f"Requirements\n- a\n{h}\n- b", "posting")
        assert [s.kind for s in secs] == ["required", "unknown"], h


def test_caps_skill_list_is_not_a_heading():
    (s,) = segment("Requirements\nSQL, GD&T\nSAP, FEA", "posting")
    assert len(s.lines) == 2


def test_excluded_section_ends_only_at_known_heading():
    secs = segment("Benefits:\nWhy Join Us:\nMEDICAL DENTAL\n**Whatever**\nRequirements:\n- x", "posting")
    assert [s.kind for s in secs] == ["excluded", "required"]
    assert len(secs[0].lines) == 3


def test_bullet_characters_and_star_rule():
    secs = segment("Requirements\n• a\n· b\n* c\n- d\n**Preferred**\n- e", "posting")
    assert [s.kind for s in secs] == ["required", "preferred"]
    assert all(ln.is_bullet for ln in secs[0].lines) and len(secs[0].lines) == 4


# ---- stage 2 ----
def test_find_is_longest_alias_first_and_non_overlapping():
    ms = mentions("C/C++ firmware and MATLAB/Simulink and Six Sigma Green Belt")
    assert [(m.canonical, m.alias) for m in ms] == [
        ("C++", "C/C++"), ("MATLAB", "MATLAB/Simulink"), ("Lean Six Sigma Green Belt", "Six Sigma Green Belt")]


def test_find_spans_are_absolute():
    ln = line("x FEA y", start=100)
    (m,) = find_mentions((ln,))
    assert m.span == (102, 105)


def test_find_case_fold_word_boundaries_and_plural():
    assert not mentions("the features of the MLS")
    assert [m.canonical for m in mentions("fea/cfd; PLC-based; PLCs")] == [
        "Finite Element Analysis", "CFD", "PLC Programming", "PLC Programming"]
    assert not mentions("plcs")  # plural needs the upper-case alias


def test_find_does_no_keep_or_drop_decisions():
    # case_sensitive and exclude_phrases are stage 3's job
    assert find_mentions((line("ros"),)) and find_mentions((line("500 ml of fluid"),))


# ---- stage 3 ----
def test_disambiguate_case_sensitive_and_exclude_phrases_from_data():
    assert mentions("ROS") and not mentions("ros")
    assert not mentions("500 ml of fluid") and mentions("ML models")


def test_disambiguate_needs_context_is_generic(monkeypatch):
    from engine import match_stages as ms

    ms._skills.cache_clear()
    ms._skill_by_name.cache_clear()
    base = ms._skills()
    patched = tuple(
        s if s.canonical != "SQL" else ms._Skill(s.canonical, s.category, s.aliases, False,
                                                 (re.compile(r"\bdata\b", re.I),), ())
        for s in base
    )
    monkeypatch.setattr(ms, "_skills", lambda: patched)
    monkeypatch.setattr(ms, "_skill_by_name", lambda: {s.canonical: s for s in patched})
    assert not [m for m in ms.disambiguate(ms.find_mentions((line("SQL"),)))]
    assert [m for m in ms.disambiguate(ms.find_mentions((line("SQL data"),)))]


# ---- stage 4 ----
def test_clause_span_bounded_by_breaks():
    ln = line("No relocation needed; SolidWorks required, but FEA is essential.")
    m = one(ln.text, "SolidWorks")
    s, e = clause_span(ln, m.span)
    assert ln.text[s:e].strip() == "SolidWorks required"
    f = one(ln.text, "Finite Element Analysis")
    s, e = clause_span(ln, f.span)
    assert ln.text[s:e].strip() == "FEA is essential"


def test_clause_span_ignores_decimal_points():
    ln = line("per ASME Y14.5 and more")
    s, e = clause_span(ln, (4, 8))
    assert (s, e) == (0, len(ln.text))


@pytest.mark.parametrize("text,status", [
    ("No FEA experience", "negated"),
    ("No relocation; FEA", "affirmed"),
    ("No prior PLC, but FEA", "affirmed"),
    ("Not familiar with FEA", "negated"),
    ("Familiar with FEA", "affirmed"),
    ("Tools: no-code automation, FEA", "affirmed"),
    ("Achieved zero defects using FEA", "affirmed"),
    ("Currently learning FEA", "hypothetical"),
    ("Willingness to learn FEA", "hypothetical"),
    ("No experience with FEA or CFD", "negated"),
    ("FEA not required", "negated"),
    ("FEA, not required: PLC", "affirmed"),
    ("Machine Learning and FEA", "affirmed"),  # "learning" sits inside another mention
])
def test_qualify(text, status):
    m = next(m for m in mentions(text) if m.canonical == "Finite Element Analysis")
    assert qualify(m).status == status


def test_qualify_returns_a_new_mention():
    m = one("No FEA", "Finite Element Analysis")
    assert m.status == "affirmed" and qualify(m).status == "negated" and qualify(m) is not m


# ---- stage 5 ----
@pytest.mark.parametrize("text,section,expected", [
    ("FEA", "required", "required"),
    ("FEA", "preferred", "preferred"),
    ("FEA", "responsibilities", "unscored"),
    ("FEA", "skills", "unscored"),
    ("FEA", "unknown", "unscored"),
    ("FEA", "excluded", "excluded"),
    ("FEA is a plus", "required", "preferred"),
    ("FEA is required", "unknown", "required"),
    ("FEA is required", "preferred", "required"),
    ("FEA is required", "excluded", "excluded"),
    ("FEA is a plus", "excluded", "excluded"),
    ("SolidWorks required; FEA preferred", "required", "preferred"),
    ("FEA must be strong", "responsibilities", "required"),
])
def test_importance(text, section, expected):
    m = next(m for m in mentions(text, section) if m.canonical == "Finite Element Analysis")
    assert importance(m) == expected


# ---- no hardcoded skills ----
def test_no_canonical_skill_name_literal_in_engine_files():
    canon = [s["canonical"] for s in load_keywords(ROOT / "data" / "keywords.json")]
    for f in ("engine/job_match.py", "engine/match_stages.py"):
        src = (ROOT / f).read_text(encoding="utf-8")
        literals = set(re.findall(r"""(?:"([^"\n]*)"|'([^'\n]*)')""", src))
        flat = {x for pair in literals for x in pair if x}
        hit = [c for c in canon if c in flat]
        assert not hit, (f, hit)
