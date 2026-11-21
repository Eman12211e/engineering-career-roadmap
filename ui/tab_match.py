"""Tab: Posting Match — compare one job posting with a resume."""

import pandas as pd
import streamlit as st

from engine.job_match import match_posting
from engine.pdf_extractor import validate_text_input
from ui.uploads import read_text_input


def _table(matches) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Skill": m.skill,
            "Found": "yes" if m.found else "no",
            "Posting line": m.posting_line,
            "Resume line": m.resume_line or "",
        }
        for m in matches
    ])


def render_match_tab() -> None:
    """Posting text + resume text -> skill coverage with evidence lines."""
    st.header("Posting Match")
    st.write(
        "Paste a job posting and your resume to see which of the skills the posting "
        "asks for appear in your resume. This is skill coverage, not hiring probability."
    )

    posting = st.text_area("Paste the job posting here:", height=200, key="match_posting")
    resume = st.text_area("Paste your resume text here:", height=200, key="match_resume")
    uploaded = st.file_uploader("Or upload a resume file", type=["pdf", "txt"], key="match_upload")

    if not st.button("Match Posting", type="primary", key="match_btn"):
        return

    resume = read_text_input(resume, uploaded)
    if resume is None:
        return
    try:
        posting = validate_text_input(posting, "job posting")
        resume = validate_text_input(resume, "resume")
    except ValueError as e:
        st.error(str(e))
        return

    result = match_posting(posting, resume)
    if result.score is None:
        st.info("No required or preferred skills were recognized in the posting, so no score was computed.")
    else:
        st.metric("Skill Coverage", f"{result.score:.0f}%", help="Share of required (80%) and preferred (20%) skills found in your resume. Not a hiring probability.")

    for title, group in (("Required skills", result.required), ("Preferred skills", result.preferred)):
        if group:
            st.subheader(title)
            st.dataframe(_table(group), hide_index=True, width="stretch")
    if result.unscored:
        with st.expander(f"Other skills mentioned, not scored ({len(result.unscored)})"):
            st.dataframe(_table(result.unscored), hide_index=True, width="stretch")
