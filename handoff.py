#!/usr/bin/env python3
"""HANDOFF command-line triage helper.

Usage:
  OPENAI_API_KEY=... python handoff.py --case "32-year-old ..."
  OPENAI_API_KEY=... python handoff.py --case-file case.txt --mode missing-info

The script returns JSON only. It is intended for research/prototyping and is not
a substitute for clinician judgment.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


TRIAGE_OPTIONS = """Triage options:

1. Does not require hand surgery consultation during the initial emergency department encounter, and may not require hand surgery follow-up.

2. Does not require immediate hand surgery consultation during the initial emergency department encounter, but most often should receive outpatient hand surgery follow-up.

3. May require immediate hand surgery consultation, or transfer if hand surgery is not available at the presenting facility.
"""

ASSH_REFERENCE = """Use the ASSH hand-surgery consultation guidance as the reference standard.

ASSH-relevant domains include:
- vascular compromise or threatened perfusion;
- amputation or near-amputation;
- open fracture, open joint, exposed cartilage, synovial fluid, or traumatic arthrotomy concern;
- tendon, nerve, or muscle injury, including partial tendon injury when suggested by weakness or pain with resisted motion;
- dislocation that is irreducible, open, recurrently unstable, or cannot be maintained after reduction;
- deep-space infection, flexor tenosynovitis, septic arthritis, abscess with deep extension, or rapidly progressive infection;
- extensive soft tissue trauma, devitalized tissue, degloving, flap compromise, or need for urgent coverage/debridement;
- multiple digit involvement or inability to reliably assess important neurovascular/tendon/joint findings.

Do not invent criteria outside these domains. If multiple domains apply, choose the highest-acuity appropriate recommendation. If the case is clinically borderline, make that uncertainty visible."""


TRIAGE_PROMPT = f"""You are HANDOFF, a clinical decision support model assisting with emergency department triage of hand and wrist injuries.

{TRIAGE_OPTIONS}

{ASSH_REFERENCE}

If a case could reasonably fit more than one triage recommendation, identify it as a borderline triage case. For borderline cases, explain the strongest lower-acuity interpretation and strongest higher-acuity interpretation before giving the final recommendation.

Return JSON only:

{{
  "triage_recommendation": 1,
  "triage_recommendation_text": "Does not require hand surgery consultation during the initial emergency department encounter, and may not require hand surgery follow-up.",
  "is_borderline_triage_case": false,
  "lower_acuity_interpretation": {{
    "assh_domain": "Brief guideline domain supporting the lower-acuity interpretation, if applicable.",
    "supporting_findings": ["Brief clinical finding supporting the lower-acuity interpretation."]
  }},
  "higher_acuity_interpretation": {{
    "assh_domain": "Brief guideline domain supporting the higher-acuity interpretation, if applicable.",
    "supporting_findings": ["Brief clinical finding supporting the higher-acuity interpretation."]
  }},
  "reasoning": "Briefly explain the key clinical findings and ASSH guideline logic that support the final triage recommendation."
}}"""


MISSING_INFO_PROMPT = f"""You are HANDOFF, a clinical decision support model assisting with emergency department triage of hand and wrist injuries.

You will be given an incomplete emergency department case description.

{TRIAGE_OPTIONS}

{ASSH_REFERENCE}

If important ASSH-relevant information is missing, ask focused clarifying questions before giving a final recommendation. Prioritize questions that would change the recommendation between options 1, 2, and 3. Do not ask broad generic questions if the case already provides the answer.

Return JSON only:

{{
  "has_enough_information": false,
  "clarifying_questions": [
    {{
      "question": "Focused question needed to make the ASSH triage decision.",
      "why_it_matters": "How the answer could change the triage recommendation.",
      "assh_domain": "Short domain label, e.g. vascular status, tendon function, open joint, infection severity."
    }}
  ],
  "provisional_triage_recommendation": 2,
  "provisional_triage_recommendation_text": "Does not require immediate hand surgery consultation during the initial emergency department encounter, but most often should receive outpatient hand surgery follow-up.",
  "reasoning": "Briefly explain what is known, what is missing, and why the recommendation is provisional or final."
}}"""


def read_case(args):
    if args.case and args.case_file:
        raise SystemExit("Use either --case or --case-file, not both.")
    if args.case:
        return args.case
    if args.case_file:
        with open(args.case_file, encoding="utf-8") as f:
            return f.read()
    data = sys.stdin.read()
    if not data.strip():
        raise SystemExit("Provide a case with --case, --case-file, or stdin.")
    return data


def extract_output_text(response):
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    chunks = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                chunks.append(text)
    return "\n".join(chunks)


def parse_json_object(text):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def call_openai(api_key, model, prompt, case_text, timeout):
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": f"Clinical case:\n\n{case_text}"}]},
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Run HANDOFF hand/wrist ED triage.")
    parser.add_argument("--case", help="Case text to triage.")
    parser.add_argument("--case-file", help="Path to a text file containing the case.")
    parser.add_argument("--mode", choices=["triage", "missing-info"], default="triage")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    case_text = read_case(args)
    prompt = TRIAGE_PROMPT if args.mode == "triage" else MISSING_INFO_PROMPT

    try:
        response = call_openai(api_key, args.model, prompt, case_text, args.timeout)
        parsed = parse_json_object(extract_output_text(response))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"OpenAI API error: {exc.code} {body}") from exc
    except Exception as exc:
        raise SystemExit(f"HANDOFF failed: {exc}") from exc

    print(json.dumps(parsed, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
