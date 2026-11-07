"""Match a job posting against a resume: which recognized skills are covered.

Pure functions: no streamlit, no file writes, no randomness. Text is never logged
or put in exception messages. See docs/SCORING.md.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from engine.keyword_extractor import build_regex_patterns, load_keywords

_KEYWORDS_PATH = Path(__file__).resolve().parent.parent / "data" / "keywords.json"
R_WEIGHT, P_WEIGHT = 0.8, 0.2


@dataclass(frozen=True)
class SkillMatch:
    skill: str
    category: str
    requirement: str  # "required" | "preferred"
    found: bool
    posting_line: str  # the posting line that made it a requirement
    resume_line: str | None  # the resume line that matched, None if missing


@dataclass(frozen=True)
class MatchResult:
    required: tuple[SkillMatch, ...]
    preferred: tuple[SkillMatch, ...]
    score: float | None  # coverage 0-100, None if no skills recognized


# ---- section headings -------------------------------------------------------
_MOD = r"(?:(?:minimum|basic|key|required|preferred|desired|additional)\s+)?"
_REQ_HEAD = re.compile(
    r"\W*" + _MOD + r"(?:requirements?|required(?:\s+(?:qualifications|skills|experience))?|"
    r"qualifications|must[- ]haves?|what\s+you(?:'ll|\s+will)?\s+need)\W*", re.I)
_PREF_HEAD = re.compile(
    r"\W*(?:preferred(?:\s+(?:qualifications|skills|requirements|experience))?|"
    r"desired(?:\s+(?:qualifications|skills))?|nice[- ]to[- ]haves?|bonus(?:\s+points)?|"
    r"(?:a\s+)?plus(?:es)?|additional\s+(?:qualifications|skills))\W*", re.I)
_OTHER_HEAD = re.compile(
    r"\W*(?:responsibilities|duties|about(?:\s+\w+){0,3}|benefits|perks|compensation|"
    r"overview|(?:job\s+)?description|what\s+you(?:'ll|\s+will)\s+do|who\s+we\s+are|"
    r"the\s+role|summary)\W*", re.I)


def _heading(line: str) -> tuple[str, str] | None:
    """Return (section, rest_of_line) if the line is a heading, else None."""
    colon = line.find(":")
    if 0 <= colon <= 45:
        head, rest = line[:colon], line[colon + 1:]
    elif len(line) <= 45:
        head, rest = line, ""
    else:
        return None
    for kind, rx in (("preferred", _PREF_HEAD), ("required", _REQ_HEAD), ("other", _OTHER_HEAD)):
        if rx.fullmatch(head):
            return kind, rest.strip()
    return None


def _lines(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"[\r\n•·]+", text) if p.strip()]


def _check(text: str, name: str) -> None:
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{name} text is empty")  # never echo the text


def split_posting_requirements(posting: str) -> tuple[list[str], list[str]]:
    """Return (required lines, preferred lines). No sections -> all lines required.

    With sections, lines outside a required/preferred section (intro,
    responsibilities, benefits) are ignored.
    """
    _check(posting, "posting")
    required, preferred, section, sectioned = [], [], None, False
    for line in _lines(posting):
        h = _heading(line)
        if h:
            section, line = h
            sectioned = sectioned or section != "other"
            if not line:
                continue
        if section == "required":
            required.append(line)
        elif section == "preferred":
            preferred.append(line)
    if not sectioned:
        return _lines(posting), []
    return required, preferred


# ---- skill matching ---------------------------------------------------------
_GUARDS = {"excel": r"(?!\s+(?:at|in)\b)"}  # the verb "excel at/in", not the spreadsheet


def _pattern(alias: str) -> re.Pattern:
    if len(alias) <= 3 and alias.isalpha() and alias.isupper():
        # Short acronym (CAN, PLC, R, C): case-sensitive, not part of R&D, C-suite, C/C++.
        return re.compile(r"(?<![\w&/+#.-])" + re.escape(alias) + r"(?![\w&/+#-])")
    pat = build_regex_patterns([{"canonical": "x", "aliases": [alias]}])["x"][0]
    guard = _GUARDS.get(alias.lower())
    return re.compile(pat.pattern + guard, re.I) if guard else pat


@lru_cache(maxsize=1)
def _default_skills() -> tuple:
    return tuple(load_keywords(_KEYWORDS_PATH))


_NEG_BEFORE = re.compile(r"\b(?:no|not|without|never|none|lacks?|lacking|zero)\b|n't\b", re.I)
_NEG_AFTER = re.compile(r"\W*(?:(?:is|are)\s+)?(?:not|no)\s+(?:required|needed|necessary)", re.I)


def _mentioned(line: str, patterns: list[re.Pattern]) -> bool:
    """True if some alias matches outside a negation ("no FEA experience")."""
    for pat in patterns:
        for m in pat.finditer(line):
            clause = re.split(r"[.;!?]", line[:m.start()])[-1]
            # shortcut: 6-word lookback; widen if real data shows misses
            if _NEG_BEFORE.search(" ".join(clause.split()[-6:])):
                continue
            if _NEG_AFTER.match(line[m.end():m.end() + 40]):
                continue
            return True
    return False


def _first_line(lines: list[str], patterns: list[re.Pattern]) -> str | None:
    return next((ln for ln in lines if _mentioned(ln, patterns)), None)


def match_posting(posting: str, resume: str, _skills=None) -> MatchResult:
    """Compare recognized posting skills with the resume.

    Output order is stable: keyword-file order within each group.
    `_skills` overrides the keyword list (tests only).
    """
    _check(posting, "posting")
    _check(resume, "resume")
    req_lines, pref_lines = split_posting_requirements(posting)
    resume_lines = _lines(resume)
    required, preferred = [], []
    for s in _default_skills() if _skills is None else _skills:
        pats = [_pattern(a) for a in s["aliases"]]
        for kind, lines, out in (("required", req_lines, required), ("preferred", pref_lines, preferred)):
            pl = _first_line(lines, pats)
            if pl is None:
                continue
            rl = _first_line(resume_lines, pats)
            out.append(SkillMatch(s["canonical"], s["category"], kind, rl is not None, pl, rl))
            break  # in both sections: counts once, as required
    return MatchResult(
        tuple(required), tuple(preferred),
        compute_coverage_score(sum(m.found for m in required), len(required),
                               sum(m.found for m in preferred), len(preferred)),
    )


def compute_coverage_score(r_matched: int, r_total: int, p_matched: int, p_total: int) -> float | None:
    """100 * (0.8 * R + 0.2 * P); an empty category passes its weight on; both empty -> None."""
    if r_total < 0 or p_total < 0 or not (0 <= r_matched <= r_total) or not (0 <= p_matched <= p_total):
        raise ValueError("matched counts must be within totals")
    if r_total == 0 and p_total == 0:
        return None
    if p_total == 0:
        return 100 * r_matched / r_total
    if r_total == 0:
        return 100 * p_matched / p_total
    return 100 * (R_WEIGHT * r_matched / r_total + P_WEIGHT * p_matched / p_total)
