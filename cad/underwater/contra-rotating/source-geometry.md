# Source geometry — Contra-rotating (CRP)

Brief: [underwater_cad.md](../../underwater_cad.md) › *Contra-rotating (CRP)*
Model: [model.stl](model.stl) — built; verdict in [README.md](../../README.md).

## Required

- **Contra-rotating series geometry for the forward `Z = 4` and aft `Z = 5` discs** — `SYNTHETIC`
  → [crp-discs.csv](crp-discs.csv)
  **Read the caveat in that file before building.** The aft disc's pitch is the whole design
  problem of a CRP — it runs inside the forward disc's slipstream, so its inflow is neither
  free-stream nor available from any table. The value there comes from a first-order
  actuator-disc estimate (axial induction `a = 0.1583` at an assumed `CT = 0.60`, partially
  offset by the swirl the opposite-turning aft disc recovers), giving `P/D` 1.0 forward and
  1.0823 aft. Both `CT` and the offset factor are assumptions. Replace with an OpenProp
  lifting-line run before anything is built for real — swirl recovery is why a CRP exists,
  and no table can supply it.
  Feeds: both blade planforms, including the aft disc's reduced diameter and its own pitch.
  Source: Wageningen contra-rotating series (van Manen / Oosterveld, 1968); B-series tables are the fallback for each disc taken alone — Wageningen B-series, Kuiper *The Wageningen Propeller Series* (MARIN 92-001, 1992); offsets tabulated in Carlton *Marine Propellers and Propulsion*. Generator: https://www.wageningen-b-series-propeller.com/
  Without it: the aft disc is pitched for undisturbed inflow rather than for the forward disc's slipstream, which is the entire reason a CRP recovers swirl. Geometry and mirror are correct in the built model; the loading distribution behind them is not sourced.

## Inherits

Nothing. The stray third propeller at `z = 0` is a modelling defect, not a data gap — delete it.
