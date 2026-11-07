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


def _key(label: str) -> str:
    """Normalise a heading label for vocabulary lookup (case, symbols, hyphens, "&")."""
    t = re.sub(r"^[\W_]+", "", label.strip()).replace("\u2019", "'").replace("&", " and ")
    t = re.sub(r"[^\w']+", " ", t.lower().replace("-", " "))
    return " ".join(t.split())


def _alt(words) -> str:
    ws = sorted({w.replace("’", "'") for w in words}, key=len, reverse=True)
    return "|".join(r"\s+".join(re.escape(t) for t in w.split()) for w in ws)


def _bounded(words) -> str:
    return r"(?<![\w-])(?:" + _alt(words) + r")(?![\w-])"


@dataclass(frozen=True)
class _Rules:
    headings: dict          # doc -> {normalised label: kind}
    bullets_always: str
    bullets_spaced: str
    numbered: re.Pattern
    neg_before: re.Pattern          # negator then only fillers, ending at the skill
    hyp_before: re.Pattern          # hypothetical cue then only fillers, ending at the skill
    neg_after: re.Pattern           # fillers then a "not required" cue, starting after the skill
    not_required_then_pref: re.Pattern
    breaks: re.Pattern
    connectors: re.Pattern          # a gap made only of list connectors
    postfix: dict                   # importance -> pattern, starting after the last skill of a list
    modal_before: dict              # importance -> pattern, ending at the first skill of a list
    labels: dict                    # importance -> pattern, at the start of a clause
    heading_test: dict


@lru_cache(maxsize=1)
def _rules() -> _Rules:
    with open(_ROOT / "data" / "match_rules.json", encoding="utf-8") as f:
        d = json.load(f)
    heads = {
        doc: {_key(label): kind for kind, labels in kinds.items() for label in labels}
        for doc, kinds in d["headings"].items()
    }
    fill_b = _bounded(d["negation_fillers"])
    cue_fill = _bounded(d["cue_fillers"])
    prefix_fill = _bounded(d["negation_fillers"] + d["cue_fillers"])
    after_gap = r"\s*(?:" + cue_fill + r"\s+)*"
    return _Rules(
        headings=heads,
        bullets_always="".join(d["bullets"]["always"]),
        bullets_spaced="".join(d["bullets"]["with_space"]),
        numbered=re.compile(d["bullets"]["numbered"]),
        neg_before=re.compile(_bounded(d["negation"]) + r"(?:\s+" + fill_b + r")*\s*$", re.I),
        hyp_before=re.compile(_bounded(d["hypothetical"]) + r"(?:\s+" + fill_b + r")*\s*$", re.I),
        neg_after=re.compile(r"^" + after_gap + _bounded(d["negation_after"]), re.I),
        not_required_then_pref=re.compile(
            r"^" + after_gap + _bounded(d["negation_after"]) + r"\s*,?\s*(?:but|though|however)\s*,?\s*"
            r"(?:(?:is|are)\s+)?" + _bounded(d["not_required_then_preferred"]), re.I),
        breaks=re.compile("|".join(f"(?:{b})" for b in d["clause_breaks"]), re.I),
        connectors=re.compile(r"^(?:\s*(?:" + _alt(d["list_connectors"]) + r")\s*)+$", re.I),
        postfix={
            imp: re.compile(r"^\s*\(?\s*(?:" + cue_fill + r"\s+)*" + _bounded(words), re.I)
            for imp, words in d["postfix_cues"].items()
        },
        modal_before={
            imp: re.compile(_bounded(words) + r"(?:\s+" + prefix_fill + r")*\s*$", re.I)
            for imp, words in d["modal_prefix"].items()
        },
        labels={
            imp: re.compile(r"^[\W_]*(?:" + _alt(words) + r")\s*:", re.I)
            for imp, words in d["prefix_labels"].items()
        },
        heading_test=d["heading_test"],
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
    """A list item: bullet marker, or a numbered / lettered item ("1.", "2)", "a.")."""
    r = _rules()
    return (text[0] in r.bullets_always
            or (len(text) > 1 and text[0] in r.bullets_spaced and text[1] in " \t")
            or r.numbered.match(text) is not None)


def classify_heading(label: str, doc: DocKind) -> SectionKind | None:
    """Map a heading label to a kind using data/match_rules.json; None if not a known heading."""
    return _rules().headings[doc].get(_key(label))


def _has_skill(text: str) -> bool:
    return any(rx.search(text) for sk in _skills() for _, rx in sk.aliases)


def _is_heading(text: str, doc: DocKind, next_text: str | None, blank_after: bool) -> tuple[bool, SectionKind | None, str]:
    """Structural heading test (R2.2) -> (is heading, known kind or None, cleaned label)."""
    ht = _rules().heading_test
    core = re.sub(r"^[\W_]+", "", text.strip()).rstrip("*_ \t")
    colon = core.endswith(":")
    label = " ".join(core.rstrip(":").rstrip("*_ \t").split())
    if not label or len(label.split()) > ht["max_words"]:
        return False, None, label
    if label[-1] in ht["sentence_end_chars"]:
        return False, None, label
    kind = classify_heading(label, doc)
    small = set(ht["small_words"])
    words = [w for w in label.split() if w.lower() not in small]
    styles = {
        "colon": colon,
        "title_case": all(not w[0].isalpha() or w[0].isupper() for w in words),
        "all_caps": label == label.upper() and any(c.isalpha() for c in label),
        "vocabulary": kind is not None,
    }
    if not any(styles[k] for k in ht["style_options"]):
        return False, None, label
    contexts = {
        "list_next": next_text is not None and _is_bullet(next_text),
        "blank_after": blank_after,
        "colon": colon,
        "vocabulary": kind is not None,
    }
    if not any(contexts[k] for k in ht["context_options"]):
        return False, None, label
    # a heading swallows its text, so a skill-bearing unknown line without a colon stays body text
    if kind is None and not colon and ht["skill_text_is_body"] and _has_skill(label):
        return False, None, label
    return True, kind, label


_NO_CONTINUE = ".:;!?"


def segment(text: str, doc: DocKind) -> tuple[Section, ...]:
    """Split text into typed sections. Headingless text is one "unknown" section.

    Hard-wrapped physical lines are joined into one logical Line (R2.3): a line continues the
    previous body line when that line does not end with . : ; ! ? and this line is not a list
    item or heading and starts with a lower-case letter. Line.text == text[start:end] always,
    newlines included.
    """
    sections: list[Section] = []
    kind: SectionKind = "unknown"
    heading: str | None = None
    hspan: tuple[int, int] | None = None
    body: list[Line] = []

    def close() -> None:
        if body or heading is not None:
            sections.append(Section(kind, heading, hspan, tuple(body)))

    phys: list[tuple[int, str]] = []  # (start offset of the stripped text, stripped text)
    pos = 0
    for chunk in text.split("\n"):
        phys.append((pos + len(chunk) - len(chunk.lstrip()), chunk.strip()))
        pos += len(chunk) + 1
    prev_body = False  # was the previous physical line a body line (not blank, not a heading)?
    for i, (start, t) in enumerate(phys):
        if not t:
            prev_body = False
            continue
        end = start + len(t)
        bullet = _is_bullet(t)
        if not bullet:
            nxt = next((x[1] for x in phys[i + 1:] if x[1]), None)
            blank_after = i + 1 < len(phys) and not phys[i + 1][1]
            is_head, known, label = _is_heading(t, doc, nxt, blank_after)
            if is_head:  # every heading ends the previous section, known or not
                close()
                kind, heading, hspan, body = known or "unknown", label, (start, end), []
                prev_body = False
                continue
            if prev_body and body and t[0].islower() and body[-1].text[-1] not in _NO_CONTINUE:
                last = body[-1]
                body[-1] = Line(text[last.start:end], last.start, end, last.section, last.heading, last.is_bullet)
                continue
        body.append(Line(t, start, end, kind, heading, bullet))
        prev_body = True
    close()
    return tuple(sections)


# ---- Normalised view of a line (whitespace runs collapsed) -------------------------------------
@dataclass(frozen=True)
class _Norm:
    text: str                     # line text with every whitespace run collapsed to one space
    to_orig: tuple[int, ...]      # normalised index -> index in Line.text
    to_norm: tuple[int, ...]      # Line.text index -> normalised index (len + 1 entries)


@lru_cache(maxsize=8192)
def _norm(line: Line) -> _Norm:
    out: list[str] = []
    to_orig: list[int] = []
    to_norm: list[int] = []
    for i, ch in enumerate(line.text):
        if ch.isspace():
            if not out or out[-1] != " ":
                out.append(" ")
                to_orig.append(i)
        else:
            out.append(ch)
            to_orig.append(i)
        to_norm.append(len(out) - 1)
    to_norm.append(len(out))
    return _Norm("".join(out), tuple(to_orig), tuple(to_norm))


def norm_span(line: Line, span: tuple[int, int]) -> tuple[str, int, int]:
    """(normalised line text, start, end) of an absolute span in normalised coordinates."""
    n = _norm(line)
    return n.text, n.to_norm[span[0] - line.start], n.to_norm[span[1] - line.start - 1] + 1


# ---- Stage 2 -- Find -------------------------------------------------------------------------
def find_mentions(lines: tuple[Line, ...]) -> tuple[Mention, ...]:
    """Longest-alias-first, non-overlapping candidate mentions. No keep/drop or importance decisions.

    Aliases match across hard-wrap newlines (whitespace runs count as one space); spans are
    absolute offsets into the original text.
    """
    out: list[Mention] = []
    for line in lines:
        n = _norm(line)
        cands = []
        for order, sk in enumerate(_skills()):
            for alias, rx in sk.aliases:
                for m in rx.finditer(n.text):
                    cands.append((-(m.end() - m.start()), m.start(), order, sk, alias, m.end()))
        cands.sort(key=lambda c: c[:3])
        taken: list[tuple[int, int]] = []
        for _, s, _, sk, alias, e in cands:
            if any(s < te and ts < e for ts, te in taken):
                continue
            taken.append((s, e))
            span = (line.start + n.to_orig[s], line.start + n.to_orig[e - 1] + 1)
            out.append(Mention(sk.canonical, sk.category, alias, span, line))
    return tuple(sorted(out, key=lambda m: (m.line.start, m.span)))


# ---- Stage 3 -- Disambiguate -----------------------------------------------------------------
def _keep(m: Mention) -> bool:
    sk = _skill_by_name()[m.canonical]
    text, s, e = norm_span(m.line, m.span)
    if sk.case_sensitive and text[s:e] not in (m.alias, m.alias + "s"):
        return False
    if sk.needs_context and not any(rx.search(text) for rx in sk.needs_context):
        return False
    return not any(p.start() < e and s < p.end() for rx in sk.exclude_phrases for p in rx.finditer(text))


def disambiguate(mentions: tuple[Mention, ...]) -> tuple[Mention, ...]:
    """Drop mentions that fail the skill's data-driven rules (case_sensitive, needs_context, exclude_phrases)."""
    return tuple(m for m in mentions if _keep(m))


# ---- Stage 4 -- Qualify ----------------------------------------------------------------------
@lru_cache(maxsize=8192)
def _chains(line: Line) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Coordinated skill lists ("X, Y or Z") as tuples of normalised spans, in line order."""
    n = _norm(line)
    spans = []
    for m in disambiguate(find_mentions((line,))):
        a, b = norm_span(line, m.span)[1:]
        spans.append((a, b))
    chains: list[list[tuple[int, int]]] = []
    for sp in spans:
        if chains and (sp[0] == chains[-1][-1][1] or _rules().connectors.match(n.text[chains[-1][-1][1]:sp[0]])):
            chains[-1].append(sp)
        else:
            chains.append([sp])
    return tuple(tuple(c) for c in chains)


def _chain_of(line: Line, nspan: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    return next((c for c in _chains(line) if nspan in c), (nspan,))


def _clause(line: Line, nspan: tuple[int, int]) -> tuple[int, int]:
    """Clause bounds in normalised coordinates; breaks inside a coordinated list do not count."""
    n = _norm(line)
    gaps = [(a[1], b[0]) for c in _chains(line) for a, b in zip(c, c[1:])]
    lo, hi = 0, len(n.text)
    for b in _rules().breaks.finditer(n.text):
        if any(b.start() < ge and gs < b.end() for gs, ge in gaps):
            continue
        if b.end() <= nspan[0]:
            lo = b.end()
        elif b.start() >= nspan[1]:
            hi = b.start()
            break
    return lo, hi


def clause_span(line: Line, span: tuple[int, int]) -> tuple[int, int]:
    """Absolute span of the clause containing `span`, bounded by clause breaks from data."""
    n = _norm(line)
    _, a, b = norm_span(line, span)
    lo, hi = _clause(line, (a, b))
    start = n.to_orig[lo] if lo < len(n.to_orig) else len(line.text)
    end = n.to_orig[hi - 1] + 1 if hi > 0 else 0
    return line.start + start, line.start + max(end, start)


def _qualify(mention: Mention, doc: DocKind) -> Mention:
    r = _rules()
    n = _norm(mention.line)
    nspan = norm_span(mention.line, mention.span)[1:]
    chain = _chain_of(mention.line, nspan)
    lo, hi = _clause(mention.line, nspan)
    before = n.text[lo:chain[0][0]]
    status: Status = "affirmed"
    if r.neg_before.search(before):
        status = "negated"
    elif r.hyp_before.search(before):
        status = "hypothetical"
    elif doc == "posting":
        after = n.text[chain[-1][1]:hi]
        if r.neg_after.match(after) and not r.not_required_then_pref.match(n.text[chain[-1][1]:]):
            status = "negated"
    return dataclasses.replace(mention, status=status)


def qualify(mention: Mention) -> Mention:
    """Return the mention with status set from cues bound to it in the same clause.

    A negator or hypothetical cue applies only directly before the skill (or the first skill of
    its coordinated list), separated by nothing but filler words. Posting rules apply,
    including the "not required" cues that follow the skill.
    """
    return _qualify(mention, "posting")


# ---- Stage 5 -- Decide -----------------------------------------------------------------------
_SECTION_IMPORTANCE: dict[str, Importance] = {
    "required": "required", "preferred": "preferred", "excluded": "excluded",
}


def _importance_cue(mention: Mention) -> Importance | None:
    """The one place a mention's inline importance cue is decided (R2.4).

    Grammatical binding only: a prefix label at the start of the clause, a postfix phrase right
    after the last skill of its coordinated list, or a modal/"preferably" cue right before the
    first skill. Only filler words may sit in the gap. "X is not required, but is a plus" is preferred.
    """
    r = _rules()
    n = _norm(mention.line)
    nspan = norm_span(mention.line, mention.span)[1:]
    chain = _chain_of(mention.line, nspan)
    lo, hi = _clause(mention.line, nspan)
    after = n.text[chain[-1][1]:]
    if r.not_required_then_pref.match(after):
        return "preferred"
    clause_after = n.text[chain[-1][1]:hi]
    for imp in ("preferred", "required"):
        if r.postfix[imp].match(clause_after):
            return imp
    before = n.text[lo:chain[0][0]]
    for imp in ("preferred", "required"):
        if r.modal_before[imp].search(before):
            return imp
    for imp in ("preferred", "required"):
        if r.labels[imp].match(n.text[lo:hi]):
            return imp
    return None


def importance(mention: Mention) -> Importance:
    """Posting importance (R2.1): required or preferred only from a known required/preferred heading
    or a bound cue; everything else is unscored. Excluded needs a known excluded heading."""
    base = _SECTION_IMPORTANCE.get(mention.line.section, "unscored")
    if base == "excluded":
        return base
    return _importance_cue(mention) or base
