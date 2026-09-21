# Toroidal ROV thruster

A ducted toroidal-bladed thruster for a small ROV, built around a
[Blue Robotics M200](https://bluerobotics.com/store/thrusters/motors/m200-motor-r1/) motor
and intended for resin printing. This is the repository's one complete design: carried from
parameters through CAD, geometric checks and CFD, with its mistakes left visible.

> **Status: UNVALIDATED.** Nothing here has been printed, and no thrust has ever been
> measured. The CFD numbers below come from a steady MRF run that was stopped before
> convergence, on one mesh, never compared with any measurement. Use them to compare
> options, not to predict performance.

## What is here

| Folder | What it is |
|---|---|
| [`toroidal_rov_prototype2A/thruster_proto2A/`](toroidal_rov_prototype2A/thruster_proto2A/) | The current design, revision **P2A-M2**. Parametric CadQuery source, checks, reports and docs. |
| [`prototype2A_M2_openFOAM/`](prototype2A_M2_openFOAM/) | The OpenFOAM v2412 case for M2, and the archived results of the forward run. |
| [`prototype1D_1B14_openFOAM/`](prototype1D_1B14_openFOAM/) | The earlier 1B-14 case, kept for its baseline (design A) which every later number is compared against. |

## Where it stands

| | |
|---|---|
| Rotor | Constant P/D 0.75 on a true helix, symmetric NACA sections, **no camber** |
| Motor | Blue Robotics M200, flooded, Kv 470, 390 W at 16 V |
| Diameter | ~100 mm envelope; tip clearance 2.13 mm (2.1% of D) |
| CAD gates | All pass — see [`docs/RELEASE_STATUS.md`](toroidal_rov_prototype2A/thruster_proto2A/docs/RELEASE_STATUS.md) |
| CFD, forward | 29.1 N, 0.413 N·m, 130 W, 0.225 N/W at 3000 rpm — **NOT CONVERGED**, stopped at iteration 4467 |
| Cavitation | Lowest rotor wall pressure −180 kPa at the loop apex: vapour predicted shallower than about 8 m |
| Physical test | **None** |

## The known problems

Kept here because they are more instructive than the result:

1. **The pitch datum does not match the repository's own convention.** `CONVENTIONS.md`
   specifies face pitch; the rotor applies the angle to the chord line. Its `P/D = 0.75` is
   therefore not comparable with a Ka-series `P/D = 0.75`.
2. **The sections have no camber.** A symmetric section must be tilted to make lift, which
   is the direct cause of the −180 kPa suction peak at the loop apex.
3. **Tip clearance is 2.1% of D**, against 0.6% in this repository's ducted-kort brief.
4. **The duct is an invented foil**, not the 19A ordinates the repository has transcribed
   and committed.
5. **No baseline.** Nothing has been built to a published design and measured, so there is
   nothing to calibrate any of this against.

The datums these depart from are defined in
[cad/CONVENTIONS.md](../../cad/CONVENTIONS.md), and the working equations in
[formulas.md](../../formulas.md).

## Running it

Build the CAD (needs CadQuery):

```bash
cd toroidal_rov_prototype2A/thruster_proto2A
python3 source/run_all.py            # builds every part and runs every gate
python3 source/export_cfd.py         # writes the CFD surfaces
```

The numeric blade gates run without a CAD kernel:

```bash
python3 source/rotor.py --check-only
```

The vendor motor STEP is not in this repository. Without it the build falls back to a
parametric M200 and skips the interface cross-check; to get it, run
[`fetch_m200_cad.py`](fetch_m200_cad.py).

For the CFD, see [`prototype2A_M2_openFOAM/RUN_GUIDE.md`](prototype2A_M2_openFOAM/RUN_GUIDE.md).
Solves take hours on a laptop.

## What would move this forward

1. Print the hub fit coupon and check it on a real M200.
2. Build a bollard rig and measure thrust against rpm. Any measurement beats none.
3. Reduce the apex suction peak (lighter loading, or more thickness/chord there) and
   recheck the minimum pressure.
4. The reverse run, and a run near 3300 rpm for the 35 N target.
