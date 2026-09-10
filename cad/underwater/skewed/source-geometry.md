# Source geometry — Skewed blade

Brief: [underwater_cad.md](../../underwater_cad.md) › *Skewed blade*
Model: not built.

## Required

- **A balanced skew distribution `θs(r)`** — `PARTIALLY SOURCED`
  → [dtmb4381-series-particulars.csv](dtmb4381-series-particulars.csv)
  Particulars of the real series are in; the per-station distributions are not.
  The brief invents a 0/15/30/45° sweep. The real Boswell series runs **0/36/72/108°** on four
  otherwise-identical propellers — which is the only construction that attributes an effect to
  skew alone. Prefer the real values. Original requirement below stays open for the offsets.

- **Per-station chord, thickness, pitch and skew for DTMB 4381–4384** — `NOT SOURCED`
  Stand-in: [skew-sweep.csv](skew-sweep.csv) — four propellers whose **only** differing column
  is skew (verified), at the real series' 0/36/72/108°, with parametric chord/pitch/thickness.
  The real offsets remain the target: DTIC `AD0732511`, still serving a maintenance page when
  retried 2026-09-10.
  Feeds: the skew spline, zero at the root and maximum at the tip, for the 0/15/30/45° sweep.
  Source: Boswell, *Design, Cavitation Performance, and Open-Water Performance of a Series of Research Skewed Propellers*, NSRDC Report 3339 (May 1971) = DTIC accession **AD0732511**, https://apps.dtic.mil/sti/tr/pdf/AD0732511.pdf — a public US government report, so this one is genuinely obtainable. DTIC was serving a maintenance page on 2026-09-10; retry. The series covers four propellers at 0°, 36°, 72° and 108° projected tip skew.
  Without it: *"use balanced skew — the skew line crosses the generator line"* is asserted rather than built, and the spindle-torque claim behind it is unsupported.

## Inherits

[Fixed-pitch (FPP)](../fixed-pitch/source-geometry.md) — same blade as FPP with skew promoted to the design variable.
