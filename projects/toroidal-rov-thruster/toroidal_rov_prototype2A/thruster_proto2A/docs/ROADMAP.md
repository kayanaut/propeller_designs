# Prototype 2A roadmap

Where the toroidal ROV thruster stands, and what comes next. Last updated 2026-09-15.

| Phase | Item | Status |
|---|---|---|
| 1 | Review M0: stalled pitch law (P/D 0.55–7.8), blunt sections, 3 mm tip gap, front nut clamping the shaft step | Done |
| 1 | M1: constant P/D 0.75 on a true helix, NACA sections, apex solved to the envelope, foil duct with 2 mm tip gap, foil struts, resin assumptions | Done |
| 2 | Choose the motor: Blue Robotics M200 (the T200's motor) | Done |
| 2 | M2: M200 hub (collar counterbore, D-flat drive, 2× M3 face screws, vent passages), shroud sized to the M200 base, radial cable exit, M3 × 8 base screws | Done: every gate in `RELEASE_STATUS.md` passes |
| 2 | Vendor M200 STEP aligned and cross-checked against the parameters (0.1 mm / 0.5°); zero overlap with every printed part | Done |
| 2 | CFD case `prototype2A_M2_openFOAM`: geometry export, 5 D / 10 D / 5 D domain, wake refinement, forward rotation; L0 mesh | Done: Mesh OK, 2.48 M cells, max non-orthogonality 69.9, 19 min, 3.6 GB (`results/P2A_M2_mesh_L0.md` in the case) |
| 3 | Short run, 300 iterations, to confirm the thrust sign and flow direction | Done: thrust toward −x, positive shaft power, jet +x. Unconverged values about 31 N, 0.5 N·m, 155 W, still rising (`results/P2A_M2_check_300.md` in the case) |
| 3 | Forward L0 solve (stopped at iteration 4467 by choice) | Done: 29.1 N (rotor 17.9, duct and support 11.3), 0.413 N·m, 130 W, 0.225 N/W, 18.1 L/s. Torque still drifting about 2%. Rotor minimum pressure −180 kPa, so cavitation shallower than about 8 m (`results/P2A_M2_L0_forward/` in the case) |
| 3 | Reverse L0 solve (`omega +314.159`, about 6 h); a run near 3300 rpm to check the 35 N target | Needs your go-ahead |
| 3 | Reduce the suction peak at the loop apex (lighter apex loading, higher `closure_t_c` or chord); recheck the minimum pressure | Next design step |
| 4 | Choose the resin printer and resin; check the 134 mm parts fit the build plate | Waiting on printer and resin |
| 4 | Print the hub fit coupon and test it on a real M200; set the allowances | Waiting on printer and resin |
| 4 | Print the rotor, duct and support; dry fit; hand-turn check | Later |
| 4 | Static balance check and a soak test for resin creep under the clamp | Later |
| 5 | Bollard test rig: load cell (HX711), power meter, forward and reverse | Later |
| 5 | Printed pitch ladder (P/D 0.65 / 0.75 / 0.85) tested on the rig | Later |
| 6 | Refinements from the data: swirl-recovery stator vanes, 4–5 struts, lighter apex loading, inlet guard | Later |
| 6 | ROV mounting lugs, cable routing to the frame, penetrator | Later |

## Decisions so far

| Decision | Choice | Why |
|---|---|---|
| Rotor | Keep P2A's own loop path, fix the pitch and sections | The loop shape stays; M0's pitch law stalled the outer blade |
| Process | Resin (SLA/MSLA) | Fine trailing edges and hub fits |
| Motor | Blue Robotics M200 | Proven flooded motor. Its 390 W at 16 V is roughly the 250–300 W shaft power the 35 N target needs, scaled from design A |
| This round | CAD, checks and a CFD mesh; no solver runs without a go-ahead | Solves take hours on this laptop |

## Things learned building M2

- **Geometry check:** OpenFOAM's `surfaceCheck` flagged full-span triangles about 0.01 mm wide on extruded struts. Lofting the struts through 9 sections fixed it.
- **Boolean fuse:** a strut leading-edge vertex in the flange ring's front plane stopped the ring fusing; the struts now start 0.2 mm behind that plane.
- **Volumes:** OpenCascade's default volume under-counts thin spline faces, by 14% on a strut. Reports now use adaptive integration.
- **Printed support STL:** it keeps two coplanar overlaps of 0.2 mm² triangles on the cable-boss end face. Slicer mesh repair handles these.
