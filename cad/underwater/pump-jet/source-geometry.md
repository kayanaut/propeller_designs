# Source geometry — Pump-jet

Brief: [underwater_cad.md](../../underwater_cad.md) › *Pump-jet*
Model: [model.stl](model.stl) — built; verdict in [README.md](../../README.md).

## Required

- **Rotor chord / thickness / skew / rake table for `Z = 7`** — `SYNTHETIC`
  → [rotor-schedule.csv](rotor-schedule.csv)
  **This fixes the model's worst defect.** The tip is pinned to throat radius minus the 0.5 mm
  gap (`r/throat = 0.9960`), where the built rotor overruns the shroud by 9.5 mm. High solidity
  (`Ae/Ao = 1.05`) and 45° tip skew, both per the brief. Radii are fractions of the **throat**
  radius from duct-decelerating.csv — never of the blade's own tip.
  Feeds: the high-skew, high-solidity rotor loft.
  Source: No open series covers this rotor. Solve it as a lifting-line design in OpenProp (https://www.epps.com/openprop) and export the distribution table.
  Without it: the rotor planform is invented. It is also the body that currently overruns the shroud inner radius by 9.5 mm, and there is no reference geometry to rebuild the tip against.

- **Stator vane section coordinates for `V = 15`** — `GENERATED`
  → [stator-vane-naca4412.csv](stator-vane-naca4412.csv). Cambered, because a stator that is
  not cambered turns no flow — the built model's vanes are flat boxes. A four-digit stand-in
  for the NACA 65-series, whose ordinates are tabulated rather than equation-derived.
  Feeds: the vane profile, currently a 12-triangle rectangular box in the built mesh.
  Source: A cambered compressor-stator section — NACA 65-series is the usual choice; coordinates from UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the vanes stay flat plates, so they neither turn the flow nor recover swirl, and the whole point of the stator is lost.

- **Decelerating shroud wall ordinates** — `SYNTHETIC` → [duct-decelerating.csv](duct-decelerating.csv)
  Inner wall contracts to a throat at the rotor plane then **diverges** — the defining
  difference from 19A, whose inner wall is cylindrical and never diverges.
  Feeds: the thick inner wall of the shroud — decelerating flow is what suppresses cavitation here.
  Source: A decelerating (pump-jet) duct profile. **19A is the wrong family and must not be substituted** — real 19A ordinates now sit one folder away in [../ducted-kort/duct-19a.csv](../ducted-kort/duct-19a.csv), which makes the mistake easy to make. 19A accelerates flow; this shroud must decelerate it, and that is what suppresses cavitation here. No open decelerating-duct table found 2026-09-10.
  Without it: the shroud is a plain annulus and the design's cavitation argument does not hold.

## Inherits

Nothing. Note the stator side — upstream for a submarine, downstream for a torpedo — is a decision the brief requires before any of this data is fetched; the built model made neither.
