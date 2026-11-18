"""Revision 4 coordinated-list regressions and metamorphic invariants.

Coordinator-written before implementation (R4.6). The implementer may not edit or exempt these.
"""

import pytest

from engine.job_match import match_posting
from engine.match_stages import _qualify, disambiguate, find_mentions, segment

UNKNOWN = "Foobar"


def resume_status(text):
    """canonical -> status of its first résumé mention."""
    out = {}
    for sec in segment(text, "resume"):
        for m in disambiguate(find_mentions(sec.lines)):
            out.setdefault(m.canonical, _qualify(m, "resume").status)
    return out


def posting_group(text):
    """canonical -> result group (required / preferred / unscored / excluded)."""
    r = match_posting(text, "placeholder")
    return {m.skill: g for g in ("required", "preferred", "unscored", "excluded") for m in getattr(r, g)}


# R4.2 table and the known failures found in round 7 and the read-only diagnosis
@pytest.mark.parametrize("text, expected", [
    ("Never used LabVIEW, SQL", {"SQL": "negated"}),
    ("Without rework by applying SPC", {"Statistical Process Control": "affirmed"}),
    ("No PLC experience, but proficient in SQL", {"PLC Programming": "negated", "SQL": "affirmed"}),
    ("No PLC experience, proficient in SQL", {"PLC Programming": "negated", "SQL": "negated"}),
    ("No experience with LabVIEW, SQL", {"SQL": "negated"}),
])
def test_resume_negation_lists(text, expected):
    got = resume_status(text)
    assert {k: got.get(k) for k in expected} == expected


@pytest.mark.parametrize("text, expected", [
    ("Qualifications:\n- Nice to have: LabVIEW, SQL", {"SQL": "preferred"}),
    ("Qualifications:\n- Preferred: LabVIEW, SQL", {"SQL": "preferred"}),
    ("Qualifications:\n- Bonus: LabVIEW, SQL", {"SQL": "preferred"}),
    ("Qualifications:\n- Preferably LabVIEW, SQL", {"SQL": "preferred"}),
    ("Qualifications:\n- Nice to have: experience with LabVIEW, SQL", {"SQL": "preferred"}),
    ("Qualifications:\n- Nice to have: SQL, LabVIEW, Python", {"SQL": "preferred", "Python": "preferred"}),
    ("Preferred Qualifications:\n- Required: LabVIEW, SQL", {"SQL": "required"}),
    ("Qualifications:\n- LabVIEW, SQL (preferred)", {"SQL": "preferred"}),
])
def test_posting_label_lists(text, expected):
    got = posting_group(text)
    assert {k: got.get(k) for k in expected} == expected


# R4.5 metamorphic invariant: one whole unknown item at start, middle or end changes nothing
RESUME_LISTS = [
    ("Never used {}", ["LabVIEW", "SQL"], {"SQL": "negated"}),
    ("Never used {}", ["Python", "SQL"], {"Python": "negated", "SQL": "negated"}),
    ("No experience with {}", ["Python", "SQL"], {"Python": "negated", "SQL": "negated"}),
    ("Currently learning {}", ["Python", "SQL"], {"Python": "hypothetical", "SQL": "hypothetical"}),
    ("Learning {}", ["LabVIEW", "SQL"], {"SQL": "hypothetical"}),
    ("Familiar with {}", ["Python", "SQL"], {"Python": "affirmed", "SQL": "affirmed"}),
]
POSTING_LISTS = [
    ("Qualifications:\n- Nice to have: {}", ["Python", "SQL"], {"Python": "preferred", "SQL": "preferred"}),
    ("Qualifications:\n- Preferred: {}", ["LabVIEW", "SQL"], {"SQL": "preferred"}),
    ("Qualifications:\n- Preferably {}", ["Python", "SQL"], {"Python": "preferred", "SQL": "preferred"}),
    ("Preferred Qualifications:\n- Required: {}", ["Python", "SQL"], {"Python": "required", "SQL": "required"}),
    ("Qualifications:\n- {} (preferred)", ["Python", "SQL"], {"Python": "preferred", "SQL": "preferred"}),
    ("Qualifications:\n- {}", ["Python", "SQL"], {"Python": "required", "SQL": "required"}),
]


def _variants(items):
    return {
        "start": [UNKNOWN] + items,
        "middle": items[:1] + [UNKNOWN] + items[1:],
        "end": items + [UNKNOWN],
    }


def _cases(table):
    for template, items, expected in table:
        for pos, its in _variants(items).items():
            yield pytest.param(template.format(", ".join(its)), expected, id=f"{template[:24]}|{pos}")


@pytest.mark.parametrize("text, expected", list(_cases(RESUME_LISTS)))
def test_metamorphic_resume(text, expected):
    got = resume_status(text)
    assert {k: got.get(k) for k in expected} == expected


@pytest.mark.parametrize("text, expected", list(_cases(POSTING_LISTS)))
def test_metamorphic_posting(text, expected):
    got = posting_group(text)
    assert {k: got.get(k) for k in expected} == expected
