# ruff: noqa
# NON-PRODUCTION simulation, used for the 2026-11-10 figures. Not engine code.
# Read-only: owner line rule. Résumé only: any cue from the fa1555e `negation` or `hypothetical` data lists anywhere in the
# line (whole word, case-insensitive, checked on the raw line before any splitting) -> every skill on the line "uncertain".
# No scope resolution. Postings untouched.
import sys, re, json, dataclasses
sys.path.insert(0, ".")
import engine.match_stages as ms, engine.job_match as jm
orig = ms._qualify
D = json.load(open("data/match_rules.json"))
CUE = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in sorted(D["negation"] + D["hypothetical"], key=len, reverse=True)) + r")\b", re.I)
def q(m, doc):
    if doc != "resume": return orig(m, doc)
    return dataclasses.replace(m, status="uncertain") if CUE.search(m.line.text) else orig(m, doc)
ms._qualify = q; jm._qualify = q
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["-q", "-p", "no:cacheprovider", "tests", "-rf", "--tb=no"]))
