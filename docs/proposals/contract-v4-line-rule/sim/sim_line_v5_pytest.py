# ruff: noqa
# NON-PRODUCTION simulation, used for the 2026-11-10 figures. Not engine code.
# Read-only: existing suite with the v4 line rule (line cues only; doc triggers need whole-document context) patched in memory.
import os, sys, dataclasses
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, ".")
import sim_line_v5 as V
import engine.match_stages as ms, engine.job_match as jm
orig = ms._qualify
def q(m, doc):
    if doc != "resume": return orig(m, doc)
    return dataclasses.replace(m, status="uncertain" if V.cues_in(m.line.text, V.CUES) else "affirmed")
ms._qualify = q; jm._qualify = q
import pytest
sys.exit(pytest.main(["-q", "-p", "no:cacheprovider", "tests", "-rf", "--tb=no"]))
