# Source geometry — eVTOL proprotor

Brief: [aerial_cad.md](../../aerial_cad.md) › *eVTOL proprotor*
Model: not built.

## Required

- **Two chord/twist tables — hover and cruise** — `NOT SOURCED`
  Feeds: the two design points the single geometry has to be blended between.
  Source: XROTOR or QPROP, solved once at hover (advance ratio ≈ 0) and once at cruise (high advance ratio, reduced rpm).
  Without it: *"the one geometry is evaluated at both design points"* is impossible, and the blend weight — which the brief calls the entire design problem — has nothing to blend.

- **Section coordinates suited to the tip Mach cap** — `NOT SOURCED`
  Feeds: sections that stay attached at a tip Mach around 0.55.
  Source: UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the tip Mach cap is a number in the parameter block with no section behind it.

## Inherits

Nothing.
