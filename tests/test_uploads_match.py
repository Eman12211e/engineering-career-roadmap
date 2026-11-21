import io

import pytest
from streamlit.testing.v1 import AppTest

from ui import uploads
from ui.uploads import read_text_input


class Fake(io.BytesIO):
    def __init__(self, data, name):
        super().__init__(data)
        self.name = name


@pytest.fixture
def errors(monkeypatch):
    msgs = []
    monkeypatch.setattr(uploads.st, "error", msgs.append)
    return msgs


@pytest.mark.parametrize("up", [
    Fake(b"\xff\xfe\xfa bad", "r.txt"),
    Fake(b"not a pdf", "r.pdf"),
    Fake(b"x" * 200_000, "r.txt"),
    Fake(b"   ", "r.txt"),
])
def test_bad_uploads_return_none(errors, up):
    assert read_text_input("pasted", up) is None
    assert len(errors) == 1


def test_bom_stripped_and_empty_paste(errors):
    assert read_text_input("", Fake(b"\xef\xbb\xbfSolidWorks", "r.txt")) == "SolidWorks"
    assert read_text_input("  ", None) == ""
    assert not errors


def test_match_tab_shows_coverage():
    at = AppTest.from_file("app.py", default_timeout=60).run()
    at.text_area(key="match_posting").set_value("Required: SolidWorks and Python.")
    at.text_area(key="match_resume").set_value("Used SolidWorks daily.")
    at.button(key="match_btn").click().run()
    assert not at.exception
    assert "Skill Coverage" in [m.label for m in at.metric]


def test_gap_and_audit_tabs_reject_overlong_text():
    at = AppTest.from_file("app.py", default_timeout=60).run()
    at.text_area(key="gap_resume_input").set_value("a" * 20_001)
    at.text_area(key="audit_resume_input").set_value("a" * 20_001)
    at.run()
    assert not at.exception
    assert sum("longer than 20,000" in e.value for e in at.error) == 2
