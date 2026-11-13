# ruff: noqa
# NON-PRODUCTION simulation, used for the 2026-11-10 figures. Not engine code.
# Read-only feasibility simulation of the supported-input MVP (SI-rules). Nothing is written; no user text is printed.
import os, sys, re, json, glob, collections
sys.path.insert(0, ".")
import engine.match_stages as ms
from engine.match_stages import segment, find_mentions, disambiguate, _qualify, _norm, norm_span
from scripts.evaluate_matching import _resolve
sys.path.insert(0, os.path.dirname(__file__))
from f_rules import F

D = json.load(open("data/match_rules.json"))
EXTRA = ["nor", "neither", "unfamiliar", "except", "other than", "apart from", "excluding", "everything but",
         "anything but", "all but", "in progress", "enrolled", "n/a", "not used", "zero", "cannot", "unable",
         "yet to", "lack", "missing", "gaps", "pending", "planned", "expected", "self-study", "self-taught",
         "pursuing", "studying", "learning", "training in", "coursework in progress", "nope"]
CUES = sorted(set(D["negation"] + D["hypothetical"] + EXTRA), key=len, reverse=True)
CUE = re.compile(r"(?:\b(?:" + "|".join(re.escape(w) for w in CUES) + r")\b|\b\w+n't\b)(?![\w-])", re.I)
NEGSTART = re.compile(r"(?:\b(?:" + "|".join(re.escape(w) for w in D["negation"] + ["nor", "neither", "nope", "zero", "cannot", "unable", "unfamiliar"]) + r")\b|\b\w+n't\b)", re.I)
BACKREF = re.compile(r"\b(it|them|this|that|these|those|either|neither|one|any of|the other|by me)\b", re.I)
LEVEL = re.compile(r"\b(basic|beginner|intermediate|advanced|proficient|expert|familiar|working knowledge|coursework|exposure|novice)\b", re.I)
ZERO_DIGIT = re.compile(r"(?<![\d.,])\b0\b(?![.,]\d)")
POSSESS = re.compile(r"\b(experience|experienced|used|use|using|familiar|familiarity|knowledge|worked|exposure|proficient|proficiency|trained|skills?|background|hands-on)\b", re.I)
ITEM_SPLIT = re.compile(r"[,;|•·]|\s/\s|\band\b|&")

def clean(t): return t.replace("\u2019", "'").replace("\u2018", "'")

def cue_in(text, own=()):
    if ZERO_DIGIT.search(text): return True  # "0 years of SQL"
    return any(not any(c.start() < e and s < c.end() for s, e in own) for c in CUE.finditer(clean(text)))

def classify(resume):
    """Per mention: (mention, state, reason). Doc flags. States: affirmed (supported), negated, hypothetical, unresolved."""
    out, flags = [], []
    secs = segment(resume, "resume")
    for sec in secs:
        if sec.heading and cue_in(sec.heading):
            flags.append("heading_cue_section")
        for ln in sec.lines:
            ments = disambiguate(find_mentions((ln,)))
            own = [norm_span(ln, m.span)[1:] for m in ments]
            n = _norm(ln).text
            # document-level: a skill-less sentence with a negation cue that points back or is elliptical
            for sent in re.split(r"[.;?!]", n):
                if sent.strip() and NEGSTART.search(clean(sent)) and (BACKREF.search(sent) or len(sent.split()) <= 4):
                    in_sent = [o for o in own if n.find(sent) <= o[0] < n.find(sent) + len(sent)]
                    if not in_sent:
                        flags.append("backref_negation")
            if not ments and cue_in(n) and POSSESS.search(n) and NEGSTART.search(clean(n)):
                flags.append("unscoped_disclaimer")  # a skill-less negative statement about experience could cover any skill
            for m in ments:
                st = _qualify(m, "resume").status
                if st != "affirmed":
                    out.append((m, st, "decided")); continue
                if sec.heading and cue_in(sec.heading):
                    out.append((m, "unresolved", "heading_cue")); continue
                if cue_in(n, own):
                    out.append((m, "unresolved", "cue_in_line")); continue
                if sec.kind == "skills":
                    a, b = norm_span(ln, m.span)[1:]
                    body = n.split(":", 1)[1] if ":" in n[:a] else n
                    off = len(n) - len(body)
                    items, pos = [], 0
                    for part in ITEM_SPLIT.split(body):
                        items.append((off + body.find(part, pos), part)); pos = body.find(part, pos) + len(part)
                    it = next((p for s_, p in items if s_ <= a < s_ + len(p)), "")
                    rest = it.replace(n[a:b], " ")
                    rest = LEVEL.sub(" ", rest)
                    rest = re.sub(r"[()\[\]\-–—:.\s]+", "", rest)
                    out.append((m, "affirmed" if not rest else "unresolved", "skills_entry" if not rest else "skills_item_extra"))
                elif sec.kind == "experience":
                    out.append((m, "affirmed", "experience_statement"))
                else:
                    out.append((m, "unresolved", f"section_{sec.kind}"))
    if F(resume, "resume"): flags.append("refused_" + F(resume, "resume")[0])
    return out, sorted(set(flags))

def skill_states(cls):
    by = collections.defaultdict(set)
    for m, st, _ in cls: by[m.canonical].add(st)
    res = {}
    for k, s in by.items():
        if "affirmed" in s and "negated" in s: res[k] = "contradicted"
        elif "affirmed" in s: res[k] = "found"
        elif "unresolved" in s: res[k] = "unresolved"
        elif "negated" in s: res[k] = "negated"
        else: res[k] = "hypothetical"
    return res

def score_mode(fx, cls, flags):
    exp = fx["expected"]; rp = set(exp.get("required", [])) | set(exp.get("preferred", []))
    if not rp: return "unavailable", []
    st = skill_states(cls)
    if any(f.startswith("refused") or f in ("backref_negation", "heading_cue_section", "unscoped_disclaimer") for f in flags): return "withheld", ["doc:" + ",".join(flags)]
    bad = [k for k in rp if st.get(k) in ("unresolved", "contradicted")]
    return ("withheld" if bad else "scored"), bad

def run_fixture(fx, C, L):
    cls, flags = classify(fx["resume_text"])
    for m, st, why in cls:
        C["mention:" + st] += 1; C["reason:" + why] += 1
    gold_found = set(fx["expected"].get("found", []))
    for lab in fx.get("mention_labels", []):
        if lab["doc"] != "resume": continue
        cands = [m for m, _, _ in cls if m.canonical == lab["canonical"] and lab["line_contains"] in m.line.text]
        claimed, err = _resolve(lab, cands)
        if err: L["label:no-mention"] += 1; continue
        sts = [next(s for mm, s, _ in cls if mm is m) for m in claimed]
        g = lab["status"]
        if any(s not in ("unresolved", g) for s in sts):
            o = "CRITICAL" if g != "affirmed" and "affirmed" in sts else "incorrect"
        elif "unresolved" in sts: o = "unresolved" + ("/loss" if g == "affirmed" else "/safe")
        else: o = "correct"
        L["label:" + o] += 1
    mode, bad = score_mode(fx, cls, flags)
    C["pair:" + mode] += 1
    if mode == "scored":
        st = skill_states(cls); rp = set(fx["expected"].get("required", [])) | set(fx["expected"].get("preferred", []))
        for k in rp:
            if st.get(k) == "found" and k not in gold_found: C["pair:CRITICAL found-not-gold"] += 1
            if st.get(k) != "found" and k in gold_found: C["pair:scored-but-gold-found-missed"] += 1
    for f in flags: C["docflag:" + f] += 1
    return mode

if __name__ == "__main__":
    for group in sys.argv[1:]:
        C, L = collections.Counter(), collections.Counter(); n = 0
        for d in group.split(","):
            for f in sorted(glob.glob(d + "/*.json")):
                n += 1; run_fixture(json.load(open(f, encoding="utf8")), C, L)
        print(f"== {group.split(',')[0][-22:]} ({n} pairs)")
        for k in sorted(L): print("  ", k, L[k])
        for k in sorted(C): print("  ", k, C[k])
