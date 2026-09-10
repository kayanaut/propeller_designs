# Source geometry — Coaxial contra-rotating

Brief: [aerial_cad.md](../../aerial_cad.md) › *Coaxial contra-rotating*
Model: not built.

## Required

- **A separate pitch value for the lower rotor** — `SYNTHETIC`
  → [rotor-pair.csv](rotor-pair.csv). Lower rotor pitched up for the upper's downwash via a
  first-order actuator-disc estimate (P/D 0.5 upper, 0.5406 lower). Both hands are a genuine
  mirror. The brief's warning stands and this table does not model it: a coaxial pair lands
  well short of 2× thrust at equal power.
  Feeds: the lower rotor's twist, which works in the upper rotor's downwash.
  Source: Solve the lower disc at its own inflow in QPROP or XROTOR; the upper disc uses the fixed-pitch distribution unchanged.
  Without it: both discs get the same pitch, which is the specific error the brief warns about — the pair then lands even further short of 2× thrust than a coaxial pair already does.

## Inherits

[Fixed-pitch (low-Re)](../fixed-pitch/source-geometry.md) — both rotors are that blade, the lower one mirrored in XZ.
