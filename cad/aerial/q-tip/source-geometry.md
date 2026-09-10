# Source geometry — Tip device (Q-tip)

Brief: [aerial_cad.md](../../aerial_cad.md) › *Tip device (Q-tip)*
Model: not built.

## Required

- **Bend path — 75° aft over `r/R = 0.92` to 1.0 at radius 8** — `SYNTHETIC`
  → [bend-path.csv](bend-path.csv). Reports the number the brief asks for: the bend cuts the
  swept disc to 0.9821 R against a developed 1.0 R. That reduction **is** the trade — ground
  clearance and tip noise bought with disc area.
  Feeds: the curved spanwise sweep path the outer sections are carried around.
  Source: Hartzell Q-Tip geometry is proprietary; derive the path from the parameters and record it, or measure a real blade — https://hartzellprop.com/products/top-prop/piper/twin-comanche-2-blade-q-tip/
  Without it: *"chord and thickness run continuous through the bend with no kink"* depends entirely on the path being smooth, and an ad-hoc arc is where the kink comes from.

## Inherits

[Fixed-pitch (low-Re)](../fixed-pitch/source-geometry.md) — base blade from Fixed-pitch.
