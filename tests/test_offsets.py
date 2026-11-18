"""Offset invariants (R2.3): every Line and every mention span points at its own evidence."""

import json
from pathlib import Path

import pytest

from engine.match_stages import disambiguate, find_mentions, segment

FIXTURES = sorted((Path(__file__).resolve().parent / "fixtures" / "postings").glob("*.json"))


def norm(s: str) -> str:
    """Case folding and whitespace-run collapse only; nothing else is removed."""
    return " ".join(s.casefold().split())


def check_text(src: str, doc: str) -> tuple[int, int]:
    """Assert both invariants over one text; return (lines checked, mentions checked)."""
    lines = tuple(ln for sec in segment(src, doc) for ln in sec.lines)
    for ln in lines:
        assert ln.text == src[ln.start:ln.end]
    n = 0
    for m in find_mentions(lines):  # every candidate, before disambiguation
        got = norm(src[m.span[0]:m.span[1]])
        assert got in (norm(m.alias), norm(m.alias) + "s"), (m.canonical, m.alias)
        assert m.line.start <= m.span[0] < m.span[1] <= m.line.end
        n += 1
    assert set(disambiguate(find_mentions(lines))) <= set(find_mentions(lines))
    return len(lines), n


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_offsets_over_fixture(path):
    fx = json.loads(path.read_text(encoding="utf-8"))
    for doc, key in (("posting", "posting_text"), ("resume", "resume_text")):
        check_text(fx[key], doc)


def test_offset_coverage_is_substantial():
    lines = mentions = 0
    for path in FIXTURES:
        fx = json.loads(path.read_text(encoding="utf-8"))
        for doc, key in (("posting", "posting_text"), ("resume", "resume_text")):
            a, b = check_text(fx[key], doc)
            lines, mentions = lines + a, mentions + b
    assert lines > 400 and mentions > 500, (lines, mentions)


def test_wrapped_alias_span_contains_the_newline():
    src = "Requirements:\n- Experience performing finite element\nanalysis on welded structures."
    (m,) = [m for m in find_mentions(tuple(ln for s in segment(src, "posting") for ln in s.lines))]
    assert src[m.span[0]:m.span[1]] == "finite element\nanalysis"
