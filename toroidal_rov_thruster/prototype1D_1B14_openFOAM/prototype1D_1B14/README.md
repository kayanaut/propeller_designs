# Prototype 1D — mesh-ready CFD case preparation (1B-14)

This package converts the screened **1B-14** design point into a reproducible OpenFOAM meshing and steady-MRF case template. It does **not** infer blade coordinates from the supplied photograph. The exact watertight 1B-14 rotor and duct STL files must be placed in `geometry/` using the filenames below.

## Locked design point

| Item | Value |
|---|---:|
| Rotor diameter | 0.100 m |
| Blade count | 3 |
| Loop axial rise | 0.0115 m |
| Duct throat diameter | 0.104 m |
| Loading scale | 1.00 |
| Rotation rate | 3000 rpm (314.159 rad/s) |
| Fluid | seawater, rho = 1025 kg/m3, nu = 1.05e-6 m2/s |
| Condition | bollard / zero inlet velocity |
| Target thrust | 35 N (objective, not a result) |

## Required geometry

Copy these watertight, metre-scaled STL files into `geometry/`:

- `rotor_1B14.stl` — rotor only, with outward normals.
- `duct_1B14.stl` — stationary duct only, with outward normals.

The rotation axis is **+x**, the hub is centred at `(0,0,0)`, and positive thrust is expected in **+x**. The case defines a cylindrical MRF zone of radius 0.0515 m and half-length 0.022 m. Its radius lies halfway across the nominal 2 mm rotor-to-duct radial gap.

Run `python3 scripts/validate_geometry.py` first. The validator rejects missing, non-finite, implausibly scaled, or out-of-envelope geometry. Watertightness and surface intersections must still be checked with `surfaceCheck` and visual inspection.

## Mesh levels

| Level | Base cell | Rotor surface | Duct surface | Gap region | Intended use |
|---|---:|---:|---:|---:|---|
| L0 | 8 mm | level 5 | level 4 | level 5 | topology/debug |
| L1 | 6 mm | level 6 | level 5 | level 6 | first quantitative run |
| L2 | 4 mm | level 7 | level 6 | level 7 | convergence check |

Nominal local cell widths at L1 are about 0.094 mm on the rotor and 0.188 mm on the duct. Cell counts depend strongly on STL complexity. Start with L0, then retain identical physics and numerics for L1/L2.

## Prism-layer target

For SST with wall-resolved treatment, target `y+ <= 1`:

- first layer: 0.020 mm
- 12 layers
- expansion ratio: 1.20
- nominal total thickness: 0.79 mm

This is a starting estimate. Recalculate the first-layer height from the first solution's wall shear and report area-weighted and 95th-percentile y+ separately for rotor and duct.

## Run sequence

1. Install OpenFOAM v10+ or a compatible Foundation release.
2. Add the two exact STLs and run `python3 scripts/validate_geometry.py`.
3. Run `./Allrun L0`.
4. Inspect mesh quality, surface capture, gap resolution, cell zones, and layer coverage.
5. Repeat with `./Allclean && ./Allrun L1`, then L2.
6. Compare thrust and torque across L0/L1/L2. Accept mesh independence only when both change by <2% from L1 to L2 and local pressure/vortex fields are qualitatively stable.

`Allrun` deliberately stops on missing geometry, failed `surfaceCheck`, absent MRF cells, or failed `checkMesh`. No CFD result is included.

## Boundary and region model

- `inlet`: zero-velocity bollard boundary, zero-gradient pressure.
- `outlet`: zero-gradient velocity, fixed pressure reference.
- `farfield`: slip wall to limit blockage bias.
- `rotor`: moving-wall velocity from the MRF rotation.
- `duct`: stationary no-slip wall.
- `mrfZone`: cell zone selected inside the cylindrical volume; MRF is active only in that zone.

The outer domain is 0.60 m long and 0.40 m square (6D axial, 4D transverse). The rotor centre is 0.20 m downstream of the inlet. This is intentionally conservative for bollard thrust; enlarge the domain if farfield pressure or velocity is visibly disturbed.

## Reported quantities

Use `forces` output to record rotor and duct contributions separately. Report:

- rotor thrust, duct thrust, and total thrust;
- rotor torque about x;
- shaft power `P = omega Q`;
- `T/P` at bollard;
- minimum pressure and cavitation margin;
- y+ distributions and layer coverage;
- cell count and mesh-level convergence.

Reverse rotation is a separate case: change the sign of `omega` and re-converge. A steady MRF solution cannot quantify blade-passing force ripple; use a later sliding-mesh transient case for that objective.

