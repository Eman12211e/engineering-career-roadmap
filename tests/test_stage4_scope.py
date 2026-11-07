"""Stage 4 qualification by scope (R3.1): the minimal-pair table and scope-end rules."""

import pytest

from engine.match_stages import Line, _qualify, disambiguate, find_mentions, qualify, segment

PLC, RCA, SW, FEA = "PLC Programming", "Root Cause Analysis", "SolidWorks", "Finite Element Analysis"


def statuses(text, doc="resume"):
    lines = tuple(ln for sec in segment(text, doc) for ln in sec.lines)
    return {m.canonical: _qualify(m, doc).status for m in disambiguate(find_mentions(lines))}


@pytest.mark.parametrize("text,expected", [
    ("Currently learning PLC troubleshooting and root cause analysis", {PLC: "hypothetical", RCA: "hypothetical"}),
    ("Never used PLC, but interested in learning root cause analysis", {PLC: "negated", RCA: "hypothetical"}),
    # known limitation (documented in SCORING.md): the scope also covers "already proficient in"
    ("Learning PLC and already proficient in root cause analysis", {PLC: "hypothetical", RCA: "hypothetical"}),
    ("Used SolidWorks; currently learning FEA", {SW: "affirmed", FEA: "hypothetical"}),
    ("Learning FEA. Expert in SolidWorks", {FEA: "hypothetical", SW: "affirmed"}),
    ("SolidWorks and learning FEA", {SW: "affirmed", FEA: "hypothetical"}),
    ("Familiar with FEA", {FEA: "affirmed"}),
    ("Not familiar with FEA", {FEA: "negated"}),
    ("Without rework by applying SPC", {"Statistical Process Control": "affirmed"}),
])
def test_r31_minimal_pairs(text, expected):
    assert statuses(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("Learning PLC, SolidWorks / FEA and RCA", {PLC: "hypothetical", SW: "hypothetical", FEA: "hypothetical"}),
    ("Learning PLC, however SolidWorks daily", {PLC: "hypothetical", SW: "affirmed"}),
    ("Learning PLC although SolidWorks daily", {PLC: "hypothetical", SW: "affirmed"}),
    ("Learning PLC whereas SolidWorks daily", {PLC: "hypothetical", SW: "affirmed"}),
    ("Learning: PLC", {PLC: "affirmed"}),                       # a colon is a hard stop
    ("Learning PLC; SolidWorks", {PLC: "hypothetical", SW: "affirmed"}),
    ("Learning PLC, never used FEA", {PLC: "hypothetical", FEA: "negated"}),  # a later cue sets a new state
    ("No experience with FEA, learning PLC", {FEA: "negated", PLC: "hypothetical"}),
    ("Machine learning and FEA", {FEA: "affirmed"}),            # a cue inside a skill name starts nothing
])
def test_scope_ends_and_later_cues(text, expected):
    got = statuses(text)
    for k, v in expected.items():
        assert got[k] == v, (k, got)


def test_scope_continues_across_a_joined_hard_wrap_but_not_a_blank_line():
    assert statuses("- Currently learning PLC\nand root cause analysis")[RCA] == "hypothetical"
    assert statuses("- Currently learning PLC\n\nRoot cause analysis")[RCA] == "affirmed"


def test_cues_never_reach_back():
    m = next(m for m in disambiguate(find_mentions((Line("SolidWorks, then learning FEA", 0, 29, "unknown", None, False),)))
             if m.canonical == SW)
    assert qualify(m).status == "affirmed"


def test_negation_keeps_the_gap_rule_and_does_not_spread():
    assert statuses("No experience with FEA or CFD")[FEA] == "negated"
    assert statuses("No rework using SPC")["Statistical Process Control"] == "affirmed"
    assert statuses("Never missed a deadline in SolidWorks")[SW] == "affirmed"
