# P2A-M2: L0 mesh check

Meshed 2026-09-15 with `./Allmesh L0` (OpenFOAM v2412). No flow solve has been run yet. Geometry: `geometry/rotor_p2a.stl` and `geometry/stator_p2a.stl` from the prototype's `source/export_cfd.py`. Layout: `geometry/preview.png`.

## Geometry checks (all mandatory, all passed)

| Check | Result |
|---|---|
| `validate_geometry.py` | Rotor radius 49.91 mm (limit 50); duct throat 103.97 mm; tip gap 2.13 mm |
| Rotating zone | r = 51 mm, x = −15.0…17.5 mm: 1.09 mm to the rotor tip, 0.98 mm to the duct, 0.50 mm to the motor pod |
| `surfaceCheck` rotor | Closed, 1 part, not self-intersecting |
| `surfaceCheck` stator | Closed, 1 part, not self-intersecting (only after the struts were lofted; see below) |
| `topoSet` | `mrfZone` 991,054 cells |

## Mesh quality (`checkMesh`: Mesh OK)

| Quantity | P2A-M2 | 1B-14 design B (for comparison) |
|---|---:|---:|
| Domain | 1.5 × 1.0 × 1.0 m (5 D / 10 D / 5 D) | 0.6 × 0.4 × 0.4 m |
| Background cell | 16 mm | 8 mm |
| Cells | 2,475,440 | 2,010,954 |
| Hexahedra / prisms / polyhedra | 2,151,413 / 78,996 / 244,874 | 1,719,508 / 49,526 / 241,861 |
| Max non-orthogonality | 69.9 (average 9.2) | 62.1 |
| Max skewness | 3.56 | 3.66 |
| Max aspect ratio | 9.9 | — |
| Rotor / stator patch faces | 156,624 / 216,032 | 189,673 (rotor) |
| Prism layers | none | none |
| Meshing time | 19.0 min (refine 4.4, snap 14.2) | 14.1 min |
| Peak memory | 3.6 GB | — |

Cells per refinement level: 0: 359,448 · 1: 7,808 · 2: 39,634 · 3: 49,243 · 4: 406,557 · 5: 964,235 · 6: 648,515. Level 6 (0.25 mm) is the rotor surface, level 5 (0.5 mm) the stator surface and level 4 (1 mm) the rotor region. The wake region is level 2 (4 mm) and level 0 (16 mm) the far field.

Max non-orthogonality sits just under snappyHexMesh's limit of 70. That is acceptable for the solver with `nNonOrthogonalCorrectors 1` (`system/fvSolution`), but refining further may push faces past it. Watch this value if levels change.

## Problems found and fixed before this mesh passed

1. **A parallel shell command changed the working directory**, so the first launch looked for `./Allclean` in the wrong folder. Background commands now use absolute paths.
2. **The stator failed `surfaceCheck`**, with 150–190 points on one strut. The extruded struts tessellated into full-span triangles about 0.01 mm wide (aspect ratio up to 2700). OpenFOAM's check flagged these, and how many it flagged depended on how the surface lined up with the axes. Splitting long edges made it worse. Lofting each strut through 9 identical sections, as the rotor blades are built, fixed it.
3. **Starting each strut exactly at the flange ring's front plane** made the ring fail to fuse. The struts now start 0.2 mm behind it.

## Not checked yet

- How closely the snapped rotor patch follows the STL. On design B the snapped mesh stayed within 0.06 mm of the geometry; this case has not been compared.
- The wake region is 4 mm cells, twice as fine as design A's wake but still coarse for the swirl. Decide after the first solve.
- No mesh-independence study (L1/L2).

## Next step (needs a go-ahead)

`./Allsolve 300`, then `python3 scripts/convergence_report.py --window 100 --batches 3`, to confirm thrust toward −x, positive shaft power and a +x jet. Then the full 5000-iteration forward run. The 300-iteration check measured 4.43 s per iteration on 6 cores, so that is about 6.2 hours. See `RUN_GUIDE.md` and `P2A_M2_check_300.md`.
