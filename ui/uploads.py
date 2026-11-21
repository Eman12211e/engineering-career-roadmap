"""Shared resume input handling for the tabs: uploaded file or pasted text -> validated text."""

import streamlit as st

from engine.pdf_extractor import PDFExtractionError, pdf_to_clean_text, validate_text_input


def read_text_input(text: str, uploaded, field: str = "resume") -> str | None:
    """Return validated text ("" if nothing entered), or None after showing an st.error.

    An uploaded file overrides the pasted text. Error messages never echo the text.
    """
    try:
        if uploaded is not None:
            if uploaded.name.lower().endswith(".pdf"):
                file_text = pdf_to_clean_text(uploaded.read())
            else:
                file_text = uploaded.read().decode("utf-8-sig")  # strips a Notepad BOM
            if not file_text.strip():
                raise ValueError("The uploaded file is empty.")
            text = file_text
        return validate_text_input(text, field) if (text or "").strip() else ""
    except PDFExtractionError as e:
        st.error(e.user_message)
    except UnicodeDecodeError:
        st.error("That text file is not UTF-8 text. Save it as UTF-8 or paste the text instead.")
    except ValueError as e:
        st.error(str(e))
    return None
