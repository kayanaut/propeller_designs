#!/usr/bin/env bash
# Fetch the SVA Potsdam PPTC VP1304 geometry into ./vendored/ (gitignored).
#
# The data are free to download and free to use. SVA ask only to be credited as the source:
#     Schiffbau-Versuchsanstalt Potsdam (SVA), Potsdam Propeller Test Case (PPTC),
#     model propeller VP1304.
# Credit them in anything built from this geometry.
#
# These files are NOT committed. They are another party's artefacts, they are binary, and
# git cannot diff them. Particulars transcribed into pptc-particulars.csv are the part this
# repo keeps under version control.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p vendored

base=https://www.sva-potsdam.de/wp-content/uploads
files=(
  "2016/03/case2-1_open_water_test_geometry.zip"        # IGES + STEP + 3dm, open water
  "2016/04/case2-2-3_vel-cavitation_test_geometry.zip"  # IGES + STEP + 3dm, LDV/cavitation
  "2016/03/case2_PPTC.PFF_.zip"                         # propeller description by radius
  "2016/03/case2_PPTC_geometry.pdf"                     # geometry description sheet
)

for f in "${files[@]}"; do
  out="vendored/$(basename "$f")"
  if [ -e "$out" ]; then echo "have    $out"; continue; fi
  echo "fetch   $out"
  curl -fsSL --retry 2 --max-time 120 -o "$out" "$base/$f" \
    || { echo "FAILED  $base/$f" >&2; rm -f "$out"; }
done
echo
echo "Done. Contents of vendored/ are not tracked by git; see ../../../.gitignore"
