# Source geometry — Ducted fan

Brief: [aerial_cad.md](../../aerial_cad.md) › *Ducted fan*
Model: not built.

## Required

- **Annular duct ordinates — inlet lip, cylindrical rotor plane, exit nozzle** — `SYNTHETIC`
  → [duct-ordinates.csv](duct-ordinates.csv). Wall runs exactly cylindrical across the rotor
  plane so tip clearance is uniform there; exit contracts to √0.85 of fan radius for the
  brief's area ratio; inlet lip is rounded outward rather than knife-edged.
  Feeds: the duct section revolved about +Z, exit area 85% of swept area.
  Source: NASA low-noise fan design methods — https://ntrs.nasa.gov/api/citations/20230003262/downloads/20230003262%20REV%20FINAL.pdf
  Without it: the lip radius and exit contraction are guessed, and the duct's static-thrust gain with it.

- **Rotor section coordinates, high-solidity and thin** — `GENERATED`
  → [rotor-section-naca2408.csv](rotor-section-naca2408.csv). 8% thick — a ducted rotor is
  thinner than an open propeller because the duct unloads the tip.
  Feeds: the `Z = 5` rotor loft at hub ratio 0.45.
  Source: UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the rotor is a shape, not a fan stage.

- **Stator vane section coordinates for `V = 11`** — `GENERATED`
  → [stator-vane-naca4412.csv](stator-vane-naca4412.csv). Cambered: a symmetric vane would
  straighten nothing. `V = 11 ≥ 2Z = 10` holds, so the blade-passing fundamental is cut off.
  Feeds: the downstream vanes that also carry the motor pod.
  Source: A cambered stator section, e.g. NACA 65-series; UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the vanes straighten nothing, and `V ≥ 2Z` buys acoustic cut-off with no aerodynamic vane behind it.

- **Rotor and stator planform** — `SYNTHETIC` → [rotor-schedule.csv](rotor-schedule.csv),
  [stator-vanes.csv](stator-vanes.csv)
  Feeds: the rotor blade loft and the vane set that carries the motor pod.
  Source: parametric, from the brief. Chord follows the real APC 10x5E inboard then is **held**
  outboard — a ducted rotor ends square because the duct carries the tip loading.
  Without it: the brief's 0.4 mm tip clearance existed only as prose. The rotor tip is now
  pinned to `r/fanR = 0.9911`, referenced to the same fan radius as
  [duct-ordinates.csv](duct-ordinates.csv), so the two files can be compared at the rotor plane.
  `V = 11` is likewise geometry now rather than a number in a sentence.

## Inherits

Nothing.
