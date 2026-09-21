# Running prototype 1B-14 on OpenFOAM v2412

A self-contained CFD case for the 1B-14 toroidal thruster at bollard (still water, 3000 rpm). The original `../prototype1D_1B14` is left unchanged.

## The geometry is regenerated, not recovered

The recovered `prototype1B_rotor.stl` was not a valid solid, so it cannot give meaningful results:
- its loop blades folded into themselves at the tip;
- the roots twisted and floated off the hub;
- every surface pointed inward;
- it measured 111 mm across.

`scripts/make_geometry.py` builds a new rotor from the same design parameters (`prototype1B_design.json`). This is a new parametric design that follows those parameters, not the recovered shape. [geometry/GEOMETRY_REPORT.md](geometry/GEOMETRY_REPORT.md) lists every parameter, every assumption, and the checks it passed.

| Design | Loops | Status |
|---|---|---|
| A: stacked legs | Legs one behind the other along the axis; closed in the front view | Meshed and solved (L0, 5000 iterations). Archived in [results/designA_stacked_loops_L0](results/designA_stacked_loops_L0), with [CHECKS.md](results/designA_stacked_loops_L0/CHECKS.md) |
| **B: front-opening loops** (current) | Each loop opens about 56° in the front view, with a round apex, like the reference toroidal rotor | Geometry and L0 mesh checked (Mesh OK, 2.01 M cells, shape kept within 0.06 mm); not yet solved. See [results/designB_mesh_L0.md](results/designB_mesh_L0.md) |

Design B's printed part (`geometry/rotor_1B14.step`) has a ring hub with 3 spokes and a splined bore. The spline dimensions are placeholders: confirm them against your shaft before printing. The CFD STL keeps a closed hub.

To see the shape, run `python3 scripts/render_geometry.py` and open `geometry/preview.png`.

Near-wall resolution: neither design has prism layers yet, and on design A 61% of the rotor area sat at y+ 5–30, where wall functions are least accurate. A mesh-only layer trial on design B is recorded in [results/layer_trial_L0.md](results/layer_trial_L0.md).

Force signs in the reports: axial forces keep their sign (negative = toward −x, which is thrust for a +x jet), and shaft power is −ω × rotor moment (must be positive).

## What the folders mean

| Folder | Holds |
|---|---|
| `geometry/` | Rotor and duct STLs for CFD (metres), rotor STEP for CAD/printing (mm), section table, geometry report |
| `0.orig/` | Starting values and boundary conditions (copied to `0/` before solving) |
| `constant/` | Physics: `MRFProperties` (3000 rpm spin), `transportProperties` (seawater); the mesh after meshing |
| `system/` | How to mesh and solve: `controlDict` (iterations, outputs), meshing dictionaries, `topoSetDict` (rotating zone) |
| `scripts/` | Geometry generator, geometry checks, mesh level setup, convergence report |

## Step 0: once per computer

```bash
sudo apt install paraview
```

## Step 1: open an OpenFOAM terminal

Do this in every new terminal:

```bash
openfoam2412
cd <repo>/projects/toroidal-rov-thruster/prototype1D_1B14_openFOAM/prototype1D_1B14_v2412
```

## Step 2: geometry (only when design parameters change)

The finished geometry is already in `geometry/`. To rebuild it (about 15 s):

```bash
python3 scripts/make_geometry.py
```

## Step 3: mesh (about 12 minutes, 3 GB RAM)

Tested result: 1.89 M cells, rotating zone 1.08 M cells, max skewness 3.42, max non-orthogonality 66.7, `Mesh OK.`

```bash
./Allclean
./Allmesh L0
```

`Allmesh` stops at the first failed check and prints what failed. Each step writes a `log.<name>` file.

| Step | Checks |
|---|---|
| `validate_geometry.py` | Units, closed outward surfaces, rotor inside 100 mm, at least 2 mm to the duct, rotating zone clear of rotor and duct |
| `surfaceCheck` | STLs closed, one piece each, not self-intersecting |
| `blockMesh`, `snappyHexMesh` | Background box, then cut out rotor and duct and refine around them |
| `topoSet` | Rotating zone (`mrfZone`) is not empty |
| `checkMesh` | Must print `Mesh OK.` |

Look at the mesh with `paraview case.foam`. Use Surface With Edges and a Slice through the axis.

## Step 4: check the flow direction (about 15 minutes)

Which way the water goes depends on the rotation direction, so check it before the long run:

```bash
./Allsolve 300
python3 scripts/convergence_report.py --window 100
```

Read the `Flow direction` line:

- "bellmouth intake ... as designed": go to step 5.
- "REVERSED": in `constant/MRFProperties`, change `omega 314.159265359` to `omega -314.159265359`, then repeat step 4.

## Step 5: baseline run (about 3 hours on 6 cores)

This laptop solves fastest on its 6 performance cores. More ranks land on the slower efficiency cores and hold every other rank back. Measured: 6 ranks 2.9 s per iteration, 12 ranks 5.1 s.

```bash
./Allsolve
```

`Allsolve` always starts from iteration 0 and runs 5000 iterations. While it runs, use another terminal (after `openfoam2412` and `cd`):

```bash
tail -f log.simpleFoam                              # live solver output
python3 scripts/convergence_report.py               # converged yet?
```

If the report says NOT CONVERGED at 5000 iterations, raise `endTime` in `system/controlDict` while the solver is still running; it picks up the change. Starting `./Allsolve` again would begin from 0.

## Step 6: record the baseline

```bash
python3 scripts/convergence_report.py --write BASELINE.md
```

The report gives one of three verdicts:

| Verdict | Meaning |
|---|---|
| CONVERGED | Thrust, torque and flow averaged over the last 500 iterations differ by < 0.5% from the 500 before and swing < 1% within them; every residual has dropped 1000× or stopped changing. |
| STATISTICALLY STEADY | The answer keeps oscillating, but about a fixed average: over the last 3000 iterations each average is known to within ±2% (95%), and every residual has stopped changing. Use the averages with their ± values. |
| NOT CONVERGED | Neither. Look at which line fails before trusting any number. |

Reported values are averages over the last 3000 iterations, with a 95% ± range. The first baseline (5000 iterations, 4 h 19 min on 6 cores) is recorded in [results/designA_stacked_loops_L0/BASELINE.md](results/designA_stacked_loops_L0/BASELINE.md).

## Reading the numbers

| Quantity | Meaning |
|---|---|
| Thrust | Force pushing the thruster, opposite the jet (+x jet gives thrust toward −x) |
| Torque | Twisting load on the shaft (N·m) |
| Shaft power | ω × torque, in W. The motor budget is 300 W electrical. |
| T/P | Thrust per watt: the main figure of merit for bollard thrust |
| Min wall pressure and cavitation margin | Lowest pressure on the rotor and on the duct, and how far it stays above the pressure where seawater boils (cavitates) at 1 m depth. "Min pressure anywhere" can be an artefact at the edge of the rotating zone, so use the wall values. |
| y+ | Wall cell size in viscous units. Large values are expected at L0; wall functions handle them. |

In ParaView, open `case.foam`, select the last time, colour by `p` or `U`, and slice along the axis to see the jet.
