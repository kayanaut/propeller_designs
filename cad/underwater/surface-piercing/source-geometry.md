# Source geometry — Surface-piercing (SPP)

Brief: [underwater_cad.md](../../underwater_cad.md) › *Surface-piercing (SPP)*
Model: [model.stl](model.stl) — built; verdict in [README.md](../../README.md).

## Required

- **Cleaver planform outline** — `SYNTHETIC` → [cleaver-planform.csv](cleaver-planform.csv)
  Scaled to hit the brief's `Ae/Ao = 0.75` exactly (achieved 0.7500), and the tip chord stays
  at `c/D = 0.35` rather than tapering — the square cut the built model is missing.
  Feeds: swept leading edge, near-radial trailing edge, and the square tip chord.
  Source: **Proprietary: no open series publishes a cleaver outline.** Rolla and Mercury Bravo geometry is commercial; confirmed unavailable 2026-09-10. Nearest published set is Newton & Rader, Trans. RINA 103 (1961), itself paywalled. The realistic route is measuring a real blade. Do not keep searching.
  Without it: this is the failure already measured: the built tip tapers to about 9 mm chord and keeps falling, where a cleaver ends square. The planform cannot be corrected without an outline.

- **Wedge section offsets with TE thickness at 3% chord** — `SYNTHETIC`
  → [wedge-sections.csv](wedge-sections.csv)
  Feeds: flat pressure face, straight ramp, sharp LE, blunt thick TE at every station.
  Source: Newton–Rader (RINA, 1961) supercavitating/ventilating section data.
  Without it: *"every section is a wedge, not an aerofoil (check the maximum thickness sits at the trailing edge)"* cannot be confirmed — and the built mesh is too sparsely sectioned to read it.

- **Cup schedule over the outer third** — `SYNTHETIC` → `cup_deg` column of
  [cleaver-planform.csv](cleaver-planform.csv)
  Feeds: the 2° trailing-edge curl and how it grows toward the tip.
  Source: Propeller cupping practice for surface drives; no public table — record the measured schedule.
  Without it: the cup is either absent or arbitrary; it is what holds the blade loaded while ventilating.

## Inherits

Nothing.
