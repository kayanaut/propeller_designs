# Source geometry — Collective pitch

Brief: [aerial_cad.md](../../aerial_cad.md) › *Collective pitch*
Model: not built.

## Required

- **Bearing bore and outer dimensions, two per grip** — `SYNTHETIC`
  → [bearing-bores.csv](bearing-bores.csv). Common 8 mm-bore deep-groove sizes; the shank
  fixes the bore, so the real choice is OD and width. Confirm against SKF/NSK before use.
  Feeds: the pitch-axis bores in each blade grip.
  Source: A bearing manufacturer's catalogue (SKF, NSK or equivalent) for the chosen size.
  Without it: the grips are dimensioned around a bearing that may not exist, and the shank Ø 8 fit is unverified.

## Inherits

[Custom carbon blade](../custom-carbon/source-geometry.md) — the brief says reuse that blade with its shank.
