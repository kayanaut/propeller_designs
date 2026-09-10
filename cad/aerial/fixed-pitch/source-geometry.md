# Source geometry — Fixed-pitch (low-Re)

Brief: [aerial_cad.md](../../aerial_cad.md) › *Fixed-pitch (low-Re)*
Model: not built.

## Required

- **A UIUC 10×5 entry — `c(r)` and `β(r)`** — `SOURCED`
  → [apc-10x5e.csv](apc-10x5e.csv) — 51 stations of APC's own mould geometry for the 10x5E:
  chord, three pitch definitions, sweep, rake, thickness ratio, twist. D = 10 in exactly as
  the brief specifies. UIUC hosts performance data and points at APC for geometry, so this
  is the geometry that database refers to.
  **Caution:** real root thickness ratio is 0.40, not the brief's 14% — the aerofoil blends
  into the hub boss inboard. Trust the file over the brief there.
  Feeds: the chord and twist distribution of the whole blade.
  Source: UIUC propeller database — https://m-selig.ae.illinois.edu/props/propDB.html ; APC publish offsets directly as `.peo` files — https://www.apcprop.com/technical-information/file-downloads/
  Without it: the brief's *"lifted from a UIUC entry of the same nominal size"* is unmet, and *"pitch measured back off the model at `r/R = 0.75` is within 2% of `P`"* has no source distribution to be within 2% of.

- **Clark-Y or Eppler E63 coordinates** — `SOURCED`
  → [clark-y.csv](clark-y.csv) (122 pts, **Lednicer** order) and
  [eppler-e63.csv](eppler-e63.csv) (61 pts, **Selig** order). The two files use opposite
  conventions — check before lofting.
  **The brief is internally inconsistent here:** it offers "Clark-Y or Eppler E63" with
  "t/c 14% root to 9% tip", but E63 is a 4.25% section and cannot carry that schedule
  without ceasing to be an E63. Clark-Y (~11.7%) is the one that can.
  Feeds: the section at every station, `t/c` 14% root to 9% tip.
  Source: UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the section is approximated, and at these Reynolds numbers the section is most of the performance.

## Inherits

Nothing. This is the root of the aerial blade chain: folding, coaxial, Q-tip and serrated all build on this blade.
