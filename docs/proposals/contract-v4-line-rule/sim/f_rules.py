# ruff: noqa
# NON-PRODUCTION simulation, used for the 2026-11-10 figures. Not engine code.
# Proposed F1-F3 rules (revised after synthetic validation). Read-only prototype, not engine code.
import re
from engine.match_stages import segment, find_mentions, disambiguate, Line
STOP = set("the and of to in a for with on as is are be by or at an we you our your will from this that".split())
CONTACT = re.compile(r"@|https?://|www\.|\.(com|org|net|io)\b|linkedin|github|\d{3}[-. ]\d{4}|^[A-Z][a-z]+(?: [A-Z][a-z]+)?, [A-Z]{2}$")
WORD = re.compile(r"[^\W\d_]+")
def is_bullet(l): return bool(re.match(r"\s*([-•*·▪●–]|\d+[.)])\s", l))
def one_skill(l):
    ms = disambiguate(find_mentions((Line(l, 0, len(l), "unknown", None, False),)))
    return len(ms) == 1 and len(l.split()) <= 3
def is_list(l): return l.count(",") + l.count(";") + l.count("|") >= len(l.split()) / 3  # a comma-separated list, not prose
def F(t, doc):
    ls = [l.strip() for l in t.splitlines() if l.strip()]
    secs = segment(t, doc); heads = {s.heading for s in secs if s.heading}
    codes = []
    if doc == "resume" and not any(is_bullet(l) for l in ls) and not heads and len(ls) <= 3 and max(len(l.split()) for l in ls if not is_list(l)) >= 40 if any(not is_list(l) for l in ls) else False:
        codes.append("F1")
    short = [l for l in ls if len(l.split()) <= 2 and not is_bullet(l) and not one_skill(l) and l not in heads and not CONTACT.search(l)]
    if len(ls) >= 12 and len(short) / len(ls) >= 0.6:
        codes.append("F2")
    letters = "".join(WORD.findall(t)); prose = [x for l in ls if len(l.split()) >= 8 and not is_list(l) for x in WORD.findall(l)]
    if (len(letters) >= 200 and sum(not c.isascii() for c in letters) / len(letters) > 0.05) or \
       (len(prose) >= 40 and sum(x.lower() in STOP for x in prose) / len(prose) < 0.08):
        codes.append("F3")
    return codes
