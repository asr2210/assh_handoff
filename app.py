#!/usr/bin/env python3
"""Gradio web interface for HANDOFF.

This is the default app entrypoint for Hugging Face Spaces. Users provide their
own OpenAI API key at runtime; keys and cases are not written to disk by the app.
"""

import json
import urllib.error

import gradio as gr

from handoff import run_handoff


PRIVACY_NOTE = (
    "This app does not store the API key or submitted cases locally. Submitted "
    "cases are sent to OpenAI using the API key provided here and are governed "
    "by that user's OpenAI organization/project settings, data retention "
    "controls, and any applicable Business Associate Agreement (BAA). Do not "
    "enter PHI unless that setup permits PHI."
)


EXAMPLE_CASE = (
    "32-year-old male presents after reportedly punching a wall. He denies "
    "punching another person or intra-oral contamination. He has a 1.5 cm "
    "laceration over the third MCP joint. X-rays show no fracture or foreign "
    "body. The finger is warm and well perfused, sensation is intact distal to "
    "the laceration, and finger extension is normal."
)


def _recommendation_number(result):
    return result.get("triage_recommendation") or result.get("provisional_triage_recommendation")


def _format_result(result):
    rec = _recommendation_number(result)
    lines = []

    if rec:
        text = result.get("triage_recommendation_text") or result.get("provisional_triage_recommendation_text", "")
        lines.append(f"## Recommendation: Category {rec}\n{text}")

    if "is_borderline_triage_case" in result:
        borderline = "Yes" if result["is_borderline_triage_case"] else "No"
        lines.append(f"**Borderline triage case:** {borderline}")

    if "has_enough_information" in result:
        enough = "Yes" if result["has_enough_information"] else "No"
        lines.append(f"**Enough information for confident triage:** {enough}")

    questions = result.get("clarifying_questions") or []
    if questions:
        lines.append("## Clarifying questions")
        for index, question in enumerate(questions, start=1):
            item = question.get("question", "")
            why = question.get("why_it_matters", "")
            domain = question.get("assh_domain", "")
            lines.append(f"**{index}. {item}**")
            if why:
                lines.append(why)
            if domain:
                lines.append(f"_Domain: {domain}_")

    if result.get("reasoning"):
        lines.append("## Reasoning")
        lines.append(result["reasoning"])

    lower = result.get("lower_acuity_interpretation") or {}
    higher = result.get("higher_acuity_interpretation") or {}
    if lower or higher:
        lines.append("## Borderline triage reasoning")
        if lower:
            findings = "; ".join(lower.get("supporting_findings") or [])
            lines.append(f"**Lower-acuity interpretation:** {lower.get('assh_domain') or lower.get('assh_language') or ''}")
            if findings:
                lines.append(findings)
        if higher:
            findings = "; ".join(higher.get("supporting_findings") or [])
            lines.append(f"**Higher-acuity interpretation:** {higher.get('assh_domain') or higher.get('assh_language') or ''}")
            if findings:
                lines.append(findings)

    return "\n\n".join(lines), json.dumps(result, indent=2, ensure_ascii=False)


def query_handoff(api_key, case_text, mode_label, model, timeout):
    if not api_key or not api_key.strip():
        raise gr.Error("Enter an OpenAI API key.")
    if not case_text or not case_text.strip():
        raise gr.Error("Enter a case description.")

    mode = "triage" if mode_label == "Triage recommendation" else "missing-info"
    try:
        result = run_handoff(
            api_key=api_key.strip(),
            case_text=case_text,
            mode=mode,
            model=(model or "gpt-5.5").strip(),
            timeout=float(timeout or 120),
        )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise gr.Error(f"OpenAI API error {exc.code}: {body}") from exc
    except Exception as exc:
        raise gr.Error(f"HANDOFF failed: {exc}") from exc

    return _format_result(result)


with gr.Blocks(title="HANDOFF") as demo:
    gr.Markdown(
        """
        # HANDOFF

        ASSH-guided emergency department triage support for hand and wrist injuries.

        HANDOFF is a research prototype and is not a substitute for clinician judgment.
        """
    )
    gr.Markdown(f"**Privacy / PHI note:** {PRIVACY_NOTE}")

    with gr.Row():
        with gr.Column(scale=1):
            api_key = gr.Textbox(
                label="OpenAI API key",
                type="password",
                placeholder="sk-...",
                info="Used only for this request/session. The app does not store the key.",
            )
            mode = gr.Radio(
                ["Triage recommendation", "Ask for missing information"],
                value="Triage recommendation",
                label="Mode",
            )
            model = gr.Textbox(label="Model", value="gpt-5.5")
            timeout = gr.Number(label="Timeout seconds", value=120, precision=0)
        with gr.Column(scale=2):
            case_text = gr.Textbox(
                label="Case description",
                lines=13,
                placeholder=EXAMPLE_CASE,
            )
            run_button = gr.Button("Run HANDOFF", variant="primary")

    result_markdown = gr.Markdown(label="Result")
    result_json = gr.Code(label="Raw JSON", language="json")

    run_button.click(
        fn=query_handoff,
        inputs=[api_key, case_text, mode, model, timeout],
        outputs=[result_markdown, result_json],
    )


if __name__ == "__main__":
    demo.launch()
