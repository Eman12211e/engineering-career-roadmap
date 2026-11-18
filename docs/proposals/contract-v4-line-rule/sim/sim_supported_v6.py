# ruff: noqa
# NON-PRODUCTION. Read-only simulation of contract v4 revision 3 (supported-form default). Not engine code.
# Résumé only. A skill is affirmed only in a supported form (Skills entry or Experience line), otherwise unresolved.
# Unit = whole bullet or paragraph after unwrapping. Document triggers and S2 aggregation as in revision 2.
# Run from the repo root at fa1555e:  python <this file> <dir holding sealed_r7/ and sealed_r8/>   (omit to skip them)
import sys, re, os, json, glob, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ".")
import sim_line_v5 as V
from engine.match_stages import Line, segment, find_mentions, disambiguate, _is_bullet

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_HEADINGS = ["skills", "technical skills", "key skills", "core competencies", "tools", "technologies", "skills and tools"]
EXPERIENCE_HEADINGS = ["experience", "work experience", "professional experience", "employment history", "projects",
                       "relevant experience", "engineering experience"]  # used only by the REQUIRE_EXP_HEADING variant
LEVEL = ["basic", "beginner", "novice", "intermediate", "advanced", "proficient", "expert", "working knowledge"]
SEPARATORS = set(" \t\r\n,;|/&()[]:.-–—•·▪◦*>")
# Written once, before any run, from general résumé convention; not tuned to the fixtures afterwards. Past tense only.
VERBS = set("""designed developed built led managed implemented created analyzed analysed tested validated verified
programmed automated modeled modelled simulated fabricated machined assembled installed commissioned calibrated
maintained operated performed conducted executed delivered produced improved reduced increased optimized optimised
streamlined integrated deployed configured debugged troubleshot diagnosed repaired inspected measured documented
drafted wrote authored reviewed supervised mentored taught coordinated launched engineered prototyped wired welded
coded scripted migrated upgraded redesigned refactored established generated completed achieved applied used
utilized utilised ran""".split())
MARKER = re.compile(r"^\s*(?:[•·▪◦\-*–—>]|(?:\d{1,3}|[A-Za-z])[.)])\s+")
REQUIRE_EXP_HEADING = os.environ.get("REQUIRE_EXP_HEADING") == "1"


def units(resume):
    """[(Line, section index)]. A unit starts at a list marker, after a heading or after a blank line; every other
    physical line merges into the unit before it (merge when the boundary is in doubt)."""
    heads = {s.heading_span: s for s in segment(resume, "resume") if s.heading_span}
    out, cur, kind, heading, sec, pos = [], None, "unknown", None, 0, 0
    for chunk in resume.split("\n"):
        start = pos + len(chunk) - len(chunk.lstrip()); t = chunk.strip(); pos += len(chunk) + 1
        if not t: cur = None; continue
        end = start + len(t)
        if (start, end) in heads:
            s = heads[(start, end)]; kind, heading, sec, cur = s.kind, s.heading, sec + 1, None; continue
        if cur is not None and not _is_bullet(t): cur[1] = end; continue
        cur = [start, end, kind, heading, _is_bullet(t), sec]; out.append(cur)
    return [(Line(resume[a:b], a, b, k, h, bul), sec) for a, b, k, h, bul, sec in out]


def skills_entry(ln, ms):
    """Only known skill names, separators and approved level words in the unit."""
    if not ms: return False
    t = list(V.norm(ln.text))
    for m in ms:
        for i in range(m.span[0] - ln.start, m.span[1] - ln.start): t[i] = " "
    rest = MARKER.sub(" ", "".join(t)).replace("working knowledge", " ")
    return all(w in LEVEL or w == "and" for w in re.findall(r"[a-z0-9']+", rest)) and \
        all(c in SEPARATORS for c in re.sub(r"[a-z0-9']+", "", rest))


def first_word(ln):
    tk = V.tokens(MARKER.sub("", ln.text)); return tk[0] if tk else ""


def analyse(resume):
    """-> (mentions [(Mention, unit Line, state, cause, cues)], doc triggers, {skill: state}, {skill: causes})."""
    ments, trig, closed = [], set(), set()
    us = units(resume)
    for s in segment(resume, "resume"):
        if s.heading and V.cues_in(s.heading, V.CUES): trig.add("heading_cue_section")
    for ln, sec in us:
        ms = disambiguate(find_mentions((ln,)))
        cues = V.cues_in(ln.text, V.CUES)
        in_skills = ln.section == "skills" and sec not in closed
        entry = in_skills and skills_entry(ln, ms)
        if in_skills and not entry: closed.add(sec)  # any other line closes the Skills section
        verb = first_word(ln) in VERBS and ln.section != "excluded" and (not REQUIRE_EXP_HEADING or ln.section == "experience")
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
        if not ms and V.cues_in(ln.text, V.NEG_DOC) and V.POSSESS & set(V.tokens(ln.text)):
            trig.add("unscoped_disclaimer")
    state, causes = {}, collections.defaultdict(set)
    for m, _, st, cause, _ in ments:
        if st == "unresolved": causes[m.canonical].add(cause)
        state[m.canonical] = "unresolved" if (trig or st == "unresolved" or state.get(m.canonical) == "unresolved") else "affirmed"
    for k in state:
        if trig: causes[k].add("document_trigger")
    return ments, trig, state, causes


def history(dirs):
    out = collections.Counter(); prompts, crit, mism = [], [], []
    for d in dirs:
        for f in sorted(glob.glob(d + "/*.json")):
            fx = json.load(open(f, encoding="utf8")); fid = fx["id"]; e = fx["expected"]
            ments, trig, state, _ = analyse(fx["resume_text"])
            out["resumes"] += 1
            for _, _, st, cause, _ in ments: out["mention:" + (st if st == "affirmed" else cause)] += 1
            if trig: out["resumes_all_unresolved_by_doc_trigger"] += 1
            for t in trig: out["trigger:" + t] += 1
            if state and all(v == "unresolved" for v in state.values()): out["resumes_with_no_affirmed_skill"] += 1
            rp = set(e.get("required", [])) | set(e.get("preferred", [])); gold = set(e.get("found", []))
            for s, st in state.items():
                if st == "affirmed" and s in (rp | set(e.get("unscored", []))) and s not in gold: crit.append((fid, s, "skill"))
            for lab in fx.get("mention_labels", []):
                if lab["doc"] != "resume" or lab["status"] == "affirmed": continue
                if any(st == "affirmed" and not trig for m, ln, st, _, _ in ments
                       if m.canonical == lab["canonical"] and lab["line_contains"] in ln.text): crit.append((fid, lab["canonical"], "mention"))
            if not rp: out["pairs_unavailable"] += 1; continue
            out["pairs_scorable"] += 1
            unres = sorted(s for s in rp if state.get(s) == "unresolved")
            prompts.append(len(unres))
            out["scored_before" if not unres else "withheld_before"] += 1
            final = {s for s in rp if state.get(s) == "affirmed"} | {s for s in unres if s in gold}
            if final != (rp & gold): mism.append((fid, sorted(final ^ (rp & gold))))
            out["scored_after"] += 1
    return out, prompts, crit, mism


# 32 development probes from probe_restricted.py: text -> skills a careful reader would NOT count as demonstrated.
P = __import__("ast").literal_eval(open(os.path.join(HERE, "probe_restricted.py"), encoding="utf8").read().split("P = ", 1)[1].split('\nprint("\\nPROBES', 1)[0])
SW, PY = "SolidWorks", "Python"
DISCLAIMED = dict(zip(P, [
    [SW, PY], [SW], [SW], [SW], [SW, "Creo"], [SW], [SW], ["MATLAB"], [SW], [SW], [PY], [SW], ["PLC Programming"], ["MATLAB"],
    [SW], [SW], [SW], ["Creo", "SQL"], [SW], [PY], ["MATLAB"], [PY], ["SQL"], [SW], [], [SW], [SW], [SW], [SW], [SW], [], []]))
# New in revision 3: a cue and a skill split across a hard wrap. Written by the contract author (not round-9 material).
WRAP = {
    "skill on capitalised continuation": ("Experience\n- Designed fixtures but never used\nSolidWorks", [SW]),
    "cue on capitalised continuation": ("Experience\n- Modelled housings in SolidWorks for a course I\nNever finished", [SW]),
    "back-reference on continuation": ("Experience\n- Shadowed a designer working in SolidWorks; I have\nnever used it myself", [SW]),
    "skills entry, disclaimer on next line": ("Skills\nSolidWorks, Creo, MATLAB\n(none used professionally)", [SW, "Creo", "MATLAB"]),
    "skills, cue line first": ("Skills\nNo experience with\nSolidWorks, Creo", [SW, "Creo"]),
    "skills wrapped, cue on second line": ("Skills\nSolidWorks, Creo,\nPython (learning)", [PY]),
    "new sentence, cue before wrap": ("Experience\n- Built test rigs. No experience with\nPython or MATLAB", [PY, "MATLAB"]),
    "digit-start continuation": ("Experience\n- Programmed PLC ladder logic is something I have\n0 experience with", ["PLC Programming"]),
    "lower-case continuation": ("Experience\n- Completed MATLAB\ncoursework only", ["MATLAB"]),
    "wrap inside a two-word cue": ("Experience\n- Automated reports despite a lack\nof SQL experience", ["SQL"]),
    "cue directly before wrap": ("Experience\n- Wrote test scripts with no\nPython", [PY]),
    "stray list marker on continuation": ("Experience\n- Designed parts without\n- SolidWorks", [SW]),
    "blank line then back-reference": ("Experience\n- Designed brackets in SolidWorks\n\nNever used it professionally.", [SW]),
    "indented continuation": ("Experience\n- Designed brackets, though I have never opened\n    SolidWorks", [SW]),
    "CONTROL wrapped, no cue": ("Experience\n- Designed brackets in\nSolidWorks", []),
    "CONTROL skills on two lines": ("Skills\nSolidWorks, Creo\nPython, MATLAB", []),
}


def probes(table):
    bad = []
    for name, (text, disclaimed) in table.items():
        state = analyse(text)[2]
        hit = sorted(s for s in disclaimed if state.get(s) == "affirmed")
        missing = sorted(s for s in disclaimed if s not in state)
        if hit or missing: bad.append((name, hit, ["not recognised: " + s for s in missing]))
    return bad


if __name__ == "__main__":
    sets = {"postings": ["tests/fixtures/postings"], "regression_r6": ["tests/fixtures/regression_r6"]}
    if len(sys.argv) > 1: sets.update({"r7": [sys.argv[1] + "/sealed_r7"], "r8": [sys.argv[1] + "/sealed_r8"]})
    allp, realp, tot = [], [], collections.Counter()
    for k, v in sets.items():
        out, prompts, crit, mism = history(v); allp += prompts; tot += out
        if k != "postings": realp += prompts
        print(f"== {k}: {dict(sorted(out.items()))}\n   prompts median {statistics.median(prompts)}, max {max(prompts)}\n   critical: {crit}\n   after-confirmation mismatches: {mism}")
    print(f"ALL: scorable {tot['pairs_scorable']}, scored before {tot['scored_before']}, after {tot['scored_after']}; prompts median {statistics.median(allp)}, max {max(allp)}")
    if realp: print(f"REALISTIC (r6-r8): n={len(realp)}, prompts median {statistics.median(realp)}, max {max(realp)}")
    c = collections.Counter(); crit = []
    for it in json.load(open(os.path.join(HERE, "minimal_pairs_zero_pronoun.json"), encoding="utf8"))["items"]:
        state = analyse(it["text"])[2]
        for sk, gold in it["labels"].items():
            one = disambiguate(find_mentions(tuple(l for s_ in segment(sk, "resume") for l in s_.lines)))
            e = state.get(one[0].canonical) if one else None
            o = "not-recognised" if e is None else "CRITICAL" if e == "affirmed" and gold != "affirmed" else \
                "correct" if e == "affirmed" else "unresolved/" + ("loss" if gold == "affirmed" else "safe")
            c[o] += 1
            if o == "CRITICAL": crit.append((it["id"], sk))
    print("independent pairs:", dict(c), "critical:", crit)
    b = probes({k: (t, DISCLAIMED[k]) for k, t in P.items()})
    print(f"32 probes: {len(P)} run, critical false affirmations {sum(bool(h) for _, h, _ in b)}: {b}")
    b = probes(WRAP)
    print(f"hard-wrap probes: {len(WRAP)} run, critical false affirmations {sum(bool(h) for _, h, _ in b)}: {b}")
    for k in ("CONTROL wrapped, no cue", "CONTROL skills on two lines"): print("  ", k, analyse(WRAP[k][0])[2])
