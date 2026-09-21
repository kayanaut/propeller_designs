# Prism-layer trial on the design B L0 mesh (mesh only, no solve)

Run 2026-09-14 on a copy of the design B L0 mesh. The main case mesh has no layers and was not changed. Inputs and logs are in [layer_trial_L0/](layer_trial_L0/): `snappyHexMeshDict.layers`, `layer_trial.sh`, `log.snappyLayers.gz`, `log.checkMesh`.

## Why

- Design A had no prism layers, and 61% of the rotor area sat at y+ 5–30, the range where wall functions are least accurate.
- Viscous forces make up 18% of the rotor torque, so near-wall resolution matters for torque and power.
- The friction velocity implied by design A was median 0.22 m/s and 95th percentile 0.65 m/s. Putting the first cell centre at y+ ≈ 1 needs a first layer of about 10 µm.

## Settings

`snappyHexMesh -dict system/snappyHexMeshDict.layers -overwrite` with `castellatedMesh false; snap false; addLayers true;`. This adds layers to the existing snapped mesh.

| Setting | Value |
|---|---|
| Layers on rotor and duct | 12 |
| First layer thickness | 10 µm (`firstLayerThickness 1e-5`, `relativeSizes false`) |
| Expansion ratio | 1.2 |
| Target stack | 0.40 mm total; last layer 74 µm under 250 µm rotor faces |
| Layer controls | featureAngle 60, maxThicknessToMedialRatio 0.3, nLayerIter 50, nRelaxedIter 20 |
| Quality controls | as the main mesh, relaxed maxNonOrtho 75 |

## Results

| Quantity | Result |
|---|---|
| Run time / peak memory | 31.7 min / 7.1 GB |
| Cells | 2,010,954 → 3,837,513 (+91%) |
| Wall faces with layers | 278,500 of 301,711 (92.3%); **23,211 faces (7.7%) without layers** |
| Layer cells added | 1.83 M of 3.62 M for full stacks (50%) |
| Rotor: mean layers / thickness | 6.25 of 12 / 0.314 mm (79.8% of target) |
| Duct: mean layers / thickness | 5.73 of 12 / 0.337 mm (86% of target) |
| snappyHexMesh final check | **50 faces fail its quality controls**: 39 with non-orthogonality > 70, 11 with face-decomposition tet quality < 1e-20 |
| `checkMesh` | Mesh OK; max non-orthogonality 74.6; max aspect ratio 65; max skewness 3.66 |

## Expected y+ (estimate: design B has not been solved)

These estimates use design A's friction velocity. A solve is needed to confirm them.

| Wall faces | First cell centre | y+ at median u_τ | y+ at P95 u_τ | y+ at the apex hot spot (u_τ ≈ 1.3 m/s) |
|---|---|---:|---:|---:|
| Full 12-layer stack | 5 µm | ≈ 1.0 | ≈ 3 | ≈ 6 |
| Reduced stack, e.g. 6 layers filling 0.31 mm at ratio 1.2 (first layer ≈ 30 µm) | ≈ 15 µm | ≈ 3 | ≈ 9 | ≈ 19 |
| No layers (7.7% of faces) | 125 µm | ≈ 24 | ≈ 77 | ≈ 157 |

## Assessment

The layers work on most of the wall but are **not yet good enough for a production run**:

- **Coverage.** About half the layer cells are missing, and 7.7% of wall faces have none. Reduced and missing stacks leave part of the surface in the buffer layer again, so the uncertainty in viscous torque shrinks but does not go away.
- **Quality.** 50 faces fail snappyHexMesh's own criteria. With non-orthogonality up to 74.6, the solver would need `nNonOrthogonalCorrectors 2`.
- **Cost.** A layered solve would have about 3.8 M cells: roughly 2× the time per iteration (about 6 s on 6 cores against 3.1 s for design A), and the thin wall cells usually slow convergence. 5000 iterations would take about 8–10 hours on this laptop, which is a long run, so it was not attempted. Solver memory, about 4 GB, fits.

## Recommended next layer settings (not yet tested)

1. **Aim for y+ 1–3 rather than ≤ 1:** 8 layers, first layer 20 µm, expansion ratio 1.25 (about 0.3 mm total). That means fewer collapses and about 1.2 M extra cells instead of 1.8 M. The Spalding and omega wall functions stay valid through y+ ≈ 1–5.
2. **Let layers wrap trailing edges and the apex:** `featureAngle 130`, `maxThicknessToMedialRatio 0.5`, `nSmoothNormals 5`.
3. **Add the layers in the full snappyHexMesh run** (castellate, snap, then layers) instead of afterwards, and write `writeFlags (layerFields)`. That lets you check the `nSurfaceLayers` field in ParaView and see exactly where layers are missing.
4. **Solve and check:** add `nNonOrthogonalCorrectors 2` to the solver settings, then check y+ and layer coverage after about 500 iterations before committing to a full run.
