# Source geometry — Ducted fan

Brief: [aerial_cad.md](../../aerial_cad.md) › *Ducted fan*
Model: not built.

## Required

- **Annular duct ordinates — inlet lip, cylindrical rotor plane, exit nozzle** — `NOT SOURCED`
  Feeds: the duct section revolved about +Z, exit area 85% of swept area.
  Source: NASA low-noise fan design methods — https://ntrs.nasa.gov/api/citations/20230003262/downloads/20230003262%20REV%20FINAL.pdf
  Without it: the lip radius and exit contraction are guessed, and the duct's static-thrust gain with it.

- **Rotor section coordinates, high-solidity and thin** — `NOT SOURCED`
  Feeds: the `Z = 5` rotor loft at hub ratio 0.45.
  Source: UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the rotor is a shape, not a fan stage.

- **Stator vane section coordinates for `V = 11`** — `NOT SOURCED`
  Feeds: the downstream vanes that also carry the motor pod.
  Source: A cambered stator section, e.g. NACA 65-series; UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the vanes straighten nothing, and `V ≥ 2Z` buys acoustic cut-off with no aerodynamic vane behind it.

## Inherits

Nothing.
