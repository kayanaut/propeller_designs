# Source geometry — Serrated edge

Brief: [aerial_cad.md](../../aerial_cad.md) › *Serrated edge*
Model: not built.

## Required

- **Serration amplitude and wavelength as a ratio of local chord** — `SYNTHETIC`
  → [serration-schedule.csv](serration-schedule.csv). Amplitude is a constant fraction of
  **local** chord at every station (verified), which is exactly what stops the serration
  biting deeper at the root than the tip — the failure the brief warns about.
  Feeds: the saw-tooth or sinusoidal edge profile over `r/R = 0.5` to the tip.
  Source: Serrated TE for drone noise — https://www.sciencedirect.com/science/article/abs/pii/S0003682X25005171
  Without it: the serration is sized arbitrarily, so the comparison against the plain blade the brief asks for measures nothing in particular.

## Inherits

[Fixed-pitch (low-Re)](../fixed-pitch/source-geometry.md) — base blade from Fixed-pitch, exported alongside the serrated one for comparison.
