# Source geometry — Podded azimuth thruster

Brief: [underwater_cad.md](../../underwater_cad.md) › *Podded azimuth thruster*
Model: not built.

## Required

- **Pod body profile** — `SYNTHETIC` → [pod-body.csv](pod-body.csv)
  Ellipsoidal nose, parallel mid-body, faired conic tail at pod Ø `0.5 D` and length `2.5 D`
  per the brief. The tail is longer than the nose because after-body separation is what costs
  a pod its efficiency. NOT ABB Azipod geometry, which is proprietary.
  Feeds: the faired nose and tail cone of the pod, as a body of revolution.
  Source: An axisymmetric fairing form (ellipsoidal nose, conic tail) sized around the motor envelope.
  Without it: the pod is a shape rather than a fairing, and its wake into the propeller is undefined.

- **Strut symmetric section coordinates** — `GENERATED` → [naca0015-strut.csv](naca0015-strut.csv)
  Feeds: the strut joining pod to hull plate.
  Source: A symmetric section — NACA 00xx, computable from NACA four-digit thickness equation — generated, not tabulated
  Without it: *"the propeller clears the strut leading edge by the stated margin"* is measurable, but the strut's own drag and its wake into a tractor propeller are not.

## Inherits

[Fixed-pitch (FPP)](../fixed-pitch/source-geometry.md) — the propeller is the FPP brief unchanged.
