# ruff: noqa
# NON-PRODUCTION. Read-only simulation of contract v4 revision 4 (confirmation-first, owner rulings R1-R7 and F1-F5). Not engine code.
# Differences from sim_supported_v6.py (revision 3):
#   R1/M2  a cue inside a recognised skill alias is not a cue (the unit cue test and the heading cue test both run
#          with skill spans blanked);
#   R1/M3  in a Skills entry, one of the nine category names from data/keywords.json directly followed by ":" is allowed;
#   F4     structural safeguards (final rulings): "[", "]", "*" and ">" are not separators, so a checkbox is not a
#          Skills entry; and a Skills section is supported only if every unit in it is a Skills entry, otherwise no
#          unit in that section qualifies as a Skills entry (cause: unsupported_form);
#   R6/R7  a résumé never makes a skill count. It yields a suggestion per skill: "suggested" (every mention affirmed)
#          or "unresolved". Every required or preferred skill is prompted; only an explicit "yes" counts.
# Importing this module patches sim_supported_v6.analyse, so the v6 harness functions run the revision 4 rule.
# Run from the repo root at fa1555e:  python <this file> [dir holding sealed_r7/ and sealed_r8/]
import sys, re, os, json, glob, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ".")
import sim_supported_v6 as X
V = X.V
CATEGORIES = sorted({s["category"].lower().replace("_", " ") for s in json.load(open("data/keywords.json", encoding="utf8"))["skills"]})
SEPARATORS = X.SEPARATORS - set("[]*>")
CAT_LABEL = re.compile(r"(?<![a-z0-9'])(?:" + "|".join(re.escape(c) for c in sorted(CATEGORIES, key=len, reverse=True)) + r"):")


def blank_skills(ln, ms):
    t = list(V.norm(ln.text))
    for m in ms:
        for i in range(m.span[0] - ln.start, m.span[1] - ln.start): t[i] = " "
    return "".join(t)


def skills_entry(ln, ms):
    """Only known skill names, separators, approved level words and category labels in the unit."""
    if not ms: return False
    rest = CAT_LABEL.sub(" ", X.MARKER.sub(" ", blank_skills(ln, ms)).replace("_", " ")).replace("working knowledge", " ")
    return all(w in X.LEVEL or w == "and" for w in re.findall(r"[a-z0-9']+", rest)) and \
        all(c in SEPARATORS for c in re.sub(r"[a-z0-9']+", "", rest))


def analyse(resume):
    """-> (mentions [(Mention, unit Line, status, cause, cues)], doc triggers, {skill: suggestion}, {skill: causes}).
    Mention status is "affirmed" (supported form, no cue) or "unresolved". Suggestion is "suggested" or "unresolved"."""
    ments, trig = [], set()
    us = [(ln, sec, X.disambiguate(X.find_mentions((ln,)))) for ln, sec in X.units(resume)]
    unclean = {sec for ln, sec, ms in us if ln.section == "skills" and not skills_entry(ln, ms)}
    for s in X.segment(resume, "resume"):
        if not s.heading: continue
        h = X.Line(s.heading, 0, len(s.heading), s.kind, None, False)
        if V.cues_in(blank_skills(h, X.disambiguate(X.find_mentions((h,)))), V.CUES): trig.add("heading_cue_section")
    for ln, sec, ms in us:
        cues = V.cues_in(blank_skills(ln, ms), V.CUES)
        entry = ln.section == "skills" and sec not in unclean  # every unit of a clean Skills section is an entry
        verb = X.first_word(ln) in X.VERBS and ln.section != "excluded"
        for m in ms:
            if cues: ments.append((m, ln, "unresolved", "cue_line", cues))
            elif entry: ments.append((m, ln, "affirmed", "skills_entry", cues))
            elif verb: ments.append((m, ln, "affirmed", "experience_line", cues))
            else: ments.append((m, ln, "unresolved", "unsupported_form", cues))
        names = [m.alias.lower() for m in ms]
        for sent in re.split(r"[.;?!]", ln.text):
            st = V.tokens(sent)
            if not st or (ms and any(a in V.norm(sent) for a in names)): continue
            if V.cues_in(sent, V.NEG_DOC) and (V.BACKREF & set(st) or any(V.cues_in(sent, [" ".join(b)]) for b in V.BACKREF2) or len(st) <= 4):
                trig.add("backref_negation")
        if not ms and V.cues_in(ln.text, V.NEG_DOC) and V.POSSESS & set(V.tokens(ln.text)): trig.add("unscoped_disclaimer")
    sugg, causes = {}, collections.defaultdict(set)
    for m, _, st, cause, _ in ments:
        if st == "unresolved": causes[m.canonical].add(cause)
        sugg[m.canonical] = "unresolved" if (trig or st == "unresolved" or sugg.get(m.canonical) == "unresolved") else "suggested"
    for k in sugg:
        if trig: causes[k].add("document_trigger")
    return ments, trig, sugg, causes


def affirmed_view(resume):
    """The v6 harness compares against the literal "affirmed"; map "suggested" to it."""
    ments, trig, sugg, causes = analyse(resume)
    return ments, trig, {k: ("affirmed" if v == "suggested" else v) for k, v in sugg.items()}, causes


X.analyse = affirmed_view

# Ten examples of the three known patterns (contract §11). The résumé suggests "yes" for a skill it disclaims.
# Under revision 4 that is a wrong suggestion, not a counted skill: nothing counts without the user's "yes".
RISK = {
    "paragraph: tools not part of my job": ("Skills\nPython, MATLAB\n\nListed tools were not part of my job.\n", ["Python", "MATLAB"]),
    "paragraph: only in a single class": ("Skills\nSolidWorks\n\nNever touched SW on the job, only in a single class.\n", ["SolidWorks"]),
    "paragraph: all self-taught": ("Skills\nPython, SQL\n\nAll self-taught; nothing professional.\n", ["Python", "SQL"]),
    "paragraph: done by a teammate": ("Experience\n- Designed brackets in SolidWorks\n\nThe CAD work above was done by a teammate.\n", ["SolidWorks"]),
    "checkbox: unchecked": ("Skills\n- [ ] MATLAB\n- [x] Python\n", ["MATLAB"]),
    "punctuation: MATLAB: -": ("Skills\nMATLAB: -", ["MATLAB"]),
    "punctuation: MATLAB (*)": ("Skills\nMATLAB (*)", ["MATLAB"]),
    "limited: once in a class": ("Experience\n- Used SolidWorks once in a class", ["SolidWorks"]),
    "limited: managed a team": ("Experience\n- Managed a team that used SolidWorks", ["SolidWorks"]),
    "limited: completed a tutorial": ("Experience\n- Completed a SolidWorks tutorial", ["SolidWorks"]),
}
LABELS = {  # R1/M3 and R1/M2 checks: text -> expected suggestion per skill
    "Skills\nCAD: SolidWorks, Creo": {"SolidWorks": "suggested", "Creo": "suggested"},
    "Skills\nCAD: SolidWorks, Creo\nProgramming: Python (advanced)": {"SolidWorks": "suggested", "Creo": "suggested", "Python": "suggested"},
    "Skills\nPlanned: SolidWorks": {"SolidWorks": "unresolved"},
    "Skills\nWishlist: SolidWorks, Creo": {"SolidWorks": "unresolved", "Creo": "unresolved"},
    "Skills\nCAD (planned): SolidWorks": {"SolidWorks": "unresolved"},
    "Skills\nMachine Learning, Python": {"Machine Learning": "suggested", "Python": "suggested"},
    "Skills\nLearning Machine Learning, Python": {"Machine Learning": "unresolved", "Python": "unresolved"},
    "Experience\n- Built a machine learning model in Python": {"Machine Learning": "suggested", "Python": "suggested"},
    "Experience\n- Design brackets in SolidWorks": {"SolidWorks": "unresolved"},
    "Machine Learning:\n- Built a model in Python\n\nSkills\nSolidWorks": {"Python": "suggested", "SolidWorks": "suggested"},
    "Currently Learning:\n- Built a model in Python": {"Python": "unresolved"},
    "Skills\nCAD : SolidWorks": {"SolidWorks": "unresolved"},
    "Skills\nSoft skills: Root Cause Analysis": {"Root Cause Analysis": "suggested"},
    "Skills\n- [ ] MATLAB\n- [x] Python": {"MATLAB": "unresolved", "Python": "unresolved"},
    "Skills\n- SolidWorks\n- Python (in progress)": {"SolidWorks": "unresolved", "Python": "unresolved"},
    "Skills\nSolidWorks, Creo\n\nListed tools were not part of my job.": {"SolidWorks": "unresolved", "Creo": "unresolved"},
    "Skills\n- SolidWorks\n- Python\n\nExperience\n- Wrote test scripts in Python": {"SolidWorks": "suggested", "Python": "suggested"},
}


def confirm(dirs):
    """Confirmation-first figures for one set."""
    c = collections.Counter(); prompts, wrong = [], []
    for d in dirs:
        for f in sorted(glob.glob(d + "/*.json")):
            fx = json.load(open(f, encoding="utf8")); e = fx["expected"]; gold = set(e.get("found", []))
            sugg = analyse(fx["resume_text"])[2]
            rp = set(e.get("required", [])) | set(e.get("preferred", []))
            for s in rp | set(e.get("unscored", [])):
                if sugg.get(s) == "suggested" and s not in gold: wrong.append((fx["id"], s))
            if not rp: c["pairs_unavailable"] += 1; continue
            c["pairs"] += 1; prompts.append(len(rp))
            for s in rp:
                k = sugg.get(s, "no_mention")
                c["prompt:" + k] += 1; c[f"prompt:{k}:gold_{'yes' if s in gold else 'no'}"] += 1
            # counted without any answer: nothing. Counted after the oracle answers: exactly the gold-found scored skills.
            c["counted_without_confirmation"] += 0
    return c, prompts, wrong


if __name__ == "__main__":
    sets = {"postings": ["tests/fixtures/postings"], "regression_r6": ["tests/fixtures/regression_r6"]}
    if len(sys.argv) > 1: sets.update({"r7": [sys.argv[1] + "/sealed_r7"], "r8": [sys.argv[1] + "/sealed_r8"]})
    allp, realp, tot = [], [], collections.Counter()
    for k, v in sets.items():
        out, _, crit, _ = X.history(v)
        c, prompts, wrong = confirm(v); allp += prompts; tot += c
        if k != "postings": realp += prompts
        keep = {a: b for a, b in sorted(out.items()) if a.startswith(("mention:", "resumes", "trigger:"))}
        print(f"== {k}: {keep}\n   confirmation: {dict(sorted(c.items()))}\n   prompts per pair: median {statistics.median(prompts)}, max {max(prompts)}"
              f"\n   wrong suggestions (suggested yes, gold not found): {wrong}\n   disclaimed mention or skill left in supported form: {crit}")
    print(f"ALL: pairs {tot['pairs']}; prompts per pair median {statistics.median(allp)}, max {max(allp)}; "
          f"prompts suggested {tot['prompt:suggested']}, unresolved {tot['prompt:unresolved']}, no mention {tot['prompt:no_mention']}")
    if realp: print(f"REALISTIC (r6-r8): n={len(realp)}, prompts per pair median {statistics.median(realp)}, max {max(realp)}")
    c = collections.Counter()
    for it in json.load(open(os.path.join(X.HERE, "minimal_pairs_zero_pronoun.json"), encoding="utf8"))["items"]:
        sugg = analyse(it["text"])[2]
        for sk, gold in it["labels"].items():
            one = X.disambiguate(X.find_mentions(tuple(l for s_ in X.segment(sk, "resume") for l in s_.lines)))
            e = sugg.get(one[0].canonical) if one else None
            c["not-recognised" if e is None else "WRONG SUGGESTION" if e == "suggested" and gold != "affirmed" else
              "suggested, gold affirmed" if e == "suggested" else "unresolved, gold " + ("affirmed" if gold == "affirmed" else "not affirmed")] += 1
    print("independent pairs:", dict(c))
    for name, table in (("32 probes", {k: (t, X.DISCLAIMED[k]) for k, t in X.P.items()}), ("16 hard-wrap probes", X.WRAP), ("10 known-pattern examples", RISK)):
        b = X.probes(table)
        print(f"{name}: wrong suggestions {sum(bool(h) for _, h, _ in b)} of {len(table)}: {[n for n, h, _ in b if h]}")
    bad = {t: analyse(t)[2] for t, exp in LABELS.items() if analyse(t)[2] != exp}
    print(f"label and skill-name checks: {len(LABELS) - len(bad)} of {len(LABELS)} as expected; unexpected: {bad}")
    print("category labels:", CATEGORIES)
