#!/usr/bin/env python3
"""Streamlit interface for HANDOFF.

Run locally:
  streamlit run app.py

The OpenAI API key is entered by the user at runtime. The app does not write
submitted cases or API keys to disk.
"""

import json
import urllib.error

import streamlit as st

from handoff import run_handoff


TRIAGE_TEXT = {
    1: "Does not require hand surgery consultation during the initial emergency department encounter, and may not require hand surgery follow-up.",
    2: "Does not require immediate hand surgery consultation during the initial emergency department encounter, but most often should receive outpatient hand surgery follow-up.",
    3: "May require immediate hand surgery consultation, or transfer if hand surgery is not available at the presenting facility.",
}


def get_recommendation(result):
    return result.get("triage_recommendation") or result.get("provisional_triage_recommendation")


def render_triage_result(result):
    rec = get_recommendation(result)
    if rec:
        st.subheader(f"Recommendation: Category {rec}")
        st.write(result.get("triage_recommendation_text") or result.get("provisional_triage_recommendation_text") or TRIAGE_TEXT.get(rec, ""))

    if result.get("is_borderline_triage_case") is not None:
        label = "Yes" if result.get("is_borderline_triage_case") else "No"
        st.metric("Borderline triage case", label)

    if result.get("has_enough_information") is not None:
        label = "Yes" if result.get("has_enough_information") else "No"
        st.metric("Enough information for confident triage", label)

    questions = result.get("clarifying_questions") or []
    if questions:
        st.subheader("Clarifying Questions")
        for idx, question in enumerate(questions, start=1):
            with st.container(border=True):
                st.markdown(f"**{idx}. {question.get('question', '')}**")
                if question.get("why_it_matters"):
                    st.write(question["why_it_matters"])
                if question.get("assh_domain"):
                    st.caption(f"Domain: {question['assh_domain']}")

    if result.get("reasoning"):
        st.subheader("Reasoning")
        st.write(result["reasoning"])

    lower = result.get("lower_acuity_interpretation") or {}
    higher = result.get("higher_acuity_interpretation") or {}
    if lower or higher:
        st.subheader("Borderline Triage Reasoning")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Lower-acuity interpretation**")
            st.write(lower.get("assh_domain") or lower.get("assh_language") or "")
            for item in lower.get("supporting_findings") or []:
                st.markdown(f"- {item}")
        with col2:
            st.markdown("**Higher-acuity interpretation**")
            st.write(higher.get("assh_domain") or higher.get("assh_language") or "")
            for item in higher.get("supporting_findings") or []:
                st.markdown(f"- {item}")

    with st.expander("Raw JSON"):
        st.code(json.dumps(result, indent=2, ensure_ascii=False), language="json")


st.set_page_config(page_title="HANDOFF", page_icon="✋", layout="wide")

st.title("HANDOFF")
st.caption("ASSH-guided emergency department triage support for hand and wrist injuries.")

with st.sidebar:
    st.header("Run Settings")
    api_key = st.text_input(
        "OpenAI API key",
        type="password",
        help="Used only for this session's model call. The app does not store the key.",
    )
    model = st.text_input("Model", value="gpt-5.5")
    mode_label = st.radio(
        "Mode",
        ["Triage recommendation", "Ask for missing information"],
        help="Use missing-information mode when the ED note is incomplete and the tool should ask focused follow-up questions.",
    )
    timeout = st.number_input("Timeout seconds", min_value=30, max_value=300, value=120, step=10)

    st.divider()
    st.markdown("**Privacy / PHI note**")
    st.write(
        "This app does not store the API key or submitted cases locally. Submitted cases are sent to "
        "OpenAI using the API key provided here and are governed by that user's OpenAI organization/"
        "project settings, data retention controls, and any applicable Business Associate Agreement "
        "(BAA). Do not enter PHI unless that setup permits PHI."
    )

example = (
    "32-year-old male presents after reportedly punching a wall. He denies punching another person "
    "or intra-oral contamination. He has a 1.5 cm laceration over the third MCP joint. X-rays show "
    "no fracture or foreign body. The finger is warm and well perfused, sensation is intact distal "
    "to the laceration, and finger extension is normal."
)

case_text = st.text_area(
    "Case description",
    height=260,
    placeholder=example,
)

run = st.button("Run HANDOFF", type="primary", use_container_width=True)

if run:
    if not api_key.strip():
        st.error("Enter an OpenAI API key in the sidebar.")
    elif not case_text.strip():
        st.error("Enter a case description.")
    else:
        mode = "triage" if mode_label == "Triage recommendation" else "missing-info"
        with st.spinner("Running HANDOFF..."):
            try:
                result = run_handoff(
                    api_key=api_key.strip(),
                    case_text=case_text,
                    mode=mode,
                    model=model.strip() or "gpt-5.5",
                    timeout=float(timeout),
                )
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                st.error(f"OpenAI API error: {exc.code}")
                st.code(body)
            except Exception as exc:
                st.error(f"HANDOFF failed: {exc}")
            else:
                render_triage_result(result)
