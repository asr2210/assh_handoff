#!/usr/bin/env python3
"""Gradio web interface for HANDOFF.

This is the default app entrypoint for Hugging Face Spaces. Users provide their
own OpenAI API key at runtime; keys and cases are not written to disk by the app.
"""

import urllib.error

import gradio as gr

from handoff import run_handoff


MODEL = "gpt-5.5"

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


CSS = """
:root {
  --handoff-ink: #17202a;
  --handoff-muted: #667085;
  --handoff-card: #ffffff;
  --handoff-accent: #2f5f7f;
  --handoff-line: #e5e7eb;
  --handoff-soft: #f8fafc;
  --handoff-warning: #fff8e6;
  --handoff-warning-line: #f2d08f;
}

.gradio-container {
  background: #ffffff;
  color: var(--handoff-ink);
}

.handoff-shell {
  max-width: 1120px;
  margin: 0 auto;
}

.handoff-hero {
  padding: 1.2rem 1.35rem;
  border: 1px solid var(--handoff-line);
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(16, 24, 40, 0.05);
}

.handoff-eyebrow {
  color: var(--handoff-accent);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.handoff-hero h1 {
  margin: 0.25rem 0 0.2rem;
  color: var(--handoff-ink);
  font-size: clamp(2rem, 5vw, 3.6rem);
  line-height: 0.95;
}

.handoff-hero p {
  max-width: 760px;
  color: var(--handoff-muted);
  font-size: 1rem;
}

.handoff-card {
  border: 1px solid var(--handoff-line);
  border-radius: 14px;
  background: var(--handoff-card);
  box-shadow: 0 6px 18px rgba(16, 24, 40, 0.04);
  padding: 0.95rem;
}

.handoff-note {
  color: var(--handoff-muted);
  font-size: 0.92rem;
}

.handoff-disclosure {
  border: 1px solid var(--handoff-warning-line);
  border-radius: 14px;
  background: var(--handoff-warning);
  padding: 0.8rem 1rem;
}

.handoff-disclosure p {
  margin: 0;
  color: #624a13;
  font-size: 0.94rem;
}

.handoff-result {
  border-left: 5px solid var(--handoff-accent);
  background: var(--handoff-soft);
}

.handoff-compact h3 {
  margin-top: 0;
}

"""


def _recommendation_number(result):
    return result.get("triage_recommendation") or result.get("provisional_triage_recommendation")


def _recommendation_heading(rec):
    headings = {
        1: "No initial ED hand-surgery consultation usually needed",
        2: "Outpatient hand-surgery follow-up usually appropriate",
        3: "Immediate hand-surgery consultation or transfer may be needed",
    }
    try:
        return headings.get(int(rec), "Triage recommendation")
    except (TypeError, ValueError):
        return "Triage recommendation"


def _as_list(items):
    return items if isinstance(items, list) else []


def _format_questions(questions):
    lines = []
    for index, question in enumerate(questions, start=1):
        item = str(question.get("question", "")).strip()
        why = str(question.get("why_it_matters", "")).strip()
        domain = str(question.get("assh_domain", "")).strip()
        if item:
            lines.append(f"**{index}. {item}**")
        if why:
            lines.append(why)
        if domain:
            lines.append(f"ASSH domain: {domain}")
    return lines


def _format_result(result):
    rec = _recommendation_number(result)
    has_enough = result.get("has_enough_information")
    questions = _as_list(result.get("clarifying_questions"))
    lines = []

    if has_enough is False and questions:
        lines.append("## More Information Needed")
        lines.append(
            "HANDOFF did not identify enough ASSH-relevant information to make a "
            "confident triage recommendation. Add answers to the questions below "
            "to the case description and run HANDOFF again."
        )
        lines.append("### Focused Questions")
        lines.extend(_format_questions(questions))
        if result.get("reasoning"):
            lines.append("### Why These Details Matter")
            lines.append(result["reasoning"])
        return "\n\n".join(lines)

    if rec:
        text = result.get("triage_recommendation_text") or result.get("provisional_triage_recommendation_text", "")
        lines.append(f"## {_recommendation_heading(rec)}")
        if text:
            lines.append(text)

    if result.get("is_borderline_triage_case"):
        lines.append(
            "**Borderline triage case:** Yes. HANDOFF identified plausible "
            "lower- and higher-acuity interpretations."
        )

    if has_enough is True:
        lines.append("**Information sufficiency:** Enough information was provided for a triage recommendation.")

    if questions:
        lines.append("### Remaining Clarifying Questions")
        lines.append("These are not required before giving the recommendation, but may refine management.")
        lines.extend(_format_questions(questions))

    if result.get("reasoning"):
        lines.append("### Clinical Reasoning")
        lines.append(result["reasoning"])

    lower = result.get("lower_acuity_interpretation") or {}
    higher = result.get("higher_acuity_interpretation") or {}
    if lower or higher:
        lines.append("### Borderline Considerations")
        if lower:
            findings = "; ".join(lower.get("supporting_findings") or [])
            domain = lower.get("assh_domain") or lower.get("assh_language") or ""
            lines.append(f"**Lower-acuity interpretation:** {domain}")
            if findings:
                lines.append(findings)
        if higher:
            findings = "; ".join(higher.get("supporting_findings") or [])
            domain = higher.get("assh_domain") or higher.get("assh_language") or ""
            lines.append(f"**Higher-acuity interpretation:** {domain}")
            if findings:
                lines.append(findings)

    if not lines:
        lines.append("HANDOFF returned a response, but it could not be formatted into a recommendation or focused questions.")

    return "\n\n".join(lines)


def query_handoff(api_key, case_text):
    if not api_key or not api_key.strip():
        raise gr.Error("Enter an OpenAI API key.")
    if not case_text or not case_text.strip():
        raise gr.Error("Enter a case description.")

    try:
        result = run_handoff(
            api_key=api_key.strip(),
            case_text=case_text,
            mode="auto",
            model=MODEL,
            timeout=120,
        )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise gr.Error(f"OpenAI API error {exc.code}: {body}") from exc
    except Exception as exc:
        raise gr.Error(f"HANDOFF failed: {exc}") from exc

    return _format_result(result)


with gr.Blocks(title="HANDOFF") as demo:
    with gr.Column(elem_classes=["handoff-shell"]):
        gr.Markdown(
            """
            <section class="handoff-hero">
              <div class="handoff-eyebrow">ASSH-guided triage support</div>
              <h1>HANDOFF</h1>
              <p>
                Emergency department decision support for hand and wrist injuries.
                Paste a case; HANDOFF will ask for missing details or return a
                triage recommendation.
              </p>
            </section>
            """
        )
        gr.Markdown(
            f"""
            <section class="handoff-disclosure">
              <p><strong>Important disclosure:</strong> HANDOFF is a research prototype and is not a substitute for clinician judgment. {PRIVACY_NOTE}</p>
            </section>
            """
        )

        with gr.Row():
            with gr.Column(scale=1, elem_classes=["handoff-card", "handoff-compact"]):
                gr.Markdown("### Access")
                api_key = gr.Textbox(
                    label="OpenAI API key",
                    type="password",
                    placeholder="sk-...",
                    info="Used only for this request/session. The app does not store the key.",
                )
            with gr.Column(scale=2, elem_classes=["handoff-card", "handoff-compact"]):
                gr.Markdown("### Case")
                case_text = gr.Textbox(
                    label="Case description",
                    lines=12,
                    placeholder=EXAMPLE_CASE,
                )
                run_button = gr.Button("Run HANDOFF", variant="primary")

        with gr.Column(elem_classes=["handoff-card", "handoff-result", "handoff-compact"]):
            gr.Markdown("### Result")
            result_markdown = gr.Markdown("Enter a case description and click **Run HANDOFF**.")

        run_button.click(
            fn=query_handoff,
            inputs=[api_key, case_text],
            outputs=[result_markdown],
            show_progress="full",
        )


if __name__ == "__main__":
    demo.launch(css=CSS)
