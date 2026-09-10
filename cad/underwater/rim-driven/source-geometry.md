# Source geometry — Rim-driven (hubless)

Brief: [underwater_cad.md](../../underwater_cad.md) › *Rim-driven (hubless)*
Model: [model.stl](model.stl) — built; verdict in [README.md](../../README.md).

## Required

- **Duct profile ordinates** — `SOURCED (shared)`
  Feeds: the duct wall section, currently a bare rectangular annulus (radii 125 and 143 only).
  Source: real 19A ordinates are already in this repo — [../ducted-kort/duct-19a.csv](../ducted-kort/duct-19a.csv). One table, one location; do not copy it here. Scale by this duct's own `L`, and note the throat is cylindrical over `x/L` 40–60% only.
  Without it: the duct contributes no thrust and the stator has no defined seat.

- **Blade section coordinates for the inward-cantilevered blade** — `SYNTHETIC`
  → [blade-schedule.csv](blade-schedule.csv)
  Thickness runs 0.040 at the ring down to 0.012 at the free inner end — **inverted** relative
  to every hubbed blade in this repo, because the structural root is at the tip radius. Getting
  it the usual way round puts the thinnest section where the bending moment is highest.
  Feeds: sections from the ring at `r/R = 1.0` inward to the free end at `r/R ≈ 0.31`.
  Source: Wageningen B-series blade geometry: Carlton, *Marine Propellers and Propulsion*, Table 6.5; also Gokarn, *Ship Resistance and Propulsion*, pp. 444–455; primary is Kuiper, *The Wageningen Propeller Series*, MARIN 92-001 (1992). Structure confirmed 2026-09-10 — chord coefficient `A_r`, `t/D`, and the `V1`/`V2` section-ordinate pair — but all three are copyrighted book tables and none is freely retrievable. Not transcribed from search snippets on purpose: a glimpsed value is not a table.
  Without it: the blade is a plausible shape rather than a designed one. The rotor is otherwise the soundest geometry in the set, which makes the invented sections the weak link.

- **Magnet band dimensions — pocket pitch, width, depth** — `SYNTHETIC` → [magnet-band.csv](magnet-band.csv)
  16 real pockets recessed 5 mm into the ring OD with a 1.2 mm bridge between neighbours,
  where the built model has 16 blocks merely overlapping the ring. Pole count is taken from the
  built model; magnet grade and flux are motor-design decisions this repo does not make.
  Feeds: the magnet-pocket band in the rotor ring OD.
  Source: A PM rotor magnet spec (segment size and count) from the motor design; not aerofoil data.
  Without it: the 16 magnets stay separate blocks overlapping the ring instead of sitting in pockets.

## Inherits

Nothing.
