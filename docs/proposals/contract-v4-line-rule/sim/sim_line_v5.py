# ruff: noqa
# NON-PRODUCTION simulation, used for the 2026-11-10 figures. Not engine code.
# Read-only simulation of contract v4 (line rule, revised 2026-11-10). Prints no résumé text except cue words.
# Résumé only: normalise (curly->straight apostrophes, lowercase), whole-token cue match on the raw logical line;
# any cue -> every skill on the line unresolved. S2 aggregation. Three document triggers -> all résumé findings unresolved.
import sys, re, json, glob, statistics, collections, os
sys.path.insert(0, ".")
from engine.match_stages import segment, find_mentions, disambiguate, _qualify
D = json.load(open("data/match_rules.json"))
BASE = [w.lower() for w in D["negation"] + D["hypothetical"]]
ADDED = ["n't", "cannot", "unable", "zero", "0", "lack", "unfamiliar", "except", "only", "learning", "studying",
         "familiar", "exposure", "coursework", "hobby"]
NEG_DOC = [w.lower() for w in D["negation"]] + ["n't", "cannot", "unable", "zero", "0", "lack", "unfamiliar", "nor", "neither", "nope"]
BACKREF = {"it", "them", "this", "that", "these", "those", "either", "neither", "one"}
BACKREF2 = [("any", "of"), ("the", "other"), ("by", "me")]
POSSESS = {"experience", "experienced", "used", "use", "using", "familiar", "familiarity", "knowledge", "worked",
           "exposure", "proficient", "proficiency", "trained", "skill", "skills", "background", "hands-on"}
TOKEN = re.compile(r"[a-z0-9]+(?:[-.,'][a-z0-9]+)*'?[a-z]*")

def norm(t): return t.replace("\u2019", "'").replace("\u2018", "'").replace("\u02bc", "'").lower()
def tokens(t): return TOKEN.findall(norm(t))
def cues_in(text, cueset):
    tk = tokens(text); found = set()
    for c in cueset:
        if c == "n't":
            if any(t.endswith("n't") for t in tk): found.add(c)
            continue
        cs = c.split()
        for i in range(len(tk) - len(cs) + 1):
            if tk[i:i + len(cs)] == cs: found.add(c); break
    return found

CUES = BASE + ADDED
def analyse(resume, cueset=None):
    """-> (per-mention list [(canonical, line_text, unresolved?, cues)], doc_triggers, skill_state dict)"""
    cueset = cueset or CUES
    secs = segment(resume, "resume"); ments = []; trig = set()
    for sec in secs:
        if sec.heading and cues_in(sec.heading, cueset): trig.add("heading_cue_section")
        for ln in sec.lines:
            ms = disambiguate(find_mentions((ln,)))
            c = cues_in(ln.text, cueset)
            for m in ms: ments.append((m, ln.text, bool(c), c))
            names = [m.alias.lower() for m in ms]
            for sent in re.split(r"[.;?!]", ln.text):
                st = tokens(sent)
                if not st or (ms and any(a in norm(sent) for a in names)): continue
                if cues_in(sent, NEG_DOC) and (BACKREF & set(st) or any(cues_in(sent, [" ".join(b)]) for b in BACKREF2) or len(st) <= 4):
                    trig.add("backref_negation")
            if not ms and cues_in(ln.text, NEG_DOC) and POSSESS & set(tokens(ln.text)):
                trig.add("unscoped_disclaimer")
    state = {}
    for m, _, unres, _ in ments:
        state[m.canonical] = "unresolved" if (trig or unres or state.get(m.canonical) == "unresolved") else "affirmed"
    return ments, trig, state

def tiers(fx):
    e = fx["expected"]; return set(e.get("required", [])) | set(e.get("preferred", [])), set(e.get("unscored", []))

def history(dirs):
    out = collections.Counter(); prompts = []; crit = []; mism = []; per_cue = collections.Counter(); sole = collections.Counter()
    for d in dirs:
        for f in sorted(glob.glob(d + "/*.json")):
            fx = json.load(open(f, encoding="utf8")); fid = fx["id"]
            ments, trig, state = analyse(fx["resume_text"])
            for m, txt, unres, c in ments:
                base_unres = bool(cues_in(txt, BASE))
                if unres and not base_unres:
                    add = c - set(BASE)
                    for x in add: per_cue[x] += 1
                    if len(add) == 1: sole[next(iter(add))] += 1
            rp, uns = tiers(fx); gold_found = set(fx["expected"].get("found", []))
            for s, st in state.items():
                if st == "affirmed" and s in (rp | uns) and s not in gold_found: crit.append((fid, s, "skill"))
            # mention-level gold
            for lab in fx.get("mention_labels", []):
                if lab["doc"] != "resume": continue
                ms = [x for x in ments if x[0].canonical == lab["canonical"] and lab["line_contains"] in x[1]]
                if not ms: continue
                if lab["status"] != "affirmed" and any(not (u or trig) for _, _, u, _ in ms): crit.append((fid, lab["canonical"], "mention"))
            if not rp: out["unavailable"] += 1; continue
            unresolved_rp = sorted(s for s in rp if state.get(s) == "unresolved")
            prompts.append(len(unresolved_rp))
            out["scored_before" if not unresolved_rp else "withheld_before"] += 1
            if trig: out["doc_trigger_pairs"] += 1
            final = {s for s in rp if state.get(s) == "affirmed"} | {s for s in unresolved_rp if s in gold_found}
            if final != (rp & gold_found): mism.append((fid, sorted(final ^ (rp & gold_found))))
            out["scored_after"] += 1
    return out, prompts, crit, mism, per_cue, sole

if __name__ == "__main__":
    S = sys.argv[1]
    sets = {"postings": ["tests/fixtures/postings"], "regression_r6": ["tests/fixtures/regression_r6"], "r7": [S + "/sealed_r7"], "r8": [S + "/sealed_r8"]}
    allp = []; tot_cue = collections.Counter(); tot_sole = collections.Counter()
    for k, v in sets.items():
        out, prompts, crit, mism, pc, so = history(v); allp += prompts; tot_cue += pc; tot_sole += so
        print(f"== {k}: {dict(out)}; prompts median {statistics.median(prompts) if prompts else 0}, max {max(prompts) if prompts else 0}")
        print(f"   critical: {crit}")
        print(f"   after-confirmation found-set mismatches vs gold: {mism}")
    print(f"ALL pairs prompts: median {statistics.median(allp)}, max {max(allp)}, n={len(allp)}")
    print("added-cue unresolved mentions (any / sole cause):", {c: (tot_cue[c], tot_sole[c]) for c in ADDED})
    # independent pairs
    items = json.load(open(S + "/minimal_pairs_zero_pronoun.json", encoding="utf8"))["items"]
    c = collections.Counter(); crit = []; pc = collections.Counter()
    for it in items:
        ments, trig, state = analyse(it["text"])
        for m, txt, unres, cs in ments:
            if unres and not cues_in(txt, BASE):
                for x in cs - set(BASE): pc[x] += 1
        for sk, gold in it["labels"].items():
            one = disambiguate(find_mentions(tuple(l for s_ in segment(sk, "resume") for l in s_.lines)))
            e = state.get(one[0].canonical) if one else None
            o = "not-recognised" if e is None else ("CRITICAL" if e == "affirmed" and gold in ("negated", "hypothetical") else
                 "correct" if e == "affirmed" and gold == "affirmed" else "unresolved/" + ("loss" if gold == "affirmed" else "safe") if e == "unresolved" else "other")
            c[(it["group"], o)] += 1
            if o == "CRITICAL": crit.append((it["id"], sk))
    print("independent pairs:", dict(c), "critical:", crit, "added-cue hits:", dict(pc))
