#!/usr/bin/env bash
# Regenerate all HANDOFF figures from scratch.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
cd "$SCRIPT_DIR"
echo "[1/4] computing statistics from root CSVs -> figures/results.json"
"$PYTHON_BIN" "$SCRIPT_DIR/analysis.py"
echo "[2/4] Figure 2 (direction of error)"
"$PYTHON_BIN" "$SCRIPT_DIR/fig2_direction_of_error.py"
echo "[3/4] Figure 3 (information identification)"
"$PYTHON_BIN" "$SCRIPT_DIR/fig3_information.py"
echo "[4/4] Figure 1 (workflow) -> PNG preview from SVG"
if "$PYTHON_BIN" -c "import cairosvg" >/dev/null 2>&1; then
  "$PYTHON_BIN" -c "import cairosvg; cairosvg.svg2png(url='fig1_workflow.svg', write_to='fig1_workflow.png', output_width=1100)"
  echo "done. outputs: fig1_workflow.{svg,png}  fig2_direction_of_error.png  fig3_information.png"
else
  echo "cairosvg not installed; keeping fig1_workflow.svg and skipping PNG preview"
  echo "done. outputs: fig1_workflow.svg  fig2_direction_of_error.png  fig3_information.png"
fi
