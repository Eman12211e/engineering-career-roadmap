"""Evidence-based resume bullet builder.

Bullets are assembled only from text the user supplies. Nothing here invents
metrics, verbs, tools or ownership, and nothing is random.
"""

import re
from dataclasses import dataclass
from typing import Dict, List

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

# Words that imply ownership/seniority or named credentials/tools.
_INFLATION = {
    "led", "lead", "leading", "managed", "owned", "ownership", "spearheaded",
    "directed", "headed", "oversaw", "supervised", "architected", "principal",
    "senior", "expert", "certified", "pmp", "six sigma", "green belt",
    "black belt", "p.e.", "solidworks", "catia", "ansys", "abaqus", "autocad",
    "creo", "matlab", "simulink", "labview", "python", "sql", "fea", "cfd",
    "gd&t", "plc", "iso 9001", "as9100", "fmea", "spc",
}
_NUM = re.compile(r"\$?\d[\d,]*(?:\.\d+)?[KkMmBb]?%?")


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
    if skill.lower() not in text.lower():
        text += f" using {skill}"
    if result:
        text += f", {result.rstrip('.')}"
    return text[0].upper() + text[1:].rstrip(".") + "."


def find_unsupported_claims(bullet: str, evidence: BulletEvidence) -> List[str]:
    """Return numbers and inflation terms in `bullet` that the evidence lacks."""
    source = " ".join(
        _clean(x) for x in (evidence.skill, evidence.action, evidence.context, evidence.result)
    ).lower()
    src_nums = {m.rstrip(".,").lower() for m in _NUM.findall(source)}
    flagged: List[str] = []
    for m in _NUM.findall(bullet):
        tok = m.rstrip(".,")
        if tok.lower() not in src_nums and tok not in flagged:
            flagged.append(tok)
    low = bullet.lower()
    for term in sorted(_INFLATION):
        pat = r"(?<![\w&])" + re.escape(term) + r"(?![\w&])"
        if re.search(pat, low) and not re.search(pat, source):
            flagged.append(term)
    return flagged


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
