# Design A (stacked loops), L0 baseline: sign, near-wall and surface checks

Checked 2026-09-14 on the archived L0 run (1.89 M cells, 5000 iterations). Force and moment values are means over iterations 2001–5000. Re-create the numbers with:

```bash
python3 scripts/convergence_report.py --case results/designA_stacked_loops_L0
```

## 1. Direction and force signs: confirmed

CFD frame: rotation axis +x, omega = +314.16 rad/s (right-handed about +x), jet designed toward +x.

| Quantity | Pressure | Viscous | Total |
|---|---:|---:|---:|
| Rotor Fx (N) | −18.91 | +0.53 | **−18.38** |
| Duct Fx (N) | −8.74 | +0.09 | **−8.65** |
| Assembly Fx (N) | | | **−27.03 ± 0.45** |
| Rotor Mx (N·m) | −0.368 | −0.083 | **−0.451 ± 0.006** |
| Duct Mx (N·m) | | | +0.332 |

- **Thrust direction.** Assembly Fx is negative, so the thrust on the assembly points toward −x, opposite the +x jet. It is negative in 100% of samples after iteration 500.
- **Jet direction.** Flow through the rotor annulus is +16.0 L/s, entering at the bellmouth. The wake swirls positively about +x, which matches the rotation sense.
- **Shaft power.** Shaft power = −omega·Mx = **+141.7 ± 1.9 W**. The water's moment on the rotor opposes the rotation, so the motor drives the rotor. Mx is negative in 100% of samples after iteration 500.
- **Duct torque.** The duct reacts +0.33 N·m, 74% of the rotor torque: it straightens most of the swirl.
- **Viscous share.** Viscous forces carry 18% of the rotor torque, so torque and power depend on the near-wall treatment (section 2).

`scripts/convergence_report.py` now reports the signed Fx and Mx, derives shaft power as −omega·Mx, and flags a non-positive power or a force direction that disagrees with the jet.

## 2. Near-wall treatment: no layers, y+ mostly in the buffer layer

- **No prism layers were generated.** `addLayers false`, and `log.snappyHexMesh` has no layer phase. The 44,899 prisms in `log.checkMesh` come from snapping.
- **Wall treatment.** `nutUSpaldingWallFunction` with `kqRWallFunction` and `omegaWallFunction`. These are blended functions, so any y+ is allowed, but accuracy is worst in the buffer layer.
- **Rotor surface cells.** Level 5: 0.25 mm faces, first cell centre about 0.125 mm off the wall.

Area-weighted y+ at iteration 5000. The rotor mean has stayed at 34.7–35.2 on every write from iteration 500 to 5000.

| Patch | P5 | P50 | P95 | max | y+ < 1 | 1–5 | 5–30 (buffer) | 30–100 | > 100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rotor | 7.6 | 24 | 77 | 157 | 0.0% | 0.8% | **60.7%** | 37.9% | 0.6% |
| duct | 1.3 | 10 | 175 | 326 | 2.3% | 34.5% | 23.2% | 24.6% | 15.4% |

- **Where y+ is highest.** Rotor: near the loop apex (x ≈ 0–2 mm, r ≈ 46–47 mm). Duct: at the throat (x ≈ 0, r = 52 mm), opposite the blade tips.
- **Implied friction velocity** on the rotor: median u_τ ≈ 0.22 m/s, P95 ≈ 0.65 m/s. Putting the first cell centre at y+ ≈ 1 needs a first layer of about 10 µm (median) or 3 µm (P95).

**Assessment.** This mesh neither resolves the viscous sublayer nor sits cleanly in the log layer, so the viscous torque carries an unquantified modelling uncertainty. Coarsening the wall cells into the log layer (y+ 30–100) would need about 0.6 mm faces, which would lose the 2.7–4.4 mm thick blades and the 0.4 mm trailing edge. The practical route is prism layers; see `results/layer_trial_L0.md`.

## 3. Poorest surface triangles: slivers on the hub, shape preserved

`log.surfaceCheck.rotor` reports a minimum triangle quality of 2.05×10⁻⁶ (OpenFOAM definition: area over the area of the equilateral triangle in the same circumcircle). The table below classifies every STL triangle by location.

| Region | Triangles | q < 1e-3 | q < 0.05 | Min q |
|---|---:|---:|---:|---:|
| hub cylinder | 679 | 40 | 147 | 2.05e-06 |
| hub end caps | 164 | 96 | 146 | 1.61e-04 |
| trailing edge | 2412 | 0 | 192 | 3.69e-03 |
| leading edge | 19087 | 3 | 3 | 1.12e-04 |
| root / flare | 2774 | 0 | 0 | 7.33e-02 |
| rest of blade | 20596 | 0 | 117 | 6.33e-03 |

- **Where the worst triangles are.** Every triangle with q < 10⁻⁵ lies on the hub cylinder, as 17 × 0.13 mm strips stretched between blade-hub intersection curves (OCC tessellation of one large cylindrical face). The end-cap fans are the next worst.
- **Blade slivers.** They follow the 0.4 mm blunt trailing-edge strip. The roots are clean.

**Does the volume mesh keep the shape?** The snapped rotor patch was compared with the STL:

| Measure | Snapped mesh vs STL |
|---|---|
| Enclosed volume | 26,770 vs 26,776 mm³ (−0.02%) |
| Surface area | 11,644 vs 11,653 mm² (−0.08%) |
| Mesh point to STL distance | P50 0, P95 0, P99 0.0005 mm, max 0.034 mm |

Distance by region:

| Region | P95 | Max |
|---|---:|---:|
| Trailing edge | 0.003 mm | 0.034 mm (near the root, r = 14.2 mm) |
| Hub cylinder | 0 | 0.018 mm |
| Hub end caps, root / flare, leading edge | ≤ 0.004 mm | |

At five stations along the loop the snapped trailing edge stays blunt, 0.50–0.58 mm across the TE midline against the designed 0.4 mm. It is neither collapsed nor rounded off.

**Conclusion.** The slivers lie flat on analytic hub surfaces and do not distort the volume mesh.

Removing them at the source was tried on design B, and rejected:

| Hub treatment | OpenFOAM self-intersection check | Min hub triangle quality |
|---|---|---|
| Unsplit (kept) | passes | 2.9×10⁻⁶ |
| Split 24 × 10 before fusing | fails, 20 locations at split seams | 1.0×10⁻² |
| Split 12 × 5 | fails, 3 locations | 6.7×10⁻⁴ |
| Split along the axis only (1 × 10) | fails, 2 locations | 8.1×10⁻⁵ |
| Split around only (24 × 1) | passes | 5.8×10⁻¹⁰ |
| Unsplit, interior mesh vertices | passes | 2.9×10⁻⁶ |
| Split after fusing | invalid solid | |

Every split along the axis makes `surfaceCheck` flag the circular split seams, and `Allmesh` treats that check as mandatory. The hub therefore stays unsplit: its slivers lie flat on the cylinder and, as measured above, do not distort the snapped mesh.
