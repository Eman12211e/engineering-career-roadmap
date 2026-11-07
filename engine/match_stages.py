"""Stage interfaces and implementations for the job-matching engine (see docs/MATCHING_DESIGN.md).

Coordinator-owned contract: names, fields and signatures here may not change without a
coordinator decision. All spans are absolute, half-open (start, end) character offsets into the
original input string. No streamlit, no file writes, no randomness. All vocabulary lives in
data/match_rules.json and data/keywords.json; no skill is named in code.
"""

from __future__ import annotations

import dataclasses
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from engine.keyword_extractor import load_keywords

SectionKind = Literal[
    "required", "preferred", "responsibilities", "skills", "experience", "excluded", "unknown"
]
DocKind = Literal["posting", "resume"]
Status = Literal["affirmed", "negated", "hypothetical"]
Importance = Literal["required", "preferred", "unscored", "excluded"]


@dataclass(frozen=True)
class Line:
    text: str                      # the line as it appears, without the newline
    start: int                     # text == source[start:end]
    end: int
    section: SectionKind
    heading: str | None            # heading text of the enclosing section, None if none
    is_bullet: bool


@dataclass(frozen=True)
class Section:
    kind: SectionKind
    heading: str | None
    heading_span: tuple[int, int] | None
    lines: tuple[Line, ...]        # body lines, heading line excluded


@dataclass(frozen=True)
class Mention:
    canonical: str
    category: str
    alias: str                     # alias as written in keywords.json
    span: tuple[int, int]          # absolute span of the matched text
    line: Line
    status: Status = "affirmed"


# ---- data ------------------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
_MAX_HEADING_WORDS = 8
_MAX_HEADING_CHARS = 80


def _key(label: str) -> str:
    """Normalise a heading label for vocabulary lookup."""
    t = label.strip().lstrip("#").strip("*_ \t").rstrip(":").strip("*_ \t")
    return " ".join(t.lower().replace("’", "'").replace("&", "and").split())


def _cue_regex(words: list[str]) -> re.Pattern:
    alts = ("\\s+".join(re.escape(w) for w in c.replace("’", "'").split()) for c in words)
    return re.compile(r"(?<![\w-])(?:" + "|".join(alts) + r")(?![\w-])", re.I)


@dataclass(frozen=True)
class _Rules:
    headings: dict          # doc -> {normalised label: kind}
    bullets_always: str
    bullets_spaced: str
    negation: re.Pattern
    negation_after: re.Pattern
    hypothetical: re.Pattern
    required_cues: re.Pattern
    preferred_cues: re.Pattern
    breaks: re.Pattern


@lru_cache(maxsize=1)
def _rules() -> _Rules:
    with open(_ROOT / "data" / "match_rules.json", encoding="utf-8") as f:
        d = json.load(f)
    heads = {
        doc: {_key(label): kind for kind, labels in kinds.items() for label in labels}
        for doc, kinds in d["headings"].items()
    }
    return _Rules(
        headings=heads,
        bullets_always="".join(d["bullets"]["always"]),
        bullets_spaced="".join(d["bullets"]["with_space"]),
        negation=_cue_regex(d["negation"]),
        negation_after=_cue_regex(d["negation_after"]),
        hypothetical=_cue_regex(d["hypothetical"]),
        required_cues=_cue_regex(d["required_cues"]),
        preferred_cues=_cue_regex(d["preferred_cues"]),
        breaks=re.compile("|".join(f"(?:{b})" for b in d["clause_breaks"]), re.I),
    )


@dataclass(frozen=True)
class _Skill:
    canonical: str
    category: str
    aliases: tuple[tuple[str, re.Pattern], ...]
    case_sensitive: bool
    needs_context: tuple[re.Pattern, ...]
    exclude_phrases: tuple[re.Pattern, ...]


def _alias_regex(alias: str) -> re.Pattern:
    """Word-bounded, case-folded alias. An all-caps alias may take an exact-case plural "s"."""
    esc = re.escape(alias)
    head = r"\b" if alias[0].isalnum() or alias[0] == "_" else r"(?<!\w)"
    tail = r"\b" if alias[-1].isalnum() or alias[-1] == "_" else r"(?!\w)"
    body = f"(?:(?-i:{esc}s)|{esc})" if alias.isupper() and alias[-1].isalnum() else esc
    return re.compile(head + body + tail, re.I)


def _phrase(p: str) -> re.Pattern:
    return re.compile(r"\s+".join(re.escape(w) for w in p.split()), re.I)


@lru_cache(maxsize=1)
def _skills() -> tuple[_Skill, ...]:
    return tuple(
        _Skill(
            s["canonical"],
            s["category"],
            tuple((a, _alias_regex(a)) for a in s["aliases"]),
            bool(s.get("case_sensitive", False)),
            tuple(re.compile(r"(?<!\w)" + re.escape(w) + r"(?!\w)", re.I) for w in s.get("needs_context", ())),
            tuple(_phrase(p) for p in s.get("exclude_phrases", ())),
        )
        for s in load_keywords(_ROOT / "data" / "keywords.json")
    )


@lru_cache(maxsize=1)
def _skill_by_name() -> dict[str, _Skill]:
    return {s.canonical: s for s in _skills()}


def skill_order() -> tuple[str, ...]:
    """Canonical names in keywords.json order (the stable output order)."""
    return tuple(s.canonical for s in _skills())


# ---- Stage 1 -- Segment ----------------------------------------------------------------------
def _is_bullet(text: str) -> bool:
    r = _rules()
    return text[0] in r.bullets_always or (len(text) > 1 and text[0] in r.bullets_spaced and text[1] in " \t")


def classify_heading(label: str, doc: DocKind) -> SectionKind | None:
    """Map a heading label to a kind using data/match_rules.json; None if not a known heading."""
    return _rules().headings[doc].get(_key(label))


def _has_skill(text: str) -> bool:
    return any(rx.search(text) for sk in _skills() for _, rx in sk.aliases)


def _heading_candidate(text: str, doc: DocKind) -> tuple[bool, SectionKind | None, str]:
    """(is a heading candidate, known kind or None, cleaned label) for a non-bullet line."""
    label = " ".join(text.strip().lstrip("#").strip("*_ \t").rstrip(":").strip("*_ \t").split())
    kind = classify_heading(label, doc)
    if kind is not None:
        return True, kind, label
    if not label or len(label) > _MAX_HEADING_CHARS or len(label.split()) > _MAX_HEADING_WORDS:
        return False, None, label
    styled = text.startswith(("#", "**", "__"))
    colon = text.rstrip("*_ \t").endswith(":")
    # ALL CAPS alone is weak evidence: a caps list of skills ("SAP, GD&T") is body text
    caps = (len(label.split()) >= 2 and label == label.upper() and any(c.isalpha() for c in label)
            and not re.search(r"[,;/]", label) and not _has_skill(label))
    return (styled or colon or caps), None, label


def segment(text: str, doc: DocKind) -> tuple[Section, ...]:
    """Split text into typed sections. Headingless text is one "unknown" section."""
    sections: list[Section] = []
    kind: SectionKind = "unknown"
    heading: str | None = None
    hspan: tuple[int, int] | None = None
    body: list[Line] = []

    def close() -> None:
        if body or heading is not None:
            sections.append(Section(kind, heading, hspan, tuple(body)))

    pos = 0
    for chunk in text.split("\n"):
        chunk_start, pos = pos, pos + len(chunk) + 1
        t = chunk.strip()
        if not t:
            continue
        start = chunk_start + len(chunk) - len(chunk.lstrip())
        end = start + len(t)
        bullet = _is_bullet(t)
        if not bullet:
            is_head, known, label = _heading_candidate(t, doc)
            # inside an excluded section only a known heading ends it
            if is_head and (known is not None or kind != "excluded"):
                close()
                kind, heading, hspan, body = known or "unknown", label, (start, end), []
                continue
        body.append(Line(t, start, end, kind, heading, bullet))
    close()
    return tuple(sections)


# ---- Stage 2 -- Find -------------------------------------------------------------------------
def find_mentions(lines: tuple[Line, ...]) -> tuple[Mention, ...]:
    """Longest-alias-first, non-overlapping candidate mentions. No keep/drop or importance decisions."""
    out: list[Mention] = []
    for line in lines:
        cands = []
        for order, sk in enumerate(_skills()):
            for alias, rx in sk.aliases:
                for m in rx.finditer(line.text):
                    cands.append((-(m.end() - m.start()), m.start(), order, sk, alias, m.end()))
        cands.sort(key=lambda c: c[:3])
        taken: list[tuple[int, int]] = []
        for neg_len, s, _, sk, alias, e in cands:
            if any(s < te and ts < e for ts, te in taken):
                continue
            taken.append((s, e))
            out.append(Mention(sk.canonical, sk.category, alias, (line.start + s, line.start + e), line))
    return tuple(sorted(out, key=lambda m: (m.line.start, m.span)))


# ---- Stage 3 -- Disambiguate -----------------------------------------------------------------
def _keep(m: Mention) -> bool:
    sk = _skill_by_name()[m.canonical]
    text = m.line.text
    s, e = m.span[0] - m.line.start, m.span[1] - m.line.start
    if sk.case_sensitive and text[s:e] not in (m.alias, m.alias + "s"):
        return False
    if sk.needs_context and not any(rx.search(text) for rx in sk.needs_context):
        return False
    return not any(
        p.start() < e and s < p.end() for rx in sk.exclude_phrases for p in rx.finditer(text)
    )


def disambiguate(mentions: tuple[Mention, ...]) -> tuple[Mention, ...]:
    """Drop mentions that fail the skill's data-driven rules (case_sensitive, needs_context, exclude_phrases)."""
    return tuple(m for m in mentions if _keep(m))


# ---- Stage 4 -- Qualify ----------------------------------------------------------------------
@lru_cache(maxsize=4096)
def _line_spans(line: Line) -> tuple[tuple[int, int], ...]:
    return tuple(m.span for m in find_mentions((line,)))


def clause_span(line: Line, span: tuple[int, int]) -> tuple[int, int]:
    """Absolute span of the clause containing `span`, bounded by clause breaks from data."""
    s, e = span[0] - line.start, span[1] - line.start
    lo, hi = 0, len(line.text)
    for b in _rules().breaks.finditer(line.text):
        if b.end() <= s:
            lo = b.end()
        elif b.start() >= e:
            hi = b.start()
            break
    return line.start + lo, line.start + hi


def _cues(rx: re.Pattern, line: Line, lo: int, hi: int) -> list[tuple[int, int]]:
    """Absolute spans of cue matches in [lo, hi) that do not sit inside a skill mention."""
    own = _line_spans(line)
    found = []
    for m in rx.finditer(line.text, lo - line.start, hi - line.start):
        a, b = line.start + m.start(), line.start + m.end()
        if not any(a < oe and os < b for os, oe in own):
            found.append((a, b))
    return found


def _qualify(mention: Mention, doc: DocKind) -> Mention:
    r = _rules()
    lo, hi = clause_span(mention.line, mention.span)
    status: Status = "affirmed"
    if _cues(r.negation, mention.line, lo, mention.span[0]):
        status = "negated"
    elif _cues(r.hypothetical, mention.line, lo, mention.span[0]):
        status = "hypothetical"
    elif doc == "posting" and _cues(r.negation_after, mention.line, mention.span[1], hi):
        status = "negated"
    return dataclasses.replace(mention, status=status)


def qualify(mention: Mention) -> Mention:
    """Return the mention with status set from cues before it in the same clause.

    Posting rules apply, including the "not required" cues that follow the mention.
    """
    return _qualify(mention, "posting")


# ---- Stage 5 -- Decide -----------------------------------------------------------------------
_SECTION_IMPORTANCE: dict[str, Importance] = {
    "required": "required", "preferred": "preferred", "excluded": "excluded",
}


def importance(mention: Mention) -> Importance:
    """Posting importance from section kind, overridden by inline cues in the mention's clause."""
    base = _SECTION_IMPORTANCE.get(mention.line.section, "unscored")
    if base == "excluded":
        return base
    r = _rules()
    lo, hi = clause_span(mention.line, mention.span)
    s, e = mention.span
    best: tuple[int, Importance] | None = None
    for rx, imp in ((r.required_cues, "required"), (r.preferred_cues, "preferred")):
        for a, b in _cues(rx, mention.line, lo, hi):
            gap = max(a - e, s - b, 0)
            if best is None or gap < best[0]:
                best = (gap, imp)
    return best[1] if best else base
