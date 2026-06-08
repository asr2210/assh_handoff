# HANDOFF Shared Analysis Files

This folder contains the minimum files needed to understand and reanalyze the HANDOFF evaluation without using the project scripts.

## Case files

- `primary_validation_cases.csv`: 60 guideline-mapped synthetic hand/wrist triage cases with reference categories.
- `gray_zone_cases.csv`: 15 harder gray-zone cases with reference categories.
- `ablation_cases.csv`: 31 missing-information cases. This is the single ablation input file.

## Result files

- `handoff_primary_validation_results_gpt_5_5.csv`: HANDOFF outputs for the 60 primary cases, 3 runs per case.
- `handoff_gray_zone_results_gpt_5_5.csv`: HANDOFF outputs for the 15 gray-zone cases, 3 runs per case.
- `handoff_ablation_question_scores_gpt_5_5.csv`: LLM-graded scoring of whether HANDOFF asked for the withheld category-relevant details in the ablation cases.

## Triage categories

1. Does not require hand surgery consultation during the initial emergency department encounter, and may not require hand surgery follow-up.
2. Does not require immediate hand surgery consultation during the initial emergency department encounter, but most often should receive outpatient hand surgery follow-up.
3. May require immediate hand surgery consultation, or transfer if hand surgery is not available at the presenting facility.

## Ablation benchmark types

- `category_changing`: a specific withheld detail could change the triage category if present versus absent/reassuring.
- `category_defining`: an expert-marked clinical detail supporting the reference category was removed. These details define why the case belongs in the assigned category, but are not always isolated one-variable category flips.

## Suggested analysis unit

For the primary and gray-zone classification files, use the vignette/case as the unit of analysis. With 3 runs per case, summarize each case by majority vote for categorical accuracy and by mean 0/1 correctness for replicate-balanced accuracy.
