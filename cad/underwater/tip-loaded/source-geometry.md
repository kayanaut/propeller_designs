# Source geometry — Tip-loaded (Kappel / CLT)

Brief: [underwater_cad.md](../../underwater_cad.md) › *Tip-loaded (Kappel / CLT)*
Model: not built.

## Required

- **A published tip-rake distribution for the Kappel variant** — `SYNTHETIC`
  → [kappel-tip-rake.csv](kappel-tip-rake.csv). A quintic Hermite blend from `r/R = 0.85`,
  so position, slope and curvature are continuous at the transition **by construction** —
  verified analytically, `y''` exactly 0 at both ends and slope matching the 15° linear rake
  to machine precision. Satisfies the brief's curvature-continuity criterion by method rather
  than by luck. Does not apply to the CLT variant, which is a plate on the pressure side.
  Feeds: the nonlinear tip curve driving the existing rake term from `r/R = 0.85` outward.
  Source: Tip rake on Kappel propellers — https://www.mdpi.com/2077-1312/11/4/748 . **Proprietary: no published tip-rake law exists.** Kappel geometry is MAN's, CLT is Sistemar's, and searching 2026-09-10 produced nothing tabulated. Either derive a curvature-continuous curve yourself and record it as your own, or licence the geometry. Do not keep searching.
  Without it: *"the Kappel tip is curvature-continuous with no crease at the transition"* becomes a shape chosen to look right rather than one that reproduces the design it is named after.

## Inherits

[Fixed-pitch (FPP)](../fixed-pitch/source-geometry.md) — the base blade is the FPP blade.
