"""Frozen stage interfaces for the job-matching engine (see docs/MATCHING_DESIGN.md).

Coordinator-owned contract. Implementations may change; names, fields and
signatures here may not without a coordinator decision.
All spans are absolute, half-open (start, end) character offsets into the
original input string. No streamlit, no file writes, no randomness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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


# Stage 1 -- Segment
def segment(text: str, doc: DocKind) -> tuple[Section, ...]:
    """Split text into typed sections. Headingless text is one "unknown" section."""
    raise NotImplementedError


def classify_heading(label: str, doc: DocKind) -> SectionKind | None:
    """Map a heading label to a kind using data/match_rules.json; None if not a known heading."""
    raise NotImplementedError


# Stage 2 -- Find
def find_mentions(lines: tuple[Line, ...]) -> tuple[Mention, ...]:
    """Longest-alias-first, non-overlapping candidate mentions. No keep/drop or importance decisions."""
    raise NotImplementedError


# Stage 3 -- Disambiguate
def disambiguate(mentions: tuple[Mention, ...]) -> tuple[Mention, ...]:
    """Drop mentions that fail the skill's data-driven rules (case_sensitive, needs_context, exclude_phrases)."""
    raise NotImplementedError


# Stage 4 -- Qualify
def clause_span(line: Line, span: tuple[int, int]) -> tuple[int, int]:
    """Absolute span of the clause containing `span`, bounded by clause breaks from data."""
    raise NotImplementedError


def qualify(mention: Mention) -> Mention:
    """Return the mention with status set from cues before it in the same clause."""
    raise NotImplementedError


# Stage 5 -- Decide
def importance(mention: Mention) -> Importance:
    """Posting importance from section kind, overridden by inline cues in the mention's clause."""
    raise NotImplementedError
