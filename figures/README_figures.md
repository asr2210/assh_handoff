# HANDOFF — figure regeneration package

Self-contained code and data to regenerate the three manuscript figures.

## Contents
- Root-level CSVs — evaluation case sets and HANDOFF outputs
- `analysis.py` — computes all statistics from the root-level CSVs and writes `results.json`
- `results.json` — precomputed statistics (so the figure scripts run without re-running analysis)
- `fig1_workflow.svg` — Figure 1, conceptual workflow. Editable in Illustrator: system fonts,
  inline styles, named layers (`input`, `handoff`, `branches`, `out-clear`, `out-close`, `out-incomplete`)
- `fig2_direction_of_error.py` — Figure 2, case-level confusion matrix (self-contained; counts in-script)
- `fig3_information.py` — Figure 3, category-defining/changing information identification (reads `results.json`)
- `extras_accuracy_flagging.py` — optional panels not used in the final manuscript
  (accuracy by case set; flagging contrast). Reads `results.json`.

## Setup
```
pip install -r requirements.txt
```

## Regenerate everything
```
./run_all.sh
```
or individually:
```
python3 analysis.py                 # root CSVs -> results.json
python3 fig2_direction_of_error.py  # -> fig2_direction_of_error.png
python3 fig3_information.py          # -> fig3_information.png
```
Figure 1 is the SVG directly; to rasterize a preview:
```
python3 -c "import cairosvg; cairosvg.svg2png(url='fig1_workflow.svg', write_to='fig1_workflow.png', output_width=1100)"
```

## Notes
- Figures are saved at 330–340 dpi PNG. For vector output, change `savefig` to `.pdf` or `.svg`.
- `fig2_direction_of_error.py` hard-codes the case-level confusion counts (documented at the top of the file);
  these correspond to the values `analysis.py` prints for the primary + gray-zone sets.
- Color convention across figures: navy = well-specified / confident disposition,
  brown = contested / close-call, teal = information request, red hatch = error region.
