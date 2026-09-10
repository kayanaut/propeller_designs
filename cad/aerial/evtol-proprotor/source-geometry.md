# Source geometry — eVTOL proprotor

Brief: [aerial_cad.md](../../aerial_cad.md) › *eVTOL proprotor*
Model: not built.

## Required

- **Two chord/twist tables — hover and cruise** — `SYNTHETIC`
  → [blend-twist.csv](blend-twist.csv), with a real reference planform in
  [xv15-reference.csv](xv15-reference.csv). Cruise comes out coarser at every station because
  the freestream dominates the local helix angle — hover washout 21.0°, cruise 45.9°. The
  blend weight stays live, which the brief calls the entire design problem.
  Feeds: the two design points the single geometry has to be blended between.
  Source: XROTOR or QPROP, solved once at hover (advance ratio ≈ 0) and once at cruise (high advance ratio, reduced rpm).
  Without it: *"the one geometry is evaluated at both design points"* is impossible, and the blend weight — which the brief calls the entire design problem — has nothing to blend.

- **Section coordinates suited to the tip Mach cap** — `NOT SOURCED`
  The XV-15 uses five **NACA 6-series** sections along the span (64-935, 64-528, 64-118,
  64-(1.5)12, 64-208 — see [xv15-reference.csv](xv15-reference.csv)). Six-series ordinates are
  **tabulated, not equation-derived**, so unlike four-digit sections they cannot be generated
  here. This one genuinely stays open.
  Feeds: sections that stay attached at a tip Mach around 0.55.
  Source: UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the tip Mach cap is a number in the parameter block with no section behind it.

## Inherits

Nothing.
