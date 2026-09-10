# Source geometry — Supercavitating

Brief: [underwater_cad.md](../../underwater_cad.md) › *Supercavitating*
Model: [model.stl](model.stl) — built; verdict in [README.md](../../README.md).

## Required

- **Design speed and cavitation number** — `SYNTHETIC (assumption)` → recorded in
  [wedge-sections.csv](wedge-sections.csv) as **45 knots**. The brief demands this number
  exist; it is an assumption made here to make the design well-posed, not a measurement.
  Change it and the section family must change with it.
  Feeds: the operating point the whole section family is drawn for.
  Source: A design decision, not a download — but the brief makes recording it mandatory.
  Without it: the brief is explicit: *"the geometry is poor below it, so a model without that number is not usable"*. It is currently recorded nowhere in the repo, so the built model cannot be assessed at all, even once its detached blades are joined to the hub.

- **Newton–Rader supercavitating section offsets for `Z = 3`** — `NOT SOURCED`
  `SYNTHETIC` stand-ins are available: [wedge-sections.csv](wedge-sections.csv) for the section
  and [blade-planform.csv](blade-planform.csv) for the planform (`Ae/Ao` 0.5500 against 0.55,
  TE held at 4% chord at every station). Neither is Newton–Rader data.
  Feeds: sharp LE with a stated included angle, straight suction-side ramp, square base at 4% chord.
  Source: Newton & Rader, *Performance data of propellers for high-speed craft*, Trans. RINA 103 (1961) — paywalled, not freely retrievable as of 2026-09-10; Tulin's supercavitating section theory for the underlying family. Checked: no open reproduction of the section offsets found.
  Without it: *"the leading-edge included angle meets spec at every station"* has no spec to meet.

## Inherits

Nothing. Do not copy the SPP sections across: that blade is ventilated through the free surface, this one runs submerged inside its own cavity.
