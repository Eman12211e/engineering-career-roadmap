"""Evidence-based resume bullet builder.

Bullets are assembled only from text the user supplies. Nothing here invents
metrics, verbs, tools or ownership, and nothing is random.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from engine.keyword_extractor import load_keywords

# Offered as suggestions only (suggest_verbs); never applied automatically.
STRONG_VERBS = {
    "cad": ["Designed", "Modeled", "Drafted", "Detailed"],
    "analysis": ["Analyzed", "Simulated", "Validated", "Evaluated"],
    "controls": ["Programmed", "Configured", "Tested", "Commissioned"],
    "manufacturing": ["Improved", "Assembled", "Machined", "Documented"],
    "standards": ["Applied", "Documented", "Reviewed", "Verified"],
    "quality": ["Inspected", "Investigated", "Measured", "Documented"],
    "programming": ["Wrote", "Automated", "Built", "Scripted"],
    "certifications": ["Earned", "Completed", "Studied"],
    "soft_skills": ["Coordinated", "Presented", "Documented", "Communicated"],
}
_DEFAULT_VERBS = ["Used", "Applied", "Built", "Tested"]

_PROMPTS = [
    "What did you actually do with {skill}? Use your own verb (helped, built, tested...).",
    "What was the project, part or system? Name it as you would to a colleague.",
    "Was there a result you can state truthfully (a number, a finished deliverable)? Leave blank if not.",
]
_CATEGORY_PROMPTS = {
    "cad": "Which parts, assemblies or drawings did you create or edit?",
    "analysis": "What did you analyze, and what did you compare the result against?",
    "controls": "What equipment or process did the program run, and what did you do on it?",
    "programming": "What did the code do, and who or what used it?",
    "certifications": "Which exam or course, and when did you complete it?",
}

# Verbs/phrases that imply ownership or impact: supported only if the user's
# action contains them. Nothing else in the evidence can vouch for them.
_VERBS = {
    "led", "lead", "leading", "managed", "owned", "spearheaded", "directed",
    "headed", "oversaw", "supervised", "architected", "optimized", "improved",
    "drove", "mentored", "owner of", "responsible for",
}
# Other inflation and number words: supported if in the user's own text.
_WORDS = {
    "ownership", "principal", "senior", "expert", "certified", "pmp",
    "six sigma", "green belt", "black belt", "p.e.", "one", "two", "three",
    "four", "five", "six", "seven", "eight", "nine", "ten", "twenty", "thirty",
    "forty", "fifty", "hundred", "thousand", "half", "doubled", "tripled",
    "halved", "twice", "percent",
}
_NUM = re.compile(r"(\$?\d[\d,]*(?:\.\d+)?[KkMmBb]?%?)(?:\s+([A-Za-z]+))?")


@lru_cache(maxsize=1)
def _tool_terms() -> tuple:
    """Canonicals and aliases from data/keywords.json (read-only)."""
    path = Path(__file__).resolve().parent.parent / "data" / "keywords.json"
    terms = {"Minitab", "Siemens TIA Portal", "TIA Portal", "CLSSGB"}  # not in keywords.json
    for sk in load_keywords(path):
        terms.update([sk["canonical"], *sk.get("aliases", [])])
    return tuple(sorted(terms))


def _has(term: str, text: str, exact_case: bool = False) -> bool:
    pat = r"(?<![\w&])" + re.escape(term) + r"(?![\w&])"
    return bool(re.search(pat, text, 0 if exact_case else re.I))


@dataclass(frozen=True)
class BulletEvidence:
    skill: str
    action: str  # required: the user's own words and verb
    context: str = ""
    result: str = ""  # blank -> bullet has no result


def _clean(text: str) -> str:
    return " ".join((text or "").split())


def build_bullet(evidence: BulletEvidence) -> str:
    """Assemble a bullet from the user's own words; the verb is never changed."""
    skill, action = _clean(evidence.skill), _clean(evidence.action)
    if not skill:
        raise ValueError("skill is required and cannot be blank")
    if not action:
        raise ValueError("action is required and cannot be blank")
    context, result = _clean(evidence.context), _clean(evidence.result)
    text = f"{action} {context}".strip()
    if result:
        text += f", {result.rstrip('.')}"
    return text[0].upper() + text[1:].rstrip(".") + "."


def skill_mentioned(bullet: str, skill: str) -> bool:
    """True if the skill appears in the bullet (it is never inserted for you)."""
    return _has(_clean(skill), bullet)


def find_unsupported_claims(bullet: str, evidence: BulletEvidence) -> List[str]:
    """Return numbers, inflation terms and tools in `bullet` that the user's own
    action/context/result do not support. The skill field is not evidence."""
    action = _clean(evidence.action)
    source = " ".join(_clean(x) for x in (action, evidence.context, evidence.result))
    def norm(n):
        return n.replace(",", "").lower()
    src = [(norm(n), u.lower()) for n, u in _NUM.findall(source)]
    flagged: List[str] = []

    def add(t):
        if t not in flagged:
            flagged.append(t)

    for n, u in _NUM.findall(bullet):
        k, u = norm(n), u.lower()
        if not any(k == sn and (not u or not su or u == su) for sn, su in src):
            add(n.rstrip(".,"))
    for term in sorted(_VERBS):
        if _has(term, bullet) and not _has(term, action):
            add(term)
    for term in sorted(_WORDS):
        if _has(term, bullet) and not _has(term, source):
            add(term)
    for term in _tool_terms():
        exact = len(term) <= 3  # short aliases like ROS are case-sensitive
        if _has(term, bullet, exact) and not _has(term, source, exact):
            add(term.lower())
    return flagged


def split_claims(bullet: str, evidence: BulletEvidence):
    """Split flags into (unsupported, personal_check).

    unsupported: terms found nowhere in the user's action/context/result.
    personal_check: ownership/impact verbs the user typed in context or result
    (not action); keep only if they personally did it.
    """
    own = " ".join(_clean(x) for x in (evidence.context, evidence.result))
    flags = find_unsupported_claims(bullet, evidence)
    check = [t for t in flags if t in _VERBS and _has(t, own)]
    return [t for t in flags if t not in check], check


def suggest_prompts(skill: str, category: str) -> List[str]:
    prompts = [p.format(skill=skill) for p in _PROMPTS]
    if category in _CATEGORY_PROMPTS:
        prompts.insert(1, _CATEGORY_PROMPTS[category])
    return prompts


def suggest_verbs(category: str) -> List[str]:
    """Suggestions only; the user chooses, and must be able to defend the verb."""
    return list(STRONG_VERBS.get(category, _DEFAULT_VERBS))


def generate_bullets(
    skills: List[str],
    industry: str,
    background: str,
    skills_metadata: List[Dict],
    num_bullets: int = 2,
) -> List[Dict]:
    """Compatibility shim: no bullets are invented, only prompts to answer.

    industry, background and num_bullets are ignored.
    """
    cat_map = {s["canonical"]: s["category"] for s in skills_metadata}
    return [
        {"skill": s, "bullets": [], "prompts": suggest_prompts(s, cat_map.get(s, ""))}
        for s in skills
    ]
