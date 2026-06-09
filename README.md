# HANDOFF

HANDOFF is a research prototype for emergency department triage of hand and wrist injuries using ASSH-guided triage categories.

This repository contains the shared evaluation datasets, HANDOFF outputs, figure-generation code, and a minimal command-line triage helper.

## Web Interface

Run the local Streamlit interface:

```bash
python3 -m pip install -r requirements.txt
streamlit run app.py
```

The interface asks each user to enter their own OpenAI API key. The key is used only for that session's model call and is not written to disk by the app. Cases are sent to the OpenAI API account associated with the key entered by the user.

For PHI-containing use, deploy HANDOFF only in an environment, OpenAI account/project, and institutional agreement that permit PHI.

## Command-Line Use

Set an OpenAI API key and run:

```bash
export OPENAI_API_KEY=...
python3 handoff.py --case "32-year-old male punched a wall and has a 1.5 cm laceration over the third MCP joint..."
```

For incomplete cases where HANDOFF should ask clarifying questions:

```bash
python3 handoff.py --mode missing-info --case-file case.txt
```

The CLI returns JSON. It is intended for research/prototyping and is not a substitute for clinician judgment.

## Triage Categories

1. Does not require hand surgery consultation during the initial emergency department encounter, and may not require hand surgery follow-up.
2. Does not require immediate hand surgery consultation during the initial emergency department encounter, but most often should receive outpatient hand surgery follow-up.
3. May require immediate hand surgery consultation, or transfer if hand surgery is not available at the presenting facility.

## Shared Case Files

- `primary_validation_cases.csv`: 60 guideline-mapped synthetic hand/wrist triage cases with reference categories.
- `gray_zone_cases.csv`: 15 harder gray-zone cases with reference categories.
- `ablation_cases.csv`: 31 missing-information cases.

## Shared Result Files

- `handoff_primary_validation_results_gpt_5_5.csv`: HANDOFF outputs for the 60 primary cases, 3 runs per case.
- `handoff_gray_zone_results_gpt_5_5.csv`: HANDOFF outputs for the 15 gray-zone cases, 3 runs per case.
- `handoff_ablation_question_scores_gpt_5_5.csv`: scoring of whether HANDOFF asked for withheld category-relevant details in ablation cases.

## Ablation Benchmark Types

- `category_changing`: a specific withheld detail could change the triage category if present versus absent/reassuring.
- `category_defining`: an expert-marked clinical detail supporting the reference category was removed. These details define why the case belongs in the assigned category, but are not always isolated one-variable category flips.

## Suggested Analysis Unit

For primary and gray-zone classification files, use the vignette/case as the unit of analysis. With 3 runs per case, summarize each case by majority vote for categorical accuracy and by mean 0/1 correctness for replicate-balanced accuracy.

## Figures

Figure-generation code is in `figures/`.

```bash
python3 -m pip install -r requirements.txt
cd figures
./run_all.sh
```

The figure scripts read the root-level CSV files and write generated images into `figures/`.
