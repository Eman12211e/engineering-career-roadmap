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
    _MOD + r"(?:requirements?|required(?:\s+(?:qualifications|skills|experience))?|"
    r"qualifications|must[- ]haves?|what\s+you(?:'ll|\s+will)?\s+(?:need|do)|responsibilities|duties|"
    r"skills|about\s+you|the\s+role|overview|summary|(?:job\s+)?description)", re.I)
_PREF_HEAD = re.compile(  # a bare "Bonus" is usually pay, so it is not a preferred label
    r"preferred(?:\s+(?:qualifications|skills|requirements|experience))?|"
    r"desired(?:\s+(?:qualifications|skills))?|nice[- ]to[- ]haves?|bonus\s+(?:points|skills)|"
    r"(?:a\s+)?plus(?:es)?|additional\s+(?:qualifications|skills)", re.I)
_SKIP_HEAD = re.compile(  # clearly non-skill sections: ignored
    r"benefits|perks|compensation|salary|about\s+us|about\s+the\s+company|who\s+we\s+are|"
    r"equal\s+opportunity(?:\s+employer)?|eeo", re.I)
# an inline "Preferred:" / "Nice to have:" label starts a new segment
_INLINE_PREF = re.compile(
    r"(?=\b(?:preferred(?:\s+\w+)?|nice[- ]to[- ]haves?|bonus\s+(?:points|skills))\s*:)", re.I)
_SENTENCE_PUNCT = re.compile(r"[.!?;](?:\s|$)")


def _is_bullet(line: str) -> bool:
    return line.startswith(("-", "–", "—", ">", "•", "·", "▪", "◦")) or line.startswith("* ")


_SMALL_WORDS = {"a", "an", "the", "of", "for", "to", "and", "or", "in", "on", "at", "with", "you", "your"}
_TRAIL_PREF = re.compile(
    r"(?:\(?(?:(?:is|are)\s+)?a\s+plus\)?|preferred|nice\s+to\s+have|(?:is\s+)?a\s+bonus)[\W_]*$", re.I)


def _title_like(label: str) -> bool:
    """Title Case / UPPER heading ("The Position"), unlike a plain line ("Free lunch")."""
    words = [w for w in label.split() if w.lower() not in _SMALL_WORDS]
    return bool(words) and all(w[0].isupper() or not w[0].isalpha() for w in words)


def _clean_label(text: str) -> str:
    """Strip markdown markers (#, **, __) and a trailing colon from a heading."""
    return text.strip().lstrip("#").strip(" \t*_").rstrip(":").strip(" \t*_")


def _classify(label: str) -> str | None:
    for kind, rx in (("preferred", _PREF_HEAD), ("required", _REQ_HEAD), ("skip", _SKIP_HEAD)):
        if rx.fullmatch(label):
            return kind
    return None


def _lines(text: str) -> list[str]:
    """Split on newlines; inline bullet characters start new pieces that keep their marker."""
    out = []
    for ln in re.split(r"[\r\n]+", text):
        parts = re.split("([•·▪◦])", ln)
        if parts[0].strip():
            out.append(parts[0].strip())
        for i in range(1, len(parts), 2):
            if parts[i + 1].strip():
                out.append(parts[i] + " " + parts[i + 1].strip())
    return out


def _check(text: str, name: str) -> None:
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{name} text is empty")  # never echo the text


def split_posting_requirements(posting: str, _skills=None) -> tuple[list[str], list[str]]:
    """Return (required lines, preferred lines).

    Only Preferred / Nice to have / Bonus points / Plus sections are preferred.
    Everything else is required, except lines under clearly non-skill sections
    (Benefits, Perks, Compensation, Salary, About us, ...), which are dropped.
    A heading-like line (no bullet, <= 45 chars once markdown is stripped, no
    sentence punctuation, no digits/$/%, no recognized skill) ends the current
    section: known headings set its type, unknown ones start a required section.
    "Label: text" lines apply a required/preferred label to the text; a skip label
    ("Salary: ...") drops only that line. Heading lines are not returned.
    """
    _check(posting, "posting")
    compiled = _default_compiled() if _skills is None else _compile(_skills)
    has_skill = lambda s: any(p.search(s) for _, _, pats in compiled for p in pats)  # noqa: E731
    required, preferred, section = [], [], "required"
    for raw in _lines(posting):
        for line in (s.strip() for s in _INLINE_PREF.split(raw)):
            if not line:
                continue
            if not _is_bullet(line):
                colon = line.find(":")
                head, rest = (line[:colon], line[colon + 1:].strip(" \t*_")) if 0 <= colon <= 45 else ("", "")
                if rest:
                    kind = _classify(_clean_label(head))
                    if kind == "skip":
                        continue  # one line only; the section is unchanged
                    if kind:
                        section, line = kind, rest
                else:
                    label = _clean_label(line)
                    kind = _classify(label)
                    if kind is None and (label and len(label) <= 45 and not _SENTENCE_PUNCT.search(label)
                            and not re.search(r"[\d$%]", label) and not has_skill(label)):
                        kind = "required"  # unknown heading
                        # inside a skip section a plain line ("Free lunch") is not a heading
                        if section == "skip" and not (line.endswith(":") or line.startswith(("#", "**"))
                                                      or _title_like(label)):
                            kind = None
                    if kind:
                        section = kind
                        continue
            if section == "preferred" or (section == "required" and _TRAIL_PREF.search(line)):
                preferred.append(line)
            elif section == "required":
                required.append(line)
    return required, preferred


# ---- skill matching ---------------------------------------------------------
_GUARDS = {"excel": r"(?!\s+(?:at|in)\b)"}  # the verb "excel at/in", not the spreadsheet
_AMBIGUOUS = {"CAN", "R", "C"}  # aliases that are also ordinary words/letters


def _pattern(alias: str) -> re.Pattern:
    if alias in _AMBIGUOUS:
        # case-sensitive, and not part of R&D, C-suite, C/C++, C#
        return re.compile(r"(?<![\w&/+#.-])" + re.escape(alias) + r"(?![\w&/+#-])")
    pat = build_regex_patterns([{"canonical": "x", "aliases": [alias]}])["x"][0].pattern
    if alias.isupper() and pat.endswith(r"\b"):
        pat = pat[:-2] + r"(?-i:(?<=[A-Z])s)?\b"  # plural only after upper case: PLCs, not MLS/mls
    return re.compile(pat + _GUARDS.get(alias.lower(), ""), re.I)


def _compile(skills) -> tuple:
    return tuple((s["canonical"], s["category"], tuple(_pattern(a) for a in s["aliases"])) for s in skills)


@lru_cache(maxsize=1)
def _default_compiled() -> tuple:
    return _compile(load_keywords(_KEYWORDS_PATH))


_NEG = re.compile(r"(?<![\w-])(?:no|not|without|never)(?![\w-])|\bdon'?t\s+need\b", re.I)
_CLAUSE_BREAK = re.compile(r"[,;.!?]|\b(?:but|and)\b", re.I)
_NEG_AFTER = re.compile(
    r"(?:[ \t]+(?!(?:and|but)\b)[\w'-]+){0,3}?[ \t]+(?:(?:is|are)[ \t]+)?not[ \t]+(?:required|needed|necessary)\b", re.I)
_RESUME_NEG = re.compile(r"(?:no\s+(?:prior\s+)?experience\s+(?:with|in)|not\s+familiar\s+with)\s+$", re.I)
_MAXLEN = 200


def _snip(line: str, start: int, end: int) -> str:
    """Cap a line at ~200 chars, centred on the match, with ellipses where cut."""
    if len(line) <= _MAXLEN:
        return line
    s = max(0, min(start - (_MAXLEN - (end - start)) // 2, len(line) - _MAXLEN))
    return ("…" if s else "") + line[s:s + _MAXLEN] + ("…" if s + _MAXLEN < len(line) else "")


def _mention(line: str, patterns, is_resume: bool) -> str | None:
    """Return the (capped) line if some alias matches outside a negation, else None.

    Posting: negated when a negator is within 3 words before the skill with no
    comma/semicolon/"but"/"and" between, or "not required/needed/necessary" follows
    within the clause. Resume: only "no experience with X" / "not familiar with X".
    """
    for pat in patterns:
        for m in pat.finditer(line):
            before = line[:m.start()]
            if is_resume:
                if _RESUME_NEG.search(before):
                    continue
            else:
                clause = _CLAUSE_BREAK.split(before)[-1]
                if _NEG.search(" ".join(clause.split()[-3:])):
                    continue
                if _NEG_AFTER.match(line[m.end():m.end() + 60]):
                    continue
            return _snip(line, m.start(), m.end())
    return None


def _first_line(lines: list[str], patterns, is_resume: bool) -> str | None:
    return next((r for r in (_mention(ln, patterns, is_resume) for ln in lines) if r is not None), None)


def match_posting(posting: str, resume: str, _skills=None) -> MatchResult:
    """Compare recognized posting skills with the resume.

    Output order is stable: keyword-file order within each group.
    `_skills` overrides the keyword list (tests only).
    """
    _check(posting, "posting")
    _check(resume, "resume")
    req_lines, pref_lines = split_posting_requirements(posting, _skills)
    resume_lines = _lines(resume)
    required, preferred = [], []
    for name, cat, pats in _default_compiled() if _skills is None else _compile(_skills):
        for kind, lines, out in (("required", req_lines, required), ("preferred", pref_lines, preferred)):
            pl = _first_line(lines, pats, False)
            if pl is None:
                continue
            rl = _first_line(resume_lines, pats, True)
            out.append(SkillMatch(name, cat, kind, rl is not None, pl, rl))
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
