# ruff: noqa
# NON-PRODUCTION. Read-only: runs the existing suite with contract v4 revision 3 patched in memory (nothing is written).
# Résumé side only: segment() returns units, _qualify() returns affirmed/unresolved at mention level (document triggers
# included), and match_posting() applies S2 (a skill counts only if all its mentions are affirmed).
# Run from the repo root at fa1555e:  python <this file> [pytest args]
import os, sys, dataclasses
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ".")
import sim_supported_v6 as X
import engine.match_stages as ms
orig_segment, orig_qualify = ms.segment, ms._qualify
TABLE, SKILL = {}, {}

def load(text):
    ments, trig, state, _ = X.analyse(text)
    TABLE.clear(); SKILL.clear(); SKILL.update(state)
    for m, ln, st, _, _ in ments: TABLE[(ln, m.span)] = "unresolved" if trig else st

def segment(text, doc):
    secs = orig_segment(text, doc)
    if doc != "resume": return secs
    load(text)
    by = {}
    for ln, i in X.units(text): by.setdefault(i, []).append(ln)
    out, i = [], 0
    for s in secs:
        if s.heading_span: i += 1
        out.append(dataclasses.replace(s, lines=tuple(by.get(i, ()))))
    return tuple(out)

def q(m, doc):
    if doc != "resume": return orig_qualify(m, doc)
    if (m.line, m.span) not in TABLE:  # a hand-built Line: treat its text as a one-unit document
        return dataclasses.replace(m, status=X.analyse(m.line.text)[2].get(m.canonical, "unresolved"))
    return dataclasses.replace(m, status=TABLE[(m.line, m.span)])

ms.segment, ms._qualify = segment, q
import engine.job_match as jm
orig_mentions = jm._mentions
jm._mentions = lambda text, doc: [p for p in orig_mentions(text, doc) if doc != "resume" or SKILL.get(p[0].canonical) == "affirmed"]
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["-q", "-p", "no:cacheprovider", "tests", "-rf", "--tb=no", *sys.argv[1:]]))
