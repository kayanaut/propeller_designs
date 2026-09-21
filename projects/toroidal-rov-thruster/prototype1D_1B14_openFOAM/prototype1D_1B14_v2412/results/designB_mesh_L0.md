# Design B (front-opening loops): L0 mesh check

Checked 2026-09-14. No flow solve has been run on design B yet. Geometry details are in [../geometry/GEOMETRY_REPORT.md](../geometry/GEOMETRY_REPORT.md), and renders in [../geometry/preview.png](../geometry/preview.png).

## Geometry checks (`Allmesh`, all mandatory, all passed)

| Check | Result |
|---|---|
| `validate_geometry.py` | Rotor radius 49.91 mm (limit 50); duct throat 104.00 mm; duct clearance 2.09 mm at x = −1.14 mm (limit 2.0) |
| MRF zone margins | r = 51 mm, x = −16.5…16.5 mm; 1.09 mm to rotor, 1.00 mm to duct (limit 0.5) |
| `surfaceCheck` rotor | Closed, 1 part, not self-intersecting, 63,046 triangles, min quality 2.9×10⁻⁶ |
| `surfaceCheck` duct | Closed, 1 part, not self-intersecting |
| `topoSet` | `mrfZone` 1,193,961 cells |

The minimum triangle quality comes from flat slivers on the hub cylinder. Splitting the hub to remove them made `surfaceCheck` fail at the split seams, so the hub stays whole; see [designA_stacked_loops_L0/CHECKS.md](designA_stacked_loops_L0/CHECKS.md), section 3. The measurements below confirm again that these slivers do not distort the mesh.

## Mesh quality (`checkMesh`: Mesh OK)

| Quantity | Design B | Design A (for comparison) |
|---|---:|---:|
| Cells | 2,010,954 | 1,893,009 |
| Hexahedra / prisms / polyhedra | 1,719,508 / 49,526 / 241,861 | 1,631,544 / 44,899 / 216,525 |
| Max non-orthogonality | 62.1 | 66.7 |
| Max skewness | 3.66 | 3.42 |
| Rotor patch faces | 189,673 | 169,661 |
| Prism layers | none | none |
| Meshing time | 14.1 min | 11.6 min |

## Does the volume mesh keep the rotor shape?

The snapped rotor patch was compared with `geometry/rotor_1B14.stl`.

**Overall:**

| Measure | Snapped mesh vs STL |
|---|---|
| Enclosed volume | 28,469 vs 28,476 mm³ (−0.02%) |
| Surface area | 13,317 vs 13,329 mm² (−0.09%) |
| Mesh point to STL distance | P50 0, P95 0, P99 0.001 mm, max 0.059 mm |

**By region:**

| Region | Mesh points | P95 distance | Max distance |
|---|---:|---:|---:|
| Trailing edge | 10,030 | 0.004 mm | 0.059 mm |
| Leading edge | 10,797 | 0.000 mm | 0.040 mm |
| Root / flare | 8,026 | 0.000 mm | 0.012 mm |
| Rest of blade | 135,343 | 0.000 mm | 0.001 mm |
| Hub cylinder | 34,548 | 0.000 mm | 0.043 mm |
| Hub end caps | 20,162 | 0.000 mm | 0.000 mm |

The worst point sits on a trailing edge near the loop apex (x = 12.9 mm, r = 43.6 mm).

**Trailing edge.** The blunt trailing edge (designed 0.4 mm) is kept. Across the TE midline the snapped mesh measures 0.54–0.63 mm at stations 20, 40, 80 and 100, and 0.85 mm at the apex (station 60). That metric reads wide where the edge curves, as it does at the apex.

**Conclusion.** The L0 mesh reproduces design B to within 0.06 mm everywhere. The 0.25 mm rotor cells capture the 0.4 mm trailing edge as a blunt edge; they neither round it off nor lose it.
