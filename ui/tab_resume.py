"""Tab 2 — Bullet Builder: turn your own evidence into accurate resume bullets."""

import streamlit as st
import pandas as pd
from typing import List, Dict
from engine.bullet_generator import (
    BulletEvidence,
    build_bullet,
    split_claims,
    skill_mentioned,
    suggest_prompts,
    suggest_verbs,
)


def render_resume_tab(
    ranked_df: pd.DataFrame,
    user_config: Dict,
    skills_metadata: List[Dict],
) -> None:
    """Let the user write bullets from their own evidence for chosen skills."""
    st.header("Resume Bullet Builder")
    st.write(
        "Bullets are built only from what you type. Nothing is invented: no "
        "numbers, tools, outcomes or ownership. Use only experience you can "
        "defend in an interview."
    )

    cat_map = {s["canonical"]: s["category"] for s in skills_metadata}
    top_skills = ranked_df.head(10)["canonical"].tolist()
    selected = st.multiselect(
        "Pick skills to write bullets for",
        options=ranked_df["canonical"].tolist(),
        default=top_skills[:3],
        help="Each skill gets a short form; fill in only what is true.",
    )

    # Reset every run so a deselected skill's old bullet never reaches the PDF.
    st.session_state["generated_bullets"] = []

    if not selected:
        st.info("Select at least one skill above to start.")
        return

    all_bullets = []
    for skill in selected:
        category = cat_map.get(skill, "")
        score = ranked_df.loc[ranked_df["canonical"] == skill, "priority_score"]
        score_val = score.values[0] if len(score) > 0 else 0

        st.subheader(f"{skill}  — in {score_val:.0f}% of postings in this synthetic sample")
        with st.expander("Prompts to help you remember your evidence"):
            for p in suggest_prompts(skill, category):
                st.markdown(f"- {p}")
        st.caption(
            "Verb ideas (suggestions only, use your own if more accurate): "
            + ", ".join(suggest_verbs(category))
        )

        action = st.text_input(
            "What you did (your own verb and words)", key=f"action_{skill}"
        )
        context = st.text_input("Project or context (optional)", key=f"context_{skill}")
        result = st.text_input(
            "Result you can state truthfully (optional, leave blank if none)",
            key=f"result_{skill}",
        )

        if not action.strip():
            st.caption("Enter what you did to see a bullet.")
            st.markdown("---")
            continue

        evidence = BulletEvidence(skill=skill, action=action, context=context, result=result)
        bullet = build_bullet(evidence)
        st.markdown(f"- {bullet}")
        problems, check = split_claims(bullet, evidence)
        if problems:
            st.warning("Not found in your evidence: " + ", ".join(problems))
        if check:
            st.info(
                "Ownership or impact words: keep only if you personally did this: "
                + ", ".join(check)
            )
        if not skill_mentioned(bullet, skill):
            st.info(
                f"Your bullet does not mention {skill}. Add it in your own words "
                "only if it is true; it is not inserted for you."
            )
        all_bullets.append(bullet)
        st.markdown("---")

    if all_bullets:
        st.subheader("Copy All Bullets")
        st.code("\n".join(f"• {b}" for b in all_bullets), language=None)

    # Store in session state for PDF export
    st.session_state["generated_bullets"] = all_bullets
