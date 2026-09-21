# Release status — P2A-M2

**FIT AND ASSEMBLY TESTING ONLY.** Built for the Blue Robotics M200 standard (BR-101376). The resin process is unconfirmed. Manufacturing release stays incomplete until the open inputs and process checks are closed.

P2A-M2 is P2A-M1 rebuilt around the Blue Robotics M200. The blade is unchanged from M1. The pitch was chosen from the 1B-14 design A data point, before any CFD of this design. A forward CFD run has since been made and is archived in `../../../prototype2A_M2_openFOAM/results/P2A_M2_L0_forward/`: 29.1 N at 130 W, stopped at iteration 4467 with the verdict NOT CONVERGED. **It is UNVALIDATED** - one mesh, no mesh-independence study, no prism layers, and never compared against a measurement. It does not qualify this design for release.

| Check | Result | Scope / limitation |
|---|---|---|
| Printed parts | PASS: 4 parts, one valid solid each | rotor, duct_full, motor_support, hub_fit_coupon |
| STL topology | PASS: closed, one component, consistent orientation, no degenerate triangles | |
| STL triangle self-intersections | rotor 0, duct_full 0, motor_support 2, hub_fit_coupon 0 | open3d. Non-zero pairs on the support are coplanar overlaps of tiny triangles on the cable-boss end face; the slicer's mesh repair handles these |
| Motor interface | PASS: the vendor STEP agrees with `parameters.json` within 0.1 mm and 0.5° on 28 features | `reports/motor_interface.json` |
| Blade gates | PASS: 0 folded stations; leg gap 14.53 mm; blade gap 3.41 mm; thinnest section 1.96 mm; trailing edge 0.50 mm | Numeric, on the loft sections |
| Blade pitch and sections | Constant P/D 0.75 (pitch angle 13.9–43.3°); chord 10.0–13.1 mm; t/c 0.17–0.38 | Per station in `reports/blade_sections.csv` |
| Forward rotation | about -Z: counter-clockwise seen from the inlet (-Z); jet toward +Z | Flat-plate sign check, not a performance result |
| Rotor triangle intersection test | 0 non-adjacent contacting triangle pairs | Triangle approximation |
| Exact rotor self-interference | PASS: no errors | OCCT BOPAlgo_CheckerSI, level 5 |
| Other exact self-interference | duct_full PASS, motor_support PASS, hub_fit_coupon PASS | Per part in `geometry_verification.json` |
| Rotor swept diameter | 99.818 mm sampled | Contained in the revolved envelope by exact boolean |
| Rotor/duct gap, full revolution | ≥ 2.03 mm nominal; ≥ 1.33 mm after the 0.70 mm radial budget | Budget is illustrative for resin, not measured |
| Rotor/support gap, full revolution | ≥ 2.50 mm (required 1.5); ≥ 1.70 mm after the 0.80 mm axial budget | No elastic deflection |
| Blade trailing edge to strut | 12.5 mm axial (required ≥ 10) | |
| M200 can in the shroud | PASS: 2.30 mm radial clearance to the spinning can | Vendor geometry |
| M200 base in the shroud | PASS: slide fit, at most 0.40 mm radial play; centres the motor on the duct | Base Ø40 ±0.2 mm |
| Flange ring clear of the jet | PASS: probe points between the struts lie outside the ring | |
| Fixed interfaces | PASS: zero overlap volume in 11 pairs, including the vendor M200 | Face contacts allowed |
| Hub clamp, vents and bolt stacks | PASS: 20 checks in `hardware_stack.json` | Nominal lengths; threads not modelled |
| STEP read-back | PASS: valid single solids; rotor volume difference 0.000% | Exact surface equivalence not certified |
| STL/3MF units | STL numeric mm; 3MF declares millimetres | Each 3MF is placed on its build plate, unscaled |
| Hub fit coupon | INCLUDED | Not yet printed or measured |
| Minimum thickness | PARTIAL: section gate ≥ 1 mm, trailing edge 0.5 mm | No full local-thickness field |
| Printer/resin profile | UNRESOLVED | Printer, resin, build volume and slicer required |
| Motor | RESOLVED: Blue Robotics M200 standard (BR-101376) | ESC, battery voltage and cable routing still open |
| Structural, powered and efficiency checks | NOT PERFORMED | No speed rating, thrust, efficiency or durability claim |

## Clearance method

The rotor tessellation was binned every 0.5 mm along the axis. Each triangle's largest radius was applied over its whole z span, plus 0.05 mm, and the result was revolved into an envelope. An exact boolean found 0 mm³ of rotor outside it. Growing the envelope by g, radially and axially, and intersecting it exactly with a stationary part proves a gap of at least g at every rotation angle. The duct result is the largest such g, to 0.01 mm. The support result comes from bisection. These bounds apply to the nominal, centred CAD with the stated illustrative budgets; real misalignment, tolerances and deformation need measured inputs.

## Next release gates

Confirm the printer, resin and build volume. Print and measure the hub fit coupon against a real M200. Inspect the resin slicer's layers and supports and keep the project. Only then approve a fit-test print. CFD, structural, balance and submerged qualification come later; see `ROADMAP.md`.
