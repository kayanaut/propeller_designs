# Source geometry — Ducted propeller / Kort nozzle

Brief: [underwater_cad.md](../../underwater_cad.md) › *Ducted propeller / Kort nozzle*
Model: [model.stl](model.stl) — built; verdict in [README.md](../../README.md).

## Required

- **19A nozzle profile ordinates** — `SOURCED` → [duct-19a.csv](duct-19a.csv)
  Feeds: the revolved nozzle wall, inner and outer.
  Source: Muljowidodo et al., "Design and testing of underwater thruster for SHRIMP ROV-ITB", *Indian J. Mar. Sci.* **38**(3), Sept 2009, pp. 338–345, Table 1 — attributed there to Oosterveld. Fetched 2026-09-10.
  Complete, 18 stations, internally consistent with the published description of 19A: the inner
  ordinate falls to exactly 0 across `x/L` 40–60% (the cylindrical throat) and the trailing edge
  stays thick at 2.36% of `L`.

- **Ka 4-70 blade offsets — chord and thickness by `r/R`** — `PARTIALLY SOURCED`
  → [ka-sections.csv](ka-sections.csv), [ka-thickness.csv](ka-thickness.csv)
  Feeds: `c(r)`, `t(r)`, section camber, and the square tip.
  Source: same paper, Tables 3–6.
  Two defects are marked inline in the CSVs rather than papered over: the pressure-side table is
  printed for `r/R` 0.2–0.5 only, and `t_max/D` at `r/R = 0.2` is printed as 0.004, which is
  impossible against a taper that must decrease outward. The `K(r)` chord-law table is absent —
  the paper's own cross-reference to it is misnumbered. Fetch Oosterveld (1970) to close all three.

## What the real ordinates settle

Having the table turns the open question in [README.md](../../README.md) into a measurement, and the
answer reverses it. Checked from [duct-19a.csv](duct-19a.csv) against the built mesh:

| Check | From 19A | Built mesh |
|---|---|---|
| Outer radius, maximum | 151.34 | 151.25 |
| Throat radius (`y_inner = 0`) | 125.000 | 125.00 |
| Tip clearance across the tip chord | 1.500, deviation 0.000 | tip radius 123.500 constant |

The blade tip chord spans `z` −12.47…+12.47 — 24.94 mm — and the cylindrical throat is 25.0 mm at
`z` −12.5…+12.5. **The tip sits inside the throat**, so the wall is genuinely cylindrical across the
sweep and clearance is uniform to 0.000 mm against a 0.1 mm tolerance. All three of this brief's
*Done when* criteria pass: uniform clearance, cylindrical wall, square tip (radius is constant to
within 0.012 over the full 24.94 mm of tip chord).

The earlier "125.0–126.0 across the sweep" note was measuring the wrong thing — the whole propeller's
`z` range (±42.2), which includes rake and skew at inner radii, rather than the tip chord. The duct
was built on 19A all along.

## Inherits

Nothing.
