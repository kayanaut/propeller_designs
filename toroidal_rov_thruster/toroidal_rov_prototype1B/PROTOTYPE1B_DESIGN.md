# Prototype 1B — CFD-driven optimization candidate

Reference motor point: **24 V, 300 W, 3000 rpm**; target **35 N static thrust**; D=100 mm; 3 blades.

**Important:** this package contains a CFD-ready candidate and a parameter sweep, but no CFD solver was available in the execution environment. Therefore 1B is a **pre-CFD optimization candidate**, not a measured or simulated performance result.

## 1B changes from 1A

- Throat ID reduced from 106 to **104 mm** to strengthen duct loading while retaining a practical 2 mm radial rotor-to-duct gap.
- Duct length increased to **38 mm** and inlet bellmouth length to **12 mm** for smoother inflow acceleration.
- Loop axial rise increased to **11.5 mm** and helical component increased to **11°** to provide useful blade loading without an abrupt closure.
- Skew reduced to **7°** and closure is biased slightly aft to reduce a sharp leading/trailing-edge interaction.
- Chord range shifted to **12.5–19.0 mm**, with mild outboard loading and root strengthening.
- Section remains **NACA 0016 symmetric** for useful reverse operation.

## DOE for actual CFD

Run the attached 27-case matrix at 3000 rpm, static first. Factors:

| Factor | Low | Mid | High |
|---|---:|---:|---:|
| Loop axial rise (mm) | 8.5 | 11.5 | 14.5 |
| Duct throat ID (mm) | 102 | 104 | 106 |
| Loading / pitch scale | 0.92 | 1.00 | 1.08 |

For each case record thrust T, torque Q, shaft power, minimum pressure, duct separation area, and force ripple. Rank by:

1. static **T/P**;
2. ability to meet **35 N** without excessive torque;
3. minimum pressure / cavitation margin;
4. reverse thrust;
5. force ripple / noise proxy.

## CFD setup

Use seawater, rho=1025 kg/m^3 and mu=1.08e-03 Pa s. Start with steady MRF, k-omega SST, y+≈1. Domain: ~5D upstream, 10D downstream, radius 5D. Then validate the best 2–3 designs with transient sliding mesh.

At 3000 rpm, the 35 N objective corresponds to CT≈**0.137**. The 300 W electrical point is an electrical budget, not a direct shaft-power guarantee. Torque from electrical power is therefore only a reference scaling value (0.955 N m); measured ESC/motor efficiency must be applied for final shaft-power matching.

## Test acceptance

Do not run at 3000 rpm before low-speed balance and integrity checks. Print in a continuous-fiber/engineering nylon or MJF/SLS-grade material where practical; use the stainless insert for the shaft interface.
