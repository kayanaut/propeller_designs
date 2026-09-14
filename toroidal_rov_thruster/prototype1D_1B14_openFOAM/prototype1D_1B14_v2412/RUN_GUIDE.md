# Running prototype 1B-14 on OpenFOAM v2412

A working copy of `../prototype1D_1B14`, fixed so it runs on OpenFOAM v2412. The original folder is unchanged.
Tested on this PC on 2026-09-14: the L0 mesh builds, and the solver runs on 8 cores.

## Warning: the geometry has a known problem

- The rotor reaches **55.5 mm** in radius, not the 50 mm in the design notes.
- Near the outlet end of the duct, the rotor goes **0.57 mm into the duct wall** (at x = +15.9 mm).
- `scripts/validate_geometry.py` rejects the rotor for this reason, so the scripts skip that check.

Use the results to learn the workflow and get rough numbers. Don't treat thrust or torque as design data until the rotor STL is fixed.

## What the folders mean

| Folder | Holds | Examples here |
|---|---|---|
| `0.orig/` | Starting values and boundary conditions (copied to `0/` before solving) | `U` velocity, `p` pressure, `k`/`omega`/`nut` turbulence |
| `constant/` | Physics and mesh | `MRFProperties` (3000 rpm spin), `transportProperties` (seawater), `polyMesh/` (after meshing) |
| `system/` | How to mesh and solve | `controlDict` (iterations, outputs), `fvSchemes`, `fvSolution`, meshing dictionaries |

## Step 0: install ParaView, the results viewer (once)

```bash
sudo apt install paraview
```

## Step 1: open an OpenFOAM terminal

Run this in every new terminal before any OpenFOAM command:

```bash
openfoam2412
cd ~/Desktop/LX/thruster/drone_propeller_designs/toroidal_rov/prototype1D_1B14_openFOAM/prototype1D_1B14_v2412
```

Optional 2-minute warm-up to confirm the install works:

```bash
cp -r $FOAM_TUTORIALS/incompressible/simpleFoam/pitzDaily ~/pitzDaily && cd ~/pitzDaily
blockMesh && simpleFoam && touch p.foam && paraview p.foam
```

## Step 2: build the mesh (about 16 minutes, 3.3 GB RAM)

```bash
./Allclean
./Allmesh L0
```

`Allmesh` runs these steps. Each step writes its output to a `log.<name>` file.

1. `surfaceTransformPoints`: converts the STLs from mm to m and turns the axis from z to x.
2. `surfaceCheck`: checks the STLs are closed surfaces.
3. `blockMesh`: the background box, 8 mm cells.
4. `surfaceFeatureExtract`: finds sharp edges.
5. `snappyHexMesh`: cuts out the rotor and duct and refines the cells around them. Watch it with `tail -f log.snappyHexMesh` in a second terminal.
6. `topoSet`: marks the cells that spin with the rotor (`mrfZone`).
7. `checkMesh`: reports mesh quality.

Expected in `log.checkMesh`: about 2.2 M cells, and `Failed 1 mesh checks` for 21 skewed faces. That is acceptable for L0.

Look at the mesh in ParaView: `paraview case.foam`, then Apply. Use a Slice filter with normal (0 0 1) to see the cells around the blades.

## Step 3: solve (about 2 hours on 8 cores)

Wait until `./Allmesh` has finished; `log.checkMesh` appears at the very end. Then:

```bash
./Allsolve
```

To use more cores, set `numberOfSubdomains` in `system/decomposeParDict` first, for example 16.

While it runs, in another terminal (after running `openfoam2412` and `cd` into the case):

```bash
tail -f log.simpleFoam                               # live solver output
tail postProcessing/rotorForces/0/force.dat          # rotor force, newtons
```

To stop early, press Ctrl+C, then run `reconstructPar -latestTime`. Rerunning `./Allsolve` does not continue from where it stopped: it restores `0/` and skips steps that already have a log. To continue, run `mpirun -np 8 simpleFoam -parallel > log.simpleFoam.2`.

## Step 4: read the results

All forces are what the water applies to each part, in newtons, at `CofR (0 0 0)`.

| Quantity | Where | How |
|---|---|---|
| Thrust | `rotorForces/0/force.dat` + `ductForces/0/force.dat` | Add the two `total_x` columns. The sign gives the direction. |
| Torque Q | `rotorForces/0/moment.dat` | `total_x`, in N·m |
| Shaft power | | P = 314.16 × Q (W). The motor budget is 300 W electrical. |
| Minimum pressure | `pressureRange/0/fieldMinMax.dat` | min × 1025 = Pa relative to ambient |
| y+ | `yPlus/0/yPlus.dat` | Much greater than 1 at L0 is expected; wall functions handle it. |
| Convergence | `residuals/0/solverInfo.dat` | Residuals flat, and thrust and torque constant over the last few hundred iterations |

In ParaView, open `case.foam`, select the last time step, and colour by `p` or `U`. Slice along the axis to see the jet.

## What was changed from the original case, and why

| Change | Why |
|---|---|
| `farfield` changed from a `symmetryPlane` to open boundaries | v2412 stops with "not planar" when four faces facing different ways are one symmetry patch. Walls around the domain also block the water the thruster draws in. |
| `inlet` changed from fixed zero velocity to total pressure | A fixed zero velocity acts like a wall. Bollard means still water, not a sealed inlet. |
| Refinement of the whole rotor cylinder: level 5 → 3 | Level 5 everywhere would be about 27 M cells at L0, far beyond 16 GB of RAM. |
| `mrfZone` radius 51.5 → 57 mm | Blade tips reach 55.5 mm. Parts outside the zone would not spin. |
| `potentialFoam` and `setFields` removed | They did nothing for a start from still water, and `potentialFoam` needed a missing entry. |
| `residuals` changed to `solverInfo`; `features` changed to `{ }` blocks | v2412 syntax |
| `addLayers false` | Twelve 0.02 mm layers rarely build on the first attempt. Turn layers on after L0 works. |
| `maxGlobalCells` 24 M → 8 M | Stops the mesher before it runs out of memory. |
| Logs, parallel solve, and `Allmesh`/`Allsolve` split | So you can inspect the mesh before solving. |

## Before L1 and L2

With the README's surface levels, L1 would be roughly 10 M cells and L2 100 M or more. That is too big for this PC. Resize the levels using the L0 cell count before trying them.
