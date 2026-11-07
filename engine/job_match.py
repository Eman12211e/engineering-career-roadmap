"""Match a job posting against a resume: which recognized skills are covered.

Thin wrappers over the five stages in engine/match_stages.py (segment, find, disambiguate,
qualify, decide). Pure functions: no streamlit, no file writes, no randomness. Text is never
logged or put in exception messages. See docs/SCORING.md and docs/MATCHING_DESIGN.md.
"""

from dataclasses import dataclass

from engine.match_stages import (
    Mention,
    _qualify,
    disambiguate,
    find_mentions,
    importance,
    norm_span,
    segment,
    skill_order,
)

R_WEIGHT, P_WEIGHT = 0.8, 0.2
_MAXLEN = 200
_TIERS = ("required", "preferred", "unscored", "excluded")  # precedence, highest first


@dataclass(frozen=True)
class SkillMatch:
    skill: str
    category: str
    requirement: str  # "required" | "preferred" | "unscored" | "excluded"
    found: bool
    posting_line: str  # snippet (<= 200 chars) of the posting line that decided the requirement
    resume_line: str | None  # snippet of the resume line that matched, None if missing
    section: str = ""  # kind of the posting section holding the evidence
    posting_span: tuple[int, int] | None = None  # exact span of the posting evidence
    resume_span: tuple[int, int] | None = None  # exact span of the resume evidence


@dataclass(frozen=True)
class MatchResult:
    required: tuple[SkillMatch, ...]
    preferred: tuple[SkillMatch, ...]
    score: float | None  # coverage 0-100, None if no required/preferred skills recognized
    unscored: tuple[SkillMatch, ...] = ()
    excluded: tuple[SkillMatch, ...] = ()


def _check(text: str, name: str) -> None:
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{name} text is empty")  # never echo the text


def _snippet(m: Mention) -> str:
    """The mention's line, capped at 200 chars around the match, with ellipses where cut."""
    text, s, e = norm_span(m.line, m.span)  # whitespace-collapsed, so a hard wrap reads as one line
    if len(text) <= _MAXLEN:
        return text
    w = _MAXLEN - 2
    a = max(0, min(s - (w - (e - s)) // 2, len(text) - w))
    return ("…" if a else "") + text[a:a + w] + ("…" if a + w < len(text) else "")


def _mentions(text: str, doc: str) -> list[tuple[Mention, str]]:
    """Kept mentions with their posting importance ("" for a resume); negated/hypothetical dropped.

    Mentions in excluded posting sections skip qualification: they never count anyway.
    """
    lines = tuple(ln for sec in segment(text, doc) for ln in sec.lines)
    out = []
    for m in disambiguate(find_mentions(lines)):
        if doc == "posting" and m.line.section == "excluded":
            out.append((m, "excluded"))
            continue
        m = _qualify(m, doc)
        if m.status == "affirmed":
            out.append((m, importance(m) if doc == "posting" else ""))
    return out


def match_posting(posting: str, resume: str) -> MatchResult:
    """Compare the skills a posting asks for with those a resume shows.

    Output order is stable: keywords.json order within each group.
    """
    _check(posting, "posting")
    _check(resume, "resume")
    evidence: dict[str, Mention] = {}
    for m, _ in sorted(_mentions(resume, "resume"), key=lambda p: p[0].span):
        evidence.setdefault(m.canonical, m)
    best: dict[str, tuple[int, int, Mention]] = {}
    for m, imp in _mentions(posting, "posting"):
        key = (_TIERS.index(imp), m.span[0])
        if m.canonical not in best or key < best[m.canonical][:2]:
            best[m.canonical] = (*key, m)
    groups: dict[str, list[SkillMatch]] = {t: [] for t in _TIERS}
    for name in skill_order():
        if name not in best:
            continue
        tier, _, m = best[name]
        r = evidence.get(name)
        groups[_TIERS[tier]].append(SkillMatch(
            name, m.category, _TIERS[tier], r is not None, _snippet(m),
            _snippet(r) if r else None, m.line.section, m.span, r.span if r else None,
        ))
    req, pref = groups["required"], groups["preferred"]
    return MatchResult(
        tuple(req), tuple(pref),
        compute_coverage_score(sum(s.found for s in req), len(req), sum(s.found for s in pref), len(pref)),
        tuple(groups["unscored"]), tuple(groups["excluded"]),
    )


def split_posting_requirements(posting: str) -> tuple[list[str], list[str]]:
    """Return (required lines, preferred lines): posting lines holding a required / preferred skill."""
    _check(posting, "posting")
    out: tuple[list[str], list[str]] = ([], [])
    seen: set[tuple[int, int]] = set()
    for m, imp in _mentions(posting, "posting"):
        if imp in ("required", "preferred") and (m.line.start, int(imp == "preferred")) not in seen:
            seen.add((m.line.start, int(imp == "preferred")))
            out[imp == "preferred"].append(m.line.text)
    return out


def compute_coverage_score(r_matched: int, r_total: int, p_matched: int, p_total: int) -> float | None:
    """100 * (0.8 * R + 0.2 * P); an empty group passes its weight on; both empty -> None."""
    if r_total < 0 or p_total < 0 or not (0 <= r_matched <= r_total) or not (0 <= p_matched <= p_total):
        raise ValueError("matched counts must be within totals")
    if r_total == 0 and p_total == 0:
        return None
    if p_total == 0:
        return 100 * r_matched / r_total
    if r_total == 0:
        return 100 * p_matched / p_total
    return 100 * (R_WEIGHT * r_matched / r_total + P_WEIGHT * p_matched / p_total)
