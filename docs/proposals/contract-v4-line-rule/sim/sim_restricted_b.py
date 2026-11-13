# ruff: noqa
# NON-PRODUCTION simulation, used for the 2026-11-10 figures. Not engine code.
# Read-only variant SI-b: an unrecognised "heading" that looks like a job/education entry line (year, "|", "City, ST",
# or "Title, Company") inherits the previous recognised section kind instead of starting an unknown section.
import os, sys, re, dataclasses
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, ".")
import sim_restricted as R
ENTRY = re.compile(r"\b(19|20)\d{2}\b|\||\b[A-Z][a-z]+, [A-Z]{2}\b|^[^:]{3,60}, [A-Z][\w&.\- ]+")
_seg = R.segment
def segment(text, doc):
    out, last = [], None
    for s in _seg(text, doc):
        if s.kind in ("skills", "experience", "excluded"):
            last = s.kind
        elif s.kind == "unknown" and s.heading and last in ("skills", "experience") and ENTRY.search(s.heading):
            s = dataclasses.replace(s, kind=last, lines=tuple(dataclasses.replace(l, section=last) for l in s.lines))
        else:
            last = None if s.heading else last
        out.append(s)
    return tuple(out)
R.segment = segment
if __name__ == "__main__":
    sys.argv = sys.argv; R.__name__ = "R"
    import runpy
    exec(open(R.__file__, encoding="utf8").read().split('if __name__ == "__main__":')[1].replace("\n    ", "\n"), vars(R))
