# Source geometry — Controllable-pitch (CPP)

Brief: [underwater_cad.md](../../underwater_cad.md) › *Controllable-pitch (CPP)*
Model: not built.

## Required

- **Blade geometry** — `SOURCED` → [pptc-particulars.csv](pptc-particulars.csv),
  full CAD via [fetch-geometry.sh](fetch-geometry.sh)
  Feeds: the whole blade — and uniquely in this repo, a real *controllable pitch* blade.
  Source: SVA Potsdam, Potsdam Propeller Test Case, model propeller VP1304. Free to download
  and use; **SVA must be credited**. `D = 250.0 mm` — exactly this repo's scale — `Z = 5`,
  `P0.7/D = 1.635`, `Ae/Ao = 0.779`, skew 18.8°. IGES/STEP/3dm and a radius-wise offsets file
  are fetched into `vendored/`, which is gitignored — the repo keeps the transcribed
  particulars, not another party's binaries.
  Per-station geometry is in [pptc-blade-radii.csv](pptc-blade-radii.csv) — the 12 radial
  stations of SVA's own PFF definition file: chord, pitch, camber, thickness and rake at each
  radius, with 43 chordwise offsets per station available in the fetched file itself.
  The hub-ratio conflict is **resolved**: the definition file gives hub diameter 75.0 on a
  250.0 propeller, so 0.300 is right and the geometry sheet's 0.1500 is hub radius over
  diameter. Settled from the source rather than guessed.

- **O-ring groove dimensions for the palm bore seal** — `SYNTHETIC` → [oring-grooves.csv](oring-grooves.csv)
  Standard design ratios (20% squeeze, width 1.30 × cord) applied to common AS568 cord sizes —
  the method those standards encode, not a copy of their tables. ISO 3601-2 and Parker ORD-5700
  remain authoritative and are not free. Note the palm bore is a **rotary** application: blades
  turn in service, so size the running seal properly rather than taking the static ratios.
  Feeds: the seal groove width, depth and corner radii in the hub palm bore.
  Source: ISO 3601 / AS568 (BS1806) groove tables; Parker O-Ring Handbook ORD-5700.
  Without it: the palm seal is dimensioned by eye, and a groove that is merely plausible will not seal.

## Inherits

[Fixed-pitch (FPP)](../fixed-pitch/source-geometry.md) — the blade is the FPP blade terminating in a palm, so it needs the same B-series tables.
