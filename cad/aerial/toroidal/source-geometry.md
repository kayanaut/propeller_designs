# Source geometry — Toroidal

Brief: [aerial_cad.md](../../aerial_cad.md) › *Toroidal*
Model: not built.

## Required

- **Closed loop path definition** — `SYNTHETIC`
  → [loop-path.csv](loop-path.csv). Catmull-Rom spline, closed and periodic, so tangent
  continuity holds by construction.
  **Licence note:** the brief's recommended starting point, the Ultimate Toroidal Propeller
  Generator, is **GPL-3.0**. Copying its code would put this repository under GPL, so the
  method (a generic spline) is implemented independently and that project is credited.
  Feeds: the 3D path out along the leading branch, over the top, back along the trailing branch.
  Source: Ultimate Toroidal Propeller Generator — https://github.com/RaulBejarano/Ultimate-Toroidal-Propeller-Generator ; the brief says start there rather than from a blank file. MIT Lincoln Laboratory holds the reference design.
  Without it: the loop is freehand and *"the loop is tangent-continuous"* is unlikely to survive it.

- **Airfoil scheduled along the path** — `SYNTHETIC`
  Schedule chord and twist by the `r_R`/`theta_deg` columns of [loop-path.csv](loop-path.csv)
  and scale [../fixed-pitch/clark-y.csv](../fixed-pitch/clark-y.csv) to it. Hold the section
  frame so it cannot flip — the classic failure on a swept loop.
  Feeds: chord and twist by path parameter, with the section frame held so it cannot flip.
  Source: UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the sweep has no section to sweep, and a flipped frame is the classic failure here.

## Inherits

Nothing.
