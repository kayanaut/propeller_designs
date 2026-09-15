# P2A-M2 CFD case — run guide

This case calculates bollard (still-water) thrust, torque and power for prototype 2A revision M2 at 3000 rpm, with OpenFOAM v2412. It is built from the 1B-14 case (`../prototype1D_1B14_openFOAM/prototype1D_1B14_v2412/`) and uses the same physics:
- steady rotating-zone (MRF) solver, `simpleFoam`;
- k-omega SST turbulence;
- seawater;
- open inlet, outlet and sides.

**What changed from 1B-14:**
- Two surfaces: `rotor` (spins) and `stator` (the duct, struts and motor pod, which do not spin).
- A bigger domain (5 D upstream, 10 D downstream, 5 D radius) and a refined wake region, as recommended after the design A run.
- Forward rotation is `omega -314.159265359`: the P2A rotor turns the opposite way to 1B-14.

## Folder layout

| Path | What it is |
|---|---|
| `geometry/` | `rotor_p2a.stl`, `stator_p2a.stl` (metres, axis +x), `cfd_geometry.json`, `preview.png` |
| `system/` | Mesh and solver settings. `blockMeshDict` and `snappyHexMeshDict` are generated from their `.template` files |
| `constant/` | `MRFProperties` (spin), `transportProperties` (water), `turbulenceProperties`; the mesh after meshing |
| `0.orig/` | Starting and boundary values; copied to `0/` when a run starts |
| `scripts/` | `configure_mesh.py`, `validate_geometry.py`, `render_cfd_geometry.py`, `convergence_report.py` |
| `results/` | Written-up results |
| `MESH_SPEC.yaml` | The mesh plan in one place |

## Step 1: make the geometry

The surfaces come from the prototype's CAD:

```bash
cd ../toroidal_rov_prototype2A/thruster_proto2A
python source/export_cfd.py
```

This writes `exports/cfd/` and copies the STLs into this case's `geometry/`. It builds a simplified CFD shape:
- the rotor hub is closed and extended to x = 17 mm;
- the flooded motor shroud is filled into a solid pod starting at x = 18 mm;
- holes, slots and the cable boss are left out.

To see where everything sits:

```bash
python3 scripts/render_cfd_geometry.py
```

This writes `geometry/preview.png`.

## Step 2: open an OpenFOAM shell

```bash
openfoam2412
cd ~/Desktop/LX/thruster/drone_propeller_designs/toroidal_rov_thruster/prototype2A_M2_openFOAM
```

Your prompt changes. All commands below run inside this shell.

## Step 3: mesh

```bash
./Allclean          # removes any old mesh and logs
./Allmesh L0        # builds and checks the mesh; stops at the first failed check
```

What `Allmesh` does, in order:
1. `configure_mesh.py L0` fills the mesh templates: 16 mm background cells, 0.25 mm on the rotor, 0.5 mm on the stator, 1 mm around the rotor and 4 mm in the wake.
2. `validate_geometry.py` checks:
   - both STLs are closed, outward-facing and in metres;
   - the rotor fits in 100 mm and has at least 2 mm tip gap;
   - the rotating zone keeps 0.5 mm from every surface.
   It then copies the STLs to `constant/triSurface/`.
3. `surfaceCheck` runs OpenFOAM's own check of each STL, including self-intersection.
4. `blockMesh` builds the background box of cubes.
5. `surfaceFeatureExtract` finds the sharp edges to keep: trailing edges, lips, strut edges.
6. `snappyHexMesh` refines cells near the surfaces, cuts the solids out and snaps cells onto the surfaces. This is the slow step.
7. `topoSet` marks the cells inside the rotating zone (`mrfZone`).
8. `checkMesh` must report "Mesh OK".

The result for this case is in `results/P2A_M2_mesh_L0.md`: cells, quality, time and memory.

Each step writes a `log.<step>` file. If a step fails, read its log, fix the cause, then run `./Allclean` before `./Allmesh` again: steps whose log already exists are skipped.

## Step 4: short direction check (about 300 iterations)

Before a long run, check that the thruster pushes water the right way:

```bash
./Allsolve 300
python3 scripts/convergence_report.py --window 100 --batches 3
```

Look for these three things. The numbers won't be converged yet; only the signs matter.

| Quantity | Expected |
|---|---|
| Assembly force | Negative: thrust toward −x |
| Shaft power | Positive |
| Jet | "+x (bellmouth intake, as designed)" |

## Step 5: full run

```bash
./Allsolve          # 5000 iterations on 6 cores (system/decomposeParDict)
python3 scripts/convergence_report.py --write results/P2A_M2_L0_forward.md
```

Design A needed 2.9 s per iteration at 2 M cells on this laptop. Scale that by this case's cell count to estimate the run time; at about 3 M cells, expect 6–7 hours.

The report averages the last 3000 iterations. It gives thrust (rotor and stator), torque, shaft power, flow, minimum wall pressure (cavitation) and y+, and ends with a verdict:
- CONVERGED;
- STATISTICALLY STEADY (oscillating about a stable mean; design A ended here);
- NOT CONVERGED.

If it isn't converged at 5000 iterations, raise `endTime` in `system/controlDict` while the solver is still running.

## Step 6: reverse thrust

Edit `constant/MRFProperties` and change `omega -314.159265359` to `omega 314.159265359`. Then repeat step 5 and write the report to `results/P2A_M2_L0_reverse.md`.

## Signs and frames

- **Frames:** the design frame is mm with the axis along +Z; this case is metres with the axis along +x, (x, y, z)_OF = 0.001 (z, y, −x).
- **Forward:** the rotor turns about −x, counter-clockwise seen from the inlet. The jet goes toward +x and the thrust on the thruster toward −x.
- **Force output:** `postProcessing/rotorForces` and `statorForces` give the force of the water on each part. Thrust is the negative of the total x force.
