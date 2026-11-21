"""Tab 3 — Skills Gap Analysis: paste resume, see what's missing."""

import streamlit as st
import pandas as pd
from typing import Dict, List
from engine.gap_analysis import analyze_gap, compute_gap_score
from ui.uploads import read_text_input
from ui.charts import gap_donut


def render_gap_tab(
    ranked_df: pd.DataFrame,
    top_n: int = 20,
) -> None:
    """Resume upload/paste → gap analysis → visual comparison."""
    st.header("Skills Gap Analysis")
    st.write(
        "Paste your resume text or upload a PDF/text file to see which "
        "top-ranked skills you already have and which ones to develop."
    )

    resume_text = st.text_area(
        "Paste your resume text here:",
        height=200,
        placeholder="Copy and paste the text content of your resume...",
        key="gap_resume_input",
    )

    uploaded = st.file_uploader("Or upload a resume file", type=["pdf", "txt"])
    resume_text = read_text_input(resume_text, uploaded)
    if resume_text is None:
        return

    if not resume_text:
        st.info("Enter your resume text above to start the analysis.")
        return

    if not st.button("Analyze My Skills Gap", type="primary"):
        # Check if we already have results in session state
        if "gap_results" not in st.session_state:
            return

    # Run analysis
    present, missing = analyze_gap(resume_text, ranked_df, top_n=top_n)
    gap_pct = compute_gap_score(present, missing)

    # Save for cross-tab use and PDF export
    st.session_state["gap_results"] = {
        "present": present,
        "missing": missing,
        "score": gap_pct,
    }

    # Donut chart
    fig = gap_donut(len(present), len(missing))
    st.plotly_chart(fig, width="stretch")

    st.metric("Skills Coverage", f"{gap_pct}%", help="Percentage of top skills found in your resume")

    # Two-column breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Skills You Have ({len(present)})")
        for s in present:
            st.markdown(
                f"**{s['canonical']}** — {s['priority_score']:.0f}% "
                f"*(#{s['rank']})*"
            )

    with col2:
        st.subheader(f"Skills to Develop ({len(missing)})")
        for s in missing:
            st.markdown(
                f"**{s['canonical']}** — {s['priority_score']:.0f}% "
                f"*(#{s['rank']})*"
            )

    # Actionable summary
    if missing:
        st.markdown("---")
        st.subheader("Priority Actions")
        top_3 = missing[:3]
        for i, s in enumerate(top_3, 1):
            st.markdown(
                f"**{i}. {s['canonical']}** appears in "
                f"{s['priority_score']:.0f}% of postings — "
                f"adding this to your resume would have the highest impact."
            )
