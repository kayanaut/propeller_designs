# Source geometry — Folding blade

Brief: [aerial_cad.md](../../aerial_cad.md) › *Folding blade*
Model: not built.

## Required

- **Hinge pin fit — Ø 3 pin in the tang bore** — `SYNTHETIC`
  → [hinge-fits.csv](hinge-fits.csv). Running-clearance classes for a Ø3 pin; a nominal Ø3
  bore on a Ø3 pin does not turn. ISO 286-2 remains authoritative.
  The binding constraint is not a fit: the blade's centre of mass must sit **outboard of the
  hinge pin** or the prop never deploys.
  Feeds: the clearance fit between pin and bore.
  Source: An ISO 286 running-clearance fit table; standard engineering fits, not aerofoil data.
  Without it: *"the pin bore is a clearance fit on the pin"* is nominal — a Ø 3 bore on a Ø 3 pin does not turn.

## Inherits

[Fixed-pitch (low-Re)](../fixed-pitch/source-geometry.md) — blade as fixed-pitch, ending in a tang instead of a root fillet.
