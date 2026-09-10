# Source geometry — Fixed-pitch (low-Re)

Brief: [aerial_cad.md](../../aerial_cad.md) › *Fixed-pitch (low-Re)*
Model: not built.

## Required

- **A UIUC 10×5 entry — `c(r)` and `β(r)`** — `NOT SOURCED`
  Feeds: the chord and twist distribution of the whole blade.
  Source: UIUC propeller database — https://m-selig.ae.illinois.edu/props/propDB.html ; APC publish offsets directly as `.peo` files — https://www.apcprop.com/technical-information/file-downloads/
  Without it: the brief's *"lifted from a UIUC entry of the same nominal size"* is unmet, and *"pitch measured back off the model at `r/R = 0.75` is within 2% of `P`"* has no source distribution to be within 2% of.

- **Clark-Y or Eppler E63 coordinates** — `NOT SOURCED`
  Feeds: the section at every station, `t/c` 14% root to 9% tip.
  Source: UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the section is approximated, and at these Reynolds numbers the section is most of the performance.

## Inherits

Nothing. This is the root of the aerial blade chain: folding, coaxial, Q-tip and serrated all build on this blade.
