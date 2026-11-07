import logging
import warnings
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_runs_without_errors_or_deprecations(caplog):
    caplog.set_level(logging.DEBUG)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert not [x for x in w if issubclass(x.category, DeprecationWarning)]
    assert "deprecat" not in caplog.text.lower()
    assert not [x for x in at.warning if "deprecat" in str(x.value).lower()]
