# Source geometry — Loop / toroidal (Sharrow)

Brief: [underwater_cad.md](../../underwater_cad.md) › *Loop / toroidal (Sharrow)*
Model: not built.

## Required

- **Closed loop path definition** — `SYNTHETIC` → [loop-path.csv](loop-path.csv)
  Single smooth periodic parametrisation, so the path is tangent-continuous by construction.
  Self-intersection of the return branch is **not** settled by this — that needs the swept solid.
  Feeds: the 3D centreline out along the leading branch, round, and back to the second root.
  Source: **Patented and unpublished.** Sharrow's loop geometry is covered by patent, so the path is described in claims but not tabulated; confirmed 2026-09-10. The patent text is the only authoritative description. Nearest usable model: marine toroidal blades — https://grabcad.com/library/e-foil-and-marine-toroidal-propeller-blades-1 . Do not keep searching.
  Without it: the loop is drawn freehand, and *"nothing self-intersects where the return branch passes the leading branch"* becomes luck rather than design.

- **Marine section schedule along the loop** — `SYNTHETIC` → [section-schedule.csv](section-schedule.csv)
  Indexed by the **same** path parameter `s` as [loop-path.csv](loop-path.csv), so row `i` here
  is the section to sweep at row `i` there. The brief's binding constraint is a minimum
  thickness holding all the way round *including the return branch* — a loop has no free tip to
  thin toward. Achieved minimum `t/D = 0.0220` against a 0.012 floor.
  Feeds: chord and thickness by path parameter, with a cavitation-driven LE radius all the way round.
  Source: Marine section offsets — Wageningen B-series, Kuiper *The Wageningen Propeller Series* (MARIN 92-001, 1992); offsets tabulated in Carlton *Marine Propellers and Propulsion*. Generator: https://www.wageningen-b-series-propeller.com/ — adapted to the loop; blunt TE, no knife edge.
  Without it: *"minimum thickness holds around the whole loop including the return"* has no basis.

## Inherits

Nothing.
