"""R2.3 hard-wrap joining, R2.4 cue binding, negation and hypothetical scope (R2.8.5-R2.8.16)."""

import pytest

from engine.job_match import match_posting
from engine.match_stages import Line, disambiguate, find_mentions, importance, qualify, segment

FEA = "Finite Element Analysis"


def body(text, doc="posting"):
    return [ln for sec in segment(text, doc) for ln in sec.lines]


def mention(text, canonical, section="unknown"):
    ln = Line(text, 0, len(text), section, None, False)
    return next(m for m in disambiguate(find_mentions((ln,))) if m.canonical == canonical)


def imp(text, canonical=FEA, section="unknown"):
    return importance(qualify(mention(text, canonical, section)))


def status(text, canonical=FEA):
    return qualify(mention(text, canonical)).status


# ---- R2.3 hard-wrap joining ----
def test_lowercase_line_joins_previous_and_keeps_newline():
    src = "Requirements:\n- Experience performing finite element\nanalysis on welded structures."
    (ln,) = body(src)
    assert ln.text == "- Experience performing finite element\nanalysis on welded structures."
    assert src[ln.start:ln.end] == ln.text and ln.is_bullet


def test_uppercase_line_or_ended_sentence_does_not_join():
    assert len(body("Requirements:\n- aaa bbb\nGD&T.")) == 2
    assert len(body("Requirements:\n- aaa bbb.\nccc ddd")) == 2
    assert len(body("Requirements:\n- aaa bbb;\nccc ddd")) == 2


def test_blank_line_and_heading_break_continuation():
    assert len(body("Requirements:\n- aaa bbb\n\nccc ddd")) == 2
    assert [s.kind for s in segment("Requirements:\n- aaa\nBenefits:\n- b", "posting")] == ["required", "excluded"]


def test_numbered_and_lettered_items_are_list_items_never_continuations():
    lines = body("Qualifications\n1. aaa\n2) bbb\n   a. ccc\nb. ddd")
    assert [ln.is_bullet for ln in lines] == [True] * 4 and len(lines) == 4


def test_numbered_item_is_not_a_heading():
    secs = segment("Requirements:\n- a\n1. Experience with at least one of the following:\n   a. SQL", "posting")
    assert [s.kind for s in secs] == ["required"]


def test_alias_matches_across_a_wrap():
    r = match_posting("Requirements:\n- Experience performing finite element\nanalysis on welded structures.", "x")
    assert [m.skill for m in r.required] == [FEA]
    assert "\n" not in r.required[0].posting_line


# ---- R2.4 cue binding ----
@pytest.mark.parametrize("text,expected", [
    ("Preferred: FEA", "preferred"),
    ("Required: FEA", "required"),
    ("Nice to have: FEA and CFD", "preferred"),
    ("FEA (preferred)", "preferred"),
    ("FEA preferred", "preferred"),
    ("FEA is a plus", "preferred"),
    ("FEA experience is required", "required"),
    ("FEA is highly desirable", "preferred"),
    ("Must have FEA", "required"),
    ("must have strong FEA", "required"),
    ("FEA is a must", "required"),
    ("Preferably FEA", "preferred"),
    ("Ideally FEA", "preferred"),
    ("Must be able to run FEA", "unscored"),
    ("Hold the desired tolerances using FEA", "unscored"),
    ("Review FEA results as required", "unscored"),
    ("FEA analysts are required", "unscored"),
    ("FEA is not required, but is a plus", "preferred"),
    ("FEA not required but nice to have", "preferred"),
])
def test_cue_binding(text, expected):
    assert imp(text) == expected


def test_cue_binds_whole_coordinated_list_across_commas():
    for c in (FEA, "CFD", "SolidWorks"):
        assert imp("SolidWorks, FEA, or CFD preferred", c) == "preferred"
        assert imp("SolidWorks, FEA and CFD a plus", c) == "preferred"


def test_prefix_label_binds_every_skill_in_its_clause():
    assert imp("Preferred: SolidWorks, FEA", "SolidWorks") == "preferred"
    assert imp("Preferred: SolidWorks; Required: FEA") == "required"
    assert imp("SolidWorks required; FEA preferred") == "preferred"


def test_no_binding_across_a_clause_break():
    assert imp("FEA, and degree preferred") == "preferred"  # R4: an unknown item does not break the list
    assert imp("FEA. Python preferred") == "unscored"


def test_section_importance_is_overridden_only_by_a_bound_cue():
    assert imp("FEA", section="required") == "required"
    assert imp("FEA is a plus", section="required") == "preferred"
    assert imp("FEA is required", section="preferred") == "required"
    assert imp("FEA", section="responsibilities") == "unscored"


# ---- negation and hypothetical scope ----
@pytest.mark.parametrize("text,expected", [
    ("No FEA experience", "negated"),
    ("No prior FEA experience", "negated"),
    ("Never used FEA", "negated"),
    ("No experience with FEA", "negated"),
    ("Not familiar with FEA", "negated"),
    ("Without FEA", "negated"),
    ("FEA experience is not necessary", "negated"),
    ("FEA is not required", "negated"),
    ("FEA coursework is not necessary", "affirmed"),
    ("Without added headcount by applying FEA", "affirmed"),
    ("Zero escapes with no rework using FEA", "affirmed"),
    ("Never missed a deadline using FEA", "affirmed"),
    ("Achieved zero defects using FEA", "affirmed"),
    ("Not only FEA but also CFD", "affirmed"),
    ("Tools: no-code automation, FEA", "affirmed"),
    ("No relocation; FEA", "affirmed"),
    ("No experience with PLC, but FEA", "affirmed"),
    ("Willing to travel 20% and have FEA skills", "affirmed"),
    ("Willing to learn FEA", "hypothetical"),
    ("Currently learning FEA", "hypothetical"),
    ("Planning to take the FEA", "hypothetical"),
    ("Preparing for FEA", "hypothetical"),
    ("Studying for FEA", "hypothetical"),
])
def test_status_by_gap_rule(text, expected):
    assert status(text) == expected


def test_negator_spans_a_coordinated_list():
    assert status("No experience with FEA or CFD", FEA) == "negated"
    assert status("No experience with FEA or CFD", "CFD") == "negated"
    assert status("Learning FEA, CFD and SolidWorks", "SolidWorks") == "hypothetical"
    assert status("No experience with PLC, but strong FEA background", FEA) == "affirmed"


def test_negation_after_is_posting_only():
    m = mention("FEA is not required", FEA)
    assert qualify(m).status == "negated"
    from engine.match_stages import _qualify

    assert _qualify(m, "resume").status == "affirmed"
