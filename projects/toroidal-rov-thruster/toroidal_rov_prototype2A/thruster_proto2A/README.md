# Toroidal ROV thruster — P2A-M2

**Parametric fit-test revision of P2A, built around the Blue Robotics M200 motor. Fit and assembly testing only.**

> **UNVALIDATED.** Nothing here has been printed and no thrust has been measured.
> The CFD result quoted anywhere in this package comes from a run that was stopped
> before convergence and has never been compared with a measurement.

M2 starts from the P2A-M1 package. The blade, duct and support concept are unchanged from M1. The motor interface is rebuilt around the real M200: its drawing and the vendor STEP.

| Area | M1 | M2 |
|---|---|---|
| Motor | Placeholder outrunner (can Ø50) | Blue Robotics M200: can Ø36 × 29, base Ø40 × 25.5, Kv 470, 390 W at 16 V |
| Rotor to motor | 4× M3 on a 16 mm circle, plain pilot bore | 2× M3 × 25 into the M200 rotor face (Ø19.05 circle); collar counterbore; D-bore on the shaft flat for positive drive |
| Motor vents | — | Two Ø4.5 passages through the hub and clamp ring, lined up with the M200's two vents |
| Shroud | Bore sized from the can only | Bore is a slide fit on the M200 base, which centres the motor on the duct; 2.3 mm clearance to the spinning can |
| Cable | Rear centre hole | Radial hole with strain-relief boss where the M200 cable leaves its base |
| Rear plate | 4× M3 on a placeholder pattern | 4× M3 × 8 into the M200 base inserts (21.2 mm square), counterbored; drain hole |
| Coupon | Plain bores | Copies of the real hub interface (collar, round bore, D-bore) plus M3 holes |
| Checks | Placeholder motor | Vendor STEP cross-checked against the parameters; zero overlap with the vendor motor; vent, collar, flat and screw-depth checks |

The blade is unchanged from M1: constant P/D 0.75 on a true helix, NACA sections, apex solved to the 100 mm envelope. Compared with M0, M1 fixed the pitch law (M0 ran from P/D 0.55 to 7.8), thinned the sections and tightened the tip gap from 3 to 2 mm.

**Forward thrust:** the rotor turns counter-clockwise seen from the inlet, and water leaves past the motor support.

## Start here

1. `docs/ROADMAP.md` shows where the project stands and what comes next. `docs/RELEASE_STATUS.md` lists every check.
2. Look at `previews/` (assembly, section, axial, rotor, exploded) and `previews/blade_distribution.png`.
3. Open `exports/assembly_with_reference_hardware.step` in a CAD viewer to see the parts on the vendor M200 model.
4. Print `hub_fit_coupon` first, in the resin and orientation you'll use for the rotor, and test it on a real M200. See `docs/COUPON.md`.

## Folder contents

| Folder | Contents |
|---|---|
| `source/` | `parameters.json`; `rotor.py` (blade and hub), `build.py` (other parts), `motor_step.py` (vendor STEP alignment and cross-check), `hardware.py`, `export_cfd.py`; checks and packaging |
| `exports/` | STEP, STL, 3MF and BREP for the four printed parts; `REFERENCE_*` meshes; assembly STEPs; `cfd/` surfaces for OpenFOAM |
| `hardware/` | Aligned M200, clamp ring and screws; `vendor/` holds Blue Robotics' original M200 CAD download |
| `previews/` | Actual-CAD images and the blade section chart |
| `reports/` | Motor interface, blade table, build, mesh, clearance, stack and self-interference reports, logs |
| `docs/` | Roadmap, release status, assembly, hardware list, resin print preparation, coupon, parameters, open inputs |
| `slicer/`, `machine_output/` | Unconfirmed resin process inputs; no fabricated slicer output |

The OpenFOAM case for this revision is `../../prototype2A_M2_openFOAM/`.

## Printable parts

Print only these: `rotor`, `duct_full`, `motor_support`, `hub_fit_coupon`. Never print `REFERENCE_*` files as working parts.

All coordinates are **millimetres** and the rotation axis is **+Z**; water enters at −Z. STEP and STL keep assembly coordinates. Each 3MF declares millimetres and moves its part onto z = 0 without scaling.

## Edit and rebuild

Use Python 3.12 with the packages in `requirements.txt`. Run from this folder:

```bash
python -m pip install -r requirements.txt
python source/rotor.py --check-only    # blade gates in under a second, no CAD
python source/run_all.py               # motor check, build, export, render and check everything
python source/package_release.py       # release status, index, manifest and ZIP
python source/export_cfd.py            # CFD surfaces, copied into the OpenFOAM case
```

A rebuild overwrites `exports/`, `reports/` and `previews/`. `motor_step.py` stops the build if the vendor M200 STEP and `parameters.json` disagree by more than 0.1 mm or 0.5°. `package_release.py` refuses to package unless every gate passes, and names the ZIP after the revision. Parameter meanings are in `docs/PARAMETERS.md`.

No CFD result, structural analysis, balance test, submerged test or calibrated resin profile is included yet.
