# ruff: noqa
# NON-PRODUCTION simulation, used for the 2026-11-10 figures. Not engine code.
# Read-only: independent minimal pairs (wrapped in an Experience section) and document-level safety probes under SI-b.
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, ".")
import sim_restricted_b  # patches segment
import sim_restricted as R
def states(text):
    cls, flags = R.classify(text)
    return R.skill_states(cls), flags
items = json.load(open(sys.argv[1], encoding="utf8"))["items"]
c = collections.Counter(); crit = []
for it in items:
    st, flags = states("Experience\n- " + it["text"])
    blocked = any(f in ("backref_negation", "heading_cue_section", "unscoped_disclaimer") for f in flags)
    for sk, gold in it["labels"].items():
        one = R.disambiguate(R.find_mentions(tuple(l for s in R.segment(sk, "resume") for l in s.lines)))
        e = st.get(one[0].canonical) if one else None
        if e is None: o = "not-recognised"
        elif gold == "ambiguous": o = "ambiguous-" + ("unresolved" if e in ("unresolved", "contradicted") or blocked else "decided:" + e)
        elif e == "found" and gold != "affirmed": o = "CRITICAL" + (" (doc withheld)" if blocked else ""); crit.append((it["id"], sk, gold, blocked))
        elif e == "found": o = "correct"
        elif e in ("unresolved", "contradicted"): o = "unresolved/" + ("loss" if gold == "affirmed" else "safe")
        elif e == gold: o = "correct"
        else: o = "incorrect"
        c[(it["group"], o)] += 1
for k in sorted(c): print(k, c[k])
print("critical:", crit)
P = {
 "skills bare + later 'Never used it professionally.'": "Skills\nSolidWorks, Python\nExperience\n- Never used it professionally.",
 "skills (learning)": "Skills\nSolidWorks (learning), Python",
 "skills (in progress)": "Skills\nSolidWorks (in progress)",
 "skills 'SolidWorks - none'": "Skills\nSolidWorks - none",
 "skills, disclaimer on next line": "Skills\nSolidWorks, Creo\nNot yet used professionally",
 "heading 'Skills I lack'": "Skills I lack\n- SolidWorks",
 "heading 'Areas for growth'": "Areas for growth\n- SolidWorks",
 "heading 'Currently learning'": "Currently learning\n- MATLAB",
 "heading 'Missing skills'": "Missing skills\n- SolidWorks",
 "exp 'Have not yet used SolidWorks'": "Experience\n- Have not yet used SolidWorks",
 "exp 'Python was not used'": "Experience\n- Python was not used",
 "exp curly 'Haven\u2019t used SolidWorks'": "Experience\n- Haven\u2019t used SolidWorks",
 "exp 'Learning: PLC'": "Experience\n- Learning: PLC",
 "exp 'MATLAB certification in progress'": "Experience\n- MATLAB certification in progress",
 "exp separate-line backref": "Experience\n- Designed brackets in SolidWorks\n- Never touched it since 2019",
 "exp backref 'I have never used it.'": "Experience\n- SolidWorks. I have never used it.",
 "exp 'SolidWorks? Nope.'": "Experience\n- SolidWorks? Nope.",
 "exp comma list after negation": "Experience\n- Never used Creo, Foobar, SQL",
 "exp 'every CAD tool except SolidWorks'": "Experience\n- Used every CAD tool except SolidWorks",
 "exp 'Cannot use Python'": "Experience\n- Cannot use Python",
 "exp 'Have yet to use MATLAB'": "Experience\n- Have yet to use MATLAB",
 "exp 'Unable to use Python'": "Experience\n- Unable to use Python",
 "exp '0 years of SQL'": "Experience\n- 0 years of SQL experience",
 "summary 'No CAD experience' + skills SolidWorks": "Summary\nNo professional CAD experience yet\nSkills\nSolidWorks",
 "skills under 'Familiar with' prefix": "Skills\nFamiliar with: SolidWorks",
 "skills 'SolidWorks (planned)'": "Skills\nSolidWorks (planned)",
 "skills 'SolidWorks (2027)'": "Skills\nSolidWorks (expected 2027)",
 "skills 'SolidWorks (academic only)'": "Skills\nSolidWorks (academic only)",
 "skills 'Tools I want to learn: SolidWorks'": "Skills\nTools I want to learn: SolidWorks",
 "interests section": "Interests\n- SolidWorks",
 "OK exp 'Designed brackets in SolidWorks'": "Experience\n- Designed brackets in SolidWorks",
 "OK skills 'SQL, basic'": "Skills\nSQL (basic), Python",
}
print("\nPROBES (found = counted present):")
for k, t in P.items():
    st, flags = states(t)
    blocked = any(f in ("backref_negation", "heading_cue_section", "unscoped_disclaimer") for f in flags)
    print(f"  {k:52} {st} {'[doc withheld: ' + ','.join(flags) + ']' if blocked else ''}")
