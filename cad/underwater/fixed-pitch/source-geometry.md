# Source geometry — Fixed-pitch (FPP)

Brief: [underwater_cad.md](../../underwater_cad.md) › *Fixed-pitch (FPP)*
Model: not built.

## Required

- **Wageningen B4-55 section offsets** — `NOT SOURCED` (stand-ins available, see below)
  A buildable parametric blade at the brief's own parameters is in
  [blade-planform.csv](blade-planform.csv) (`SYNTHETIC`, `Ae/Ao` 0.5500 achieved against 0.55),
  and a real measured blade is in [dtmb4119.csv](dtmb4119.csv). Neither is the B-series, so this
  requirement stays open.
  Feeds: the aerofoil shape at every station of the loft.
  Source: Wageningen B-series blade geometry: Carlton, *Marine Propellers and Propulsion*, Table 6.5; also Gokarn, *Ship Resistance and Propulsion*, pp. 444–455; primary is Kuiper, *The Wageningen Propeller Series*, MARIN 92-001 (1992). Structure confirmed 2026-09-10 — chord coefficient `A_r`, `t/D`, and the `V1`/`V2` section-ordinate pair — but all three are copyrighted book tables and none is freely retrievable. Not transcribed from search snippets on purpose: a glimpsed value is not a table.
  Without it: the brief's *"section offsets taken from the B-series tables rather than invented"* is unmet, and the FPP baseline every other underwater design is judged against is itself a guess.

- **Baseline blade geometry** — `SOURCED (substitute)` → [dtmb4119.csv](dtmb4119.csv)
  Feeds: `c(r)`, `P(r)`, `t(r)`, camber — a complete, real, measured blade.
  Source: DTMB 4119, Table 2 of arXiv:2104.13363, citing the DTMB originals. `Z = 3`,
  `D = 0.305`, hub 0.2, `J = 0.833`, NACA 66 modified thickness, `a = 0.8` mean line.
  **This is not the B-series blade the brief asks for** — different blade count, no skew — but
  it is real geometry from an openly published propeller used worldwide for CFD validation,
  so a model built on it can be checked against measurements. Two source defects are recorded
  in the CSV: a comma decimal at `r/R = 0.9`, and the mean line printed as `a = 0.08`.
  Next lead for genuine B-series geometry: **INSEAN E779A**, a B4.70-type constant-pitch
  propeller published openly for validation — the closest retrievable thing to the real series.

- **B-series chord and thickness distributions `c(r)`, `t(r)`** — `NOT SOURCED`
  Feeds: blade outline and thickness taper for `Z = 4`, `Ae/Ao = 0.55`.
  Source: Wageningen B-series blade geometry: Carlton, *Marine Propellers and Propulsion*, Table 6.5; also Gokarn, *Ship Resistance and Propulsion*, pp. 444–455; primary is Kuiper, *The Wageningen Propeller Series*, MARIN 92-001 (1992). Structure confirmed 2026-09-10 — chord coefficient `A_r`, `t/D`, and the `V1`/`V2` section-ordinate pair — but all three are copyrighted book tables and none is freely retrievable. Not transcribed from search snippets on purpose: a glimpsed value is not a table. The generator at https://www.wageningen-b-series-propeller.com/ will emit geometry but does not publish the underlying tables, so it cannot serve as the cross-check the brief asks for.
  Without it: *"geometry cross-checks against the B-series generator ... within a few percent on blade area and pitch at `r/R = 0.7`"* cannot be run — there is nothing to check against.

## Inherits

Nothing. This is the root of the marine blade chain: tip-loaded, skewed, CPP and podded-azimuth all draw on these tables.
